// Run with `npm test` (Node's built-in test runner; no extra dependencies).
import { test } from "node:test";
import assert from "node:assert/strict";

import { getErrorMessage } from "../src/utils/errors.js";
import { matchesAccept, partitionFiles } from "../src/utils/files.js";
import { formatSize } from "../src/utils/format.js";
import { buildMergeRequest, diffSources, withoutSources } from "../src/utils/merge.js";
import { rangesFromPages } from "../src/utils/pages.js";
import { retryOnRateLimit } from "../src/utils/retry.js";

const blobError = (status, body) => ({
  response: { status, data: new Blob([JSON.stringify(body)], { type: "application/json" }) },
});

test("getErrorMessage reads detail from a Blob body (FUN-02 regression)", async () => {
  const msg = await getErrorMessage(blobError(400, { detail: "This PDF is password-protected." }), "Split failed");
  assert.equal(msg, "This PDF is password-protected.");
});

test("getErrorMessage reads detail from a JSON body", async () => {
  assert.equal(await getErrorMessage({ response: { status: 400, data: { detail: "Bad" } } }), "Bad");
});

test("getErrorMessage falls back for non-JSON bodies and known statuses", async () => {
  const html = { response: { status: 413, data: new Blob(["<html>413</html>"]) } };
  assert.equal(await getErrorMessage(html, "x"), "The upload is too large.");
  assert.equal(await getErrorMessage({ response: { status: 500, data: "oops" } }, "Merge failed"), "Merge failed");
  assert.match(await getErrorMessage({ response: { status: 429, data: {} } }), /Too many requests/);
});

test("getErrorMessage handles network errors and timeouts", async () => {
  assert.match(await getErrorMessage({ message: "Network Error" }), /Could not reach the server/);
  assert.match(await getErrorMessage({ code: "ECONNABORTED" }), /timed out/);
});

test("matchesAccept handles extensions, wildcards and exact types", () => {
  assert.equal(matchesAccept({ name: "a.PDF", type: "" }, ".pdf"), true);
  assert.equal(matchesAccept({ name: "a.txt", type: "text/plain" }, ".pdf"), false);
  assert.equal(matchesAccept({ name: "a.png", type: "image/png" }, "image/*"), true);
  assert.equal(matchesAccept({ name: "a.pdf", type: "application/pdf" }, "image/*"), false);
  assert.equal(matchesAccept({ name: "x", type: "application/pdf" }, "application/pdf"), true);
  assert.equal(matchesAccept({ name: "anything" }, ""), true);
});

test("partitionFiles reports why files were rejected (FUN-06 regression)", () => {
  const MB = 1024 * 1024;
  const files = [
    { name: "ok.pdf", type: "application/pdf", size: 10 },
    { name: "notes.txt", type: "text/plain", size: 10 },
    { name: "big.pdf", type: "application/pdf", size: 60 * MB },
    { name: "empty.pdf", type: "application/pdf", size: 0 },
  ];
  const { accepted, rejected } = partitionFiles(files, { accept: ".pdf", maxBytes: 50 * MB, typeLabel: "PDF" });
  assert.deepEqual(accepted.map((f) => f.name), ["ok.pdf"]);
  assert.deepEqual(
    rejected.map((r) => [r.file.name, r.reason]),
    [["notes.txt", "Not a supported PDF"], ["big.pdf", "Larger than 50MB"], ["empty.pdf", "File is empty"]],
  );
});

test("rangesFromPages compacts selections", () => {
  assert.equal(rangesFromPages([]), "");
  assert.equal(rangesFromPages([3, 1, 2, 5, 7, 8]), "1-3,5,7-8");
  assert.equal(rangesFromPages([4]), "4");
});

test("formatSize", () => {
  assert.equal(formatSize(512), "512 B");
  assert.equal(formatSize(2048), "2.0 KB");
  assert.equal(formatSize(5 * 1024 * 1024), "5.0 MB");
});

test("diffSources matches files by identity, not by name (FUN-05 regression)", () => {
  const a = { name: "scan.pdf" };
  const b = { name: "scan.pdf" }; // different file, same name
  const sources = [{ id: 1, file: a }];
  assert.deepEqual(diffSources(sources, [a, b]), { added: [b], removedIds: [] });
  assert.deepEqual(diffSources(sources, [b]), { added: [b], removedIds: [1] });
});

test("withoutSources drops pages of removed files (FUN-05 regression)", () => {
  const pages = [{ file_index: 1, page_num: 1 }, { file_index: 2, page_num: 1 }, { file_index: 1, page_num: 2 }];
  assert.deepEqual(withoutSources(pages, [1]), [{ file_index: 2, page_num: 1 }]);
});

test("buildMergeRequest re-indexes sources in first-use order", () => {
  const sources = [{ id: 10, file: "A" }, { id: 11, file: "B" }, { id: 12, file: "C" }];
  const pages = [
    { file_index: 12, page_num: 2 },
    { file_index: 10, page_num: 1 },
    { file_index: 12, page_num: 1 },
  ];
  assert.deepEqual(buildMergeRequest(pages, sources), {
    files: ["C", "A"],
    pageOrder: [
      { file_index: 0, page: 2 },
      { file_index: 1, page: 1 },
      { file_index: 0, page: 1 },
    ],
  });
});

test("retryOnRateLimit retries 429 then succeeds (FUN-04 regression)", async () => {
  let calls = 0;
  const waits = [];
  const result = await retryOnRateLimit(
    async () => {
      calls++;
      if (calls < 3) throw { response: { status: 429 } };
      return "ok";
    },
    { delays: [5, 10, 20], sleep: async (ms) => waits.push(ms) },
  );
  assert.equal(result, "ok");
  assert.deepEqual(waits, [5, 10]);
});

test("retryOnRateLimit gives up and does not retry other errors", async () => {
  const sleep = async () => {};
  await assert.rejects(
    retryOnRateLimit(async () => { throw { response: { status: 429 } }; }, { delays: [1], sleep }),
    (e) => e.response.status === 429,
  );
  let calls = 0;
  await assert.rejects(
    retryOnRateLimit(async () => { calls++; throw { response: { status: 400 } }; }, { delays: [1, 1], sleep }),
  );
  assert.equal(calls, 1);
});
