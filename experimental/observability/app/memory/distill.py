from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import MemoryEntry, Span, Turn
from app.utils import normalize_text


def _extract_episode_turns(db: Session, conversation_id: str) -> list[Turn]:
    turns = list(
        db.scalars(
            select(Turn)
            .where(Turn.conversation_id == conversation_id)
            .order_by(Turn.created_at.desc())
            .limit(40)
        ).all()
    )
    turns.reverse()
    return turns


def _semantic_candidates(turns: list[Turn]) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    for turn in turns:
        if turn.speaker != "user":
            continue
        text = normalize_text(turn.text)
        if len(text) < 20:
            continue
        title = text[:60]
        content = f"Fact: {text}"
        items.append((title, content))
        if len(items) >= 8:
            break
    return items


def _procedural_candidates(turns: list[Turn]) -> list[tuple[str, str]]:
    user_lines = [t.text for t in turns if t.speaker == "user"]
    assistant_lines = [t.text for t in turns if t.speaker == "assistant"]
    if not user_lines:
        return []

    title = "Task procedure from recent episode"
    applicability = user_lines[-1][:120]
    steps = [
        "Identify goal and constraints from user request.",
        "Apply minimal deterministic pipeline steps.",
        "Validate outputs and surface uncertainties.",
    ]
    if assistant_lines:
        steps.append(f"Reference working pattern: {assistant_lines[-1][:80]}")

    failure_modes = [
        "Missing thread segmentation causes off-target context.",
        "Over-budget context can hide critical evidence spans.",
        "Outdated memory entries can mislead procedure selection.",
    ]

    content = (
        f"Applicability: {applicability}\n"
        f"Steps:\n" + "\n".join(f"- {s}" for s in steps) + "\n"
        f"Failure modes:\n" + "\n".join(f"- {f}" for f in failure_modes)
    )
    return [(title, content)]


def _source_ids_for_turns(db: Session, conversation_id: str, turns: list[Turn]) -> tuple[list[str], list[str]]:
    turn_ids = [t.turn_id for t in turns]
    spans = list(
        db.scalars(
            select(Span)
            .where(Span.conversation_id == conversation_id)
            .order_by(Span.created_at.desc())
        ).all()
    )
    span_ids = []
    turn_set = set(turn_ids)
    for span in spans:
        if any(tid in turn_set for tid in (span.source_turn_ids_json or [])):
            span_ids.append(span.span_id)
    return turn_ids, span_ids


def distill_memory(db: Session, conversation_id: str, trigger: str) -> tuple[list[str], list[str], list[str]]:
    turns = _extract_episode_turns(db, conversation_id)
    now = datetime.utcnow()
    source_turn_ids, source_span_ids = _source_ids_for_turns(db, conversation_id, turns)

    existing = list(
        db.scalars(
            select(MemoryEntry)
            .where(MemoryEntry.conversation_id == conversation_id)
            .where(MemoryEntry.status == "active")
        ).all()
    )
    existing_titles = {normalize_text(e.title).lower(): e for e in existing}

    created: list[str] = []
    merged: list[str] = []
    quarantined: list[str] = []

    for title, content in _semantic_candidates(turns):
        key = normalize_text(title).lower()
        if key in existing_titles:
            e = existing_titles[key]
            e.updated_at = now
            e.strength = min(1.0, e.strength + 0.05)
            merged.append(e.memory_id)
            continue
        m = MemoryEntry(
            conversation_id=conversation_id,
            memory_type="semantic",
            title=title,
            content=content,
            tags_json=["distilled", trigger],
            strength=0.5,
            status="active",
            source_turn_ids_json=source_turn_ids,
            source_span_ids_json=source_span_ids,
        )
        db.add(m)
        db.flush()
        created.append(m.memory_id)

    for title, content in _procedural_candidates(turns)[:3]:
        key = normalize_text(title).lower()
        if key in existing_titles:
            e = existing_titles[key]
            if e.content != content:
                e.status = "deprecated"
                quarantined.append(e.memory_id)
            else:
                e.updated_at = now
                e.strength = min(1.0, e.strength + 0.05)
                merged.append(e.memory_id)
            continue

        m = MemoryEntry(
            conversation_id=conversation_id,
            memory_type="procedural",
            title=title,
            content=content,
            tags_json=["distilled", trigger],
            strength=0.5,
            status="active",
            source_turn_ids_json=source_turn_ids,
            source_span_ids_json=source_span_ids,
        )
        db.add(m)
        db.flush()
        created.append(m.memory_id)

    db.flush()
    return created, merged, quarantined
