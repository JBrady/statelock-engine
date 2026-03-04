from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Conversation, Thread, Turn
from app.services.pipeline_log import log_pipeline
from app.utils import cosine_similarity

SIMILARITY_THRESHOLD = 0.35


def infer_target_thread(
    db: Session,
    conversation: Conversation,
    query: str,
    target_thread_mode: str | None = None,
    pinned_thread_id: str | None = None,
) -> tuple[str, dict]:
    mode = target_thread_mode or conversation.target_thread_mode
    pinned = pinned_thread_id if pinned_thread_id is not None else conversation.pinned_thread_id

    threads = list(db.scalars(select(Thread).where(Thread.conversation_id == conversation.conversation_id)).all())
    if not threads:
        return "thread-1", {"mode": mode, "reason": "no_threads"}

    if mode == "pinned" and pinned:
        if any(t.thread_id == pinned for t in threads):
            return pinned, {"mode": "pinned", "reason": "conversation_or_request_pin"}

    scored = [(t, cosine_similarity(query, t.summary)) for t in threads]
    scored.sort(key=lambda x: x[1], reverse=True)
    best_thread, best_score = scored[0]

    if best_score >= SIMILARITY_THRESHOLD:
        top_score = best_score
        contenders = [t for t, score in scored if abs(score - top_score) < 1e-9]
        if len(contenders) > 1:
            contenders.sort(key=lambda t: t.last_activity_at, reverse=True)
            recent_t = contenders[0]
            recent_turns = list(
                db.scalars(
                    select(Turn)
                    .where(Turn.conversation_id == conversation.conversation_id)
                    .order_by(Turn.created_at.desc())
                    .limit(5)
                ).all()
            )
            overlap_scores = []
            for contender in contenders:
                text = " ".join(t.text for t in recent_turns)
                overlap_scores.append((contender, cosine_similarity(contender.summary, text)))
            overlap_scores.sort(key=lambda x: (x[1], x[0].thread_id == recent_t.thread_id), reverse=True)
            chosen = overlap_scores[0][0]
            rationale = {
                "mode": "auto",
                "score": best_score,
                "tie_break": "most_recent_activity_then_overlap_with_recent_turn",
            }
            return chosen.thread_id, rationale

        return best_thread.thread_id, {"mode": "auto", "score": best_score, "tie_break": "none"}

    threads.sort(key=lambda t: t.last_activity_at, reverse=True)
    return threads[0].thread_id, {"mode": "auto", "score": best_score, "reason": "below_threshold_recent_fallback"}


def log_target_thread(db: Session, conversation_id: str, target_thread_id: str, rationale: dict) -> None:
    log_pipeline(
        db,
        conversation_id,
        pipeline="target_thread_inference",
        stage="infer",
        details={"target_thread_id": target_thread_id, "rationale": rationale},
    )
