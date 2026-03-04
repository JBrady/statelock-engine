from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.backends.stub_llm import StubLLMBackend
from app.context_builder.builder import build_working_context
from app.db.models import Conversation, Span, TelemetrySnapshot, Turn
from app.telemetry.ablation import ablation_kl_influence, build_candidate_set
from app.telemetry.influence import proxy_influence
from app.telemetry.metrics import alarms, influence_entropy, off_thread_coupling, topk_threads


def _latest_coff(db: Session, conversation_id: str) -> float | None:
    latest = db.scalar(
        select(TelemetrySnapshot)
        .where(TelemetrySnapshot.conversation_id == conversation_id)
        .order_by(TelemetrySnapshot.created_at.desc())
    )
    if not latest:
        return None
    return float((latest.metrics_json or {}).get("off_thread_coupling_Coff", 0.0))


def _mode_for(conversation: Conversation, mode_override: str | None) -> str:
    if mode_override:
        return mode_override
    if conversation.telemetry_mode == "off":
        return "minimal"
    return conversation.telemetry_mode


def _should_run_ablation(mode: str, turn_index: int) -> tuple[bool, int]:
    if mode == "minimal":
        return False, 0
    if mode == "standard":
        return turn_index % 8 == 0, 12
    if mode == "verbose":
        return True, 16
    return False, 0


def _build_snapshot_metrics(rows: list[dict], target_thread_id: str, prev_coff: float | None, span_lookup: dict[str, Span]) -> dict:
    weights = [r["w"] for r in rows]
    h = influence_entropy(weights)
    _, coff = off_thread_coupling(rows, target_thread_id)
    alarm_map = alarms(rows, target_thread_id, prev_coff, span_lookup)
    return {
        "influence_entropy_H": h,
        "off_thread_coupling_Coff": coff,
        "topk_threads": topk_threads(rows),
        "alarms": {
            "anchor_rot": alarm_map["anchor_rot"],
            "smear_rot": alarm_map["smear_rot"],
            "off_thread_spike": alarm_map["off_thread_spike"],
        },
        "delta_coff": alarm_map["delta_coff"],
    }


def run_telemetry(
    db: Session,
    conversation: Conversation,
    turn_id: str,
    query: str,
    mode_override: str | None,
    backend: StubLLMBackend,
) -> list[TelemetrySnapshot]:
    mode = _mode_for(conversation, mode_override)
    wc = build_working_context(db, conversation, query=query)
    selected_spans = list(
        db.scalars(select(Span).where(Span.span_id.in_(wc.selected_span_ids_json))).all()
    )
    span_lookup = {s.span_id: s for s in selected_spans}

    run_group_id = str(uuid.uuid4())
    prev_coff = _latest_coff(db, conversation.conversation_id)

    proxy_kind, proxy_rows = proxy_influence(backend, selected_spans, query=query, target_thread_id=wc.target_thread_id)
    proxy_metrics = _build_snapshot_metrics(proxy_rows, wc.target_thread_id, prev_coff, span_lookup)

    proxy_snapshot = TelemetrySnapshot(
        conversation_id=conversation.conversation_id,
        turn_id=turn_id,
        run_group_id=run_group_id,
        target_thread_id=wc.target_thread_id,
        method="grad_proxy",
        proxy_kind=proxy_kind,
        spans_considered_json=[r["span_id"] for r in proxy_rows],
        weights_json=proxy_rows,
        metrics_json=proxy_metrics,
        actions_taken_json={
            "rebuilt_context": False,
            "quarantined_spans": [],
            "notes": "",
        },
    )
    db.add(proxy_snapshot)
    db.flush()

    snapshots = [proxy_snapshot]

    turn_index = db.query(Turn).filter(Turn.conversation_id == conversation.conversation_id).count()

    should_ablate, cap = _should_run_ablation(mode, max(1, turn_index))
    if should_ablate:
        if not selected_spans:
            proxy_snapshot.actions_taken_json = {
                "rebuilt_context": False,
                "quarantined_spans": [],
                "notes": "ablation_skipped_no_selected_spans",
            }
            db.flush()
            return snapshots

        candidates = build_candidate_set(
            db,
            conversation_id=conversation.conversation_id,
            selected_spans=selected_spans,
            proxy_rows=proxy_rows,
            query=query,
            max_total=cap,
        )
        if not candidates:
            proxy_snapshot.actions_taken_json = {
                "rebuilt_context": False,
                "quarantined_spans": [],
                "notes": "ablation_skipped_no_candidates",
            }
            db.flush()
            return snapshots

        ablation_rows = ablation_kl_influence(
            backend,
            query=query,
            target_thread_id=wc.target_thread_id,
            baseline_spans=selected_spans,
            candidate_spans=candidates,
        )
        ablation_span_lookup = {s.span_id: s for s in candidates}
        ablation_metrics = _build_snapshot_metrics(ablation_rows, wc.target_thread_id, prev_coff, ablation_span_lookup)

        ablation_snapshot = TelemetrySnapshot(
            conversation_id=conversation.conversation_id,
            turn_id=turn_id,
            run_group_id=run_group_id,
            target_thread_id=wc.target_thread_id,
            method="ablation_kl",
            proxy_kind=None,
            spans_considered_json=[s.span_id for s in candidates],
            weights_json=ablation_rows,
            metrics_json=ablation_metrics,
            actions_taken_json={
                "rebuilt_context": False,
                "quarantined_spans": [],
                "notes": "",
            },
        )
        db.add(ablation_snapshot)
        db.flush()
        snapshots.append(ablation_snapshot)

    return snapshots
