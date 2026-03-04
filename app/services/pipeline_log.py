from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import PipelineLog


def log_pipeline(db: Session, conversation_id: str, pipeline: str, stage: str, details: dict) -> None:
    db.add(PipelineLog(conversation_id=conversation_id, pipeline=pipeline, stage=stage, details_json=details))
    db.flush()
