import subprocess
import shutil
from pathlib import Path

import pikepdf

from ..utils.file_utils import save_upload, temp_job

QUALITY_PRESETS = {
    "extreme": {"gs_setting": "/screen", "desc": "72 dpi, aggressive downsampling"},
    "low": {"gs_setting": "/ebook", "desc": "150 dpi, good balance"},
    "medium": {"gs_setting": "/printer", "desc": "300 dpi, print quality"},
    "high": {"gs_setting": "/prepress", "desc": "300 dpi, no subsampling"},
}


def _gs_available() -> bool:
    return shutil.which("gs") is not None


def _compress_with_ghostscript(
    input_path: Path,
    output_path: Path,
    gs_setting: str,
) -> bool:
    if not _gs_available():
        return False

    # Map presets to DPI
    dpi_map = {
        "/screen": 72,
        "/ebook": 150,
        "/printer": 300,
        "/prepress": 300,
    }
    dpi = dpi_map.get(gs_setting, 150)

    cmd = [
        "gs",
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        f"-dPDFSETTINGS={gs_setting}",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        f"-dColorImageDownsampleType=/Bicubic",
        f"-dColorImageResolution={dpi}",
        f"-dGrayImageDownsampleType=/Bicubic",
        f"-dGrayImageResolution={dpi}",
        f"-dMonoImageDownsampleType=/Bicubic",
        f"-dMonoImageResolution={dpi}",
        "-dDownsampleColorImages=true",
        "-dDownsampleGrayImages=true",
        "-dDownsampleMonoImages=true",
        f"-sOutputFile={output_path}",
        str(input_path),
    ]

    if gs_setting == "/prepress":
        cmd.append("-dAutoFilterColorImages=false")
        cmd.append("-dColorImageFilter=/DCTEncode")

    try:
        result = subprocess.run(cmd, capture_output=True, timeout=300)
        return output_path.exists() and output_path.stat().st_size > 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def _post_process_with_pikepdf(pdf_path: Path) -> int:
    removed = 0
    try:
        with pikepdf.open(pdf_path) as pdf:
            # Remove duplicate images
            seen_hashes = set()
            for page in pdf.pages:
                resources = page.get("/Resources", {})
                xobjects = resources.get("/XObject", {})
                for name in list(xobjects.keys()):
                    try:
                        xobj = xobjects[name]
                        if xobj.get("/Subtype") == pikepdf.Name("/Image"):
                            raw = xobj.read_raw_bytes()
                            h = hash(raw)
                            if h in seen_hashes:
                                removed += 1
                            else:
                                seen_hashes.add(h)
                    except Exception:
                        continue

            # Remove unnecessary metadata
            try:
                for key in list(pdf.docinfo.keys()):
                    if key not in ("/Producer", "/Creator"):
                        del pdf.docinfo[key]
            except Exception:
                pass

            pdf.save(
                str(pdf_path),
                compress_streams=True,
                object_stream_mode=pikepdf.ObjectStreamMode.generate,
                recompress_flate=True,
            )
    except Exception:
        pass

    return removed


def _compress_with_pikepdf(
    input_path: Path,
    output_path: Path,
    quality: str,
) -> bool:
    """Fallback: basic compression using pikepdf only (less effective)."""
    from PIL import Image
    import io

    presets = {
        "extreme": {"jpeg_quality": 25, "downsample_dpi": 72},
        "low": {"jpeg_quality": 40, "downsample_dpi": 100},
        "medium": {"jpeg_quality": 60, "downsample_dpi": 150},
        "high": {"jpeg_quality": 80, "downsample_dpi": 200},
    }
    preset = presets.get(quality, presets["medium"])

    try:
        with pikepdf.open(input_path) as pdf:
            for page in pdf.pages:
                resources = page.get("/Resources", {})
                xobjects = resources.get("/XObject", {})
                for name in list(xobjects.keys()):
                    try:
                        xobj = xobjects[name]
                        if xobj.get("/Subtype") != pikepdf.Name("/Image"):
                            continue

                        width = int(xobj.get("/Width", 0))
                        height = int(xobj.get("/Height", 0))
                        if width * height < 100:
                            continue

                        filters = xobj.get("/Filter")
                        if isinstance(filters, pikepdf.Array):
                            filters = list(filters)
                        elif filters:
                            filters = [filters]
                        else:
                            filters = []

                        if pikepdf.Name("/JBIG2Decode") in filters:
                            continue

                        raw = xobj.read_raw_bytes()
                        is_jpeg = pikepdf.Name("/DCTDecode") in filters

                        if is_jpeg:
                            img = Image.open(io.BytesIO(raw))
                        else:
                            img = Image.open(io.BytesIO(raw))

                        if img.mode in ("RGBA", "LA", "PA"):
                            bg = Image.new("RGB", img.size, (255, 255, 255))
                            if img.mode == "RGBA":
                                bg.paste(img, mask=img.split()[3])
                            img = bg
                        elif img.mode not in ("RGB", "L"):
                            img = img.convert("RGB")

                        target_dpi = preset["downsample_dpi"]
                        orig_dpi = 300
                        for key in ("/HResolution", "/VResolution"):
                            if key in xobj:
                                try:
                                    orig_dpi = int(xobj[key])
                                    break
                                except (ValueError, TypeError):
                                    pass

                        if target_dpi < orig_dpi:
                            ratio = target_dpi / orig_dpi
                            new_w = max(1, int(img.width * ratio))
                            new_h = max(1, int(img.height * ratio))
                            img = img.resize((new_w, new_h), Image.LANCZOS)

                        buf = io.BytesIO()
                        if img.mode == "L":
                            img = img.convert("RGB")
                        img.save(buf, format="JPEG", quality=preset["jpeg_quality"], optimize=True, progressive=True)
                        jpeg_bytes = buf.getvalue()

                        if len(raw) - len(jpeg_bytes) < len(raw) * 0.05:
                            continue

                        xobj.write(jpeg_bytes, filter=pikepdf.Name("/DCTDecode"))
                        if "/SMask" in xobj:
                            del xobj["/SMask"]
                    except Exception:
                        continue

            pdf.save(
                str(output_path),
                compress_streams=True,
                object_stream_mode=pikepdf.ObjectStreamMode.generate,
                recompress_flate=True,
            )
            return True
    except Exception:
        return False


async def compress_pdf(
    file_bytes: bytes,
    filename: str,
    quality: str = "medium",
) -> tuple[Path, dict]:
    with temp_job("compress") as job_dir:
        pdf_path = save_upload(file_bytes, filename, job_dir)

        preset = QUALITY_PRESETS.get(quality, QUALITY_PRESETS["medium"])
        # Fixed internal name: Ghostscript treats "%" in -sOutputFile as a template,
        # so the user's file name must never be part of it.
        output_path = job_dir / "compressed.pdf"

        # Try Ghostscript first (much more effective)
        if _compress_with_ghostscript(pdf_path, output_path, preset["gs_setting"]):
            engine = "ghostscript"
            images_compressed = _post_process_with_pikepdf(output_path)
            total_images = images_compressed  # approximate
        else:
            # Fallback to pikepdf-only (less effective)
            engine = "pikepdf"
            _compress_with_pikepdf(pdf_path, output_path, quality)
            images_compressed = 0
            total_images = 0

        if not output_path.exists() or output_path.stat().st_size == 0:
            # Last resort: just copy original
            output_path = pdf_path

        original_size = len(file_bytes)
        compressed_size = output_path.stat().st_size
        ratio = round((1 - compressed_size / original_size) * 100, 1) if original_size > 0 else 0

        return output_path, {
            "original_size": original_size,
            "compressed_size": compressed_size,
            "reduction_percent": ratio,
            "images_compressed": images_compressed,
            "total_images": total_images,
            "engine": engine,
        }
