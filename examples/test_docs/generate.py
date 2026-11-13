"""Crea cuestionarios ficticios para pruebas manuales. No requiere acceso a Gemini."""

from pathlib import Path

import pymupdf
from docx import Document
from docx.shared import Pt
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

ROOT = Path(__file__).resolve().parent


def make_pdf():
    pages = [
        [
            "Community workshop - sample questionnaire",
            "FICTIONAL MATERIAL - no personal information is requested.",
            "SECTION A. Shared scale for items 1-3:",
            "0 = Never | 1 = Rarely | 2 = Sometimes | 3 = Often | 4 = Always",
            "1. The workshop instructions are easy to follow.",
            "2. The available materials support the activity.",
            "3. The examples help explain the main ideas.",
            "Choose one value for each statement.",
        ],
        [
            "SECTION B. Practice exercises",
            "4. Which number completes the sequence: 3, 6, 12, 24, ...?",
            "A. 30    B. 48    C. 36    D. 42",
            "5. True or false: A triangle always has four sides.",
            "A. True    B. False",
            "6. Match each item with its category:",
            "1. Carrot    2. Apple    3. Spoon",
            "A. Utensil   B. Vegetable   C. Fruit",
            "7. Describe one fictional activity for a community workshop.",
            "8. Which word is the opposite of 'early'?",
            "A. Near    B. Fast    C. Quiet    D. Late",
            "ANSWER KEY: item 4 = B; item 5 = B; item 6 = 1-B, 2-C, 3-A; item 8 = D.",
            "No answer key is provided for items 1-3 and 7.",
        ],
    ]
    document = pymupdf.open()
    for index, lines in enumerate(pages, 1):
        page = document.new_page(width=595, height=842)
        page.insert_text((54, 48), f"WORKSHOP / SAMPLE                                      PAGE {index} OF 2", fontsize=9)
        y = 90
        for line in lines:
            page.insert_text((54, y), line, fontsize=10)
            y += 24 if line.startswith(("SECTION", "Community")) else 21
    document.save(ROOT / "01_en_workshop.pdf")
    document.close()


def make_italian_docx():
    doc = Document()
    doc.styles["Normal"].font.size = Pt(10)
    doc.add_heading("Questionario dimostrativo sulle attività di gruppo", 0)
    doc.add_paragraph("Materiale inventato. Non inserire nomi o dati personali.")
    doc.add_heading("Sezione A · Scala condivisa", level=1)
    doc.add_paragraph("Per gli item 1-3 usare: 0 = Mai; 1 = Raramente; 2 = Spesso; 3 = Sempre.")
    table = doc.add_table(rows=1, cols=5)
    table.style = "Table Grid"
    for cell, text in zip(table.rows[0].cells, ["Enunciato", "0", "1", "2", "3"]):
        cell.text = text
    for text in [
        "1. Le istruzioni dell'attività sono chiare.",
        "2. Gli esempi aiutano a comprendere il compito.",
        "3. I materiali sono disponibili quando servono.",
    ]:
        cells = table.add_row().cells
        cells[0].text = text
        for cell in cells[1:]:
            cell.text = "□"
    doc.add_heading("Sezione B · Esercizi", level=1)
    doc.add_paragraph("4. Quale numero completa la serie: 5, 10, 15, 20, ...?")
    options = doc.add_table(rows=3, cols=2)
    options.style = "Table Grid"
    for row, (label, value) in zip(options.rows, [("A", "22"), ("B", "24"), ("C", "25")]):
        row.cells[0].text, row.cells[1].text = label, value
    doc.add_paragraph("5. Vero o falso: un quadrato ha quattro lati.\nA. Vero\nB. Falso")
    doc.add_paragraph("6. Associa ogni oggetto alla categoria corretta:")
    matching = doc.add_table(rows=3, cols=2)
    matching.style = "Table Grid"
    for row, (left, right) in zip(matching.rows, [("1. Mela", "A. Strumento"), ("2. Martello", "B. Frutto"), ("3. Carota", "C. Verdura")]):
        row.cells[0].text, row.cells[1].text = left, right
    doc.add_paragraph("7. Descrivi un'attività immaginaria da svolgere in gruppo.")
    doc.add_paragraph("8. Quale parola è il contrario di 'alto'?\nA. Basso\nB. Lungo\nC. Largo")
    doc.add_heading("Soluzioni esplicitamente indicate", level=1)
    doc.add_paragraph("4: C; 5: A; 6: 1-B, 2-A, 3-C; 8: A. Per gli altri item non è prevista una soluzione.")
    doc.save(ROOT / "02_it_attivita.docx")


def setup_sheet(sheet, widths):
    sheet.freeze_panes = "A2"
    for index, width in enumerate(widths, 1):
        sheet.column_dimensions[chr(64 + index)].width = width
    for cell in sheet[1]:
        cell.fill = PatternFill("solid", fgColor="285C41")
        cell.font = Font(color="FFFFFF", bold=True)
        cell.alignment = Alignment(wrap_text=True, vertical="top")


def make_spanish_xlsx():
    workbook = Workbook()
    info = workbook.active
    info.title = "Instrucciones"
    info.append(["Cuestionario ficticio de actividades comunitarias", "Valor"])
    info.append(["Material inventado; no incluir datos personales.", ""])
    info.append(["Escala compartida para ítems 1-3", ""])
    for value, label in [(0, "Nunca"), (1, "Casi nunca"), (2, "A veces"), (3, "Casi siempre"), (4, "Siempre")]:
        info.append([label, value])
    setup_sheet(info, [65, 20])

    sheet = workbook.create_sheet("Ítems")
    sheet.append(["Número", "Enunciado", "Alternativa A", "Alternativa B", "Alternativa C", "Alternativa D"])
    for row in [
        (1, "Las instrucciones de la actividad son fáciles de comprender.", "Usar escala compartida", None, None, None),
        (2, "Los ejemplos explican las tareas con claridad.", "Usar escala compartida", None, None, None),
        (3, "Los materiales disponibles son suficientes.", "Usar escala compartida", None, None, None),
        (4, "¿Qué número completa la serie: 4, 8, 12, 16, ...?", "18", "20", "22", "24"),
        (5, "Verdadero o falso: un hexágono tiene seis lados.", "Verdadero", "Falso", None, None),
        (6, "Empareja: 1. Libro; 2. Taza; 3. Lápiz.", "A. Bebida", "B. Lectura", "C. Escritura", None),
        (7, "Describe una actividad ficticia para mejorar la colaboración.", None, None, None, None),
        (8, "¿Cuál es el opuesto de abierto?", "Amplio", "Lejano", "Cerrado", "Fuerte"),
    ]:
        sheet.append(row)
    setup_sheet(sheet, [12, 65, 26, 22, 22, 20])

    key = workbook.create_sheet("Claves")
    key.append(["Ítem", "Respuesta indicada"])
    for row in [(4, "B"), (5, "A"), (6, "1-B, 2-A, 3-C"), (8, "C")]:
        key.append(row)
    key.append(["Nota", "Los ítems 1-3 y 7 no tienen respuesta correcta."])
    setup_sheet(key, [15, 60])
    workbook.save(ROOT / "03_es_actividades.xlsx")


def make_spanish_english_docx():
    doc = Document()
    doc.add_heading("Actividades de aprendizaje / Learning activities", 0)
    doc.add_paragraph("Cuestionario inventado. Do not include names or personal data.")
    doc.add_paragraph("Ítems 1 y 2: escala 0 = Nunca, 1 = A veces, 2 = Siempre.")
    doc.add_paragraph("1. Las instrucciones del taller son claras.")
    doc.add_paragraph("2. Los materiales de la actividad son suficientes.")
    doc.add_paragraph("Items 3 and 4: use 0 = Never, 1 = Sometimes, 2 = Always.")
    doc.add_paragraph("3. The examples help explain the activity.")
    doc.add_paragraph("4. The workshop materials are easy to locate.")
    doc.add_paragraph("5. ¿Qué número completa la serie 2, 5, 8, 11, ...?\nA. 12\nB. 14\nC. 16")
    doc.add_paragraph("6. True or false: every rectangle has four sides.\nA. True\nB. False")
    doc.add_paragraph("7. Describe una actividad ficticia para un grupo.")
    doc.add_paragraph("8. Describe an imaginary way to organize a workshop.")
    doc.add_paragraph("Respuestas indicadas / Answer key: 5 = B; 6 = A. No correct answer is given for other items.")
    doc.save(ROOT / "04_bilingue_es_en.docx")


def make_italian_english_xlsx():
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Questionario"
    sheet.append(["Numero / Number", "Domanda / Question", "A", "B", "C"])
    for row in [
        (1, "Quanto sono chiare le istruzioni?", "Mai", "A volte", "Sempre"),
        (2, "Quanto sono utili gli esempi?", "Mai", "A volte", "Sempre"),
        (3, "Quale numero completa la serie 3, 6, 9, ...?", "10", "12", "15"),
        (4, "How often are the workshop instructions clear?", "Never", "Sometimes", "Always"),
        (5, "How often are the examples useful?", "Never", "Sometimes", "Always"),
        (6, "True or false: a triangle has three sides.", "True", "False", None),
        (7, "Descrivi un'attività immaginaria per il gruppo.", None, None, None),
        (8, "Describe an imaginary group activity.", None, None, None),
    ]:
        sheet.append(row)
    setup_sheet(sheet, [18, 65, 20, 20, 20])
    key = workbook.create_sheet("Soluzioni - Answer key")
    key.append(["Numero / Number", "Risposta / Answer"])
    key.append([3, "B"])
    key.append([6, "A"])
    key.append(["Nota / Note", "Gli altri item non hanno soluzione / No other answers are provided."])
    setup_sheet(key, [24, 70])
    workbook.save(ROOT / "05_bilingue_it_en.xlsx")


if __name__ == "__main__":
    make_pdf()
    make_italian_docx()
    make_spanish_xlsx()
    make_spanish_english_docx()
    make_italian_english_xlsx()
