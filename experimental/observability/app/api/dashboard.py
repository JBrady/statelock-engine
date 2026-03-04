from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db.models import Conversation
from app.deps import db_session

router = APIRouter(tags=["dashboard"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def dashboard_home(request: Request, db: Session = Depends(db_session)):
    conversation_count = db.query(Conversation).count()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "show_welcome": conversation_count == 0,
        },
    )


@router.get("/threads", response_class=HTMLResponse)
def dashboard_threads(request: Request):
    return templates.TemplateResponse("threads.html", {"request": request})


@router.get("/memory", response_class=HTMLResponse)
def dashboard_memory(request: Request):
    return templates.TemplateResponse("memory.html", {"request": request})


@router.get("/learn", response_class=HTMLResponse)
def dashboard_learn(request: Request):
    return templates.TemplateResponse("learn.html", {"request": request})


@router.get("/telemetry/run_group/{run_group_id}", response_class=HTMLResponse)
def dashboard_run_group_detail(request: Request, run_group_id: str):
    return templates.TemplateResponse(
        "run_group_detail.html",
        {"request": request, "run_group_id": run_group_id},
    )


@router.get("/spans", response_class=HTMLResponse)
def dashboard_spans(request: Request):
    return templates.TemplateResponse("spans.html", {"request": request})
