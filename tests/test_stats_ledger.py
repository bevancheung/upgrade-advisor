# -*- coding: utf-8 -*-
import os
import tempfile

from upgrade_advisor import ledger as L
from upgrade_advisor import stats as S


def test_mcnemar_extremes():
    a = {str(i): True for i in range(100)}
    b = {str(i): i >= 50 for i in range(100)}   # a wins 50, b wins 0
    b01, c10, p = S.mcnemar(a, b)
    assert (b01, c10) == (50, 0) and p < 1e-10
    _, _, p2 = S.mcnemar(a, a)
    assert p2 == 1.0


def test_paired_ci_covers_truth():
    a = {str(i): i % 10 != 0 for i in range(1000)}   # 90%
    b = {str(i): i % 5 != 0 for i in range(1000)}    # 80%
    mean, lo, hi = S.paired_diff_ci(a, b, n_resamples=2000)
    assert abs(mean - 10.0) < 1e-6 and lo < 10.0 < hi


def test_beta_projection_roundtrip():
    with tempfile.TemporaryDirectory() as wd:
        L.append(wd, {"event": "recommend", "target": "gen1",
                      "floor": 0.50, "reference": 0.70})
        L.append(wd, {"event": "recommend", "target": "gen2",
                      "floor": 0.60, "reference": 0.75})
        h = L.history(wd)
        beta, old, new = L.beta_estimate(h)
        assert abs(beta - 0.5) < 1e-9
        proj = L.project_reference(h, new_floor=0.70)
        assert abs(proj["projected_reference"] - 0.80) < 1e-9


def test_beta_denominator_gate():
    with tempfile.TemporaryDirectory() as wd:
        L.append(wd, {"target": "g1", "floor": 0.50, "reference": 0.70})
        L.append(wd, {"target": "g2", "floor": 0.51, "reference": 0.75})
        assert L.beta_estimate(L.history(wd)) is None  # dFloor < 2pp


def test_costs_summary_three_dimensions():
    with tempfile.TemporaryDirectory() as wd:
        L.append(wd, {"event": "retrain", "target": "g1",
                      "train_minutes": 10.0, "gold_labels_consumed": 2000,
                      "teacher_queries": 0, "validation_items": 200})
        L.append(wd, {"event": "refresh", "target": "g1",
                      "train_minutes": 8.0, "gold_labels_consumed": 0,
                      "teacher_queries": 2000, "validation_items": 200})
        cs = L.costs_summary(L.history(wd))
        assert cs["gold_labels_consumed"] == 2000
        assert cs["teacher_queries"] == 2000
        assert cs["validation_items"] == 400
        assert abs(cs["train_gpu_minutes"] - 18.0) < 1e-9
