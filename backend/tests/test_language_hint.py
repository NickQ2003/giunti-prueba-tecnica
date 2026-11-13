import pytest

from app.services.language_hint import analyze_language


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Las personas describen la preocupación y la evaluación de su bienestar.", "es"),
        ("When you are thinking about your day, how often are you feeling calm?", "en"),
        ("La valutazione della preoccupazione delle persone è importante per lei.", "it"),
        ("", "und"),
        ("preocupación", "und"),
        ("the the the the the the", "und"),
        ("the and you with cuando siempre usted las", "und"),
    ],
)
def test_language_hints_and_abstention(text, expected):
    assert analyze_language(text).candidate == expected


def test_unicode_and_case_are_normalized():
    assert (
        analyze_language("LAS PERSONAS Y LA PREOCUPACIO\u0301N POR SU EVALUACIO\u0301N").candidate
        == "es"
    )


def test_scores_are_deterministic_and_do_not_count_repetition_unboundedly():
    text = "you are always thinking about your worries"
    assert analyze_language(text) == analyze_language(text)
    assert analyze_language("the " * 100).scores["en"] == 2
