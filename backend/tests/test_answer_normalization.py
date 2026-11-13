import pytest
from pydantic import ValidationError

from app.schemas import Item


def item(answer, values=("A", "C"), item_type="seleccion_multiple"):
    return Item(
        numero=1,
        enunciado="Pregunta",
        tipo=item_type,
        alternativas=[{"valor": v, "texto": str(v)} for v in values],
        respuesta_correcta=answer,
    )


@pytest.mark.parametrize("answer", ["C.", " c ", "c)"])
def test_normalizes_only_unambiguous_labels(answer):
    assert item(answer).respuesta_correcta == "C"


def test_exact_match_wins():
    assert item("C.", ("C", "C.")).respuesta_correcta == "C."


@pytest.mark.parametrize(
    ("answer", "values"), [("c)", ("C", "C.")), ("Z", ("A", "C")), ("1", (1, 2))]
)
def test_ambiguous_or_missing_does_not_guess(answer, values):
    with pytest.raises(ValidationError):
        item(answer, values)


def test_matching_composite_answer_is_preserved():
    assert item("1-A; 2-B", ("A", "B"), "emparejamiento").respuesta_correcta == "1-A; 2-B"
