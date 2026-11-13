from io import BytesIO

import pytest
from starlette.datastructures import UploadFile

from app.errors import ProcessingError
from app.services.file_validation import MAX_FILE_SIZE, read_upload


def run_read(filename, content):
    import asyncio

    return asyncio.run(read_upload(UploadFile(filename=filename, file=BytesIO(content))))


def test_accepts_supported_extension_case_insensitive():
    assert run_read("test.DOCX", b"test") == (".docx", b"test")


@pytest.mark.parametrize(
    ("name", "content", "code"),
    [("file.txt", b"x", "unsupported_format"), ("file.pdf", b"", "empty_file")],
)
def test_invalid_upload(name, content, code):
    with pytest.raises(ProcessingError) as exc:
        run_read(name, content)
    assert exc.value.code == code


def test_size_limit():
    with pytest.raises(ProcessingError) as exc:
        run_read("file.pdf", b"x" * (MAX_FILE_SIZE + 1))
    assert exc.value.status == 413
