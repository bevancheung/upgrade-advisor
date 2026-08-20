# -*- coding: utf-8 -*-
"""案例纪要（dossier，review-3 定稿格式）：七节结构、证据表、双语、叙事键。"""
import json
import os
import tempfile

from upgrade_advisor.dossier import build, evidence_rows

EJ = {
    "task": "cardco", "target": r"E:\models\Qwen2.5-7B-Instruct",
    "action": "collect", "verdict": "unresolved", "epsilon": 0.01,
    "genealogy": {"edge_type": "fresh_pretraining", "confidence": "inferred",
                  "continuation_tokens": None,
                  "documented_continuation": False},
    "measurements": {"freeze_score": 0.96, "adopt_floor": 0.77,
                     "reference_score": 0.97, "reference_is_estimate": False,
                     "gate_set_size": 100, "paired_n": 400, "paired_n01": 5,
                     "paired_n10": 3, "paired_freeze_errors": 16,
                     "economic_epsilon": None},
    "evidence": {
        "opportunity_pp": 0.5,
        "paired_evidence": {"n": 400, "reference_fixes": 5,
                            "reference_breaks": 3},
        "opportunity_ci_pooled_pp": [-1.1, 2.1],
        "excluded_gain_above_pp": 2.1,
        "posterior": {"post_mu_pp": 0.55, "post_sd_pp": 0.62,
                      "p_gain_above_eps": 0.25,
                      "p_loss_below_neg_eps": 0.01, "p_within_band": 0.74},
        "opportunity_rer": 0.125, "freeze_errors_on_gate": 16,
        "opportunity_ci_pp": [-1.4, 5.1], "opportunity_mcnemar_p": 0.6,
        "nll_ref_minus_freeze": [-0.03, -0.08, 0.02],
        "ece": {"freeze": 0.01, "reference": 0.012},
        "aurc": {"freeze": 0.001, "reference": 0.0008},
        "robustness": {"freeze_perturbed": 0.96, "reference_perturbed": 0.966,
                       "robustness_delta_pp": 0.6},
        "disagreement": {"n_disagreements": 10, "disagreement_rate": 0.025,
                         "sign_test_p": 0.7266,
                         "collection_plan": [
                             {"label_k_more": 25,
                              "p_direction_settles": 0.4}]},
        "label_metrics": {"freeze": {"macro_f1": 0.95, "invalid_rate": 0.0,
                                     "n_classes": 20}},
        "ledger": {"episodes": 2, "train_gpu_minutes": 6.4,
                   "eval_gpu_minutes": 9.1, "gold_labels_consumed": 800},
    },
    "reasons": ["the pooled evidence cannot resolve epsilon"],
    "warnings": ["EVAL-SATURATED: only 16 errors"],
}


def _mk_episode(wd):
    with open(os.path.join(wd, "evidence.json"), "w", encoding="utf-8") as f:
        json.dump(EJ, f)
    with open(os.path.join(wd, "recommendation.md"), "w",
              encoding="utf-8") as f:
        f.write("# Upgrade recommendation\n## Action: **COLLECT**\n")
    with open(os.path.join(wd, "decision_brief.md"), "w",
              encoding="utf-8") as f:
        f.write("# brief\n**Spend a little to settle it.**\n## Next steps\n"
                "1. label the list\n")
    with open(os.path.join(wd, "decision_brief_zh.md"), "w",
              encoding="utf-8") as f:
        f.write("# 决策书\n【先花小钱把问题定死，再决定】\n## 下一步\n"
                "1. 标注分歧题单\n")


def test_dossier_seven_sections_both_langs():
    with tempfile.TemporaryDirectory() as wd:
        _mk_episode(wd)
        cfg = {"task_name": "cardco", "flip_budget": 0.03,
               "case_background": ["CardCo 用 LoRA 做 20 类意图路由。"],
               "case_notes": ["由 FREEZE 转 COLLECT。"]}
        paths = build(wd, cfg, lang="both")
        zh = open(paths["zh"], encoding="utf-8").read()
        en = open(paths["en"], encoding="utf-8").read()
        for sec in ("决策卡", "一、背景", "二、数据", "三、评估过程",
                    "四、系统判定", "五、决策书", "六、对照与讨论",
                    "七、技术附录"):
            assert sec in zh, sec
        for sec in ("Decision card", "1. Background", "4. Verdict",
                    "5. Executive brief", "7. Technical appendix"):
            assert sec in en, sec
        # 叙事键注入
        assert "CardCo 用 LoRA" in zh and "由 FREEZE 转 COLLECT" in zh
        # 证据表关键行
        assert "| 池化配对证据" in zh and "修好 5 题、改错 3 题" in zh
        assert "pooled paired evidence" in en
        # 决策书内嵌 + 技术附录围栏
        assert "先花小钱" in zh and "```" in zh


def test_evidence_rows_cover_all_layers():
    rows_zh = evidence_rows(EJ, "zh")
    items = [r[0] for r in rows_zh]
    for key in ("现役 specialist", "池化配对证据", "池化 95% 置信区间",
                "增益后验", "谱系裁决", "置信层：配对 log-loss",
                "鲁棒层：扰动重测", "分歧集", "任务台账"):
        assert any(key in x for x in items), key
    # 每行三列且数值列非空
    assert all(len(r) == 3 and str(r[1]).strip() for r in rows_zh)


def test_dossier_placeholder_without_narrative():
    with tempfile.TemporaryDirectory() as wd:
        _mk_episode(wd)
        paths = build(wd, {"task_name": "cardco"}, lang="zh")
        zh = open(paths["zh"], encoding="utf-8").read()
        assert "case_background" in zh and "case_notes" in zh
