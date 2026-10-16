import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from PIL import Image, UnidentifiedImageError
from pdf2image.exceptions import PDFPageCountError, PDFSyntaxError
from pypdf.errors import FileNotDecryptedError, PyPdfError

logger = logging.getLogger(__name__)

INVALID_PDF_MESSAGE = "The PDF could not be read. It may be damaged or not a PDF."
ENCRYPTED_PDF_MESSAGE = "This PDF is password-protected. Remove the password and try again."
INVALID_IMAGE_MESSAGE = "The image could not be read. It may be damaged or in an unsupported format."
GENERIC_ERROR_MESSAGE = "Something went wrong while processing the file. Please try again."


class UserInputError(Exception):
    """A problem with the request that the user can fix. The message is shown to them."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _detail(status_code: int, message: str) -> JSONResponse:
    return JSONResponse({"detail": message}, status_code=status_code)


async def _user_input_error(request: Request, exc: UserInputError):
    return _detail(exc.status_code, exc.message)


async def _encrypted_pdf(request: Request, exc: FileNotDecryptedError):
    return _detail(400, ENCRYPTED_PDF_MESSAGE)


async def _invalid_pdf(request: Request, exc: Exception):
    logger.info("Rejected unreadable PDF on %s: %s", request.url.path, exc)
    return _detail(400, INVALID_PDF_MESSAGE)


async def _invalid_image(request: Request, exc: Exception):
    logger.info("Rejected unreadable image on %s: %s", request.url.path, exc)
    return _detail(400, INVALID_IMAGE_MESSAGE)


async def _unexpected_error(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s", request.url.path, exc_info=exc)
    return _detail(500, GENERIC_ERROR_MESSAGE)


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(UserInputError, _user_input_error)
    app.add_exception_handler(FileNotDecryptedError, _encrypted_pdf)
    app.add_exception_handler(PyPdfError, _invalid_pdf)
    app.add_exception_handler(PDFPageCountError, _invalid_pdf)
    app.add_exception_handler(PDFSyntaxError, _invalid_pdf)
    app.add_exception_handler(UnidentifiedImageError, _invalid_image)
    app.add_exception_handler(Image.DecompressionBombError, _invalid_image)
    app.add_exception_handler(Exception, _unexpected_error)
