from pathlib import Path

import pytest

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
