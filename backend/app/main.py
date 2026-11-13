import logging
from pathlib import Path

from fastapi import FastAPI, File, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.errors import ProcessingError
from app.schemas import Questionnaire
from app.services.extraction import extract_text
from app.services.file_validation import read_upload
from app.services.questionnaire import extract_questionnaire

logger = logging.getLogger(__name__)

app = FastAPI(title="Cuestionarios API")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.exception_handler(ProcessingError)
async def processing_error_handler(request: Request, exc: ProcessingError):
    return JSONResponse(
        status_code=exc.status, content={"error": {"codigo": exc.code, "mensaje": exc.message}}
    )


@app.exception_handler(Exception)
async def unexpected_error_handler(request: Request, exc: Exception):
    logger.error("Unexpected processing error: %s", type(exc).__name__)
    return JSONResponse(
        status_code=500,
        content={"error": {"codigo": "internal_error", "mensaje": "Ocurrió un error interno."}},
    )


@app.post("/api/process", response_model=Questionnaire)
async def process(file: UploadFile = File(...)):
    try:
        extension, content = await read_upload(file)
        text = await run_in_threadpool(extract_text, extension, content)
        return await run_in_threadpool(extract_questionnaire, text)
    finally:
        await file.close()


frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
