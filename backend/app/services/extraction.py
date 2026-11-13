from io import BytesIO
from zipfile import ZipFile

import pymupdf
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from openpyxl import load_workbook

from app.errors import ProcessingError

MAX_TEXT = 100_000
MAX_UNCOMPRESSED = 50 * 1024 * 1024
MAX_CELLS = 50_000
MAX_PAGES = 200


def _check_zip(data: bytes) -> None:
    with ZipFile(BytesIO(data)) as archive:
        entries = archive.infolist()
        if len(entries) > 5000 or sum(entry.file_size for entry in entries) > MAX_UNCOMPRESSED:
            raise ProcessingError("document_too_large", "El documento es demasiado complejo.", 422)


def _pdf(data: bytes) -> str:
    with pymupdf.open(stream=data, filetype="pdf") as document:
        if document.needs_pass:
            raise ProcessingError("protected_file", "El PDF está protegido con contraseña.", 422)
        if len(document) > MAX_PAGES:
            raise ProcessingError("document_too_large", "El PDF supera las 200 páginas.", 422)
        pages = []
        for index, page in enumerate(document):
            pages.append(f"[Página {index + 1}]\n{page.get_text()}")
            if sum(map(len, pages)) > MAX_TEXT:
                raise ProcessingError(
                    "document_too_large", "El texto supera el límite permitido.", 422
                )
        return "\n".join(pages)


def _docx(data: bytes) -> str:
    _check_zip(data)
    document = Document(BytesIO(data))
    lines = []
    size = 0
    for block in document.iter_inner_content():
        if isinstance(block, Paragraph):
            new_lines = [block.text]
        elif isinstance(block, Table):
            new_lines = [" | ".join(cell.text for cell in row.cells) for row in block.rows]
        else:
            continue
        lines.extend(new_lines)
        size += sum(map(len, new_lines))
        if size > MAX_TEXT:
            raise ProcessingError("document_too_large", "El texto supera el límite permitido.", 422)
    return "\n".join(lines)


def _xlsx(data: bytes) -> str:
    _check_zip(data)
    workbook = load_workbook(BytesIO(data), read_only=True, data_only=True)
    lines = []
    cells = 0
    size = 0
    try:
        for sheet in workbook:
            if sheet.max_row and sheet.max_column and sheet.max_row * sheet.max_column > MAX_CELLS:
                raise ProcessingError(
                    "document_too_large", "La hoja supera el límite de celdas.", 422
                )
            lines.append(f"[Hoja: {sheet.title}]")
            for row in sheet.iter_rows(values_only=True):
                cells += len(row)
                if cells > MAX_CELLS:
                    raise ProcessingError(
                        "document_too_large", "La hoja supera el límite de celdas.", 422
                    )
                if any(value is not None for value in row):
                    line = " | ".join(str(value) if value is not None else "" for value in row)
                    lines.append(line)
                    size += len(line)
                if size > MAX_TEXT:
                    raise ProcessingError(
                        "document_too_large", "El texto supera el límite permitido.", 422
                    )
    finally:
        workbook.close()
    return "\n".join(lines)


def extract_text(extension: str, data: bytes) -> str:
    try:
        if extension == ".pdf":
            text = _pdf(data)
            # Los encabezados de página no cuentan como contenido.
            content = "".join(line for line in text.splitlines() if not line.startswith("[Página "))
        elif extension == ".docx":
            text = _docx(data)
            content = text
        elif extension == ".xlsx":
            text = _xlsx(data)
            content = "".join(line for line in text.splitlines() if not line.startswith("[Hoja: "))
        else:
            raise ProcessingError("unsupported_format", "Formato no soportado.", 415)
    except ProcessingError:
        raise
    except Exception as exc:
        raise ProcessingError(
            "invalid_document", "No se pudo leer el archivo; verifica su formato.", 422
        ) from exc
    if not content.strip():
        raise ProcessingError(
            "no_text", "No se encontró texto. Los PDF escaneados requieren OCR, no incluido.", 422
        )
    return text
