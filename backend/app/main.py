import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import CLEANUP_INTERVAL
from .utils.file_utils import cleanup_old_files
from .middleware import RateLimitMiddleware
from .api import convert, edit, ocr, compress

app = FastAPI(title="PDF Tools API", version="1.0.0")

app.add_middleware(RateLimitMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(convert.router)
app.include_router(edit.router)
app.include_router(ocr.router)
app.include_router(compress.router)


@app.on_event("startup")
async def start_cleanup_task():
    async def _cleanup_loop():
        while True:
            cleanup_old_files()
            await asyncio.sleep(CLEANUP_INTERVAL)

    asyncio.create_task(_cleanup_loop())


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}
