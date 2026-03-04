from __future__ import annotations

import math
from datetime import datetime
from typing import Any

from app.db.models import Span


def _safe_non_negative(value: Any) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return 0.0
    if not math.isfinite(out) or out < 0.0:
        return 0.0
    return out


def normalize_weights(raw_items: list[Any], eps: float = 1e-12) -> list[float]:
    n = len(raw_items)
    if n == 0:
        return []

    raw_values: list[float] = []
    for item in raw_items:
        if isinstance(item, dict):
            raw_values.append(_safe_non_negative(item.get("raw_score", 0.0)))
        else:
            raw_values.append(_safe_non_negative(item))

    total = sum(raw_values)
    if total <= eps:
        return [1.0 / n] * n

    weights = [v / total for v in raw_values]
    sum_w = sum(weights)
    if sum_w <= eps:
        return [1.0 / n] * n

    weights = [w / sum_w for w in weights]
    drift = 1.0 - sum(weights)
    if abs(drift) > 1e-9:
        idx_max = max(range(n), key=lambda i: weights[i])
        weights[idx_max] += drift

    weights = [max(0.0, w) for w in weights]
    sum_w = sum(weights)
    if sum_w <= eps:
        return [1.0 / n] * n
    weights = [w / sum_w for w in weights]
    drift = 1.0 - sum(weights)
    if abs(drift) > 1e-9:
        idx_max = max(range(n), key=lambda i: weights[i])
        weights[idx_max] += drift
    return weights


def normalize_scores(rows: list[dict]) -> list[dict]:
    weights = normalize_weights(rows)
    for row, weight in zip(rows, weights):
        row["w"] = weight
    return rows


def influence_entropy(weights: list[float], eps: float = 1e-12) -> float:
    if not weights:
        return 0.0
    if len(weights) == 1:
        return 0.0

    weights = normalize_weights(weights, eps=eps)
    h = float(-sum(w * math.log(w + eps) for w in weights))
    if h < 0:
        h = 0.0
    return h


def off_thread_coupling(rows: list[dict], target_thread_id: str) -> tuple[float, float]:
    if not rows:
        return 0.0, 0.0

    weights = normalize_weights([r.get("w", 0.0) for r in rows])
    w_target = sum(w for w, row in zip(weights, rows) if row.get("thread_id") == target_thread_id)
    w_target = min(1.0, max(0.0, w_target))
    coff = 1.0 - w_target
    coff = min(1.0, max(0.0, coff))
    return w_target, coff


def topk_threads(rows: list[dict], k: int = 3) -> list[dict]:
    acc: dict[str, float] = {}
    for row in rows:
        tid = row["thread_id"]
        acc[tid] = acc.get(tid, 0.0) + row.get("w", 0.0)
    return [{"thread_id": t, "W": w} for t, w in sorted(acc.items(), key=lambda x: x[1], reverse=True)[:k]]


def alarms(rows: list[dict], target_thread_id: str, prev_coff: float | None, span_lookup: dict[str, Span]) -> dict:
    now = datetime.utcnow()
    stable_weights = normalize_weights([r.get("w", 0.0) for r in rows])
    stable_rows = []
    for row, weight in zip(rows, stable_weights):
        stable = dict(row)
        stable["w"] = weight
        stable_rows.append(stable)

    top = max(stable_rows, key=lambda r: r.get("w", 0.0), default=None)
    anchor_rot = False
    if top:
        span = span_lookup.get(top["span_id"])
        if span:
            age_min = (now - span.created_at).total_seconds() / 60.0
            anchor_rot = bool(top["w"] >= 0.55 and age_min > 120 and span.thread_id != target_thread_id)

    weights = [r.get("w", 0.0) for r in stable_rows]
    h = influence_entropy(weights)
    active_spread = sum(1 for w in weights if w > 0.05)
    smear_rot = bool(h >= 2.0 and active_spread >= 10)

    _, coff = off_thread_coupling(stable_rows, target_thread_id)
    delta = coff - prev_coff if prev_coff is not None else 0.0
    off_thread_spike = bool(coff >= 0.35 and delta >= 0.15)

    return {
        "anchor_rot": anchor_rot,
        "smear_rot": smear_rot,
        "off_thread_spike": off_thread_spike,
        "delta_coff": delta,
        "H": h,
        "Coff": coff,
    }
