# -*- coding: utf-8 -*-
"""Policy fixtures drawn from UpgradeBench's measured episodes."""
from upgrade_advisor.policy import Action, Measurements, recommend


def _m(**kw):
    base = dict(task_kind="classification", freeze_score=0.90,
                adopt_floor=0.60, gate_set_size=1500)
    base.update(kw)
    return Measurements(**base)


def test_freeze_on_low_coupling_task():
    # Banking77-like: reference barely beats the frozen specialist
    r = recommend(_m(freeze_score=0.9276, adopt_floor=0.6594,
                     reference_score=0.9321))
    assert r.action == Action.FREEZE


def test_copy_licensed_only_by_short_documented_continuation():
    # Qwen2->2.5-like fresh run: shape-compatible, copy measured, NOT licensed
    r = recommend(_m(freeze_score=0.9276, adopt_floor=0.6071,
                     reference_score=0.9312, shape_compatible=True,
                     documented_continuation=False, copy_score=0.4286))
    assert r.action != Action.COPY
    # 1M-like short continuation: licensed and passing
    r = recommend(_m(freeze_score=0.9312, adopt_floor=0.60,
                     reference_score=0.9450, shape_compatible=True,
                     documented_continuation=True,
                     continuation_tokens=2.0e10, copy_score=0.9440,
                     copy_negative_flip_rate=0.012))
    assert r.action == Action.COPY


def test_long_continuation_not_licensed():
    # OLMo 2.9T-like: documented continuation but far beyond the budget
    r = recommend(_m(freeze_score=0.9279, adopt_floor=0.1432,
                     reference_score=0.9289, shape_compatible=True,
                     documented_continuation=True,
                     continuation_tokens=2.9e12, copy_score=0.1279))
    assert r.action != Action.COPY


def test_refresh_when_inputs_retained_and_passing():
    r = recommend(_m(task_kind="structured", freeze_score=0.6963,
                     adopt_floor=0.6963, reference_score=0.7501,
                     inputs_retained=True, refresh_score=0.7450))
    assert r.action == Action.REFRESH


def test_retrain_on_high_coupling_without_cheaper_path():
    r = recommend(_m(task_kind="structured", freeze_score=0.6963,
                     adopt_floor=0.6963, reference_score=0.7501))
    assert r.action == Action.RETRAIN


def test_small_gate_set_warns():
    r = recommend(_m(reference_score=0.95, gate_set_size=120))
    assert any("gate set" in w for w in r.warnings)


def test_epsilon_boundary_rer_overrides():
    # 理论重审 fix#1：机会差恰在 epsilon 上，但错误率 1%→0%（RER=100%，
    # 错误数=15≥10）→ 错误率口径打开升级瀑布（默认 n=1500）
    r = recommend(_m(freeze_score=0.99, reference_score=1.0000))
    assert r.action == Action.RETRAIN


def test_epsilon_boundary_without_error_mass_stays_conservative():
    # 同样的边界但 n=300 → freeze 错误仅 3 条，RER 门不开；
    # 欠功效 → INCONCLUSIVE（浮点容差仍在，不会误判 RETRAIN）
    r = recommend(_m(freeze_score=0.99, reference_score=1.0000,
                     gate_set_size=300, discordant_rate=0.03))
    assert r.action in (Action.FREEZE, Action.INCONCLUSIVE)
