from __future__ import annotations

import math

from app.telemetry.metrics import influence_entropy, normalize_scores, normalize_weights, off_thread_coupling


def test_entropy_and_off_thread_coupling():
    rows = [
        {"thread_id": "networking", "w": 0.7},
        {"thread_id": "cosmology", "w": 0.2},
        {"thread_id": "networking", "w": 0.1},
    ]
    h = influence_entropy([r["w"] for r in rows])
    expected_h = -(0.7 * math.log(0.7) + 0.2 * math.log(0.2) + 0.1 * math.log(0.1))
    assert abs(h - expected_h) < 1e-9

    w_target, coff = off_thread_coupling(rows, "networking")
    assert abs(w_target - 0.8) < 1e-9
    assert abs(coff - 0.2) < 1e-9


def test_normalize_weights_all_zero_is_uniform():
    rows = [
        {"raw_score": 0.0, "w": 0.0},
        {"raw_score": 0.0, "w": 0.0},
        {"raw_score": 0.0, "w": 0.0},
    ]
    weights = normalize_weights(rows)
    assert len(weights) == 3
    assert all(abs(w - (1.0 / 3.0)) < 1e-12 for w in weights)
    assert abs(sum(weights) - 1.0) < 1e-12

    normalized_rows = normalize_scores(rows)
    assert all(r["w"] >= 0.0 for r in normalized_rows)
    assert abs(sum(r["w"] for r in normalized_rows) - 1.0) < 1e-12


def test_normalize_weights_nan_inf_and_negative_are_zeroed():
    weights = normalize_weights([1.0, float("nan"), float("inf"), -5.0])
    assert len(weights) == 4
    assert weights[0] > 0.999999999
    assert weights[1] == 0.0
    assert weights[2] == 0.0
    assert weights[3] == 0.0
    assert abs(sum(weights) - 1.0) < 1e-12


def test_normalize_weights_sum_is_one_after_float_drift_correction():
    weights = normalize_weights([0.1, 0.2, 0.3, 0.4])
    assert all(w >= 0.0 for w in weights)
    assert abs(sum(weights) - 1.0) < 1e-12


def test_entropy_and_coff_stay_in_valid_bounds_with_invalid_inputs():
    rows = [
        {"thread_id": "target", "w": float("nan")},
        {"thread_id": "other", "w": float("inf")},
        {"thread_id": "other", "w": -1.0},
    ]
    w_target, coff = off_thread_coupling(rows, "target")
    h = influence_entropy([r["w"] for r in rows])

    assert 0.0 <= w_target <= 1.0
    assert 0.0 <= coff <= 1.0
    assert h >= 0.0
