from app.schemas import Questionnaire
from app.services.source_check import count_unmatched_statements


def test_detects_unmatched_statement_without_changing_result():
    questionnaire = Questionnaire.model_validate(
        {
            "titulo": "Test",
            "idioma": "es",
            "items": [
                {
                    "numero": 1,
                    "enunciado": "¿Cómo estás?",
                    "tipo": "desarrollo",
                    "alternativas": [],
                },
                {
                    "numero": 2,
                    "enunciado": "Una frase ausente",
                    "tipo": "desarrollo",
                    "alternativas": [],
                },
            ],
        }
    )
    assert count_unmatched_statements("1. ¿CÓMO\n estás?", questionnaire) == 1
    assert questionnaire.total_items == 2
