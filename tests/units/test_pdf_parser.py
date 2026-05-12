import pytest

from services.exceptions import AppServiceError
from services.pdf_parser import extract_pdf_pages


def _single_page_pdf_bytes() -> bytes:
    content = b"BT /F1 24 Tf 100 700 Td (Remote work is allowed.) Tj ET"

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        (
            b"<< /Length " + str(len(content)).encode() + b" >>\n"
            b"stream\n" + content + b"\nendstream"
        ),
    ]

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = []

    for object_number, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{object_number} 0 obj\n".encode())
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")

    startxref = len(pdf)

    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    pdf.extend(b"0000000000 65535 f \n")

    for offset in offsets:
        pdf.extend(f"{offset:010d} 00000 n \n".encode())

    pdf.extend(
        (
            f"trailer\n<< /Root 1 0 R /Size {len(objects) + 1} >>\n"
            f"startxref\n{startxref}\n"
            "%%EOF\n"
        ).encode()
    )

    return bytes(pdf)


def test_extract_pdf_pages_returns_page_text_and_page_number():
    pages = extract_pdf_pages(_single_page_pdf_bytes())

    assert len(pages) == 1
    assert pages[0].page_number == 1
    assert "Remote work is allowed." in pages[0].text


def test_extract_pdf_pages_rejects_invalid_pdf_bytes():
    with pytest.raises(AppServiceError, match="could not be read as a PDF"):
        extract_pdf_pages(b"not a pdf")