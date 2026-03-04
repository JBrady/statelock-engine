from __future__ import annotations

import os

from fastapi import APIRouter, Depends

from app.config import settings
from app.deps import require_api_key
from app.runtime import STARTED_AT

router = APIRouter(prefix="/debug", tags=["debug"], dependencies=[Depends(require_api_key)])


@router.get("/info", response_model=dict)
def debug_info() -> dict:
    return {
        "resolved_db_url": settings.db_url,
        "sqlite_path": settings.sqlite_path,
        "cwd": os.getcwd(),
        "pid": os.getpid(),
        "started_at": STARTED_AT.isoformat(),
    }
