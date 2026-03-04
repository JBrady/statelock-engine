from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Conversation, MemoryEntry, Span, Turn, WorkingContext
from app.pipelines.threading import infer_target_thread, log_target_thread
from app.services.pipeline_log import log_pipeline
from app.utils import cosine_similarity, token_count_est, tokenize

DEFAULT_RECENT_TURNS = 6
MIN_RECENT_TURNS = 3
PINNED_MIN_TARGET_SPANS = 2


@dataclass
class ContextBuildOptions:
    restrict_to_target_thread: bool = False
    max_spans_delta: int = 0
    similarity_threshold_delta: float = 0.0


def _active_spans(db: Session, conversation_id: str, include_quarantined: bool = False) -> list[Span]:
    spans = list(
        db.scalars(
            select(Span)
            .where(Span.conversation_id == conversation_id)
            .order_by(Span.created_at.desc())
        ).all()
    )
    if include_quarantined:
        return spans
    now = datetime.utcnow()
    return [s for s in spans if not s.quarantined_until or s.quarantined_until <= now]


def _select_procedures(db: Session, conversation_id: str, query: str, target_thread_id: str) -> list[MemoryEntry]:
    mems = list(
        db.scalars(
            select(MemoryEntry)
            .where(MemoryEntry.memory_type == "procedural")
            .where(MemoryEntry.status == "active")
            .where((MemoryEntry.conversation_id == conversation_id) | (MemoryEntry.conversation_id.is_(None)))
            .order_by(MemoryEntry.updated_at.desc())
        ).all()
    )
    scored = []
    for m in mems:
        score = cosine_similarity(query + " " + target_thread_id, m.title + " " + m.content)
        scored.append((m, score + (0.1 * m.strength)))
    scored.sort(key=lambda x: x[1], reverse=True)
    return [m for m, _ in scored[:2]]


def _score_span(span: Span, query: str, now: datetime) -> tuple[float, float, float]:
    relevance = cosine_similarity(query, span.text)
    age_minutes = max(0.0, (now - span.created_at).total_seconds() / 60.0)
    recency_score = 1.0 / (1.0 + age_minutes / 60.0)
    trust = span.trust_score
    total = 0.55 * relevance + 0.2 * recency_score + 0.25 * trust
    return total, relevance, recency_score


def _expand_with_provenance(span_by_id: dict[str, Span], selected: list[Span]) -> list[Span]:
    seen = {s.span_id for s in selected}
    expanded = list(selected)
    for span in selected:
        for pid in (span.provenance_json or []):
            if pid in span_by_id and pid not in seen:
                expanded.append(span_by_id[pid])
                seen.add(pid)
    return expanded


def _assemble_text(procedures: list[MemoryEntry], selected_spans: list[Span], recent_turns: list[Turn]) -> str:
    return _assemble_text_with_options(
        procedures=procedures,
        selected_spans=selected_spans,
        recent_turns=recent_turns,
        recent_turn_limit=DEFAULT_RECENT_TURNS,
        tool_output_word_limit=180,
    )


def _truncate_words(text: str, max_words: int) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + " ... [truncated]"


def _assemble_text_with_options(
    procedures: list[MemoryEntry],
    selected_spans: list[Span],
    recent_turns: list[Turn],
    recent_turn_limit: int,
    tool_output_word_limit: int,
) -> str:
    header = (
        "You are the assistant. Use ONLY the provided context. "
        "If you need missing details, ask a single focused question."
    )

    proc_txt = "\n".join(f"- {m.title}: {m.content}" for m in procedures) or "- None"
    fact_spans = [s for s in selected_spans if s.span_type in {"dialog", "distilled_fact"}]
    facts_txt = "\n".join(f"- {s.text[:220]} [span:{s.span_id} thread:{s.thread_id}]" for s in fact_spans[:8]) or "- None"

    if recent_turn_limit > 0:
        recent_slice = recent_turns[-recent_turn_limit:]
    else:
        recent_slice = []
    recent_txt = "\n".join(f"- {t.speaker}: {t.text[:220]}" for t in recent_slice) or "- None"
    evidence_txt = "\n".join(
        f"- {s.text[:260]} [span:{s.span_id} thread:{s.thread_id}]" for s in selected_spans
    ) or "- None"
    tool_txt = "\n".join(
        f"- {_truncate_words(s.text, tool_output_word_limit)[:260]} [span:{s.span_id} thread:{s.thread_id}]"
        for s in selected_spans
        if s.span_type == "tool_output"
    ) or "- None"

    return (
        f"{header}\n\n"
        f"Procedures:\n{proc_txt}\n\n"
        f"Key Facts:\n{facts_txt}\n\n"
        f"Recent Turns:\n{recent_txt}\n\n"
        f"Evidence Spans:\n{evidence_txt}\n\n"
        f"Tool Outputs (truncated):\n{tool_txt}\n"
    )


def build_working_context(
    db: Session,
    conversation: Conversation,
    query: str,
    target_thread_mode: str | None = None,
    pinned_thread_id: str | None = None,
    max_context_tokens: int | None = None,
    options: ContextBuildOptions | None = None,
) -> WorkingContext:
    opts = options or ContextBuildOptions()

    target_thread_id, rationale = infer_target_thread(
        db,
        conversation,
        query=query,
        target_thread_mode=target_thread_mode,
        pinned_thread_id=pinned_thread_id,
    )
    log_target_thread(db, conversation.conversation_id, target_thread_id, rationale)
    pinned_mode = rationale.get("mode") == "pinned"

    procedures = _select_procedures(db, conversation.conversation_id, query, target_thread_id)
    spans = _active_spans(db, conversation.conversation_id)
    span_by_id = {s.span_id: s for s in spans}
    now = datetime.utcnow()

    scored: list[tuple[Span, float, float, float, bool]] = []
    for span in spans:
        if opts.restrict_to_target_thread and span.thread_id != target_thread_id:
            continue
        if span.thread_id != target_thread_id:
            base, rel, rec = _score_span(span, query, now)
            # keep off-thread spans only when query similarity is meaningful.
            if rel < 0.5:
                continue
            base *= 0.35
            scored.append((span, base, rel, rec, True))
        else:
            base, rel, rec = _score_span(span, query, now)
            scored.append((span, base, rel, rec, False))

    scored.sort(key=lambda x: x[1], reverse=True)
    max_spans = max(4, 24 + opts.max_spans_delta)
    selected_base: list[Span] = []
    off_thread_count = 0
    for span, _, _, _, is_off_thread in scored:
        if is_off_thread and off_thread_count >= 2:
            continue
        selected_base.append(span)
        if is_off_thread:
            off_thread_count += 1
        if len(selected_base) >= max_spans:
            break

    if pinned_mode:
        target_ranked = [span for span, _, _, _, _ in scored if span.thread_id == target_thread_id]
        for span in target_ranked:
            if len([s for s in selected_base if s.thread_id == target_thread_id]) >= PINNED_MIN_TARGET_SPANS:
                break
            if span not in selected_base:
                selected_base.append(span)

    selected = _expand_with_provenance(span_by_id, selected_base)

    span_scoring_all = {
        s.span_id: {"score": score, "relevance": rel, "recency": rec}
        for s, score, rel, rec, _ in scored
    }

    recent_turns = list(
        db.scalars(
            select(Turn)
            .where(Turn.conversation_id == conversation.conversation_id)
            .order_by(Turn.created_at.asc())
        ).all()
    )

    selected_unique = list({s.span_id: s for s in selected}.values())
    selected_before_budget = [s.span_id for s in selected_unique]
    span_scoring: dict[str, dict] = {}
    for span in selected_unique:
        if span.span_id in span_scoring_all:
            span_scoring[span.span_id] = span_scoring_all[span.span_id]
        else:
            score, rel, rec = _score_span(span, query, now)
            span_scoring[span.span_id] = {"score": score, "relevance": rel, "recency": rec}

    recent_turn_limit = DEFAULT_RECENT_TURNS
    tool_output_word_limit = 180
    assembled = _assemble_text_with_options(
        procedures=procedures,
        selected_spans=selected_unique,
        recent_turns=recent_turns,
        recent_turn_limit=recent_turn_limit,
        tool_output_word_limit=tool_output_word_limit,
    )
    budget = max_context_tokens or conversation.max_context_tokens

    dropped: list[dict] = []
    pinned_protected_ids: set[str] = set()
    if pinned_mode:
        target_ranked_scores = sorted(
            [s for s in selected_unique if s.thread_id == target_thread_id],
            key=lambda s: span_scoring.get(s.span_id, {}).get("score", 0.0),
            reverse=True,
        )
        pinned_protected_ids = {s.span_id for s in target_ranked_scores[:PINNED_MIN_TARGET_SPANS]}

    def _drop_until_budget(candidates: list[Span], reason: str) -> None:
        nonlocal assembled, selected_unique
        if token_count_est(assembled) <= budget:
            return
        for span in candidates:
            if reason == "drop_low_relevance" and span.span_id in pinned_protected_ids:
                continue
            if span in selected_unique:
                selected_unique.remove(span)
                dropped.append({"span_id": span.span_id, "reason": reason})
                assembled = _assemble_text_with_options(
                    procedures=procedures,
                    selected_spans=selected_unique,
                    recent_turns=recent_turns,
                    recent_turn_limit=recent_turn_limit,
                    tool_output_word_limit=tool_output_word_limit,
                )
                if token_count_est(assembled) <= budget:
                    break

    if token_count_est(assembled) > budget and recent_turn_limit > MIN_RECENT_TURNS:
        recent_turn_limit = MIN_RECENT_TURNS
        dropped.append({"reason": "trim_recent_turns", "kept_recent_turns": MIN_RECENT_TURNS})
        assembled = _assemble_text_with_options(
            procedures=procedures,
            selected_spans=selected_unique,
            recent_turns=recent_turns,
            recent_turn_limit=recent_turn_limit,
            tool_output_word_limit=tool_output_word_limit,
        )

    if token_count_est(assembled) > budget and any(s.span_type == "tool_output" for s in selected_unique):
        tool_output_word_limit = 40
        dropped.append({"reason": "compress_long_tool_outputs", "tool_output_word_limit": tool_output_word_limit})
        assembled = _assemble_text_with_options(
            procedures=procedures,
            selected_spans=selected_unique,
            recent_turns=recent_turns,
            recent_turn_limit=recent_turn_limit,
            tool_output_word_limit=tool_output_word_limit,
        )

    low_trust = sorted([s for s in selected_unique if s.trust_score < 0.5], key=lambda s: s.trust_score)
    _drop_until_budget(low_trust, "drop_low_trust")

    old_unused = sorted(
        [
            s
            for s in selected_unique
            if (now - s.first_seen_at).total_seconds() / 60.0 > 120
            and (s.last_used_at is None or (now - s.last_used_at).total_seconds() / 60.0 > 120)
        ],
        key=lambda s: s.first_seen_at.timestamp(),
    )
    _drop_until_budget(old_unused, "drop_old_unused")

    low_relevance = sorted(
        [s for s in selected_unique if s.span_type != "tool_output"],
        key=lambda s: span_scoring.get(s.span_id, {}).get("relevance", 0.0),
    )
    _drop_until_budget(low_relevance, "drop_low_relevance")

    if not selected_unique and selected_before_budget:
        best_span_id = max(
            selected_before_budget,
            key=lambda sid: span_scoring.get(sid, {}).get("score", 0.0),
        )
        best_span = span_by_id.get(best_span_id)
        if best_span is not None:
            selected_unique = [best_span]
            dropped.append({"span_id": best_span_id, "reason": "fallback_keep_best_span"})
            assembled = _assemble_text_with_options(
                procedures=procedures,
                selected_spans=selected_unique,
                recent_turns=recent_turns,
                recent_turn_limit=recent_turn_limit,
                tool_output_word_limit=tool_output_word_limit,
            )

    if token_count_est(assembled) > budget:
        clipped_tokens = tokenize(assembled)[:budget]
        assembled = " ".join(clipped_tokens)

    for span in selected_unique:
        span.last_used_at = now

    wc = WorkingContext(
        conversation_id=conversation.conversation_id,
        target_thread_id=target_thread_id,
        selected_span_ids_json=[s.span_id for s in selected_unique],
        assembled_text=assembled,
        token_count_est=token_count_est(assembled),
        selection_method="heuristic",
        selection_log_json={
            "target_rationale": rationale,
            "budget": budget,
            "selected_before_budget": selected_before_budget,
            "selected_after_budget": [s.span_id for s in selected_unique],
            "drop_order": dropped,
            "scores": span_scoring,
            "options": {
                "restrict_to_target_thread": opts.restrict_to_target_thread,
                "max_spans_delta": opts.max_spans_delta,
                "similarity_threshold_delta": opts.similarity_threshold_delta,
            },
        },
    )
    db.add(wc)
    db.flush()

    log_pipeline(
        db,
        conversation.conversation_id,
        pipeline="working_context_builder",
        stage="build",
        details={
            "working_context_id": wc.working_context_id,
            "target_thread_id": target_thread_id,
            "token_count_est": wc.token_count_est,
            "selected_span_ids": wc.selected_span_ids_json,
            "drop_order": dropped,
        },
    )

    return wc
