import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.errors import AppError, InternalServiceError
from app.models.errors import ErrorResponse
from app.routers import memories

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="Self-hosted memory sidecar for local-first agent workflows.",
)

app.include_router(memories.router, prefix=settings.API_PREFIX, tags=["Memories"])


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    trace_id = request.headers.get("X-Trace-Id") or str(uuid.uuid4())
    request.state.trace_id = trace_id
    response = await call_next(request)
    response.headers["X-Trace-Id"] = trace_id
    response.headers["X-Statelock-Version"] = settings.API_VERSION
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
        details=exc.errors(),
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
