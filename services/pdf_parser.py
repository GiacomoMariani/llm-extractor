from dataclasses import dataclass
from io import BytesIO

from pypdf import PdfReader

from services.exceptions import AppServiceError


@dataclass(frozen=True)
class ParsedPdfPage:
    page_number: int
    text: str


def extract_pdf_pages(file_bytes: bytes) -> list[ParsedPdfPage]:
    try:
        reader = PdfReader(BytesIO(file_bytes))
    except Exception as ex:
        raise AppServiceError("Uploaded file could not be read as a PDF.") from ex

    pages: list[ParsedPdfPage] = []

    for index, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()

        if text:
            pages.append(
                ParsedPdfPage(
                    page_number=index,
                    text=text,
                )
            )

    if not pages:
        raise AppServiceError(
            "No readable text was found in the PDF. Scanned PDFs are not supported yet."
        )

    return pages