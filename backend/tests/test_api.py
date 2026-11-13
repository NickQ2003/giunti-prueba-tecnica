from io import BytesIO

from docx import Document
from fastapi.testclient import TestClient

from app.main import app
from app.schemas import Questionnaire

client = TestClient(app)


def document_bytes():
    document = Document()
    document.add_paragraph("1. ¿Cómo estás?")
    stream = BytesIO()
    document.save(stream)
    return stream.getvalue()


def test_success(monkeypatch):
    result = Questionnaire.model_validate(
        {
            "titulo": "Ejemplo",
            "idioma": "es",
            "items": [
                {"numero": 1, "enunciado": "¿Cómo estás?", "tipo": "desarrollo", "alternativas": []}
            ],
        }
    )
    monkeypatch.setattr("app.main.extract_questionnaire", lambda text: result)
    response = client.post("/api/process", files={"file": ("example.docx", document_bytes())})
    assert response.status_code == 200
    assert response.json()["total_items"] == 1


def test_invalid_file_does_not_call_provider(monkeypatch):
    def fail(text):
        raise AssertionError("provider must not be called")

    monkeypatch.setattr("app.main.extract_questionnaire", fail)
    response = client.post("/api/process", files={"file": ("bad.pdf", b"invalid")})
    assert response.status_code == 422
    assert response.json()["error"]["codigo"] == "invalid_document"


def test_unsupported_format():
    response = client.post("/api/process", files={"file": ("bad.txt", b"test")})
    assert response.status_code == 415
