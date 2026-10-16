"""Regression tests: invalid input must give a clear 4xx, never a 500 or internal details."""
import json
import unittest

from fastapi.testclient import TestClient

from app.main import app
from tests import samples

PDF = "application/pdf"


def pdf_file(data: bytes, name: str = "doc.pdf", field: str = "file"):
    return (field, (name, data, PDF))


class ApiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app, raise_server_exceptions=False)
        cls.pdf3 = samples.text_pdf(3)

    def post(self, url, files, data=None):
        return self.client.post(url, files=files, data=data or {})

    def assertUserError(self, response, status=400, contains=None):
        self.assertEqual(response.status_code, status, response.text)
        detail = response.json()["detail"]
        self.assertIsInstance(detail, str)
        if contains:
            self.assertIn(contains.lower(), detail.lower())
        for leak in ("Traceback", "/usr/", "/app/", "temp/", "tessdata"):
            self.assertNotIn(leak, detail)


class PdfValidationTests(ApiTestCase):
    def test_garbage_pdf_is_rejected_everywhere(self):
        cases = [
            ("/api/edit/split", {"pages": "1"}),
            ("/api/edit/delete-pages", {"pages": "1"}),
            ("/api/edit/info", None),
            ("/api/compress", {"quality": "low"}),
            ("/api/convert/pdf-to-word", None),
            ("/api/convert/pdf-to-image", {"format": "png", "dpi": "72"}),
            ("/api/edit/thumbnails", {"dpi": "72"}),
            ("/api/ocr/extract-text", {"language": "eng"}),
        ]
        for url, data in cases:
            with self.subTest(url=url):
                r = self.post(url, [pdf_file(samples.GARBAGE)], data)
                self.assertUserError(r, contains="could not be read")

    def test_compress_no_longer_accepts_garbage(self):
        # Regression (SEC-10): random bytes used to be "compressed" with HTTP 200.
        r = self.post("/api/compress", [pdf_file(samples.GARBAGE)], {"quality": "low"})
        self.assertEqual(r.status_code, 400)

    def test_truncated_pdf(self):
        r = self.post("/api/edit/split", [pdf_file(self.pdf3[: len(self.pdf3) // 2])], {"pages": "1"})
        self.assertUserError(r, contains="could not be read")

    def test_empty_pdf(self):
        r = self.post("/api/edit/split", [pdf_file(b"")], {"pages": "1"})
        self.assertUserError(r, contains="empty")

    def test_password_protected_pdf(self):
        r = self.post("/api/edit/split", [pdf_file(samples.encrypted_pdf())], {"pages": "1"})
        self.assertUserError(r, contains="password")

    def test_wrong_extension(self):
        r = self.post("/api/edit/split", [("file", ("notes.txt", self.pdf3, "text/plain"))], {"pages": "1"})
        self.assertUserError(r, contains="not a PDF")

    def test_filename_directory_parts_are_not_echoed(self):
        r = self.post("/api/edit/split", [("file", ("../../etc/notes.txt", b"x", "text/plain"))], {"pages": "1"})
        self.assertUserError(r)
        self.assertNotIn("../", r.json()["detail"])

    def test_merge_with_one_bad_file(self):
        files = [pdf_file(self.pdf3, "a.pdf", "files"), pdf_file(samples.GARBAGE, "b.pdf", "files")]
        self.assertUserError(self.post("/api/edit/merge", files))


class PageRangeTests(ApiTestCase):
    def test_non_numeric_range(self):
        r = self.post("/api/edit/split", [pdf_file(self.pdf3)], {"pages": "abc"})
        self.assertUserError(r, contains="Invalid page range")

    def test_out_of_range_split(self):
        r = self.post("/api/edit/split", [pdf_file(self.pdf3)], {"pages": "9"})
        self.assertUserError(r, contains="3 page")

    def test_delete_invalid_range(self):
        r = self.post("/api/edit/delete-pages", [pdf_file(self.pdf3)], {"pages": "x"})
        self.assertUserError(r, contains="Invalid page range")

    def test_valid_split_still_works(self):
        r = self.post("/api/edit/split", [pdf_file(self.pdf3)], {"pages": " 1 , 3 "})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers["content-type"], "application/zip")

    def test_valid_delete_still_works(self):
        r = self.post("/api/edit/delete-pages", [pdf_file(self.pdf3)], {"pages": "2"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(samples.page_count(r.content), 2)

    def test_parse_page_ranges_unit(self):
        from app.utils.validation import parse_page_ranges

        self.assertEqual(parse_page_ranges("1-3,5", 10), [0, 1, 2, 4])
        self.assertEqual(parse_page_ranges("8-20", 10), [7, 8, 9])
        self.assertEqual(parse_page_ranges("0,11", 10), [])
        self.assertEqual(parse_page_ranges("3-1", 10), [])
        self.assertEqual(parse_page_ranges(" 2 - 3 ,, ", 10), [1, 2])


class MergeCustomTests(ApiTestCase):
    def files(self):
        return [pdf_file(self.pdf3, "a.pdf", "files"), pdf_file(samples.text_pdf(1), "b.pdf", "files")]

    def test_order_items_must_be_objects(self):
        r = self.post("/api/edit/merge-custom", self.files(), {"page_order": "[1,2]"})
        self.assertUserError(r, contains="page_order")

    def test_order_values_must_be_integers(self):
        order = json.dumps([{"file_index": "a", "page": 1}])
        r = self.post("/api/edit/merge-custom", self.files(), {"page_order": order})
        self.assertUserError(r, contains="integer")

    def test_order_not_json(self):
        r = self.post("/api/edit/merge-custom", self.files(), {"page_order": "{"})
        self.assertUserError(r, contains="JSON")

    def test_valid_custom_merge(self):
        order = json.dumps([{"file_index": 1, "page": 1}, {"file_index": 0, "page": 2}])
        r = self.post("/api/edit/merge-custom", self.files(), {"page_order": order})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(samples.page_count(r.content), 2)


@unittest.skipUnless(samples.HAS_POPPLER, "Poppler (pdftoppm) not installed")
class DpiTests(ApiTestCase):
    def test_dpi_bounds(self):
        # Regression (SEC-01): dpi was unbounded (dpi=0 and huge values accepted).
        for url, extra in (("/api/edit/thumbnails", {}), ("/api/convert/pdf-to-image", {"format": "png"})):
            for dpi in ("0", "5000"):
                with self.subTest(url=url, dpi=dpi):
                    r = self.post(url, [pdf_file(samples.text_pdf(1))], {"dpi": dpi, **extra})
                    self.assertUserError(r, contains="DPI")

    def test_ui_dpi_values_still_work(self):
        for dpi in ("72", "100"):
            r = self.post("/api/edit/thumbnails", [pdf_file(samples.text_pdf(1))], {"dpi": dpi})
            self.assertEqual(r.status_code, 200)


class ImageValidationTests(ApiTestCase):
    def test_fake_image(self):
        r = self.post("/api/convert/image-to-pdf", [("files", ("a.png", b"not an image", "image/png"))])
        self.assertUserError(r, contains="image could not be read")

    def test_unsupported_type(self):
        r = self.post("/api/convert/image-to-pdf", [("files", ("a.gif", b"GIF89a", "image/gif"))])
        self.assertUserError(r, contains="not a supported image")

    def test_valid_images(self):
        files = [("files", ("a.png", samples.png(), "image/png")), ("files", ("b.png", samples.png((200, 0, 0)), "image/png"))]
        r = self.post("/api/convert/image-to-pdf", files)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(samples.page_count(r.content), 2)


class WordToPdfTests(ApiTestCase):
    def post_docx(self, data, name="doc.docx"):
        return self.post("/api/convert/word-to-pdf", [("file", (name, data, "application/octet-stream"))])

    def test_legacy_doc_rejected_clearly(self):
        # Regression (FUN-09): .doc was accepted and then failed with a 500.
        self.assertUserError(self.post_docx(b"\xd0\xcf\x11\xe0junk", "old.doc"), contains=".docx")

    def test_corrupt_docx(self):
        self.assertUserError(self.post_docx(samples.GARBAGE), contains="could not be read")

    def test_non_latin_text_gives_clear_error(self):
        # Regression (FUN-08): non-Latin-1 text produced a 500.
        r = self.post_docx(samples.docx("Привет мир"))
        self.assertUserError(r, status=422, contains="characters")

    def test_plain_docx_still_converts(self):
        r = self.post_docx(samples.docx("Hello"))
        self.assertEqual(r.status_code, 200)
        self.assertGreaterEqual(samples.page_count(r.content), 1)

    def test_multiple_paragraphs(self):
        # Regression (FUN-18): a second paragraph failed with "Not enough horizontal space".
        r = self.post_docx(samples.docx("First paragraph.", "Second paragraph.", "Third."))
        self.assertEqual(r.status_code, 200, r.text)
        from pypdf import PdfReader
        import io

        text = PdfReader(io.BytesIO(r.content)).pages[0].extract_text()
        for expected in ("First paragraph.", "Second paragraph.", "Third."):
            self.assertIn(expected, text)


class OcrValidationTests(ApiTestCase):
    def test_unknown_language_rejected_without_leaking(self):
        # Regression (SEC-07/SEC-08): the response used to include tessdata paths.
        r = self.post("/api/ocr/extract-text", [pdf_file(samples.scanned_pdf())], {"language": "xyz"})
        self.assertUserError(r, contains="Unsupported OCR language")

    def test_language_injection_like_value(self):
        r = self.post("/api/ocr/extract-text", [pdf_file(samples.scanned_pdf())], {"language": "eng --psm 0"})
        self.assertUserError(r, contains="Unsupported OCR language")

    def test_unknown_backend(self):
        r = self.post("/api/ocr/extract-text", [pdf_file(samples.scanned_pdf())], {"backend": "nope"})
        self.assertUserError(r, contains="Unknown OCR backend")

    @unittest.skipUnless(samples.HAS_TESSERACT and samples.HAS_POPPLER, "Tesseract/Poppler not installed")
    def test_extract_text_works(self):
        r = self.post("/api/ocr/extract-text", [pdf_file(samples.scanned_pdf())], {"language": "eng"})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertIn("HELLO", r.json()["full_text"])


class CompressValidationTests(ApiTestCase):
    def test_bad_quality(self):
        r = self.post("/api/compress", [pdf_file(self.pdf3)], {"quality": "ultra"})
        self.assertUserError(r, contains="Quality")


class UnexpectedErrorTests(ApiTestCase):
    def test_unexpected_errors_are_generic(self):
        from unittest import mock

        with mock.patch("app.api.edit.get_pdf_info", side_effect=RuntimeError("/secret/path boom")):
            r = self.post("/api/edit/info", [pdf_file(self.pdf3)])
        self.assertEqual(r.status_code, 500)
        self.assertNotIn("/secret/path", r.text)
        self.assertIn("Something went wrong", r.json()["detail"])


if __name__ == "__main__":
    unittest.main()
