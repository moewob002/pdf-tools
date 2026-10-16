import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

import { THEME_STORAGE_KEY, readStoredTheme, resolveTheme, storeTheme } from "../src/utils/theme.js";

test("explicit choice wins over the OS preference", () => {
  assert.equal(resolveTheme("light", true), "light");
  assert.equal(resolveTheme("dark", false), "dark");
});

test("without a choice the OS preference is used", () => {
  assert.equal(resolveTheme(null, true), "dark");
  assert.equal(resolveTheme(null, false), "light");
  assert.equal(resolveTheme("garbage", true), "dark");
});

test("storage errors are tolerated", () => {
  const blocked = { getItem() { throw new Error("blocked"); }, setItem() { throw new Error("blocked"); } };
  assert.equal(readStoredTheme(blocked), null);
  assert.doesNotThrow(() => storeTheme(blocked, "dark"));
  const map = new Map();
  const ok = { getItem: (k) => map.get(k) ?? null, setItem: (k, v) => map.set(k, v) };
  storeTheme(ok, "dark");
  assert.equal(readStoredTheme(ok), "dark");
});

test("the no-flash boot script in index.html uses the same storage key", () => {
  const html = readFileSync(new URL("../index.html", import.meta.url), "utf8");
  assert.ok(html.includes(`localStorage.getItem("${THEME_STORAGE_KEY}")`));
  assert.ok(html.indexOf("data-theme") < html.indexOf('src="/src/main.js"'), "theme must be set before the app loads");
});
