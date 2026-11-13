from types import SimpleNamespace

import httpx
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
    assert exc.value.code == "llm_invalid_json"


def test_no_items(monkeypatch):
    configure(monkeypatch, iter(['{"titulo":"Ejemplo","idioma":"es","items":[]}']))
    with pytest.raises(ProcessingError) as exc:
        questionnaire.extract_questionnaire("texto")
    assert exc.value.code == "no_items"


def test_parse_response_does_not_call_provider():
    result = questionnaire.parse_response('{"titulo":"Ejemplo","idioma":"es","items":[]}')
    assert result.total_items == 0


def test_language_hint_is_sent_before_document_as_nonbinding_context(monkeypatch):
    calls = []
    monkeypatch.setattr(
        questionnaire,
        "get_settings",
        lambda: SimpleNamespace(gemini_api_key="test", gemini_model="test"),
    )

    def generate(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(
            text='{"titulo":"Ejemplo","idioma":"es","items":[{"numero":1,"enunciado":"Pregunta","tipo":"desarrollo","alternativas":[]}]}'
        )

    monkeypatch.setattr(
        questionnaire.genai,
        "Client",
        lambda **kwargs: SimpleNamespace(models=SimpleNamespace(generate_content=generate)),
    )
    document = "Las personas describen la preocupación y la evaluación de su bienestar."
    questionnaire.extract_questionnaire(document)
    call = calls[0]
    assert '"candidato": "es"' in call["contents"]
    assert call["contents"].index("PISTA LINGÜÍSTICA") < call["contents"].index(
        "DOCUMENTO NO CONFIABLE"
    )
    assert call["contents"].endswith(document)
    assert "orientativa" in call["config"].system_instruction
    assert document not in call["config"].system_instruction


def test_timeout_has_bounded_retries(monkeypatch):
    attempts = []
    monkeypatch.setattr(
        questionnaire,
        "get_settings",
        lambda: SimpleNamespace(gemini_api_key="test", gemini_model="test"),
    )

    def timeout(**kwargs):
        attempts.append(1)
        raise httpx.ReadTimeout("sensitive provider detail")

    monkeypatch.setattr(
        questionnaire.genai,
        "Client",
        lambda **kwargs: SimpleNamespace(models=SimpleNamespace(generate_content=timeout)),
    )
    with pytest.raises(ProcessingError) as exc:
        questionnaire.extract_questionnaire("secret text")
    assert exc.value.code == "llm_timeout"
    assert len(attempts) == 2
    assert "secret" not in str(exc.value)


def test_schema_failure_is_distinct(monkeypatch):
    configure(monkeypatch, iter(['{"titulo":"Ejemplo","idioma":"xx","items":[]}'] * 2))
    with pytest.raises(ProcessingError) as exc:
        questionnaire.extract_questionnaire("texto")
    assert exc.value.code == "llm_invalid_schema"


@pytest.mark.parametrize(
    ("status", "expected", "attempts"),
    [
        (401, "llm_configuration_error", 1),
        (404, "llm_configuration_error", 1),
        (429, "llm_unavailable", 1),
        (503, "llm_unavailable", 2),
    ],
)
def test_provider_statuses_are_safe_and_bounded(monkeypatch, status, expected, attempts):
    calls = []
    monkeypatch.setattr(
        questionnaire,
        "get_settings",
        lambda: SimpleNamespace(gemini_api_key="test", gemini_model="test"),
    )

    def fail(**kwargs):
        calls.append(1)
        raise questionnaire.errors.APIError(status, {"error": {"message": "secret"}})

    monkeypatch.setattr(
        questionnaire.genai,
        "Client",
        lambda **kwargs: SimpleNamespace(models=SimpleNamespace(generate_content=fail)),
    )
    with pytest.raises(ProcessingError) as exc:
        questionnaire.extract_questionnaire("document")
    assert exc.value.code == expected
    assert len(calls) == attempts
    assert "secret" not in str(exc.value)
