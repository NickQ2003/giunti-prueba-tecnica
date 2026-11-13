"""Genera un documento inventado para demostración; no requiere un proveedor de IA."""

from pathlib import Path

from docx import Document

document = Document()
document.add_heading("Questionario di esempio", 0)
document.add_paragraph("Per la domanda 1: 0 = Mai, 1 = A volte, 2 = Spesso, 3 = Sempre.")
document.add_paragraph("1. Mi preoccupo per cose di poca importanza.")
document.add_paragraph("2. Quale numero completa la serie: 2, 4, 8, 16, ...?")
document.add_paragraph("A. 18\nB. 24\nC. 32")
document.add_paragraph("Risposta corretta alla domanda 2: C.")
document.add_paragraph("3. Descriva una situazione recente in cui si è sentito sotto pressione.")
document.save(Path(__file__).with_name("cuestionario_inventado.docx"))
