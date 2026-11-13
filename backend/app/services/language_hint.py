"""Deterministic, uncalibrated linguistic clues; never a language guarantee."""

import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from typing import Literal

Language = Literal["es", "en", "it", "und"]
TOKEN = re.compile(r"[^\W\d_]+", re.UNICODE)

# Shared words deliberately count for both languages; they cannot prove a language alone.
WORD_PATTERNS = {
    "es": re.compile(r"^(?:el|los|las|usted|ustedes|para|por|que|con|una|cuando|nunca|siempre)$"),
    "en": re.compile(r"^(?:the|you|your|with|and|when|never|always|often|sometimes|does|are)$"),
    "it": re.compile(r"^(?:il|gli|della|delle|lei|perché|per|che|con|una|quando|mai|sempre)$"),
}
SUFFIX_PATTERNS = {
    "es": re.compile(r"^[^\W\d_]{3,}(?:ción|ciones)$"),
    "en": re.compile(r"^[^\W\d_]{3,}(?:ing|tion)$"),
    "it": re.compile(r"^[^\W\d_]{3,}(?:zione|zioni)$"),
}


@dataclass(frozen=True)
class LanguageHint:
    candidate: Language
    scores: dict[str, int]


def analyze_language(text: str) -> LanguageHint:
    words = TOKEN.findall(unicodedata.normalize("NFKC", text).casefold())
    frequencies = Counter(words)
    scores = {language: 0 for language in WORD_PATTERNS}
    distinct = {language: 0 for language in WORD_PATTERNS}
    for word, count in frequencies.items():
        for language in WORD_PATTERNS:
            weight = (1 if WORD_PATTERNS[language].fullmatch(word) else 0) + (
                (1 if language == "en" else 2) if SUFFIX_PATTERNS[language].fullmatch(word) else 0
            )
            if weight:
                scores[language] += weight * min(count, 2)
                distinct[language] += 1
    ranked = sorted(scores, key=scores.get, reverse=True)
    winner, second = ranked[:2]
    # Heuristic thresholds, not calibrated probabilities. Abstain on weak or tied evidence.
    if (
        len(words) < 5
        or scores[winner] < 4
        or distinct[winner] < 2
        or scores[winner] - scores[second] < 2
    ):
        return LanguageHint(candidate="und", scores=scores)
    return LanguageHint(candidate=winner, scores=scores)
