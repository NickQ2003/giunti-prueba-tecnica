from io import BytesIO

import pymupdf
import pytest
from docx import Document
from openpyxl import Workbook

from app.errors import ProcessingError
from app.services.extraction import extract_text


def test_docx_paragraphs_and_tables():
    document = Document()
    document.add_paragraph("1. Pregunta")
    table = document.add_table(rows=1, cols=2)
    table.cell(0, 0).text, table.cell(0, 1).text = "A", "Sí"
    stream = BytesIO()
    document.save(stream)
    text = extract_text(".docx", stream.getvalue())
    assert "1. Pregunta" in text and "A | Sí" in text


def test_pdf():
    document = pymupdf.open()
    document.new_page().insert_text((72, 72), "1. Question?")
    data = document.tobytes()
    document.close()
    assert "1. Question?" in extract_text(".pdf", data)


def test_xlsx():
    workbook = Workbook()
    workbook.active.append(["1. Pregunta", "Sí", "No"])
    stream = BytesIO()
    workbook.save(stream)
    assert "1. Pregunta | Sí | No" in extract_text(".xlsx", stream.getvalue())


@pytest.mark.parametrize("extension", [".pdf", ".docx", ".xlsx"])
def test_corrupt_files(extension):
    with pytest.raises(ProcessingError) as exc:
        extract_text(extension, b"not a document")
    assert exc.value.code == "invalid_document"


def test_empty_docx():
    stream = BytesIO()
    Document().save(stream)
    with pytest.raises(ProcessingError) as exc:
        extract_text(".docx", stream.getvalue())
    assert exc.value.code == "no_text"
