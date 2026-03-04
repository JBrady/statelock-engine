from __future__ import annotations

import logging
import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api import context, conversations, dashboard, debug, governance, memory, segmentation, spans, telemetry, turns
from app.config import settings
from app.db.init_db import init_db
from app.runtime import CWD, GIT_SHA, STARTED_AT

logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    if settings.sqlite_path:
        logger.info("SQLite database path: %s", settings.sqlite_path)
    else:
        logger.info("Database URL: %s", settings.db_url)


@app.get("/health")
def health() -> dict:
    return {
        "ok": True,
        "resolved_db_url": settings.db_url,
        "sqlite_path": settings.sqlite_path,
        "pid": os.getpid(),
        "started_at": STARTED_AT.isoformat(),
        "cwd": CWD,
        "git_sha": GIT_SHA,
    }


app.include_router(dashboard.router)

for router in [
    conversations.router,
    turns.router,
    segmentation.router,
    context.router,
    telemetry.router,
    governance.router,
    memory.router,
    spans.router,
    debug.router,
]:
    app.include_router(router, prefix=settings.api_prefix)
