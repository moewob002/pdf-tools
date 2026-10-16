# PDF Tools — Project Audit

- **Audit date:** 2026-10-16
- **Audited revision:** `main` @ `a8d4718` ("add cryptography dependency for pypdf AES support")
- **Working branch:** `audit/pdf-tools-improvements`
- **Method:** full read of all 57 tracked files; every endpoint exercised with locally generated
  valid and invalid samples through FastAPI's `TestClient`; live uvicorn + `vite preview` +
  headless Chromium (driven over the DevTools protocol) for UI checks; measurements taken on
  the auditor's machine (Linux, Python 3.11.13, Node 26.8.1, Ghostscript, Poppler, Tesseract 5 with `eng` only).

Every finding below records whether it is a **verified defect** (reproduced by running code)
or a **potential risk** (from code inspection only). Performance items are marked
**measured** or **theoretical**.

---

## 1. Project overview

| Area | Finding |
|---|---|
| Languages | Python 3.11 (backend), JavaScript / Vue SFC (frontend) |
| Backend | FastAPI 0.115.6 on uvicorn; entry `backend/app/main.py`; dev runner `backend/run.py` |
| Frontend | Vue 3.5 + vue-router 4 + axios, built with Vite 6, styled with Tailwind CSS 3; entry `frontend/src/main.js` |
| Split | SPA calls `/api/*`; in dev Vite proxies to `localhost:8000`; in Docker, nginx (`frontend/nginx.conf`) proxies `/api/` to the `backend` service |
| PDF libraries | pypdf (split/merge/delete/info/text extraction), pikepdf (compression fallback & post-processing), pdf2image → Poppler `pdftoppm` (rasterising), Ghostscript CLI (compression), pytesseract → Tesseract CLI (OCR), reportlab (OCR text layer), fpdf2 (DOCX→PDF), python-docx, Pillow |
| Manifests | `backend/requirements.txt` (pinned, except `cryptography>=3.1`); `frontend/package.json` (caret ranges). **No lockfile** for either side. |
| Build / deploy | `docker-compose.yml` (backend + nginx frontend, `temp_data` volume), two Dockerfiles, `config.env.example` |
| CI | None |
| Tests / lint / format | None configured |
| Generated artefacts | `backend/temp/` (job dirs), `frontend/dist/`, `node_modules/`, `__pycache__/` — all git-ignored |

### API routes

| Method | Route | Service |
|---|---|---|
| POST | `/api/convert/pdf-to-image` | `convert_service.pdf_to_images` → ZIP |
| POST | `/api/convert/image-to-pdf` | `convert_service.images_to_pdf` |
| POST | `/api/convert/pdf-to-word` | `convert_service.pdf_to_word` |
| POST | `/api/convert/word-to-pdf` | `convert_service.word_to_pdf` (no UI) |
| POST | `/api/edit/split` | `edit_service.split_pdf` → ZIP |
| POST | `/api/edit/merge` | `edit_service.merge_pdfs` (no UI) |
| POST | `/api/edit/merge-custom` | `edit_service.merge_custom_pages` |
| POST | `/api/edit/delete-pages` | `edit_service.delete_pages` |
| POST | `/api/edit/info` | `edit_service.get_pdf_info` (no UI) |
| POST | `/api/edit/thumbnails` | inline in route (base64 JPEGs in JSON) |
| POST | `/api/ocr/extract-text` | `ocr_service.extract_text_from_pdf` |
| POST | `/api/ocr/make-selectable` | `ocr_service.make_selectable_pdf` |
| GET | `/api/ocr/backends` | static |
| POST | `/api/compress` | `compress_service.compress_pdf` |
| GET | `/api/health` | static |

### PDF data flow

1. Browser `FileUpload.vue` keeps `File` objects in memory; views POST them as multipart via axios (`responseType: "blob"` for file results).
2. Route handler: `await file.read()` (whole file into memory) → size check against `MAX_FILE_SIZE` → extension check on the client-supplied filename.
3. Service: `create_temp_dir()` makes `backend/temp/<op>_<uuid12>/`; `save_upload()` writes the bytes as `<uuid8><ext>`; processing writes outputs into the same dir.
4. Route returns `FileResponse(path)` (or JSON). **Nothing is deleted after the response**; a background loop deletes entries older than `FILE_TTL` (24 h) every `CLEANUP_INTERVAL`.
5. Browser receives a `Blob`; `ResultCard.vue` creates an object URL and triggers the download.

### Feature status (code inspection + actual runs)

| Feature | Status | Evidence |
|---|---|---|
| PDF → images (PNG/JPG/TIFF) | **Working** | 200, ZIP with `page_N.png` |
| Images → PDF | **Working** for valid images; 500 on non-image | probe |
| PDF → Word | **Working** (text or rasterised pages) | 200 for text and scanned PDFs |
| Word → PDF | **Broken** for common inputs | drops all text when any image present; 500 on non-Latin-1 text and on `.doc` (FUN-07/08/09) |
| Split | **Working** for valid input; 500 for any invalid range | FUN-01 |
| Merge (custom order, UI) | **Incomplete** — silently loses pages when previews fail | FUN-04 (reproduced in browser) |
| Delete pages | **Working**; can emit a 0-page PDF | FUN-12 |
| Thumbnails | **Working**; unbounded DPI and memory | SEC-01, PERF-02 |
| OCR extract / make-selectable | **Working** (eng verified) | leaks internals on error (SEC-07) |
| Compress | **Working**; mislabels engine, can grow files, accepts garbage | FUN-10/11, SEC-10 |
| Nav "Convert" link | **Broken** — `/convert` has no route, renders an empty page | FUN-03 (reproduced in browser) |
| Error display in UI | **Broken** for every file-returning call | FUN-02 (reproduced in browser) |
| Rate limiting | **Incomplete** — ignores config; bypassable | SEC-03/04 |

---

## 2. Baseline results (before any change)

| Check | Command | Result |
|---|---|---|
| Frontend build | `cd frontend && npm run build` | ✅ pass, 1.63 s; main chunk 111.45 kB (43.55 kB gz); `ResultCard` chunk 58.90 kB (22.02 kB gz, contains axios); CSS 21.81 kB |
| Backend compile | `python -m compileall -q app` | ✅ pass |
| Backend lint (no project config; ad-hoc) | `ruff check --isolated --select E,F app run.py` | 28 findings (10 E501 long lines, 9 F401 unused imports, 3 F841 unused vars, 4 F541, …) |
| Tests | — | none exist |
| Endpoint probe (valid + invalid samples) | scratch script, see §6 | 30 cases: 17 × 200 for valid input, **14 × 500** for invalid input, 1 info leak |
| Event-loop blocking | live uvicorn; `/api/health` polled during a 40-page 300-dpi PDF→PNG | **health blocked 8.00 s** (heavy request 8.31 s) — measured |
| Peak memory | `pdf_to_images(40 pages, 300 dpi)` direct call | **3 032 MB RSS** — measured |
| Merge in browser | 7 × 3-page PDFs uploaded together | UI offered **17 pages instead of 21** — measured |

Invalid-input probe (original code):

| Case | Status |
|---|---|
| split `pages=abc` / out of range / reversed `3-1` | 500 / 500 / 500 |
| split garbage / truncated / empty / encrypted PDF | 500 ×4 |
| delete `pages=x` | 500 |
| delete all pages | 200, **0-page PDF** |
| merge with a garbage PDF | 500 |
| merge-custom `page_order=[1,2]` / `file_index:"a"` | 500 / 500 |
| merge-custom only invalid refs | 200, **0-page PDF** |
| thumbnails garbage / `dpi=0` | 500 / 200 |
| pdf-to-image garbage | 500 |
| image-to-pdf non-image bytes | 500 |
| pdf-to-word garbage | 500 |
| word-to-pdf unicode text / `.doc` | 500 / 500 |
| word-to-pdf text + image | 200, **text silently dropped** |
| compress garbage | **200**, returns a 2.7 kB Ghostscript artefact |
| compress filename `report_%d.pdf` | 200, Ghostscript wrote `compressed_report_1..3.pdf`; pikepdf fallback used but `X-Engine: ghostscript` |
| OCR `language=xyz` | 500 with `/usr/share/tessdata/xyz.traineddata …` in the body |

---

## 3. Findings

Legend — **Priority:** Critical / High / Medium / Low. **Effort:** Low / Medium / High.
**Type:** Verified defect / Potential risk. **Plan:** *Proceeding* (pre-approved) or *Needs approval*.
The **Status** line is updated as work completes; the original text above it is unchanged.

### 3.1 Security

#### SEC-01 — Unbounded rasterisation DPI
- **Location:** `backend/app/api/edit.py` (`/thumbnails`, `dpi`), `backend/app/api/convert.py` (`/pdf-to-image`, `dpi`)
- **Evidence:** `dpi` is passed straight to `pdftoppm`. `dpi=0` returned 200; no upper bound exists. A single A4 page at 300 dpi is ~26 MB of RGB; memory grows with dpi².
- **Impact:** one request with a large `dpi` can exhaust server memory/CPU (DoS).
- **Fix:** validate `dpi` to a range that covers every value the UI sends (72–300) with headroom: 36–600; reject others with 400.
- **Priority:** High · **Effort:** Low · **Type:** Verified defect (no bound) / potential DoS · **Plan:** Proceeding
- **Status:** ✅ Fixed in `6048566` — DPI limited to 36–600 on `/thumbnails` and `/pdf-to-image`; regression test `DpiTests`.

#### SEC-02 — No page-count, file-count or total-upload limits
- **Location:** all routes; `merge`/`merge-custom`/`image-to-pdf` accept unlimited files.
- **Evidence:** only a per-file 50 MB check after `await file.read()`. A small PDF can have thousands of pages; OCR renders each at 300 dpi.
- **Impact:** resource exhaustion; long-running requests.
- **Fix:** add `MAX_PAGES`, `MAX_FILES` config with sensible defaults.
- **Priority:** High · **Effort:** Low · **Type:** Potential risk · **Plan:** **Needs approval** (new configuration contract; may reject requests that work today)
- **Status:** **Not implemented — awaiting approval.**

#### SEC-03 — Rate limiter trusts `X-Forwarded-For`
- **Location:** `backend/app/middleware.py` `_get_client_ip`
- **Evidence:** the endpoint probe rotated `X-Forwarded-For` per request and was never limited; with a fixed value the 6th request got 429.
- **Impact:** any client can bypass rate limiting. The backend port is also published directly in `docker-compose.yml`, so the header is fully attacker-controlled.
- **Fix:** only honour the header from configured trusted proxies (e.g. `TRUSTED_PROXIES`), otherwise use the socket peer address; stop publishing the backend port.
- **Priority:** Medium · **Effort:** Low · **Type:** Verified defect · **Plan:** **Needs approval** (deployment/config contract)
- **Status:** **Not implemented — awaiting approval.** README now documents the caveat (`46217d3`).

#### SEC-04 — Rate-limit configuration is ignored
- **Location:** `backend/app/middleware.py` (hard-coded `RATE_LIMIT_MAX = 5`, `PROCESSING_MIN_DELAY = 1.0`); `backend/app/config.py` reads `RATE_LIMIT_DELAY`/`RATE_LIMIT_MAX` but nothing imports them.
- **Evidence:** `grep` shows no import of `config.RATE_LIMIT_*`; README and `config.env.example` document them as effective.
- **Impact:** operators cannot tune limits; documented contract not honoured.
- **Fix:** read the values from `config.py`. Defaults are identical, so default behaviour is unchanged.
- **Priority:** Medium · **Effort:** Low · **Type:** Verified defect · **Plan:** Proceeding
- **Status:** ✅ Fixed in `dd55cb4` — middleware reads `RATE_LIMIT_MAX`/`RATE_LIMIT_DELAY`; test `test_defaults_come_from_config`.

#### SEC-05 — Rate-limiter state grows without bound
- **Location:** `backend/app/middleware.py` (`self.requests`, `self.last_request`)
- **Evidence:** entries are never removed for IPs that stop sending requests.
- **Impact:** slow memory growth; amplified by SEC-03 (arbitrary spoofed IPs).
- **Fix:** drop empty/expired entries during dispatch.
- **Priority:** Low · **Effort:** Low · **Type:** Potential risk · **Plan:** Proceeding
- **Status:** ✅ Fixed in `dd55cb4` — idle clients swept once per window; test `test_idle_clients_are_forgotten`.

#### SEC-06 — Uploaded PDFs and results kept on disk for 24 h
- **Location:** `backend/app/utils/file_utils.py`, every service, every route
- **Evidence:** one probe run left 38 job dirs (2.9 MB) in `backend/temp/`, each containing the user's original upload; failed jobs are also left behind.
- **Impact:** user documents persist on the server long after download (privacy); disk exhaustion under load.
- **Fix:** delete the job directory once the response has been sent (Starlette background task) and on failure; keep the TTL sweeper as a safety net.
- **Priority:** High · **Effort:** Low · **Type:** Verified defect · **Plan:** Proceeding
- **Status:** ✅ Fixed in `c24079b` — job dirs removed after the response, after JSON results and on errors; `backend/temp/` was empty after the full test suite, the 30-case probe and 15 browser workflows. Tests in `test_temp_files.py`.

#### SEC-07 — OCR errors leak internal details
- **Location:** `backend/app/api/ocr.py` (`f"OCR processing failed: {str(e)}"`)
- **Evidence:** `language=xyz` returned the Tesseract data path and TESSDATA hint to the client.
- **Impact:** information disclosure (paths, tool versions).
- **Fix:** log the exception server-side; return a generic message.
- **Priority:** Medium · **Effort:** Low · **Type:** Verified defect · **Plan:** Proceeding
- **Status:** ✅ Fixed in `6048566` — generic messages, server-side logging; test `test_unknown_language_rejected_without_leaking`.

#### SEC-08 — OCR `language` not validated
- **Location:** `backend/app/api/ocr.py`, `backend/app/ocr/tesseract_backend.py`
- **Evidence:** free text is passed to `tesseract -l`. No shell is used (pytesseract builds an argv list), so this is not command injection, but arbitrary values reach the CLI.
- **Impact:** 500s and error leakage; unexpected traineddata lookup.
- **Fix:** accept only codes from the backend's supported list (allowing `+` combinations); return 400 otherwise.
- **Priority:** Medium · **Effort:** Low · **Type:** Potential risk · **Plan:** Proceeding
- **Status:** ✅ Fixed in `6048566` — allow-list with `+` combinations; unavailable language data gives a clear 422.

#### SEC-09 — User-controlled text in server-side output paths
- **Location:** `compress_service.py` (`compressed_{filename}` passed to Ghostscript `-sOutputFile`), `ocr_service.py` (`selectable_{filename}`), `edit_service.py` (`removed_{page_ranges}.pdf`)
- **Evidence:** an upload named `report_%d.pdf` made Ghostscript treat `%d` as a page template and write `compressed_report_1..3.pdf`; the expected file was missing, so the pikepdf fallback ran silently. Ghostscript also gives `%` special meaning at the start of an output path (e.g. `%pipe%`); here the job-dir prefix prevents that, but the pattern is fragile. `Path(name).name` prevents directory traversal.
- **Impact:** wrong engine used, stray files, fragile path handling.
- **Fix:** use fixed internal file names; the download name stays derived from the user's file name.
- **Priority:** Medium · **Effort:** Low · **Type:** Verified defect · **Plan:** Proceeding
- **Status:** ✅ Fixed in `c24079b` — fixed internal names, sanitised upload suffixes; `report_%d.pdf` now compresses with Ghostscript (test `test_percent_in_filename_does_not_break_ghostscript`).

#### SEC-10 — Uploads not validated by content
- **Location:** all routes (extension check on client filename only; images checked by client `Content-Type` only)
- **Evidence:** 4 kB of random bytes named `.pdf` were "compressed" with HTTP 200; garbage everywhere else produced 500.
- **Impact:** misleading results; untrusted bytes reach Ghostscript/Poppler unchecked.
- **Fix:** one central validator: open the PDF with pypdf (reject unreadable, empty or encrypted files with 400) and decode images with Pillow before processing.
- **Priority:** Medium · **Effort:** Low · **Type:** Verified defect · **Plan:** Proceeding
- **Status:** ✅ Fixed in `6048566` — PDFs parsed and images decoded before processing; garbage now gets 400.

#### SEC-11 — CORS wildcard with credentials
- **Location:** `backend/app/main.py`
- **Evidence:** `allow_origins=["*"]`, `allow_credentials=True`. The app has no cookies or auth, and the UI is same-origin (Vite proxy / nginx).
- **Impact:** low today; would become serious if auth were added.
- **Fix:** set `allow_credentials=False` (no behaviour change for the bundled UI).
- **Priority:** Low · **Effort:** Low · **Type:** Potential risk · **Plan:** Proceeding
- **Status:** ✅ Fixed in `afd68a3`. Verification on the original code showed `https://evil.example` reflected with credentials allowed, so this was a verified defect rather than only a potential risk.

#### SEC-12 — Deployment hardening
- **Location:** `backend/Dockerfile` (runs as root), `backend/run.py` (`reload=True` on `0.0.0.0`), `docker-compose.yml` (publishes backend port, bypassing nginx's 50 MB body limit)
- **Impact:** larger blast radius if a parser bug is exploited; dev server exposed on the LAN.
- **Fix:** non-root user, drop the backend port mapping, bind dev server to 127.0.0.1.
- **Priority:** Medium · **Effort:** Low · **Type:** Potential risk · **Plan:** **Needs approval** (infrastructure)
- **Status:** **Not implemented — awaiting approval.**

#### SEC-13 — No authentication
- **Location:** whole API. Acceptable for a single-user self-hosted tool, but anyone who can reach the port can use CPU-heavy endpoints.
- **Priority:** Low · **Effort:** Medium · **Type:** Potential risk · **Plan:** **Needs approval** (new feature) — documented only
- **Status:** **Not implemented — awaiting approval.**

#### SEC-14 — Dependency vulnerabilities not checked; versions are old
- **Location:** `backend/requirements.txt`, `frontend/package.json`
- **Evidence:** `pip list --outdated` / `npm outdated` (see §3.5). `pip-audit`/`npm audit` were **not run**: they send the dependency list to an external service, which this task's constraints exclude. From memory (unverified): Starlette < 0.47.2 and < 0.49.1 had published DoS advisories (multipart handling; `FileResponse` Range parsing — this app uses `FileResponse`), and pypdf received several malformed-PDF resource-exhaustion fixes after 5.1.0.
- **Fix:** run `pip-audit -r backend/requirements.txt` and `npm audit` locally, then upgrade FastAPI/Starlette and pypdf.
- **Priority:** High · **Effort:** Medium · **Type:** Potential risk · **Plan:** **Needs approval** (dependency changes)
- **Status:** **Not implemented — awaiting approval.** Run `pip-audit -r backend/requirements.txt` and `cd frontend && npm audit` locally first.

XSS: no `v-html`, `innerHTML` or `eval` in the frontend; Vue escapes interpolations; filenames are rendered as text. CSRF: not applicable (no cookies or session auth). Secrets: none found in code, config or history. Logging: there is none, so no secrets are logged.

### 3.2 Functionality

#### FUN-01 — Invalid input returns HTTP 500
- **Location:** all routes/services (no exception mapping; `_parse_page_ranges` raises bare `ValueError`; `split_pdf` raises `ValueError` the route never catches)
- **Evidence:** 14 × 500 in the baseline probe (§2).
- **Impact:** users see "Internal Server Error"; real server faults are indistinguishable from bad input.
- **Fix:** central error handling — a `UserInputError` → 400, PDF/image parse errors → 400 with a clear message, unexpected errors → logged and returned as a generic 500.
- **Priority:** High · **Effort:** Medium · **Type:** Verified defect · **Plan:** Proceeding
- **Status:** ✅ Fixed in `6048566` — re-running the baseline probe: **0 × 500** (was 14); valid requests return byte-for-byte the same sizes as before.

#### FUN-02 — UI never shows server error messages for file operations
- **Location:** every view using `responseType: "blob"` (`e.response?.data?.detail` is always `undefined` because `data` is a `Blob`)
- **Evidence:** in the browser, split with `pages=abc` showed "Split failed".
- **Impact:** users cannot tell what went wrong (e.g. "too large", "encrypted").
- **Fix:** shared `getErrorMessage()` that reads JSON out of a Blob error body.
- **Priority:** High · **Effort:** Low · **Type:** Verified defect · **Plan:** Proceeding
- **Status:** ✅ Fixed in `890ea54` — browser check: split with `abc` now shows "Invalid page range 'abc'. Use numbers and ranges like 1-3,5."

#### FUN-03 — "Convert" navigation leads to an empty page
- **Location:** `frontend/src/App.vue` (`/convert` link), `frontend/src/main.js` (no `/convert` route, no catch-all)
- **Evidence:** headless browser on `/convert`: `<main>` contained 0 characters.
- **Fix:** add a Convert hub (mirrors the existing Edit hub) and a catch-all route that redirects to `/`.
- **Priority:** High · **Effort:** Low · **Type:** Verified defect · **Plan:** Proceeding
- **Status:** ✅ Fixed in `e90d96d` (Convert hub + catch-all redirect); redesigned in `9aac87e`.

#### FUN-04 — Merge silently drops pages when a preview fails
- **Location:** `frontend/src/views/MergeView.vue` (`catch (_) { newPages.push({ page_num: 1, … }) }`)
- **Evidence:** 7 × 3-page PDFs uploaded at once → rate limiter returned 429 for two thumbnail calls → UI showed "17 pages total" (expected 21); the merged PDF would be missing 4 pages with no warning.
- **Fix:** retry once on 429; if a preview still fails, mark that file as failed with a visible message and do not add a fake 1-page entry.
- **Priority:** High · **Effort:** Low · **Type:** Verified defect · **Plan:** Proceeding
- **Status:** ✅ Fixed in `890ea54` — browser check: 7 × 3-page PDFs now give 21 pages; failed files are listed, never faked.

#### FUN-05 — Merge file list and page list get out of sync
- **Location:** `MergeView.vue` `onFilesChange`
- **Evidence:** the handler only adds; removing a file in `FileUpload` leaves its pages in the merge. Files are de-duplicated by **name**, so two different files called `scan.pdf` are silently ignored.
- **Fix:** reconcile pages against the current file list by `File` identity.
- **Priority:** Medium · **Effort:** Low · **Type:** Verified defect (code path) · **Plan:** Proceeding
- **Status:** ✅ Fixed in `890ea54` — removing a file removes its pages (browser check: 21 → 18 pages, merge produced 18 pages from 6 files).

#### FUN-06 — Upload zone: silent rejection, no keyboard access, `accept` bypass
- **Location:** `frontend/src/components/FileUpload.vue`
- **Evidence:** oversize files are filtered out with no message; dropped files ignore `accept` (a `.txt` can be dropped onto a PDF tool); the "Click to upload" `<label>` has no `for`/`tabindex`, so keyboard users cannot open the picker; "+ Add more files" is shown on single-file tools, where it replaces the file.
- **Fix:** validate type and size on add and list rejected files with a reason; make the zone a real button; label single-file "Replace file".
- **Priority:** Medium · **Effort:** Low · **Type:** Verified defect · **Plan:** Proceeding
- **Status:** ✅ Fixed in `890ea54` and `9aac87e` — rejected files listed with reasons, keyboard Browse button, "Replace file" on single-file tools.

#### FUN-07 — Word → PDF discards all text if the document contains any image
- **Location:** `backend/app/services/convert_service.py` `word_to_pdf` (`if images: return await images_to_pdf(...)`)
- **Evidence:** DOCX with two paragraphs + one image → PDF whose extracted text is `''`.
- **Fix:** render text and images in document order.
- **Priority:** High · **Effort:** Medium · **Type:** Verified defect · **Plan:** **Needs approval** (changes PDF output)
- **Status:** **Not implemented — awaiting approval.**

#### FUN-08 — Word → PDF fails on non-Latin-1 text
- **Location:** `word_to_pdf` (fpdf2 core font Helvetica)
- **Evidence:** DOCX containing Cyrillic/CJK/curly quotes → 500.
- **Fix (now):** return a clear 422 explaining the limitation. **Fix (later):** embed a Unicode TTF font — needs approval (changes output, adds a font asset).
- **Priority:** Medium · **Effort:** Low (message) / Medium (font) · **Type:** Verified defect · **Plan:** Proceeding (message) / Needs approval (font)
- **Status:** ◐ Partly fixed in `6048566` — clear 422 message instead of a 500. Unicode font support: **Not implemented — awaiting approval.**

#### FUN-09 — `.doc` accepted but unsupported
- **Location:** `backend/app/api/convert.py` `word-to-pdf`
- **Evidence:** legacy `.doc` upload → 500 (python-docx reads only OOXML).
- **Fix:** reject `.doc` with a 400 explaining that only `.docx` is supported.
- **Priority:** Low · **Effort:** Low · **Type:** Verified defect · **Plan:** Proceeding
- **Status:** ✅ Fixed in `6048566` — `.doc` rejected with a 400 that names `.docx`.

#### FUN-10 — `X-Engine` reports Ghostscript when the pikepdf fallback ran
- **Location:** `compress_service.compress_pdf` (`gs_success` is reassigned to the fallback's result)
- **Evidence:** `%d` filename case: fallback produced the file, header said `ghostscript`.
- **Fix:** track the engine separately.
- **Priority:** Low · **Effort:** Low · **Type:** Verified defect · **Plan:** Proceeding
- **Status:** ✅ Fixed in `c24079b` — test `test_engine_header_reports_fallback`.

#### FUN-11 — Compression can return a larger file
- **Location:** `compress_service.compress_pdf`
- **Evidence:** a 2 538 B text PDF became 4 409 B (`X-Reduction-Percent: -73.7`) and the larger file was returned.
- **Fix:** return the original when the result is not smaller (and say so in the UI).
- **Priority:** Medium · **Effort:** Low · **Type:** Verified defect · **Plan:** **Needs approval** (changes PDF output)
- **Status:** **Not implemented — awaiting approval.** The UI now states "+N% larger" instead of "No change" (`9aac87e`).

#### FUN-12 — Operations can produce a 0-page PDF
- **Location:** `edit_service.delete_pages`, `edit_service.merge_custom_pages`
- **Evidence:** deleting pages `1-3` of a 3-page PDF, or a `page_order` with only invalid refs, returned 200 with a 0-page PDF. Invalid refs are skipped silently.
- **Fix:** reject with 400 ("cannot remove every page" / "page_order references no valid pages").
- **Priority:** Medium · **Effort:** Low · **Type:** Verified defect · **Plan:** **Needs approval** (changes processing results)
- **Status:** **Not implemented — awaiting approval.**

#### FUN-13 — Preview failures swallowed; stale errors
- **Location:** `OcrView.vue`, `PdfToImageViews.vue` (`catch (_) {}`), `SplitView.vue`/`DeleteView.vue` (error not cleared on a new file)
- **Evidence:** after uploading a garbage PDF then a valid one, "Failed to load preview" stayed on screen.
- **Fix:** show preview errors; clear the error when the file changes.
- **Priority:** Low · **Effort:** Low · **Type:** Verified defect · **Plan:** Proceeding
- **Status:** ✅ Fixed in `890ea54`; single-file status chips also reflect preview failures (`9aac87e`).

#### FUN-14 — Timeouts shorter than processing limits
- **Location:** `nginx.conf` `proxy_read_timeout 120s`, `api/index.js` axios `timeout: 120000`, Ghostscript `timeout=300`
- **Impact:** long compressions/OCR jobs fail at the proxy while the backend keeps working.
- **Fix:** align the timeouts, or move to async jobs.
- **Priority:** Medium · **Effort:** Low · **Type:** Potential risk · **Plan:** **Needs approval** (config/infrastructure)
- **Status:** **Not implemented — awaiting approval.**

#### FUN-15 — nginx body limit applies to the whole multipart request
- **Location:** `nginx.conf` `client_max_body_size 50M`
- **Impact:** merging several files (each < 50 MB) totalling > 50 MB fails with an nginx HTML 413 in Docker but works in dev.
- **Priority:** Medium · **Effort:** Low · **Type:** Potential risk · **Plan:** **Needs approval** (infrastructure)
- **Status:** **Not implemented — awaiting approval.**

#### FUN-16 — Endpoints without UI
- `word-to-pdf`, `merge` (sequential), `info` have no frontend. Adding UI is a new feature. **Plan:** Needs approval. **Priority:** Low.
- **Status:** **Not implemented — awaiting approval.**

#### FUN-17 — README inaccuracies
- **Location:** `README.md`
- **Evidence:** compress `quality` values documented as `low|medium|high|very_high` (code: `extreme|low|medium|high`); a non-existent `engine` parameter; `X-Engine` values `gs|pikepdf` (code: `ghostscript|pikepdf`); dev port documented as 5173 (Vite config: 3000); Docker instructions omit `cp config.env.example config.env` (compose's `env_file: config.env` fails without it); `make-selectable` endpoint undocumented.
- **Fix:** correct the docs.
- **Priority:** Low · **Effort:** Low · **Type:** Verified defect · **Plan:** Proceeding
- **Status:** ✅ Fixed in `46217d3`.

### 3.3 Architecture and maintainability

#### ARC-01 — Duplicated validation and error handling (backend)
- **Location:** `api/convert.py::_validate_file`, `api/edit.py::_validate_pdf`, inline copies in `api/ocr.py` (×2) and `api/compress.py`; the "max 50MB" text is hard-coded in 6 places regardless of `MAX_FILE_SIZE`.
- **Fix:** one `app/utils/validation.py` module + exception handlers in `main.py`.
- **Priority:** Medium · **Effort:** Low · **Type:** Verified · **Plan:** Proceeding
- **Status:** ✅ Fixed in `6048566` (`app/errors.py`, `app/utils/validation.py`).

#### ARC-02 — `async def` services doing blocking work
- **Location:** all `services/*.py` (declared `async`, but every call is synchronous CPU/subprocess/file I/O)
- **Fix:** make services plain functions and call them with `run_in_threadpool` from the routes (see PERF-01).
- **Priority:** High · **Effort:** Low · **Type:** Verified (measured) · **Plan:** Proceeding
- **Status:** ✅ Fixed in `24caf08`.

#### ARC-03 — Dead code
- **Location:** `frontend/src/views/ConvertView.vue` (313 lines, not routed), `frontend/src/components/PdfPreview.vue` (never imported; only user of `pdfjs-dist`); `convert_service.pdf_to_word` `if False else None` branch; unused imports/variables (ruff F401/F841: 12).
- **Fix:** remove the in-file dead code and unused imports now. Deleting the two unused component files (and with them the reason for `pdfjs-dist`) needs approval.
- **Priority:** Low · **Effort:** Low · **Type:** Verified · **Plan:** Proceeding (in-file) / Needs approval (file deletion)
- **Status:** ◐ In-file dead code and unused imports removed in `ede4930` (ruff F-findings 18 → 0). Deleting `ConvertView.vue`/`PdfPreview.vue`/`pdfjs-dist`: **Not implemented — awaiting approval.**

#### ARC-04 — Duplicated frontend logic
- **Location:** `rangesFromPages` (Split, Delete), `loadThumbnails` (4 views), `formatSize` (3 files), error extraction (11 sites), page-header markup (8 views)
- **Fix:** `src/utils/` helpers + shared components.
- **Priority:** Medium · **Effort:** Low · **Type:** Verified · **Plan:** Proceeding
- **Status:** ✅ Fixed in `890ea54` and `9aac87e` (`src/utils`, `src/api/thumbnails.js`, shared components).

#### ARC-05 — No logging; exceptions swallowed
- **Location:** `compress_service.py` (bare `except Exception: pass/continue/return False`), whole backend (no `logging`)
- **Fix:** module loggers; log unexpected errors in the central handler and the compression fallbacks.
- **Priority:** Low · **Effort:** Low · **Type:** Verified · **Plan:** Proceeding
- **Status:** ✅ Fixed in `ede4930` and `6048566` (Ghostscript/pikepdf fallbacks and unexpected errors are logged).

#### ARC-06 — No lockfile; Docker uses `npm install`
- **Location:** `frontend/` (no `package-lock.json`), `frontend/Dockerfile`; `requirements.txt` has `cryptography>=3.1`
- **Impact:** non-reproducible builds; an upstream compromise or regression ships silently.
- **Fix:** commit a lockfile, use `npm ci`, pin `cryptography`.
- **Priority:** Medium · **Effort:** Low · **Type:** Potential risk · **Plan:** **Needs approval** (dependency/infra change)
- **Status:** **Not implemented — awaiting approval.**

#### ARC-07 — Deprecated startup hook
- `@app.on_event("startup")` is deprecated in FastAPI in favour of `lifespan`. Works today. **Priority:** Low · **Plan:** Deferred (no functional benefit now).
- **Status:** Deferred (no functional benefit now).

### 3.4 Performance

#### PERF-01 — CPU-bound work blocks the event loop (measured)
- **Location:** all routes → `async` services; `/thumbnails` calls `convert_from_bytes` inline
- **Evidence:** live server, 40-page PDF → PNG @ 300 dpi: `/api/health` took **8.00 s** while the request ran.
- **Impact:** while one user converts, every other request (including health checks) stalls.
- **Fix:** run processing in Starlette's thread pool.
- **Priority:** High · **Effort:** Low · **Type:** Verified defect, **measured** · **Plan:** Proceeding
- **Status:** ✅ Fixed in `24caf08` — **measured**: `/api/health` max **0.02 s** (median 7 ms, 143 pings) during the same 40-page job (was 8.00 s). Test `test_health_responds_while_a_job_is_processing`.

#### PERF-02 — Every page bitmap held in memory at once (measured)
- **Location:** `convert_service.pdf_to_images`, `ocr_service.*` (300 dpi), `api/edit.py` thumbnails
- **Evidence:** `pdf_to_images` on a 40-page PDF @ 300 dpi peaked at **3 032 MB RSS**.
- **Fix:** rasterise one page at a time (`pdf2image.convert_from_path(first_page=n, last_page=n)`); output files are byte-identical because the same renderer and Pillow save calls are used.
- **Priority:** High · **Effort:** Low · **Type:** Verified, **measured** · **Plan:** Proceeding
- **Status:** ✅ Fixed in `24caf08` — **measured**: peak RSS **155 MB** (was 3 032 MB); wall time 8.8–9.3 s vs 7.9–10.9 s before (within noise). Outputs byte-identical (sha256) for pdf-to-image ×4 formats, thumbnails and OCR.

#### PERF-03 — Redundant copies of upload bytes (theoretical)
- **Location:** services call `save_upload()` then `pdf_path.read_bytes()` into `convert_from_bytes`, which writes yet another temp file.
- **Fix:** render from the saved path (part of PERF-02).
- **Priority:** Low · **Effort:** Low · **Type:** Potential, **theoretical** · **Plan:** Proceeding (with PERF-02)
- **Status:** ✅ Fixed in `24caf08` (render from the saved path).

#### PERF-04 — Uploads fully read before the size check (theoretical)
- **Location:** every route (`await file.read()` then `len(data)`)
- **Fix (now):** reject early using `UploadFile.size` when the multipart parser provides it. **Fix (later):** stream to disk instead of memory — larger refactor, needs approval.
- **Priority:** Low · **Effort:** Low · **Type:** Potential, **theoretical** · **Plan:** Proceeding (early check)
- **Status:** ◐ Early `UploadFile.size` check added in `6048566`; streaming uploads to disk: **Not implemented — awaiting approval.**

#### PERF-05 — Thumbnails for every page as base64 JSON (theoretical)
- **Location:** `/api/edit/thumbnails`; `PdfToImageViews.vue` shows 8 but fetches all.
- **Fix:** add `max_pages` / paging to the endpoint (API change → **needs approval**).
- **Priority:** Low · **Effort:** Medium · **Type:** Potential, **theoretical**
- **Status:** **Not implemented — awaiting approval.**

#### PERF-06 — Frontend bundle (measured)
- 111.45 kB main JS (43.55 kB gz) + lazily loaded route chunks. `pdfjs-dist` is not bundled (its only importer is dead code). No action needed.
- **Status:** No action needed. After the redesign: main JS 115.41 kB (45.08 kB gz, +1.5 kB gz), CSS 35.43 kB (6.77 kB gz, +2.1 kB gz) — measured.

### 3.5 Dependencies

| Package | Version | Used by | Classification |
|---|---|---|---|
| fastapi | 0.115.6 | app | used; **outdated** (0.143.x available) |
| starlette (transitive) | 0.41.3 | app | used; **outdated**; *possibly vulnerable* — verify with `pip-audit` (SEC-14) |
| uvicorn[standard] | 0.34.0 | server | used; outdated |
| python-multipart | 0.0.20 | FastAPI form parsing (runtime, implicit) | used; outdated |
| pypdf | 5.1.0 | edit/convert/ocr | used; **outdated** (6.x); *possibly vulnerable* to malformed-PDF DoS — verify |
| cryptography | >=3.1 (unpinned) | pypdf AES (runtime, implicit) | used; unpinned |
| pikepdf | 9.5.2 | compress | used; outdated |
| Pillow | 11.1.0 | convert/compress/ocr | used; outdated |
| pdf2image | 1.17.0 | convert/ocr/thumbnails | used; current |
| pytesseract | 0.3.13 | ocr | used; current |
| python-docx | 1.1.2 | pdf↔word | used; outdated |
| fpdf2 | 2.8.1 | word→pdf | used; **redundant** with reportlab (both generate PDFs) |
| reportlab | 4.2.5 | OCR text layer | used; outdated |
| vue / vue-router / axios | 3.5 / 4.6 / 1.20 (resolved) | frontend | used |
| pdfjs-dist | 4.10.38 | only `PdfPreview.vue` (never imported) | **unused** at runtime (checked: no dynamic import, not in the build output) |
| vite, @vitejs/plugin-vue, tailwindcss, postcss, autoprefixer | dev | build | used; vite/plugin-vue/tailwind have newer majors |

Removing `pdfjs-dist` or consolidating fpdf2/reportlab **needs approval**.

### 3.6 Testing

| Gap | Priority |
|---|---|
| No backend tests at all (unit, integration, API) | High |
| No frontend tests | Medium |
| No E2E tests | Medium |
| No CI to run build/tests | Medium (needs approval: infrastructure) |
| Untested edge cases: malformed/encrypted/empty PDFs, invalid ranges, huge DPI, non-Latin text, `%` in filenames, rate-limit interaction with multi-file merge | High |

**Plan (proceeding):** add a stdlib-`unittest` API regression suite under `backend/tests/` (runs with `python -m unittest` or pytest; needs `httpx` for FastAPI's `TestClient`, listed in a new `backend/requirements-dev.txt` and not installed in the runtime image), plus `node --test` unit tests for the extracted pure frontend helpers (no new npm dependency).

### 3.7 UI, accessibility and visual design

The project has a web UI, so Phase 4 applies.

| ID | Finding | Type | Priority |
|---|---|---|---|
| UI-01 | No design tokens: colours are hard-coded Tailwind utilities (`indigo-600`, `gray-500`, …) in every file | Verified | Medium |
| UI-02 | No dark theme; OS dark preference ignored (screenshot) | Verified | Medium |
| UI-03 | Upload zone not keyboard-operable; icon-only buttons (remove file, close modal, remove page, back) lack accessible names | Verified | High |
| UI-04 | Hover-only controls (remove page in merge, zoom on page tiles) are invisible to keyboard and touch users | Verified | Medium |
| UI-05 | Modal lacks `role="dialog"`, Escape handling and focus management | Verified | Medium |
| UI-06 | Page-selection tiles are clickable `<div>`s (not focusable; selection signalled by colour only) | Verified | High |
| UI-07 | Errors only in a red box; loading spinners lack `role="status"`; no live regions | Verified | Medium |
| UI-08 | Mobile header: brand wraps to two lines and nav is cramped at 375 px (screenshot) | Verified | Low |
| UI-09 | Workflow steps (upload → options → run → download) are not visually distinguished | Verified | Medium |
| UI-10 | No `prefers-reduced-motion` handling (`animate-spin`, `animate-pulse`, scale transforms) | Verified | Low |

**Status (UI-01 … UI-10):** ✅ Fixed in `ba7fbb5` (tokens, themes, shell) and `9aac87e` (components and views). Verified in headless Chromium at 320/375/1280 px in light and dark: no horizontal overflow on any route; Tab/Enter/Space/Escape paths; dialog focus trap and return; reduced-motion; WCAG AA contrast checked by `frontend/tests/contrast.test.js`.

**Plan:** Proceeding with the "Vibrant Color Systems & Chromatic Expression" redesign — CSS custom-property tokens wired into Tailwind, light/dark themes with a persisted toggle and no-flash boot script, accessible shared components, and contrast verified by script.

---

## 4. Proposed changes

### Proceeding now (pre-approved: bug fixes, hardening, tests, measured perf, redesign, docs)
1. **Backend validation & errors** — ARC-01, FUN-01, SEC-10, SEC-07, SEC-08, SEC-01, FUN-08 (message), FUN-09, PERF-04 (early check), ARC-05
2. **Temp-file lifecycle and paths** — SEC-06, SEC-09, FUN-10
3. **Event loop and memory** — PERF-01/ARC-02, PERF-02/PERF-03
4. **Rate limiter and CORS** — SEC-04, SEC-05, SEC-11
5. **Backend regression tests** — §3.6
6. **Frontend bug fixes** — FUN-02, FUN-03, FUN-04, FUN-05, FUN-06, FUN-13, ARC-04, ARC-03 (in-file dead code only), plus `node --test` tests
7. **Visual redesign and accessibility** — UI-01 … UI-10
8. **Docs** — FUN-17, `docs/IMPROVEMENTS.md`, status updates here

### Needs approval (not implemented)
| ID | Change | Reason approval is needed |
|---|---|---|
| SEC-02 | `MAX_PAGES` / `MAX_FILES` limits | new config contract; may reject requests that work today |
| SEC-03 | trusted-proxy handling for `X-Forwarded-For` | deployment/config contract |
| SEC-12 | non-root container, drop backend port, dev bind 127.0.0.1 | infrastructure |
| SEC-13 | authentication | new feature |
| SEC-14 | dependency upgrades after `pip-audit`/`npm audit` | dependency changes |
| FUN-07 | keep DOCX text when images are present | changes PDF output |
| FUN-08 | Unicode font for Word→PDF | changes output, adds asset |
| FUN-11 | return the original when compression grows the file | changes PDF output |
| FUN-12 | reject 0-page results | changes processing results |
| FUN-14/15 | align nginx/axios timeouts and body limits | infrastructure/config |
| FUN-16 | UI for word-to-pdf / sequential merge / info | new features |
| ARC-03 | delete `ConvertView.vue`, `PdfPreview.vue`, drop `pdfjs-dist` | removes files/dependency |
| ARC-06 | lockfile, `npm ci`, pin `cryptography` | dependency/infra |
| ARC-07 | migrate to `lifespan` | refactor with no functional gain now |
| PERF-05 | paged thumbnails API | public API change |
| — | CI pipeline | infrastructure |

---

## 5. Recommended implementation order

1. Central validation + exception handling (FUN-01, ARC-01, SEC-10, SEC-07, SEC-08, SEC-01, FUN-08/09) — largest user-visible win; prerequisite for clean tests.
2. Temp-file cleanup and fixed internal names (SEC-06, SEC-09, FUN-10).
3. Thread-pool execution and per-page rasterising (PERF-01/02/03) — measured high impact, low risk.
4. Rate-limiter config/pruning, CORS credentials (SEC-04/05/11).
5. Backend regression test suite.
6. Frontend error surfacing, routing, merge correctness, upload validation (FUN-02/03/04/05/06/13) with helper tests.
7. Design tokens → theme system → component redesign → accessibility pass (UI-*).
8. Documentation (README fixes, IMPROVEMENTS.md, audit status).
9. After approval: SEC-14 dependency upgrades, SEC-02/03/12, FUN-07/11/12, ARC-06, then the rest.

---

## 6. Appendix — how the evidence was produced

All scripts lived outside the repository (session scratch directory) and used only locally generated files:
- `make_samples.py` — reportlab/Pillow/python-docx generated 1/3/10/40-page text PDFs, an image-only "scanned" PDF, PNG/JPG/RGBA/LA/CMYK images, garbage/truncated/empty/encrypted PDFs, `report_%d.pdf`, DOCX with text+image and with non-Latin text.
- `probe.py` — FastAPI `TestClient` against `app.main:app`, one request per case.
- `bench_loop.py` — live `uvicorn` on :8765, one heavy request plus `/api/health` polling.
- `bench_mem.py` — `resource.getrusage(...).ru_maxrss` after a direct service call.
- `cdp.mjs` — dependency-free Chrome DevTools Protocol driver for screenshots and UI checks.

---

## 7. Addendum — findings discovered during implementation

#### FUN-18 — Word → PDF failed for any document with two or more paragraphs
- **Location:** `backend/app/services/convert_service.py` `word_to_pdf`
- **Evidence:** a new regression test failed; reproduced on `a8d4718`: 1 paragraph → 200, 2 paragraphs → **500** ("Not enough horizontal space to render a single character"). fpdf2's `multi_cell()` leaves the cursor at the right margin by default.
- **Impact:** Word → PDF never worked for ordinary text documents.
- **Fix:** move to the left margin on the next line after each paragraph.
- **Priority:** High · **Effort:** Low · **Type:** Verified defect · **Plan:** Proceeding (bug fix, no prior working output to preserve)
- **Status:** ✅ Fixed in `c11d71a`; test `test_multiple_paragraphs`.

#### FUN-19 — "High" compression options placed after the input file
- **Location:** `compress_service._compress_with_ghostscript` (`-dAutoFilterColorImages=false`, `-dColorImageFilter=/DCTEncode` are appended after the input path)
- **Evidence:** code inspection; Ghostscript applies switches in order, so options after the input file do not affect it.
- **Impact:** the "high" preset probably behaves like plain `/prepress`.
- **Fix:** move the two options before the input file — changes PDF output.
- **Priority:** Low · **Effort:** Low · **Type:** Potential risk (not measured) · **Plan:** **Needs approval** (changes PDF output)
- **Status:** **Not implemented — awaiting approval.**

#### UI-11 — Merge source labels failed contrast
- **Location:** `frontend/src/components/MergeReorder.vue` (`FILE_COLORS`, white 9 px labels on e.g. `#f59e0b` amber ≈ 2.1:1)
- **Status:** ✅ Fixed in `9aac87e` — palette replaced with colours that are all ≥ 4.5:1 against white; checked by `contrast.test.js`.
