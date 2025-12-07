from fastapi import FastAPI
from app.core.config import settings
from app.routers import memories

app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="Middleware for managing Agentic Memory.",
)

app.include_router(memories.router, prefix="/memories", tags=["Memories"])

@app.get("/", tags=["Root"])
async def root():
    return {"message": "Welcome to StateLock Engine API v2"}
