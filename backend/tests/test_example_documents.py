import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import questionnaire
from app.services.extraction import extract_text

EXAMPLES = Path(__file__).resolve().parents[2] / "examples" / "test_docs"


@pytest.mark.parametrize(
    ("filename", "markers"),
    [
        ("01_en_workshop.pdf", ("Community workshop", "8. Which word", "ANSWER KEY")),
        ("02_it_attivita.docx", ("attività di gruppo", "8. Quale parola", "Soluzioni")),
        ("03_es_actividades.xlsx", ("[Hoja: Ítems]", "opuesto de abierto", "[Hoja: Claves]")),
        ("04_bilingue_es_en.docx", ("Las instrucciones", "The workshop", "Answer key")),
        ("05_bilingue_it_en.xlsx", ("Quanto sono", "How often", "Answer key")),
    ],
)
def test_example_document_can_be_extracted(filename, markers):
    path = EXAMPLES / filename
    text = extract_text(path.suffix, path.read_bytes())
    assert all(marker in text for marker in markers)


def test_italian_example_accepts_translated_statement_key_from_provider(monkeypatch):
    model_response = {
        "titulo": "Questionario dimostrativo",
        "idioma": "it",
        "items": [
            {"numero": n, "enunciato": f"Domanda {n}", "tipo": "desarrollo", "alternativas": []}
            for n in range(1, 9)
        ],
    }
    monkeypatch.setattr(
        questionnaire,
        "get_settings",
        lambda: SimpleNamespace(gemini_api_key="test", gemini_model="test"),
    )
    monkeypatch.setattr(
        questionnaire.genai,
        "Client",
        lambda **kwargs: SimpleNamespace(
            models=SimpleNamespace(
                generate_content=lambda **kwargs: SimpleNamespace(text=json.dumps(model_response))
            )
        ),
    )
    path = EXAMPLES / "02_it_attivita.docx"
    response = TestClient(app).post("/api/process", files={"file": (path.name, path.read_bytes())})
    assert response.status_code == 200
    assert response.json()["total_items"] == 8
    assert all("enunciado" in item and "enunciato" not in item for item in response.json()["items"])
