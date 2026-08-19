# -*- coding: utf-8 -*-
"""COLLECT 通道（review-2）：分歧集提取与标注收敛预估。"""
import json
import os
import tempfile

from upgrade_advisor import disagree as D


def _rec(i, gold, pred):
    return {"id": i, "gold": gold, "pred": pred, "correct": gold == pred}


def test_disagreement_set_outcomes():
    f = {str(i): _rec(str(i), "a", "a") for i in range(10)}
    r = {str(i): _rec(str(i), "a", "a") for i in range(10)}
    f["1"] = _rec("1", "a", "b")   # frozen wrong, ref right -> fixes
    r["2"] = _rec("2", "a", "b")   # frozen right, ref wrong -> breaks
    f["3"] = _rec("3", "a", "b"); r["3"] = _rec("3", "a", "c")  # both wrong
    rows = D.disagreement_set(f, r)
    assert len(rows) == 3
    outcomes = {x["id"]: x["outcome"] for x in rows}
    assert outcomes == {"1": "reference_fixes", "2": "reference_breaks",
                        "3": "both_wrong"}


def test_convergence_forecast_bounds():
    # 已显著：k=0 即收敛
    assert D.convergence_forecast(10, 0, 0) == 1.0
    # 未显著、方向强偏（6/0）：再标 25 条大概率收敛
    p = D.convergence_forecast(4, 0, 25)
    assert 0.5 < p <= 1.0
    # 真平局（10/10）：再标 25 条也难收敛
    q = D.convergence_forecast(10, 10, 25)
    assert q < 0.35
    # pmf 求和守恒（间接）：概率在 [0,1]
    assert 0.0 <= D.convergence_forecast(0, 0, 10) <= 1.0


def test_summarize_writes_files():
    wd = tempfile.mkdtemp()
    for stem, wrong in (("freeze", {"3", "5"}), ("reference", {"5", "7"})):
        with open(os.path.join(wd, stem + ".jsonl"), "w",
                  encoding="utf-8") as fh:
            for i in range(20):
                gold = "x"
                pred = "y" if str(i) in wrong else "x"
                fh.write(json.dumps(_rec(str(i), gold, pred)) + "\n")
    s = D.summarize(wd)
    # 3: frozen 错 ref 对（fixes）；7: frozen 对 ref 错（breaks）；5: 都错但
    # pred 相同(y=y) -> 不算分歧
    assert s["n_disagreements"] == 2
    assert s["labeled_outcomes"]["reference_fixes"] == 1
    assert s["labeled_outcomes"]["reference_breaks"] == 1
    assert os.path.exists(s["disagreements_file"])
    assert os.path.exists(os.path.join(wd, "disagree_summary.json"))
    assert s["collection_plan"][0]["label_k_more"] == 10
