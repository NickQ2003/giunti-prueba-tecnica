from io import BytesIO

import pymupdf
import pytest
from docx import Document
from fastapi.testclient import TestClient
from openpyxl import Workbook

from app.main import app
from app.schemas import Questionnaire


def make_file(extension, question):
    stream = BytesIO()
    if extension == "pdf":
        pdf = pymupdf.open()
        pdf.new_page().insert_text((72, 72), question)
        data = pdf.tobytes()
        pdf.close()
        return data
    if extension == "docx":
        doc = Document()
        doc.add_paragraph(question)
        doc.save(stream)
    else:
        workbook = Workbook()
        workbook.active.append([question])
        workbook.save(stream)
    return stream.getvalue()


@pytest.mark.parametrize(
    ("extension", "language", "question"),
    [("pdf", "en", "How are you?"), ("docx", "es", "Como estas?"), ("xlsx", "it", "Come stai?")],
)
def test_format_to_api_with_mocked_model(monkeypatch, extension, language, question):
    def fake_provider(text):
        assert question in text
        return Questionnaire.model_validate(
            {
                "titulo": "Example",
                "idioma": language,
                "items": [
                    {"numero": 1, "enunciado": question, "tipo": "desarrollo", "alternativas": []}
                ],
            }
        )

    monkeypatch.setattr("app.main.extract_questionnaire", fake_provider)
    response = TestClient(app).post(
        "/api/process", files={"file": (f"example.{extension}", make_file(extension, question))}
    )
    assert response.status_code == 200
    assert response.json()["idioma"] == language
    assert response.json()["total_items"] == 1


@pytest.mark.parametrize("extension", ["pdf", "docx", "xlsx"])
def test_preview_extracts_without_calling_model(monkeypatch, extension):
    def fail(_text):
        raise AssertionError("preview must not call the model")

    monkeypatch.setattr("app.main.extract_questionnaire", fail)
    response = TestClient(app).post(
        "/api/preview",
        files={"file": (f"example.{extension}", make_file(extension, "1. Example question?"))},
    )
    assert response.status_code == 200
    assert "Example question?" in response.json()["text"]
    assert response.json()["truncated"] is False
    assert response.headers["Cache-Control"] == "no-store"
