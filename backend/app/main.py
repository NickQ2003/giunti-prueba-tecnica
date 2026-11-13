import json
import logging
import time
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.errors import ProcessingError
from app.schemas import Questionnaire
from app.services.extraction import extract_text
from app.services.file_validation import read_upload
from app.services.questionnaire import extract_questionnaire

logger = logging.getLogger("uvicorn.error")

app = FastAPI(title="Cuestionarios API")


@app.middleware("http")
async def trace_request(request: Request, call_next):
    request.state.request_id = uuid4().hex
    request.state.stage = "request"
    request.state.error_code = None
    started = time.monotonic()
    try:
        response = await call_next(request)
    except Exception:
        request.state.error_code = "internal_error"
        response = JSONResponse(
            status_code=500,
            content={
                "error": {
                    "codigo": "internal_error",
                    "mensaje": "Ocurrió un error interno.",
                    "request_id": request.state.request_id,
                }
            },
        )
    response.headers["X-Request-ID"] = request.state.request_id
    logger.info(
        json.dumps(
            {
                "event": "request_complete",
                "request_id": request.state.request_id,
                "stage": request.state.stage,
                "error_code": request.state.error_code,
                "status": response.status_code,
                "duration_ms": round((time.monotonic() - started) * 1000),
            }
        )
    )
    return response


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.exception_handler(ProcessingError)
async def processing_error_handler(request: Request, exc: ProcessingError):
    request.state.error_code = exc.code
    return JSONResponse(
        status_code=exc.status,
        content={
            "error": {
                "codigo": exc.code,
                "mensaje": exc.message,
                "request_id": request.state.request_id,
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(request: Request, exc: RequestValidationError):
    request.state.error_code = "invalid_request"
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "codigo": "invalid_request",
                "mensaje": "La solicitud no es válida.",
                "request_id": request.state.request_id,
            }
        },
    )


@app.post("/api/process", response_model=Questionnaire)
async def process(request: Request, file: UploadFile = File(...)):
    try:
        request.state.stage = "file_validation"
        extension, content = await read_upload(file)
        request.state.stage = "text_extraction"
        text = await run_in_threadpool(extract_text, extension, content)
        request.state.stage = "llm_processing"
        return await run_in_threadpool(extract_questionnaire, text)
    finally:
        await file.close()


frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
