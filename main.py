import logging
import uuid
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import Database
from app.core.errors import AppError, InternalServiceError, ServiceUnavailableError
from app.models.errors import ErrorResponse
from app.routers import insights, memories
from app.services.embedder import get_embedder

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="Self-hosted memory sidecar for local-first agent workflows.",
)

app.include_router(memories.router, prefix=settings.API_PREFIX, tags=["Memories"])
app.include_router(insights.router, tags=["Insights"])

site_app_path = Path(__file__).resolve().parent / "site" / "app"
if site_app_path.exists():
    app.mount("/app", StaticFiles(directory=str(site_app_path), html=True), name="console-app")


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    trace_id = request.headers.get("X-Trace-Id") or str(uuid.uuid4())
    requested_version = request.headers.get("X-Statelock-Version")
    request.state.trace_id = trace_id
    request.state.requested_version = requested_version
    response = await call_next(request)
    response.headers["X-Trace-Id"] = trace_id
    response.headers["X-Statelock-Version"] = settings.API_VERSION
    if requested_version:
        response.headers["X-Statelock-Version-Requested"] = requested_version
    return response


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    payload = ErrorResponse(
        code=exc.code,
        message=exc.message,
        details=exc.details,
        trace_id=getattr(request.state, "trace_id", "unknown"),
    )
    return JSONResponse(status_code=exc.status_code, content=payload.model_dump())


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    payload = ErrorResponse(
        code="validation_error",
        message="Request validation failed",
        details=jsonable_encoder(exc.errors()),
        trace_id=getattr(request.state, "trace_id", "unknown"),
    )
    return JSONResponse(status_code=422, content=payload.model_dump())


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error", exc_info=exc)
    err = InternalServiceError()
    payload = ErrorResponse(
        code=err.code,
        message=err.message,
        details=None,
        trace_id=getattr(request.state, "trace_id", "unknown"),
    )
    return JSONResponse(status_code=err.status_code, content=payload.model_dump())


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Welcome to StateLock Engine API v3",
        "version": settings.API_VERSION,
        "role": "memory-sidecar",
    }


@app.get("/healthz", tags=["Health"])
async def healthz():
    return {"status": "ok"}


@app.get("/readyz", tags=["Health"])
async def readyz():
    try:
        Database.get_collection()
        get_embedder()
    except Exception as exc:
        raise ServiceUnavailableError(details=str(exc))
    return {"status": "ready"}
