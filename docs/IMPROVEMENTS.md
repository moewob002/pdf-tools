# PDF Tools — Improvements

Work on branch `audit/pdf-tools-improvements`, starting from `main` @ `a8d4718`.
Every item references the finding ID in [`PROJECT_AUDIT.md`](PROJECT_AUDIT.md) and the commit that implements it.
Measurements were taken on the auditor's Linux machine (Python 3.11.13, Node 26.8.1, Ghostscript, Poppler, Tesseract with `eng` only).

## Commits

| Commit | Summary |
|---|---|
| `e3f7ce7` | docs: record initial project audit |
| `dd55cb4` | fix: honour rate-limit config and prune idle clients (SEC-04, SEC-05) |
| `6048566` | fix: centralise upload validation and map bad input to clear 4xx errors (FUN-01, SEC-01/07/08/10, ARC-01, FUN-08/09, PERF-04) |
| `c11d71a` | fix: word-to-pdf failed on any document with more than one paragraph (FUN-18) |
| `c24079b` | fix: delete job files after each response and stop using user names in paths (SEC-06, SEC-09, FUN-10) |
| `24caf08` | perf: run PDF work off the event loop and rasterise one page at a time (PERF-01/02/03, ARC-02) |
| `afd68a3` | fix: stop reflecting arbitrary origins with credentials in CORS (SEC-11) |
| `ede4930` | refactor: remove dead code and log swallowed processing errors (ARC-03 in-file, ARC-05) |
| `e90d96d` | fix: give the Convert nav link a page and redirect unknown routes (FUN-03) |
| `890ea54` | fix: show server errors, stop merge from silently dropping pages, validate uploads (FUN-02/04/05/06/13, ARC-04) |
| `ba7fbb5` | feat: add vibrant design tokens and an accessible light/dark theme (UI-01/02/10) |
| `9aac87e` | feat: redesign tool workflow UI with vibrant identity and accessible components (UI-03…09, UI-11) |
| `46217d3` | docs: correct README API, setup and security details (FUN-17) |
| (this commit) | docs: record improvements and update audit status |

The commit order differs slightly from the audit's recommended order: the rate-limiter configuration fix went first because the API tests need a configurable limiter.

## Bug fixes

| ID | Before (verified) | After (verified) |
|---|---|---|
| FUN-01 | 14 of 30 probe cases returned HTTP 500 for invalid input | 0 × 500; clear 400/413/422 messages |
| FUN-02 | UI always showed "Split failed" / "Merge failed" … (Blob error bodies were never read) | the server's message is shown, e.g. "This PDF is password-protected. Remove the password and try again." |
| FUN-03 | "Convert" in the header opened an empty page | Convert hub page; unknown routes redirect home |
| FUN-04 | 7 × 3-page PDFs in Merge → 17 pages offered (two previews hit HTTP 429 and became fake 1-page entries) | 21 pages; 429 is retried; a file that still fails is listed with the reason and not added |
| FUN-05 | removing a file in Merge left its pages; same-named files were ignored | pages follow the file list; files tracked by identity |
| FUN-06 | oversize/wrong-type files silently dropped; upload not keyboard-operable | rejected files listed with reasons; keyboard "Browse" button |
| FUN-08 | Word → PDF with non-Latin-1 text: 500 | clear 422 explaining the limitation |
| FUN-09 | `.doc` accepted then 500 | 400 "… is not a Word document (.docx)" |
| FUN-10 | `X-Engine: ghostscript` when pikepdf produced the file | correct engine reported |
| FUN-13 | preview errors swallowed; stale errors stayed on screen | errors shown and cleared on a new file; single-file status chip shows "Can't read" |
| FUN-18 | Word → PDF with ≥ 2 paragraphs: 500 | converts; all paragraphs present in the PDF text |

## Security hardening

- **Content validation (SEC-10):** PDFs are parsed and images decoded before any processing; random bytes are no longer "compressed" with HTTP 200.
- **Bounds (SEC-01):** DPI limited to 36–600 (the UI uses 72–300).
- **No internal details in responses (SEC-07):** OCR no longer returns Tesseract stderr or paths; unexpected errors return a generic message and are logged server-side.
- **OCR language allow-list (SEC-08):** only supported codes (optionally `+`-joined).
- **Temp files (SEC-06):** uploads and results are deleted once the response is sent, immediately for JSON results, and on failure. `remove_job_dir()` only deletes direct children of `TEMP_DIR`. The 24-hour sweeper remains as a safety net.
- **Paths (SEC-09):** internal files use fixed names, so client file names (e.g. with `%`) never reach Ghostscript's `-sOutputFile` or other paths; upload suffixes are sanitised.
- **Rate limiter (SEC-04/05):** honours `RATE_LIMIT_MAX`/`RATE_LIMIT_DELAY`; idle-client state is pruned.
- **CORS (SEC-11):** credentials disabled; arbitrary origins are no longer reflected.

## Performance (measured)

| Metric | Before | After | How |
|---|---|---|---|
| `/api/health` latency while a 40-page, 300-dpi PDF → PNG job runs | **8.00 s** (1 ping) | **max 0.02 s, median 7 ms** (143 pings) | live uvicorn + polling script |
| Peak RSS of that job (direct service call) | **3 032 MB** | **155 MB** | `ru_maxrss`, two runs each |
| Wall time of that job | 7.9–10.9 s | 8.8–9.3 s | within run-to-run noise |
| Output equality | — | byte-identical (sha256) | pdf-to-image in PNG/JPG/TIFF/BMP, thumbnails JSON, OCR JSON on two PDFs, compared against `a8d4718` |
| Frontend bundle (main JS / CSS, gzip) | 43.55 kB / 4.64 kB | 45.08 kB / 6.77 kB | `vite build` |

Concurrent jobs are capped at `min(4, CPU count)` worker threads so the new concurrency cannot multiply peak memory without bound.

## Visual redesign — "Vibrant Color Systems & Chromatic Expression"

**Tokens** (`frontend/src/style.css`, exposed to Tailwind in `tailwind.config.js`): background, surface, surface-2/3, text, muted text, hairline and strong borders, primary (electric blue), secondary (violet), accent (coral), cyan, success/warning/danger/info, focus ring and `on-primary`, plus brand/text gradients and shadows.

**Colour rules**

| Colour | Used for |
|---|---|
| Electric blue (primary) | primary actions, selection, links, the Convert tools |
| Violet (secondary) | second gradient stop, focus ring, the Edit tools |
| Coral (accent) | the Compress tool, decorative highlights |
| Cyan | the OCR tool, decorative highlights |
| `*-text` variants | the only versions used for text and meaningful icons (vivid coral/cyan fills are below 4.5:1 and are decoration only) |
| Status colours | always paired with an icon and words, never colour alone |
| Gradients | hero, primary buttons, step badges, the active navigation item |

**Workflow:** every tool page uses numbered steps (1 Upload → 2 Options → 3 Run), and the result card takes focus and holds the Download button. The home page lists all eight operations, grouped and colour-coded by category.

**Components:**
- Gradient drop zone with a keyboard "Browse" button.
- File lists with per-file status chips.
- Accessible page-selection tiles (`aria-pressed`, check or cross badge).
- Merge cards with keyboard reorder and remove buttons, shown on hover or focus and always visible on touch.
- An alert component (`role=alert`/`status`).
- Spinners and progress with `role=status`.
- A preview dialog with focus trap, focus return and Escape to close.
- Labelled form fields, and a fieldset/legend for the compression levels.

**Themes:**
- Light and dark share one identity.
- The OS preference is the default; an explicit choice from the header toggle is persisted in `localStorage`, and storage failures are tolerated.
- An inline script in `index.html` sets `data-theme` before first paint, with a CSS-only OS fallback when JavaScript is off.

**Motion:** only CSS transitions, soft shadows and small hover lifts. `prefers-reduced-motion` disables them (verified: card transition 0.2 s → 0.00001 s). Decorative layers are `pointer-events: none` and never cover inputs or previews.

**Accessibility verification:**
- `frontend/tests/contrast.test.js` checks WCAG AA in both themes from the real token values:
  - 4.5:1 for every text token on bg/surface/surface-2, white text on both gradient stops, status text on its tint, and text over the hero blobs on bg and surface;
  - 3:1 for borders, focus ring and tool icons;
  - merge label colours against white.
- Headless Chromium checks:
  - no horizontal overflow on any route at 320 and 375 px, or at 1280 px in light and dark;
  - Tab reaches the skip link first and focus outlines render;
  - Space toggles page tiles;
  - Enter opens the preview dialog with focus on Close, Tab stays inside, and Escape closes it and returns focus.

Screenshots were taken at 375 and 1280 px in both themes (home, split, merge, compress) and of the focus, error and dialog states. They are not committed because they are generated artefacts.

## Dependency changes

- **Runtime:** none.
- **`backend/requirements-dev.txt` (new):** `-r requirements.txt` plus `httpx==0.28.1`, which FastAPI's `TestClient` needs to run the tests. It is not installed by the Dockerfile.
- **`frontend/package.json`:** new `"test": "node --test tests/"` script, using Node's built-in runner with no new packages.

## Tests and checks run (final state)

| Check | Command | Result |
|---|---|---|
| Backend tests | `cd backend && python -m unittest discover -s tests -t .` | **49 tests, OK** (against the original code: 42 failures, 5 errors) |
| Frontend tests | `cd frontend && npm test` | **22 tests, pass** |
| Frontend build | `cd frontend && npm run build` | ✅ |
| Backend compile | `python -m compileall -q app tests` | ✅ |
| Lint (ad-hoc, no project config) | `ruff check --isolated --select E,F app run.py` | pyflakes (F) findings **18 → 0**; E501 (88-column lines) **10 → 29**. The project has no line-length rule, and the original code already used 90–117-column lines |
| Endpoint probe, 30 valid/invalid cases | scratch `probe.py` | 0 × 500 (was 14); valid outputs same sizes as before |
| Browser workflows (valid and invalid files) | headless Chromium via CDP | all 15 flows: PDF→images, images→PDF, PDF→Word, split, delete, merge, OCR extract, OCR selectable and compress succeed; garbage/truncated/encrypted/fake files show clear alerts; `backend/temp/` empty afterwards |

Tests that need Poppler, Ghostscript or Tesseract skip themselves when those tools are missing. All ran here.

## Known limitations

- `X-Forwarded-For` is still trusted by the rate limiter (SEC-03), so the limit can be bypassed when the backend is reachable directly.
- These results are still returned with HTTP 200 (output changes need approval):
  - deleting every page, or a `page_order` with only invalid references, returns a 0-page PDF (FUN-12);
  - Word → PDF drops text when the document has images (FUN-07);
  - compression can return a larger file (FUN-11). The UI now says so.
- Word → PDF supports only Latin-1 text (FUN-08); other text gets a clear 422.
- OCR supports only the language data installed on the server. This machine has `eng` only; other languages return a clear 422.
- No page/file-count limits (SEC-02); nginx/axios timeouts are shorter than Ghostscript's (FUN-14).
- Dependency vulnerability status is unverified (SEC-14). `pip-audit`/`npm audit` were not run because they send the dependency list to an external service.
- `ConvertView.vue` and `PdfPreview.vue` are still unused and were not restyled (their deletion awaits approval).

## Deferred (awaiting approval)

SEC-02, SEC-03, SEC-12, SEC-13, SEC-14, FUN-07, FUN-08 (font), FUN-11, FUN-12, FUN-14, FUN-15, FUN-16, FUN-19, ARC-03 (file deletion), ARC-06, ARC-07, PERF-04 (streaming), PERF-05, CI. Reasons are listed in `PROJECT_AUDIT.md` §4.
