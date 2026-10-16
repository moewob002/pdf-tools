"""Regression tests for PERF-01 (event-loop blocking) and PERF-02 (all pages in memory)."""
import asyncio
import time
import unittest
from unittest import mock

import httpx

from app.main import app
from app.utils import pdf_render
from tests import samples


class EventLoopTests(unittest.TestCase):
    def test_health_responds_while_a_job_is_processing(self):
        def slow_split(*args, **kwargs):
            time.sleep(1.0)  # stands in for CPU-bound PDF work
            raise RuntimeError("stop here")

        async def scenario():
            transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                job = asyncio.create_task(
                    client.post(
                        "/api/edit/split",
                        files={"file": ("a.pdf", samples.text_pdf(1), "application/pdf")},
                        data={"pages": "1"},
                    )
                )
                await asyncio.sleep(0.2)
                start = time.perf_counter()
                health = await client.get("/api/health")
                elapsed = time.perf_counter() - start
                await job
                return health.status_code, elapsed

        with mock.patch("app.api.edit.split_pdf", side_effect=slow_split):
            status, elapsed = asyncio.run(scenario())
        self.assertEqual(status, 200)
        self.assertLess(elapsed, 0.5, "health check was blocked by a processing job")


class PerPageRenderingTests(unittest.TestCase):
    def test_pages_are_rendered_one_at_a_time(self):
        calls = []

        def fake_convert(path, dpi, first_page, last_page, **kwargs):
            calls.append((first_page, last_page))
            return ["image"]

        with mock.patch.object(pdf_render, "pdfinfo_from_path", return_value={"Pages": 3}), \
                mock.patch.object(pdf_render, "convert_from_path", side_effect=fake_convert):
            images = list(pdf_render.iter_page_images("x.pdf", dpi=300))

        self.assertEqual(images, ["image"] * 3)
        self.assertEqual(calls, [(1, 1), (2, 2), (3, 3)])

    @unittest.skipUnless(samples.HAS_POPPLER, "Poppler not installed")
    def test_real_rendering_matches_whole_document_rendering(self):
        import tempfile
        from pathlib import Path

        from pdf2image import convert_from_path

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.pdf"
            path.write_bytes(samples.text_pdf(3))
            whole = [img.tobytes() for img in convert_from_path(str(path), dpi=50)]
            paged = [img.tobytes() for img in pdf_render.iter_page_images(path, dpi=50)]
        self.assertEqual(whole, paged)


if __name__ == "__main__":
    unittest.main()
