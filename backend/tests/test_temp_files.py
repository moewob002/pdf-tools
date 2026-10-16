"""Regression tests for SEC-06 / SEC-09 / FUN-10: temp files and internal file names."""
import json
import unittest
from unittest import mock

from fastapi.testclient import TestClient

from app.config import TEMP_DIR
from app.main import app
from app.utils.file_utils import remove_job_dir, save_upload
from tests import samples

PDF = "application/pdf"


def job_dirs() -> set[str]:
    return {p.name for p in TEMP_DIR.iterdir()} if TEMP_DIR.exists() else set()


class TempFileLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app, raise_server_exceptions=False)
        cls.pdf = samples.text_pdf(3)

    def assertNoLeftovers(self, url, files, data=None, expected_status=200):
        before = job_dirs()
        r = self.client.post(url, files=files, data=data or {})
        self.assertEqual(r.status_code, expected_status, r.text[:200])
        self.assertEqual(job_dirs() - before, set(), f"{url} left files in {TEMP_DIR}")
        return r

    def test_successful_jobs_leave_nothing_behind(self):
        pdf = ("file", ("a.pdf", self.pdf, PDF))
        two = [("files", ("a.pdf", self.pdf, PDF)), ("files", ("b.pdf", self.pdf, PDF))]
        cases = [
            ("/api/edit/split", [pdf], {"pages": "1-2"}),
            ("/api/edit/delete-pages", [pdf], {"pages": "1"}),
            ("/api/edit/merge", two, None),
            ("/api/edit/merge-custom", two, {"page_order": json.dumps([{"file_index": 1, "page": 1}])}),
            ("/api/convert/image-to-pdf", [("files", ("a.png", samples.png(), "image/png"))], None),
            ("/api/convert/word-to-pdf", [("file", ("a.docx", samples.docx("Hi"), "application/octet-stream"))], None),
            ("/api/compress", [pdf], {"quality": "low"}),
        ]
        if samples.HAS_POPPLER:
            cases += [
                ("/api/convert/pdf-to-image", [pdf], {"format": "png", "dpi": "72"}),
                ("/api/convert/pdf-to-word", [pdf], None),
                ("/api/edit/thumbnails", [pdf], {"dpi": "72"}),
            ]
        if samples.HAS_POPPLER and samples.HAS_TESSERACT:
            scanned = ("file", ("s.pdf", samples.scanned_pdf(), PDF))
            cases += [
                ("/api/ocr/extract-text", [scanned], {"language": "eng"}),
                ("/api/ocr/make-selectable", [scanned], {"language": "eng"}),
            ]
        for url, files, data in cases:
            with self.subTest(url=url):
                self.assertNoLeftovers(url, files, data)

    def test_failed_jobs_leave_nothing_behind(self):
        # The service creates its job directory before discovering there are no valid pages.
        self.assertNoLeftovers(
            "/api/edit/split", [("file", ("a.pdf", self.pdf, PDF))], {"pages": "99"}, 400
        )

    def test_remove_job_dir_refuses_paths_outside_temp(self):
        outside = TEMP_DIR.parent / "not_a_job_dir_for_tests"
        outside.mkdir(exist_ok=True)
        try:
            remove_job_dir(outside)
            self.assertTrue(outside.exists())
            remove_job_dir(TEMP_DIR)
            self.assertTrue(TEMP_DIR.exists())
        finally:
            outside.rmdir()

    def test_save_upload_sanitises_suffix(self):
        job = TEMP_DIR / "test_suffix_job"
        job.mkdir(exist_ok=True)
        try:
            self.assertEqual(save_upload(b"x", "a.PDF", job).suffix, ".PDF")
            self.assertEqual(save_upload(b"x", "weird.p%d f", job).suffix, ".pdf")
            self.assertEqual(save_upload(b"x", "noext", job).suffix, ".pdf")
        finally:
            remove_job_dir(job)


class CompressNamingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app, raise_server_exceptions=False)

    @unittest.skipUnless(samples.HAS_GHOSTSCRIPT, "Ghostscript not installed")
    def test_percent_in_filename_does_not_break_ghostscript(self):
        # Regression (SEC-09): "%d" made Ghostscript write one file per page and the
        # job silently fell back to pikepdf.
        before = job_dirs()
        r = self.client.post(
            "/api/compress",
            files=[("file", ("report_%d.pdf", samples.text_pdf(3), PDF))],
            data={"quality": "low"},
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers["x-engine"], "ghostscript")
        self.assertEqual(samples.page_count(r.content), 3)
        self.assertIn("compressed_report_%25d.pdf", r.headers["content-disposition"])
        self.assertEqual(job_dirs() - before, set())

    def test_engine_header_reports_fallback(self):
        # Regression (FUN-10): the pikepdf fallback was reported as "ghostscript".
        with mock.patch("app.services.compress_service._compress_with_ghostscript", return_value=False):
            r = self.client.post(
                "/api/compress",
                files=[("file", ("a.pdf", samples.text_pdf(2), PDF))],
                data={"quality": "low"},
            )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers["x-engine"], "pikepdf")


if __name__ == "__main__":
    unittest.main()
