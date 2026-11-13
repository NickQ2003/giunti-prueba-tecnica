import pytest
from pydantic import ValidationError

from app.schemas import Questionnaire


def test_total_is_calculated_and_answer_can_be_null():
    data = {
        "titulo": "Ejemplo",
        "idioma": "es",
        "total_items": 99,
        "items": [
            {
                "numero": 1,
                "enunciado": "¿Cómo estás?",
                "tipo": "desarrollo",
                "alternativas": [],
                "respuesta_correcta": None,
            }
        ],
    }
    result = Questionnaire.model_validate(data).model_dump()
    assert result["total_items"] == 1
    assert result["items"][0]["respuesta_correcta"] is None


@pytest.mark.parametrize(
    "item_type",
    ["escala_likert", "seleccion_multiple", "verdadero_falso", "desarrollo", "emparejamiento"],
)
def test_supported_types(item_type):
    item = {"numero": 1, "enunciado": "Pregunta", "tipo": item_type, "alternativas": []}
    assert Questionnaire(titulo="Ejemplo", idioma="it", items=[item]).items[0].tipo == item_type


def test_invalid_type_rejected():
    with pytest.raises(ValidationError):
        Questionnaire(
            titulo="Ejemplo",
            idioma="es",
            items=[{"numero": 1, "enunciado": "?", "tipo": "otro", "alternativas": []}],
        )


def test_duplicate_numbers_rejected():
    item = {"numero": 1, "enunciado": "Pregunta", "tipo": "desarrollo", "alternativas": []}
    with pytest.raises(ValidationError):
        Questionnaire(titulo="Ejemplo", idioma="es", items=[item, item])


@pytest.mark.parametrize("language", ["xx", "esp", "  "])
def test_unsupported_language_rejected(language):
    with pytest.raises(ValidationError):
        Questionnaire(titulo="Ejemplo", idioma=language, items=[])


def test_duplicate_alternative_values_rejected():
    item = {
        "numero": 1,
        "enunciado": "Pregunta",
        "tipo": "seleccion_multiple",
        "alternativas": [{"valor": "A", "texto": "Uno"}, {"valor": " a ", "texto": "Dos"}],
    }
    with pytest.raises(ValidationError):
        Questionnaire(titulo="Ejemplo", idioma="es", items=[item])


def test_open_ended_rejects_alternatives():
    item = {
        "numero": 1,
        "enunciado": "Pregunta",
        "tipo": "desarrollo",
        "alternativas": [{"valor": "A", "texto": "Uno"}],
    }
    with pytest.raises(ValidationError):
        Questionnaire(titulo="Ejemplo", idioma="es", items=[item])
