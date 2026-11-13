import json
import logging
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
    assert response.headers["X-Unmatched-Statements"] == "0"


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


def test_request_id_matches_error_and_cannot_be_supplied_by_client():
    response = client.post(
        "/api/process",
        headers={"X-Request-ID": "untrusted-secret"},
        files={"file": ("bad.txt", b"test")},
    )
    request_id = response.headers["X-Request-ID"]
    assert len(request_id) == 32 and request_id != "untrusted-secret"
    assert response.json()["error"]["request_id"] == request_id


def test_missing_file_has_consistent_error():
    response = client.post("/api/process")
    assert response.status_code == 422
    assert response.json()["error"]["codigo"] == "invalid_request"
    assert response.headers["X-Request-ID"] == response.json()["error"]["request_id"]


def test_unexpected_exception_does_not_leak_content(monkeypatch, caplog):
    def fail(text):
        raise RuntimeError("secret document text")

    monkeypatch.setattr("app.main.extract_questionnaire", fail)
    with caplog.at_level(logging.INFO, logger="uvicorn.error"):
        response = client.post(
            "/api/process", files={"file": ("secret-name.docx", document_bytes())}
        )
    assert response.status_code == 500
    assert response.json()["error"]["codigo"] == "internal_error"
    assert response.json()["error"]["request_id"] == response.headers["X-Request-ID"]
    assert "secret" not in response.text
    assert "secret" not in caplog.text
    event = json.loads(caplog.records[-1].message)
    assert event["request_id"] == response.headers["X-Request-ID"]
    assert event["error_code"] == "internal_error"
    assert event["stage"] == "llm_processing"
