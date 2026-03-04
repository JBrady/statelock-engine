from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Conversation, MemoryEntry, Span, TelemetrySnapshot, Thread, Turn

BUNDLE_VERSION = "statelock_v2_bundle_v1"


def _row_to_dict(row: Any) -> dict[str, Any]:
    return {column.name: getattr(row, column.name) for column in row.__table__.columns}


def _parse_dt(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    raise ValueError(f"Invalid datetime value: {value!r}")


def _ts(payload: dict[str, Any], key: str, now: datetime, default: datetime | None = None) -> datetime | None:
    if key not in payload:
        return default if default is not None else now
    parsed = _parse_dt(payload.get(key))
    if parsed is None:
        return default
    return parsed


def _sorted_rows(rows: list[dict[str, Any]], id_key: str) -> list[dict[str, Any]]:
    def _key(row: dict[str, Any]) -> tuple[datetime, str]:
        created = _parse_dt(row.get("created_at")) or datetime.min
        return created, str(row.get(id_key) or "")

    return sorted(rows, key=_key)


def _new_id(kind: str, source_id: str, conversation_seed: str) -> str:
    namespace = uuid.uuid5(uuid.NAMESPACE_URL, f"statelock:{conversation_seed}")
    return str(uuid.uuid5(namespace, f"{kind}:{source_id}"))


def _map_id_list(values: list[Any], id_map: dict[str, str]) -> list[Any]:
    out = []
    for value in values or []:
        if isinstance(value, str) and value in id_map:
            out.append(id_map[value])
        else:
            out.append(value)
    return out


def _validate_scoped_rows(rows: list[dict[str, Any]], old_conversation_id: str, entity_name: str) -> None:
    for row in rows:
        row_cid = row.get("conversation_id")
        if row_cid is not None and row_cid != old_conversation_id:
            raise ValueError(
                f"Invalid {entity_name} row: conversation_id {row_cid} does not match bundle conversation_id {old_conversation_id}"
            )


def export_conversation_bundle(db: Session, conversation_id: str) -> dict[str, Any] | None:
    conversation = db.get(Conversation, conversation_id)
    if not conversation:
        return None

    turns = list(
        db.scalars(
            select(Turn)
            .where(Turn.conversation_id == conversation_id)
            .order_by(Turn.created_at.asc(), Turn.turn_id.asc())
        ).all()
    )
    spans = list(
        db.scalars(
            select(Span)
            .where(Span.conversation_id == conversation_id)
            .order_by(Span.created_at.asc(), Span.span_id.asc())
        ).all()
    )
    threads = list(
        db.scalars(
            select(Thread)
            .where(Thread.conversation_id == conversation_id)
            .order_by(Thread.created_at.asc(), Thread.thread_id.asc())
        ).all()
    )
    snapshots = list(
        db.scalars(
            select(TelemetrySnapshot)
            .where(TelemetrySnapshot.conversation_id == conversation_id)
            .order_by(TelemetrySnapshot.created_at.asc(), TelemetrySnapshot.snapshot_id.asc())
        ).all()
    )
    memories = list(
        db.scalars(
            select(MemoryEntry)
            .where(MemoryEntry.conversation_id == conversation_id)
            .order_by(MemoryEntry.created_at.asc(), MemoryEntry.memory_id.asc())
        ).all()
    )

    return {
        "bundle_version": BUNDLE_VERSION,
        "exported_at": datetime.utcnow(),
        "conversation": _row_to_dict(conversation),
        "turns": [_row_to_dict(row) for row in turns],
        "spans": [_row_to_dict(row) for row in spans],
        "threads": [_row_to_dict(row) for row in threads],
        "telemetry_snapshots": [_row_to_dict(row) for row in snapshots],
        "memory_records": [_row_to_dict(row) for row in memories],
    }


def import_conversation_bundle(db: Session, bundle: dict[str, Any]) -> dict[str, Any]:
    now = datetime.utcnow()

    version = bundle.get("bundle_version")
    if not version:
        raise ValueError("Missing bundle_version")
    if version != BUNDLE_VERSION:
        raise ValueError(f"Unknown bundle_version: {version}")

    conversation_payload = bundle.get("conversation")
    if not isinstance(conversation_payload, dict):
        raise ValueError("Bundle is missing conversation object")

    old_conversation_id = str(conversation_payload.get("conversation_id") or "")
    if not old_conversation_id:
        raise ValueError("Conversation object missing conversation_id")

    turns_payload = list(bundle.get("turns") or [])
    spans_payload = list(bundle.get("spans") or [])
    threads_payload = list(bundle.get("threads") or [])
    snapshots_payload = list(bundle.get("telemetry_snapshots") or [])
    memories_payload = list(bundle.get("memory_records") or [])

    _validate_scoped_rows(turns_payload, old_conversation_id, "turn")
    _validate_scoped_rows(spans_payload, old_conversation_id, "span")
    _validate_scoped_rows(threads_payload, old_conversation_id, "thread")
    _validate_scoped_rows(snapshots_payload, old_conversation_id, "telemetry")
    _validate_scoped_rows(memories_payload, old_conversation_id, "memory")

    new_conversation_id = str(uuid.uuid4())

    import_map = {
        "conversations": {old_conversation_id: new_conversation_id},
        "turns": {},
        "spans": {},
        "threads": {},
        "snapshots": {},
        "memory": {},
        "run_groups": {},
    }

    new_conversation = Conversation(
        conversation_id=new_conversation_id,
        created_at=_ts(conversation_payload, "created_at", now),
        updated_at=_ts(conversation_payload, "updated_at", now),
        title=str(conversation_payload.get("title") or "Imported conversation"),
        tags_json=list(conversation_payload.get("tags_json") or []),
        notes=str(conversation_payload.get("notes") or ""),
        max_context_tokens=int(conversation_payload.get("max_context_tokens") or 6000),
        telemetry_mode=str(conversation_payload.get("telemetry_mode") or "standard"),
        target_thread_mode=str(conversation_payload.get("target_thread_mode") or "auto"),
        pinned_thread_id=None,
    )
    db.add(new_conversation)

    sorted_threads = _sorted_rows(threads_payload, "thread_id")
    for payload in sorted_threads:
        old_thread_id = str(payload.get("thread_id") or "")
        if not old_thread_id:
            raise ValueError("Thread row missing thread_id")
        new_thread_id = _new_id("thread", old_thread_id, new_conversation_id)
        import_map["threads"][old_thread_id] = new_thread_id

    pinned_old = conversation_payload.get("pinned_thread_id")
    if pinned_old:
        new_conversation.pinned_thread_id = import_map["threads"].get(str(pinned_old))

    for payload in sorted_threads:
        old_thread_id = str(payload.get("thread_id"))
        db.add(
            Thread(
                conversation_id=new_conversation_id,
                thread_id=import_map["threads"][old_thread_id],
                name=str(payload.get("name") or "Thread"),
                summary=str(payload.get("summary") or ""),
                created_at=_ts(payload, "created_at", now),
                updated_at=_ts(payload, "updated_at", now),
                span_count=int(payload.get("span_count") or 0),
                last_activity_at=_ts(payload, "last_activity_at", now, default=now) or now,
            )
        )

    sorted_turns = _sorted_rows(turns_payload, "turn_id")
    for payload in sorted_turns:
        old_turn_id = str(payload.get("turn_id") or "")
        if not old_turn_id:
            raise ValueError("Turn row missing turn_id")
        import_map["turns"][old_turn_id] = _new_id("turn", old_turn_id, new_conversation_id)

    for payload in sorted_turns:
        old_turn_id = str(payload.get("turn_id"))
        db.add(
            Turn(
                turn_id=import_map["turns"][old_turn_id],
                conversation_id=new_conversation_id,
                created_at=_ts(payload, "created_at", now),
                speaker=str(payload.get("speaker") or "user"),
                text=str(payload.get("text") or ""),
                tool_name=payload.get("tool_name"),
                tool_payload_ref=payload.get("tool_payload_ref"),
                token_count=payload.get("token_count"),
                thread_hint=payload.get("thread_hint"),
                importance_hint=payload.get("importance_hint"),
            )
        )

    sorted_spans = _sorted_rows(spans_payload, "span_id")
    for payload in sorted_spans:
        old_span_id = str(payload.get("span_id") or "")
        if not old_span_id:
            raise ValueError("Span row missing span_id")
        import_map["spans"][old_span_id] = _new_id("span", old_span_id, new_conversation_id)

    for payload in sorted_spans:
        old_span_id = str(payload.get("span_id"))
        old_thread_id = str(payload.get("thread_id") or "")
        new_thread_id = import_map["threads"].get(old_thread_id)
        if not new_thread_id:
            raise ValueError(f"Span {old_span_id} references unknown thread_id {old_thread_id}")

        db.add(
            Span(
                span_id=import_map["spans"][old_span_id],
                conversation_id=new_conversation_id,
                created_at=_ts(payload, "created_at", now),
                source_turn_ids_json=_map_id_list(list(payload.get("source_turn_ids_json") or []), import_map["turns"]),
                text=str(payload.get("text") or ""),
                token_count_est=int(payload.get("token_count_est") or 0),
                thread_id=new_thread_id,
                span_type=str(payload.get("span_type") or "dialog"),
                trust_score=float(payload.get("trust_score") or 0.8),
                trust_reason=str(payload.get("trust_reason") or "default"),
                last_used_at=_ts(payload, "last_used_at", now, default=None),
                first_seen_at=_ts(payload, "first_seen_at", now, default=_ts(payload, "created_at", now)) or now,
                semantic_neighbors_json=_map_id_list(list(payload.get("semantic_neighbors_json") or []), import_map["spans"]),
                provenance_json=_map_id_list(list(payload.get("provenance_json") or []), import_map["spans"]),
                contradictions_json=_map_id_list(list(payload.get("contradictions_json") or []), import_map["spans"]),
                quarantined_until=_ts(payload, "quarantined_until", now, default=None),
            )
        )

    run_group_map: dict[str, str] = {}
    sorted_snapshots = _sorted_rows(snapshots_payload, "snapshot_id")
    for payload in sorted_snapshots:
        old_snapshot_id = str(payload.get("snapshot_id") or "")
        old_turn_id = str(payload.get("turn_id") or "")
        old_target_thread = str(payload.get("target_thread_id") or "")
        old_run_group_id = str(payload.get("run_group_id") or "")

        if not old_snapshot_id:
            raise ValueError("Telemetry row missing snapshot_id")
        if not old_turn_id:
            raise ValueError(f"Telemetry snapshot {old_snapshot_id} missing turn_id")
        if not old_target_thread:
            raise ValueError(f"Telemetry snapshot {old_snapshot_id} missing target_thread_id")
        if old_turn_id and old_turn_id not in import_map["turns"]:
            raise ValueError(f"Telemetry snapshot {old_snapshot_id} references unknown turn_id {old_turn_id}")
        if old_target_thread and old_target_thread not in import_map["threads"]:
            raise ValueError(
                f"Telemetry snapshot {old_snapshot_id} references unknown target_thread_id {old_target_thread}"
            )

        if old_run_group_id and old_run_group_id not in run_group_map:
            run_group_map[old_run_group_id] = _new_id("run_group", old_run_group_id, new_conversation_id)

        new_snapshot_id = _new_id("snapshot", old_snapshot_id, new_conversation_id)
        import_map["snapshots"][old_snapshot_id] = new_snapshot_id

        weights = []
        for row in list(payload.get("weights_json") or []):
            if not isinstance(row, dict):
                continue
            row_copy = dict(row)
            if isinstance(row_copy.get("span_id"), str):
                row_copy["span_id"] = import_map["spans"].get(row_copy["span_id"], row_copy["span_id"])
            if isinstance(row_copy.get("thread_id"), str):
                row_copy["thread_id"] = import_map["threads"].get(row_copy["thread_id"], row_copy["thread_id"])
            weights.append(row_copy)

        actions = dict(payload.get("actions_taken_json") or {})
        if isinstance(actions.get("quarantined_spans"), list):
            actions["quarantined_spans"] = _map_id_list(actions["quarantined_spans"], import_map["spans"])

        db.add(
            TelemetrySnapshot(
                snapshot_id=new_snapshot_id,
                conversation_id=new_conversation_id,
                turn_id=import_map["turns"].get(old_turn_id, ""),
                run_group_id=run_group_map.get(old_run_group_id, _new_id("run_group", old_run_group_id, new_conversation_id)),
                created_at=_ts(payload, "created_at", now),
                target_thread_id=import_map["threads"].get(old_target_thread, old_target_thread),
                method=str(payload.get("method") or "grad_proxy"),
                proxy_kind=payload.get("proxy_kind"),
                spans_considered_json=_map_id_list(list(payload.get("spans_considered_json") or []), import_map["spans"]),
                weights_json=weights,
                metrics_json=dict(payload.get("metrics_json") or {}),
                actions_taken_json=actions,
            )
        )

    import_map["run_groups"] = run_group_map

    sorted_memory = _sorted_rows(memories_payload, "memory_id")
    for payload in sorted_memory:
        old_memory_id = str(payload.get("memory_id") or "")
        if not old_memory_id:
            raise ValueError("Memory row missing memory_id")

        new_memory_id = _new_id("memory", old_memory_id, new_conversation_id)
        import_map["memory"][old_memory_id] = new_memory_id

        db.add(
            MemoryEntry(
                memory_id=new_memory_id,
                conversation_id=new_conversation_id,
                created_at=_ts(payload, "created_at", now),
                updated_at=_ts(payload, "updated_at", now),
                memory_type=str(payload.get("memory_type") or "semantic"),
                title=str(payload.get("title") or "Imported memory"),
                content=str(payload.get("content") or ""),
                tags_json=list(payload.get("tags_json") or []),
                strength=float(payload.get("strength") or 0.5),
                status=str(payload.get("status") or "active"),
                source_turn_ids_json=_map_id_list(list(payload.get("source_turn_ids_json") or []), import_map["turns"]),
                source_span_ids_json=_map_id_list(list(payload.get("source_span_ids_json") or []), import_map["spans"]),
                success_count=int(payload.get("success_count") or 0),
                failure_count=int(payload.get("failure_count") or 0),
                last_applied_at=_ts(payload, "last_applied_at", now, default=None),
            )
        )

    return {
        "new_conversation_id": new_conversation_id,
        "import_map": import_map,
    }
