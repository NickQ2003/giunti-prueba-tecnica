from types import SimpleNamespace

import pytest

from app.errors import ProcessingError
from app.services import questionnaire


def configure(monkeypatch, responses):
    monkeypatch.setattr(
        questionnaire,
        "get_settings",
        lambda: SimpleNamespace(gemini_api_key="test", gemini_model="test"),
    )
    model = SimpleNamespace(generate_content=lambda **kwargs: SimpleNamespace(text=next(responses)))
    monkeypatch.setattr(
        questionnaire.genai, "Client", lambda **kwargs: SimpleNamespace(models=model)
    )


def test_provider_response_is_validated(monkeypatch):
    configure(
        monkeypatch,
        iter(
            [
                '{"titulo":"Ejemplo","idioma":"es","items":[{"numero":1,"enunciado":"Pregunta","tipo":"desarrollo","alternativas":[]}]}'
            ]
        ),
    )
    assert questionnaire.extract_questionnaire("texto").total_items == 1


def test_invalid_json_retried(monkeypatch):
    configure(monkeypatch, iter(["bad", "bad"]))
    with pytest.raises(ProcessingError) as exc:
        questionnaire.extract_questionnaire("texto")
    assert exc.value.code == "invalid_response"


def test_no_items(monkeypatch):
    configure(monkeypatch, iter(['{"titulo":"Ejemplo","idioma":"es","items":[]}']))
    with pytest.raises(ProcessingError) as exc:
        questionnaire.extract_questionnaire("texto")
    assert exc.value.code == "no_items"


def test_parse_response_does_not_call_provider():
    result = questionnaire.parse_response('{"titulo":"Ejemplo","idioma":"es","items":[]}')
    assert result.total_items == 0
