# PDF Tools

A self-hosted web application for PDF operations: convert, edit, OCR, and compress. All processing happens locally on the server — no external API calls, your files never leave.

## Features

| Feature | Capabilities |
|---------|-------------|
| **Convert** | PDF ↔ Images (PNG/JPG/TIFF), PDF ↔ Word (DOCX) |
| **Edit** | Split by page ranges, merge multiple PDFs, delete pages |
| **OCR** | Extract text from scanned PDFs with multi-language support |
| **Compress** | Reduce PDF file size with low/medium/high quality presets |

## Tech Stack

- **Backend:** Python 3.11, FastAPI, pypdf, pikepdf, Pillow, pdf2image, pytesseract, python-docx
- **Frontend:** Vue 3, Vite, Tailwind CSS, PDF.js
- **Deployment:** Docker Compose or direct Python/Node run

## Project Structure

```
pdf-tools/
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI entry point
│   │   ├── config.py              # Environment-based configuration
│   │   ├── api/                   # API route handlers
│   │   │   ├── convert.py         # PDF conversion endpoints
│   │   │   ├── edit.py            # Split, merge, delete endpoints
│   │   │   ├── ocr.py             # OCR endpoints
│   │   │   └── compress.py        # Compression endpoints
│   │   ├── services/              # Business logic
│   │   │   ├── convert_service.py
│   │   │   ├── edit_service.py
│   │   │   ├── ocr_service.py
│   │   │   └── compress_service.py
│   │   ├── ocr/                   # Pluggable OCR backends
│   │   │   ├── base.py            # Abstract OCR interface
│   │   │   ├── tesseract_backend.py
│   │   │   └── factory.py         # Backend selector
│   │   └── utils/
│   │       └── file_utils.py      # Temp file management
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── views/                 # Page components
│   │   ├── components/            # Reusable UI components
│   │   ├── api/index.js           # Axios HTTP client
│   │   └── main.js
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

### Option 1: Docker (Recommended)

```bash
git clone <repo-url>
cd pdf-tools
docker-compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000

### Option 2: Direct Run

**System dependencies (Ubuntu/Debian):**

```bash
sudo apt install tesseract-ocr tesseract-ocr-eng poppler-utils
```

**Backend:**

```bash
cd backend
pip install -r requirements.txt
python run.py
```

Backend runs at http://localhost:8000

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at http://localhost:3000 (proxies API to backend)

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
| `POST` | `/api/edit/merge` | Merge multiple PDFs |
| `POST` | `/api/edit/delete-pages` | Remove pages from PDF |
| `POST` | `/api/edit/info` | Get PDF metadata |

**Page range format:** `"1-3,5,7-9"` (comma-separated, supports ranges)

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
| `POST` | `/api/compress` | Compress PDF file |

**Parameters:**
- `file` — PDF file
- `quality` — `low` | `medium` | `high`

**Response headers:**
- `X-Original-Size` — original file size in bytes
- `X-Compressed-Size` — compressed file size in bytes
- `X-Reduction-Percent` — size reduction percentage

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
| `CLEANUP_INTERVAL` | `1800` | Temp file cleanup interval (seconds) |
| `FILE_TTL` | `1800` | Temp file time-to-live (seconds) |

## Adding a New OCR Backend

The OCR system uses a pluggable architecture. To add a new engine:

**1. Create the backend class:**

```python
# backend/app/ocr/my_backend.py
from .base import OCRBackend
from pathlib import Path

class MyOCRBackend(OCRBackend):
    def extract_text(self, image_path: Path, language: str = "eng") -> str:
        # Your OCR implementation here
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
- Temporary files are auto-cleaned after 30 minutes
- File uploads are limited to 50MB
- Input validation on all endpoints
- Rate limiting recommended for production

## License

MIT
