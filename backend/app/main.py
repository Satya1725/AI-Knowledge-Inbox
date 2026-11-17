import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import repository
from app.config import get_settings
from app.db import init_db
from app.errors import AppError
from app.logging_setup import request_id_var, setup_logging
from app.routes import ingest, items, query

logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    setup_logging(settings.log_level)
    init_db()
    interrupted = repository.fail_interrupted_items()
    logger.info(
        "server started",
        extra={
            "database": settings.database_path,
            "embedding_provider": settings.embedding_provider,
            "chat_provider": settings.chat_provider,
            "interrupted_items": interrupted,
        },
    )
    yield


app = FastAPI(title="AI Knowledge Inbox", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)


@app.middleware("http")
async def request_logging(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
    token = request_id_var.set(request_id)
    started = time.perf_counter()
    try:
        response = await call_next(request)
    finally:
        request_id_var.reset(token)

    response.headers["X-Request-ID"] = request_id
    logger.info(
        "request",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": round((time.perf_counter() - started) * 1000),
        },
    )
    return response


# ---------- error handlers: every error has the same JSON shape ----------


def _error_response(status_code: int, code: str, message: str, details: list | None = None) -> JSONResponse:
    body: dict = {"error": {"code": code, "message": message}}
    if details:
        body["error"]["details"] = details
    return JSONResponse(status_code=status_code, content=body)


@app.exception_handler(AppError)
async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
    return _error_response(exc.status_code, exc.code, exc.message)


@app.exception_handler(RequestValidationError)
async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    details = [
        {"field": ".".join(str(part) for part in err["loc"] if part != "body"), "message": err["msg"]}
        for err in exc.errors()
    ]
    first = details[0] if details else {"field": "", "message": "Invalid request"}
    message = f"{first['field']}: {first['message']}" if first["field"] else first["message"]
    return _error_response(422, "validation_error", message, details)


@app.exception_handler(Exception)
async def handle_unexpected_error(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled error")
    return _error_response(500, "internal_error", "Something went wrong on the server. Check the logs for details.")


# ---------- routes ----------

app.include_router(ingest.router)
app.include_router(items.router)
app.include_router(query.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
