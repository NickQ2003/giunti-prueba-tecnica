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
