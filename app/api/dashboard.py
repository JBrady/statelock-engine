from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["dashboard"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def dashboard_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/threads", response_class=HTMLResponse)
def dashboard_threads(request: Request):
    return templates.TemplateResponse("threads.html", {"request": request})


@router.get("/memory", response_class=HTMLResponse)
def dashboard_memory(request: Request):
    return templates.TemplateResponse("memory.html", {"request": request})
