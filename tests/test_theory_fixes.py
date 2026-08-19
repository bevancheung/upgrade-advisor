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
    # 池化 n=100，3修/2破：gain=1pp，CI 横跨 eps → 未决 + 倾向 + 排除界
    r = recommend(_m(freeze_score=0.970, reference_score=0.975,
                     gate_set_size=100, paired_n=100, paired_n01=3,
                     paired_n10=2, paired_freeze_errors=3))
    assert r.action == Action.INCONCLUSIVE
    assert any("cannot resolve" in x for x in r.reasons)
    assert r.evidence["leaning"] in ("lean-freeze", "lean-upgrade")
    assert "excluded_gain_above_pp" in r.evidence


def test_equivalence_is_a_verdict_not_a_default():
    # 池化 n=2000，2修/2破：CI [-0.25,+0.25]pp，上界<eps → 确证 FREEZE
    r = recommend(_m(freeze_score=0.97, reference_score=0.97,
                     gate_set_size=2000, paired_n=2000, paired_n01=2,
                     paired_n10=2, paired_freeze_errors=60))
    assert r.action == Action.FREEZE
    assert any("equivalence established" in x for x in r.reasons)


def test_zero_discordance_rule_of_three():
    # 零不一致：n=500 → 排除界 3.69/500=0.74pp < eps → 确证 FREEZE
    r = recommend(_m(freeze_score=0.99, reference_score=0.99,
                     gate_set_size=500, paired_n=500, paired_n01=0,
                     paired_n10=0, paired_freeze_errors=5))
    assert r.action == Action.FREEZE
    assert any("agree on every pooled item" in x for x in r.reasons)
    # AirOne 型：n=163 → 排除界 2.26pp > eps → 未决（不是确证平局）
    r2 = recommend(_m(freeze_score=0.9939, reference_score=0.9939,
                      gate_set_size=163, paired_n=163, paired_n01=0,
                      paired_n10=0, paired_freeze_errors=1))
    assert r2.action == Action.INCONCLUSIVE


def test_established_gain_opens_waterfall():
    # n=2000，60修/10破：gain=2.5pp，CI 下界 ~1.6pp > eps → 瀑布(RETRAIN)
    r = recommend(_m(freeze_score=0.95, reference_score=0.975,
                     gate_set_size=2000, paired_n=2000, paired_n01=60,
                     paired_n10=10, paired_freeze_errors=100))
    assert r.action == Action.RETRAIN
    assert any("opportunity established" in x for x in r.reasons)


def test_point_above_epsilon_but_straddling_ci_stays_inconclusive():
    # 旧不对称的病例：点估计 2pp > eps 但只有 2修/0破（AirOne 病理）
    # → 不再直接 RETRAIN，而是未决+偏升级
    r = recommend(_m(freeze_score=0.98, reference_score=1.0,
                     gate_set_size=100, paired_n=100, paired_n01=2,
                     paired_n10=0, paired_freeze_errors=2))
    assert r.action == Action.INCONCLUSIVE
    assert r.evidence["leaning"] == "lean-upgrade"


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


def test_rer_gate_requires_sign_test_with_pairs():
    # RER=50%、错误数 12 条，但 6修/0破 的方向显著(p=2*0.5^6=0.031<0.05) → 开门
    r = recommend(_m(freeze_score=0.988, reference_score=0.994,
                     gate_set_size=1000, paired_n=1000, paired_n01=6,
                     paired_n10=0, paired_freeze_errors=12))
    assert r.action == Action.RETRAIN
    # 同 RER 但 4修/0破 (p=0.125) → 方向未确立不开门；且 CI 上界 0.89pp<eps
    # → 数据已排除有意义增益 → 确证 FREEZE（附饱和警告）
    r2 = recommend(_m(freeze_score=0.992, reference_score=0.996,
                      gate_set_size=1000, paired_n=1000, paired_n01=4,
                      paired_n10=0, paired_freeze_errors=8))
    assert r2.action == Action.FREEZE
    assert any("equivalence established" in x for x in r2.reasons)
    assert any("EVAL-SATURATED" in w for w in r2.warnings)


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
