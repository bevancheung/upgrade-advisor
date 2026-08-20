# -*- coding: utf-8 -*-
"""高管决策书（review-3）：各动作分支渲染、口径换算、双语。"""
from types import SimpleNamespace

from upgrade_advisor.exec_report import decision_card, render_exec
from upgrade_advisor.policy import Action, Measurements, recommend

CFG = {"task_name": "cardco"}
VER = SimpleNamespace(edge_type="fresh_pretraining", confidence="inferred",
                      continuation_tokens=None, note="",
                      documented_continuation=False)


def _m(**kw):
    base = dict(task_kind="classification", freeze_score=0.96,
                adopt_floor=0.60, gate_set_size=400)
    base.update(kw)
    return Measurements(**base)


def _render_both(m):
    rec = recommend(m)
    en = render_exec(CFG, r"E:\models\Qwen3-8B", VER, m, rec, lang="en")
    zh = render_exec(CFG, r"E:\models\Qwen3-8B", VER, m, rec, lang="zh")
    return rec, en, zh


def test_collect_brief_mentions_disagreements_and_cost_free_stance():
    m = _m(reference_score=0.97, paired_n=400, paired_n01=5, paired_n10=1,
           paired_freeze_errors=16, prior_mu=0.0082, prior_sd=0.024)
    rec, en, zh = _render_both(m)
    rec.evidence["disagreement"] = {
        "n_disagreements": 6, "disagreement_rate": 0.015,
        "sign_test_p": 0.2188,
        "collection_plan": [{"label_k_more": 25,
                             "p_direction_settles": 0.61}]}
    en2 = render_exec(CFG, "t", VER, m, rec, lang="en")
    zh2 = render_exec(CFG, "t", VER, m, rec, lang="zh")
    assert rec.action == Action.COLLECT
    assert "Spend a little" in en2 and "先花小钱" in zh2
    assert "6" in en2 and "分歧" in zh2
    # 每100个请求口径：0.96 -> 4.0 wrong per 100
    assert "**4.0** wrong per 100" in en2 and "**4.0** 个" in zh2


def test_wait_brief_mentions_low_probability_and_next_release():
    m = _m(reference_score=0.955, paired_n=200, paired_n01=2, paired_n10=5,
           paired_freeze_errors=8, prior_mu=0.0082, prior_sd=0.024)
    rec, en, zh = _render_both(m)
    assert rec.action == Action.WAIT
    assert "Skip this generation" in en and "跳过这一代" in zh
    assert "193" in en and "193" in zh
    assert "next release" in en.lower() or "next base-model release" in en


def test_equivalence_freeze_brief_states_exclusion_bound():
    m = _m(freeze_score=0.97, reference_score=0.97, paired_n=2000,
           paired_n01=2, paired_n10=2, paired_freeze_errors=60)
    rec, en, zh = _render_both(m)
    assert rec.action == Action.FREEZE and rec.verdict == "equivalence"
    assert "at most" in en and "最多带来" in zh
    assert "Zero spend" in en and "零支出" in zh


def test_retrain_brief_and_card():
    m = _m(freeze_score=0.95, reference_score=0.975, paired_n=2000,
           paired_n01=60, paired_n10=10, paired_freeze_errors=100)
    rec, en, zh = _render_both(m)
    assert rec.action == Action.RETRAIN
    assert "Upgrade" in en and "值得升级" in zh
    assert "regression gate" in en and "回归门" in zh
    card = decision_card(rec, rec.evidence, lang="en")
    assert "fixes 60" in card and "breaks 10" in card
    assert "**" not in card  # 终端卡片不带 markdown 粗体


def test_no_invented_numbers_without_evidence():
    # 无参考、无探针：决策书仍可渲染，且不出现置信/鲁棒/后验小节
    m = _m()
    rec = recommend(m)
    en = render_exec(CFG, "t", VER, m, rec, lang="en")
    assert "Confidence quality" not in en
    assert "Noise tolerance" not in en
    assert "193 published measured upgrade cases" not in en
