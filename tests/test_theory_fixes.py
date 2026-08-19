# -*- coding: utf-8 -*-
"""理论重审五修的回归测试。"""
import json
import os
import tempfile

from upgrade_advisor import stats as S
from upgrade_advisor.policy import Action, Measurements, recommend


def _m(**kw):
    base = dict(task_kind="classification", freeze_score=0.90,
                adopt_floor=0.60, gate_set_size=1500)
    base.update(kw)
    return Measurements(**base)


def test_inconclusive_when_underpowered():
    # n=100, pi=0.05 -> MDE~6.3pp >> eps=1pp; 观察差 0.5pp 在噪声底内
    r = recommend(_m(freeze_score=0.970, reference_score=0.975,
                     gate_set_size=100, discordant_rate=0.05))
    assert r.action == Action.INCONCLUSIVE
    assert any("cannot resolve" in x for x in r.reasons)


def test_powered_null_stays_freeze():
    # n=5000 时 MDE<1pp，同样 0.5pp 差 -> 有功效的 FREEZE
    r = recommend(_m(freeze_score=0.970, reference_score=0.975,
                     gate_set_size=5000, discordant_rate=0.05))
    assert r.action == Action.FREEZE


def test_rer_gate_opens_waterfall_near_ceiling():
    # 3%->0.9% 错误率：绝对差 2.1pp>eps 本来就开；改造成绝对差<=eps 的构造：
    # 1.5%->0.9% = 0.6pp <= 1pp 但 RER=40%，freeze错误=30条(n=2000)
    r = recommend(_m(freeze_score=0.985, reference_score=0.991,
                     gate_set_size=2000, discordant_rate=0.02))
    assert r.action == Action.RETRAIN
    assert any("error-rate scale" in x for x in r.reasons)


def test_rer_gate_needs_error_mass():
    # 同样 RER 但 freeze 错误只有 3 条（n=200）→ 不开门；且欠功效 → INCONCLUSIVE
    r = recommend(_m(freeze_score=0.985, reference_score=0.991,
                     gate_set_size=200, discordant_rate=0.02))
    assert r.action in (Action.FREEZE, Action.INCONCLUSIVE)


def test_saturation_warning():
    r = recommend(_m(freeze_score=1.0, reference_score=1.0,
                     gate_set_size=80, discordant_rate=0.0))
    assert any("EVAL-SATURATED" in w for w in r.warnings)


def test_mde_matches_formula():
    assert abs(S.mde(0.05, 100) - 0.0626) < 0.001
    assert S.required_n(0.05, 0.01) == 3920


def test_confidence_metrics():
    with tempfile.TemporaryDirectory() as wd:
        p = os.path.join(wd, "lp.jsonl")
        rows = ([{"id": i, "gold": "a", "pred": "a", "correct": True,
                  "conf": 0.9, "nll": 0.1} for i in range(90)]
                + [{"id": 90 + i, "gold": "a", "pred": "b", "correct": False,
                    "conf": 0.6, "nll": 2.0} for i in range(10)])
        with open(p, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        # ECE: bin0.9: acc1.0 conf0.9 gap.1*0.9 + bin0.6: acc0 conf0.6 gap.6*0.1
        assert abs(S.ece(p) - (0.9 * 0.1 + 0.1 * 0.6)) < 1e-6
        assert 0 < S.aurc(p) < 0.1  # 高置信全对 -> 低 AURC
        m, lo, hi = S.paired_nll_ci(p, p, n_resamples=200)
        assert m == 0.0 and lo == 0.0 and hi == 0.0


def test_weighted_flips():
    from upgrade_advisor.flips import weighted_flips
    with tempfile.TemporaryDirectory() as wd:
        a, b = os.path.join(wd, "a.jsonl"), os.path.join(wd, "b.jsonl")
        rows_a = [{"id": i, "gold": "hi" if i < 5 else "lo", "correct": True}
                  for i in range(10)]
        rows_b = [{"id": i, "gold": rows_a[i]["gold"],
                   "correct": i not in (0, 9)} for i in range(10)]
        for p, rows in [(a, rows_a), (b, rows_b)]:
            with open(p, "w", encoding="utf-8") as f:
                for r in rows:
                    f.write(json.dumps(r) + "\n")
        rep = weighted_flips(a, b, {"hi": 5.0, "lo": 1.0}, half="all")
        # 总权重 5*5+5*1=30；负翻转: id0(hi,w5)+id9(lo,w1)=6 -> NFR=0.2
        assert abs(rep.nfr - 6 / 30) < 1e-9
