from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class AppError(Exception):
    code: str
    message: str
    status_code: int = 400
    details: Any = None


class NotFoundError(AppError):
    def __init__(self, message: str, details: Any = None):
        super().__init__(code="not_found", message=message, status_code=404, details=details)


class ValidationError(AppError):
    def __init__(self, message: str, details: Any = None):
        super().__init__(
            code="validation_error",
            message=message,
            status_code=422,
            details=details,
        )


class InternalServiceError(AppError):
    def __init__(self, message: str = "Internal service error", details: Any = None):
        super().__init__(
            code="internal_error",
            message=message,
            status_code=500,
            details=details,
        )


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Unauthorized", details: Any = None):
        super().__init__(
            code="unauthorized",
            message=message,
            status_code=401,
            details=details,
        )


class ServiceUnavailableError(AppError):
    def __init__(self, message: str = "Service unavailable", details: Any = None):
        super().__init__(
            code="service_unavailable",
            message=message,
            status_code=503,
            details=details,
        )
