# PDF Tools

A self-hosted web application for PDF operations: convert, edit, OCR, and compress. All processing happens locally — no external API calls, your files never leave your server.

## Features

| Feature | Capabilities |
|---------|-------------|
| **Convert** | PDF to PNG/JPG/TIFF images, images to PDF, PDF to Word (DOCX) |
| **Edit** | Split by page ranges, merge multiple PDFs with page-level reorder, delete pages |
| **OCR** | Extract text from scanned PDFs with multi-language support |
| **Compress** | Reduce PDF file size using Ghostscript (screen/ebook/printer/prepress presets) |

### Highlights

- **Page-level merge reorder** — drag and drop individual pages across multiple PDFs with color-coded source tracking
- **Download-before-save** — preview results in a card, then download at your convenience
- **Ghostscript compression** — four quality presets (screen 72dpi, ebook 150dpi, printer 300dpi, prepress 300dpi) with pikepdf fallback
- **Rate limiting** — 1s minimum delay between requests per IP, max 5 requests per 10s (configurable)
- **Auto-cleanup** — uploads and results are deleted as soon as the response is sent; a sweeper also purges anything older than 24 hours
- **50MB max upload** per file
- **Light and dark themes** — follows the OS by default, remembers an explicit choice; WCAG AA contrast checked by tests

## Tech Stack

- **Backend:** Python 3.11, FastAPI, pypdf, pikepdf, Pillow, pdf2image, pytesseract, python-docx, reportlab
- **Frontend:** Vue 3, Vite, Tailwind CSS
- **OCR:** Tesseract (pluggable architecture for adding more engines)
- **Compression:** Ghostscript (primary) + pikepdf (fallback)
- **Deployment:** Docker Compose or direct run

## Project Structure

```
pdf-tools/
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI entry point, middleware, cleanup task
│   │   ├── config.py              # Environment-based configuration
│   │   ├── middleware.py           # Rate limiting middleware
│   │   ├── api/                   # API route handlers
│   │   │   ├── convert.py         # PDF conversion endpoints
│   │   │   ├── edit.py            # Split, merge, delete, thumbnails, merge-custom
│   │   │   ├── ocr.py             # OCR endpoints
│   │   │   └── compress.py        # Ghostscript compression endpoints
│   │   ├── services/              # Business logic
│   │   │   ├── convert_service.py
│   │   │   ├── edit_service.py    # merge_pdfs + merge_custom_pages
│   │   │   ├── ocr_service.py
│   │   │   └── compress_service.py
│   │   ├── ocr/                   # Pluggable OCR backends
│   │   │   ├── base.py            # Abstract OCR interface
│   │   │   ├── tesseract_backend.py
│   │   │   └── factory.py         # Backend selector
│   │   ├── errors.py              # User-facing errors + exception handlers
│   │   └── utils/
│   │       ├── file_utils.py      # Temp job dirs, cleanup after response + TTL sweeper
│   │       ├── validation.py      # Shared upload / parameter validation
│   │       ├── pdf_render.py      # Page-by-page rasterising
│   │       ├── processing.py      # Runs PDF work in a bounded worker pool
│   │       └── responses.py       # File responses that delete their job dir
│   ├── tests/                     # unittest suite (python -m unittest discover -s tests -t .)
│   ├── requirements.txt
│   ├── requirements-dev.txt       # + test-only dependencies
│   └── Dockerfile
├── docs/                          # PROJECT_AUDIT.md, IMPROVEMENTS.md
├── frontend/
│   ├── src/
│   │   ├── views/                 # Page components (lazy-loaded)
│   │   │   ├── HomeView.vue       # Tool grid
│   │   │   ├── ConvertHubView.vue # Convert tools hub
│   │   │   ├── CompressView.vue   # Ghostscript compression
│   │   │   ├── OcrView.vue        # OCR extraction
│   │   │   ├── EditView.vue       # Edit tools hub
│   │   │   ├── SplitView.vue      # Split PDF
│   │   │   ├── MergeView.vue      # Merge with page reorder
│   │   │   ├── DeleteView.vue     # Delete pages
│   │   │   ├── PdfToImageViews.vue   # PDF to images
│   │   │   ├── ImagesToPdfView.vue   # Images to PDF
│   │   │   └── PdfToWordView.vue     # PDF to Word
│   │   ├── components/            # Reusable UI components
│   │   │   ├── FileUpload.vue     # Drag-and-drop file upload
│   │   │   ├── MergeReorder.vue   # Pointer-event drag reorder grid
│   │   │   ├── ResultCard.vue     # Download-before-save result card
│   │   │   ├── ImageModal.vue     # Full-size image preview
│   │   │   └── ...
│   │   ├── api/                   # Axios client + thumbnails helper
│   │   ├── utils/                 # Pure helpers (errors, files, merge, theme, …)
│   │   ├── tools.js               # Tool registry: names, routes, colours, icons
│   │   ├── style.css              # Design tokens (light/dark) + component classes
│   │   └── main.js                # Router + lazy imports
│   ├── tests/                     # node:test unit + contrast tests (npm test)
│   ├── package.json
│   └── Dockerfile
├── config.env.example             # Copy to config.env
├── docker-compose.yml
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Tesseract OCR (for OCR feature)
- Poppler utilities (for PDF-to-image conversion)
- Ghostscript (for compression)

### Option 1: Docker (Recommended)

```bash
git clone <repo-url>
cd pdf-tools
cp config.env.example config.env   # docker-compose reads config.env
docker-compose up --build
```

- Frontend: http://localhost:3000 (configurable via `FRONTEND_PORT`)
- Backend API: http://localhost:8000 (configurable via `BACKEND_PORT`)

### Option 2: Direct Run

**System dependencies (Ubuntu/Debian):**

```bash
sudo apt install tesseract-ocr tesseract-ocr-eng poppler-utils ghostscript
```

**Backend:**

```bash
cd backend
pip install -r requirements.txt
python run.py
```

Backend runs at http://localhost:8000 (configurable via `BACKEND_PORT`)

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at http://localhost:3000 (proxies `/api` to the backend on port 8000)

### Running tests

```bash
# Backend (unittest; httpx is needed for FastAPI's TestClient)
cd backend
pip install -r requirements-dev.txt
python -m unittest discover -s tests -t .

# Frontend (Node's built-in test runner, no extra dependencies)
cd frontend
npm test
```

Tests that need Poppler, Ghostscript or Tesseract are skipped when those tools are not installed.

## API Reference

### Convert

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/convert/pdf-to-image` | PDF to PNG/JPG/TIFF (returns ZIP) |
| `POST` | `/api/convert/image-to-pdf` | Images to PDF |
| `POST` | `/api/convert/pdf-to-word` | PDF to DOCX |
| `POST` | `/api/convert/word-to-pdf` | DOCX to PDF |

**Parameters (form-data):**
- `file` — source file
- `format` — image format: `png`, `jpg`, `tiff` (for pdf-to-image)
- `dpi` — resolution: `150`, `200`, `300` in the UI; the API accepts 36–600 (pdf-to-image and thumbnails)

### Edit

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/edit/split` | Split PDF by page ranges |
| `POST` | `/api/edit/merge` | Merge multiple PDFs (sequential) |
| `POST` | `/api/edit/merge-custom` | Merge pages in custom order (page-level reorder) |
| `POST` | `/api/edit/delete-pages` | Remove pages from PDF |
| `POST` | `/api/edit/thumbnails` | Extract page thumbnails for preview |
| `POST` | `/api/edit/info` | Get PDF metadata |

**Page range format:** `"1-3,5,7-9"` (comma-separated, supports ranges)

**merge-custom body:** multipart form with `files` (multiple PDFs) + `page_order` (JSON array of `{file_index, page}`)

### OCR

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/ocr/extract-text` | Extract text from scanned PDF |
| `POST` | `/api/ocr/make-selectable` | Return the PDF with an invisible, selectable text layer |
| `GET` | `/api/ocr/backends` | List available OCR backends |

**Parameters:**
- `file` — PDF file
- `language` — Tesseract language code: `eng`, `ind`, `jpn`, `kor`, `chi_sim`, `chi_tra`, `ara`, `deu`, `fra`, `spa`, `por`, `rus` (or a `+`-joined combination); the language data must be installed on the server
- `backend` — OCR engine name (optional, uses config default)

### Compress

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/compress` | Compress PDF using Ghostscript |

**Parameters:**
- `file` — PDF file
- `quality` — `extreme` (screen/72dpi) | `low` (ebook/150dpi) | `medium` (printer/300dpi, default) | `high` (prepress/300dpi)

Ghostscript is used when installed; otherwise pikepdf is used as a fallback.

**Response headers:**
- `X-Original-Size` — original file size in bytes
- `X-Compressed-Size` — compressed file size in bytes
- `X-Reduction-Percent` — size reduction percentage
- `X-Images-Compressed`, `X-Total-Images` — image statistics (Ghostscript path)
- `X-Engine` — engine that produced the file (`ghostscript` or `pikepdf`)

### Errors

Invalid input returns `400` (or `413` for oversized uploads, `422` for content the converter cannot handle) with a JSON body `{"detail": "<message safe to show users>"}`. Unexpected failures return `500` with a generic message; details are only logged on the server.

### Health Check

```
GET /api/health → {"status": "ok"}
```

## Configuration

All settings are in `config.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `OCR_BACKEND` | `pytesseract` | Active OCR engine |
| `OCR_LANGUAGES` | `eng` | Default OCR languages |
| `MAX_FILE_SIZE` | `52428800` | Max upload size in bytes (50MB) |
| `CLEANUP_INTERVAL` | `3600` | Temp file cleanup interval (seconds) |
| `FILE_TTL` | `86400` | Temp file time-to-live (24 hours) |
| `RATE_LIMIT_DELAY` | `1.0` | Minimum seconds between requests per IP |
| `RATE_LIMIT_MAX` | `5` | Max requests per 10-second window |
| `BACKEND_PORT` | `8000` | Backend server port |
| `FRONTEND_PORT` | `3000` | Frontend server port (Docker only) |

## Adding a New OCR Backend

The OCR system uses a pluggable architecture. To add a new engine:

**1. Create the backend class:**

```python
# backend/app/ocr/my_backend.py
from .base import OCRBackend
from pathlib import Path

class MyOCRBackend(OCRBackend):
    def extract_text(self, image_path: Path, language: str = "eng") -> str:
        return extracted_text

    def get_name(self) -> str:
        return "my_ocr"

    def get_supported_languages(self) -> list[str]:
        return ["eng", "ind"]
```

**2. Register in the factory:**

```python
# backend/app/ocr/factory.py
from .my_backend import MyOCRBackend

_registry: dict[str, type[OCRBackend]] = {
    "pytesseract": TesseractOCR,
    "my_ocr": MyOCRBackend,  # add here
}
```

**3. Update config:**

```
OCR_BACKEND=my_ocr
```

## Security

- All processing runs locally — no external API calls
- Uploads and results are deleted right after each response (24-hour sweeper as a safety net)
- File uploads are limited to 50MB; DPI and OCR language are validated
- Uploads are checked by content (PDFs are parsed, images decoded) before processing; error messages never include server paths or tool output
- Built-in rate limiting (1s delay, 5 req/10s per IP). Note: the limiter trusts `X-Forwarded-For`, so it is only effective behind a proxy that sets it (see `docs/PROJECT_AUDIT.md`, SEC-03)

See `docs/PROJECT_AUDIT.md` for the full audit and `docs/IMPROVEMENTS.md` for what has changed.

## Built With AI

This entire repository was generated with [opencode](https://opencode.ai) — an AI-powered coding assistant. All code, configuration, documentation, and project structure were produced through AI-assisted development.
