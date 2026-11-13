from pathlib import Path

from fastapi import UploadFile

from app.errors import ProcessingError

MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".xlsx"}


async def read_upload(upload: UploadFile) -> tuple[str, bytes]:
    extension = Path(upload.filename or "").suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise ProcessingError("unsupported_format", "Usa un archivo PDF, DOCX o XLSX.", 415)
    content = bytearray()
    while chunk := await upload.read(1024 * 1024):
        content.extend(chunk)
        if len(content) > MAX_FILE_SIZE:
            raise ProcessingError("file_too_large", "El archivo supera el límite de 10 MB.", 413)
    if not content:
        raise ProcessingError("empty_file", "El archivo está vacío.", 422)
    return extension, bytes(content)
