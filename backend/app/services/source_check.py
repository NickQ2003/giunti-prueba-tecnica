"""Conservative diagnostic only; matching text does not prove correctness."""

import re
import unicodedata

from app.schemas import Questionnaire


def _normalize(text: str) -> str:
    return re.sub(r"\W+", " ", unicodedata.normalize("NFKC", text).casefold()).strip()


def count_unmatched_statements(source: str, questionnaire: Questionnaire) -> int:
    normalized_source = _normalize(source)
    return sum(
        1
        for item in questionnaire.items
        if not (statement := _normalize(item.enunciado)) or statement not in normalized_source
    )
