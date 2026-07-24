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
- **Rate limiting** — 1s minimum delay between requests per IP, max 5 requests per 10s
- **Auto-cleanup** — temporary files are purged after 24 hours
- **50MB max upload** per file

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
│   │   └── utils/
│   │       └── file_utils.py      # Temp file management + auto-cleanup
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── views/                 # Page components (lazy-loaded)
│   │   │   ├── HomeView.vue       # Tool grid
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
│   │   ├── api/index.js           # Axios HTTP client
│   │   └── main.js                # Router + lazy imports
│   ├── package.json
│   └── Dockerfile
├── config.env                     # Environment variables
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

Frontend runs at http://localhost:5173 (proxies API to backend)

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
- `dpi` — resolution: `150`, `200`, `300` (for pdf-to-image)

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
| `GET` | `/api/ocr/backends` | List available OCR backends |

**Parameters:**
- `file` — PDF file
- `language` — Tesseract language code: `eng`, `ind`, `jpn`, `kor`, `chi_sim`, `deu`, `fra`, `spa`
- `backend` — OCR engine name (optional, uses config default)

### Compress

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/compress` | Compress PDF using Ghostscript |

**Parameters:**
- `file` — PDF file
- `quality` — `low` (screen/72dpi) | `medium` (ebook/150dpi) | `high` (printer/300dpi) | `very_high` (prepress/300dpi)
- `engine` — `gs` (Ghostscript, default) | `pikepdf` (fallback)

**Response headers:**
- `X-Original-Size` — original file size in bytes
- `X-Compressed-Size` — compressed file size in bytes
- `X-Reduction-Percent` — size reduction percentage
- `X-Engine` — engine used (`gs` or `pikepdf`)

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
- Temporary files are auto-cleaned after 24 hours
- File uploads are limited to 50MB
- Input validation on all endpoints
- Built-in rate limiting (1s delay, 5 req/10s per IP)

## Built With AI

This entire repository was generated with [opencode](https://opencode.ai) — an AI-powered coding assistant. All code, configuration, documentation, and project structure were produced through AI-assisted development.
