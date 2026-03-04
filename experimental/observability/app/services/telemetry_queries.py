from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Conversation, TelemetrySnapshot
from app.services.serializers import telemetry_snapshot_out

EMPTY_ACTIONS = {"rebuilt_context": False, "quarantined_spans": [], "notes": ""}


ALARM_EXPLANATIONS = {
    "anchor_rot": "A stale or off-thread anchor dominates influence.",
    "smear_rot": "Influence is spread thinly across many spans, indicating context smear.",
    "off_thread_spike": "Influence from non-target threads spiked relative to prior state.",
}


def _canonical_snapshot_order(stmt):
    return stmt.order_by(TelemetrySnapshot.created_at.desc(), TelemetrySnapshot.snapshot_id.desc())


def get_recent_snapshots(
    db: Session,
    conversation_id: str,
    limit: int = 20,
    include_actions: bool = True,
):
    rows = list(
        db.scalars(
            _canonical_snapshot_order(
                select(TelemetrySnapshot).where(TelemetrySnapshot.conversation_id == conversation_id)
            ).limit(max(1, limit))
        ).all()
    )

    out = []
    for row in rows:
        snap = telemetry_snapshot_out(row)
        if not include_actions:
            snap.actions_taken = dict(EMPTY_ACTIONS)
        out.append(snap)
    return out


def _group_sort_key(group: dict) -> tuple[datetime, str]:
    return group["created_at_max"], group["run_group_id"]


def get_recent_run_groups(
    db: Session,
    conversation_id: str,
    limit: int = 20,
) -> list[dict]:
    rows = list(
        db.scalars(
            _canonical_snapshot_order(
                select(TelemetrySnapshot).where(TelemetrySnapshot.conversation_id == conversation_id)
            )
        ).all()
    )

    by_group: dict[str, list[TelemetrySnapshot]] = {}
    for row in rows:
        by_group.setdefault(row.run_group_id, []).append(row)

    groups: list[dict] = []
    for run_group_id, snaps in by_group.items():
        snaps_sorted = sorted(
            snaps,
            key=lambda s: (s.created_at, s.snapshot_id),
            reverse=True,
        )

        has_proxy = any(s.method == "grad_proxy" for s in snaps_sorted)
        has_ablation = any(s.method == "ablation_kl" for s in snaps_sorted)

        preferred = next((s for s in snaps_sorted if s.method == "ablation_kl"), None)
        if preferred is None:
            preferred = next((s for s in snaps_sorted if s.method == "grad_proxy"), None)
        if preferred is None:
            preferred = snaps_sorted[0]

        metrics = preferred.metrics_json or {}
        groups.append(
            {
                "run_group_id": run_group_id,
                "created_at_min": min(s.created_at for s in snaps_sorted),
                "created_at_max": max(s.created_at for s in snaps_sorted),
                "turn_id": preferred.turn_id,
                "target_thread_id": preferred.target_thread_id,
                "has_proxy": has_proxy,
                "has_ablation": has_ablation,
                "Coff": float(metrics.get("off_thread_coupling_Coff", 0.0)),
                "H": float(metrics.get("influence_entropy_H", 0.0)),
                "alarms": metrics.get("alarms", {}),
                "snapshot_ids": [s.snapshot_id for s in snaps_sorted],
            }
        )

    groups.sort(key=_group_sort_key, reverse=True)
    return groups[: max(1, limit)]


def get_run_group_details(db: Session, conversation_id: str, run_group_id: str) -> list[TelemetrySnapshot]:
    rows = list(
        db.scalars(
            _canonical_snapshot_order(
                select(TelemetrySnapshot)
                .where(TelemetrySnapshot.conversation_id == conversation_id)
                .where(TelemetrySnapshot.run_group_id == run_group_id)
            )
        ).all()
    )
    return rows


def explain_snapshot(db: Session, conversation_id: str, snapshot_id: str) -> dict | None:
    snap = db.get(TelemetrySnapshot, snapshot_id)
    if not snap or snap.conversation_id != conversation_id:
        return None

    metrics = snap.metrics_json or {}
    alarms = metrics.get("alarms", {})
    alarm_explanations = {
        name: {
            "triggered": bool(alarms.get(name, False)),
            "explanation": text,
        }
        for name, text in ALARM_EXPLANATIONS.items()
    }

    coff = float(metrics.get("off_thread_coupling_Coff", 0.0))
    entropy_h = float(metrics.get("influence_entropy_H", 0.0))
    active = [name for name, value in alarms.items() if value]
    active_text = ", ".join(sorted(active)) if active else "none"
    summary = (
        f"Snapshot {snap.snapshot_id} uses {snap.method}; "
        f"Coff={coff:.3f}, H={entropy_h:.3f}; active alarms: {active_text}."
    )

    return {
        "snapshot": {
            "snapshot_id": snap.snapshot_id,
            "conversation_id": snap.conversation_id,
            "turn_id": snap.turn_id,
            "run_group_id": snap.run_group_id,
            "created_at": snap.created_at,
            "target_thread_id": snap.target_thread_id,
            "method": snap.method,
            "proxy_kind": snap.proxy_kind,
            "spans_considered": snap.spans_considered_json or [],
            "metrics": metrics,
            "actions_taken": snap.actions_taken_json or dict(EMPTY_ACTIONS),
        },
        "influence_weights": snap.weights_json or [],
        "alarm_explanations": alarm_explanations,
        "diagnostic_summary": summary,
    }


def ensure_conversation_exists(db: Session, conversation_id: str) -> Conversation | None:
    return db.get(Conversation, conversation_id)
