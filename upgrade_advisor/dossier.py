# -*- coding: utf-8 -*-
"""Case dossier: the complete decision memo an organization files after an
upgrade evaluation -- one document per (task, candidate) episode, holding
the decision card, the background, the asset/cost tables, the FULL
evidence table with plain-language readings, the executive brief, and the
technical report as an appendix. This is the output format validated with
users on the eleven industry case studies (案例报告v2).

Everything is assembled from artifacts recommend already wrote
(evidence.json, decision_brief*.md, recommendation.md) -- the dossier
invents no numbers. Optional yaml keys let the owner add narrative:
  case_background: ["paragraph 1", "paragraph 2"]   # section 1
  case_notes: ["discussion point", ...]             # section 6
Render to .docx with scripts/render_dossier_docx.js.
"""
import json
import os

ACTION_ZH = {"collect": "COLLECT（先采证再定）", "wait": "WAIT（跳过本代）",
             "freeze": "FREEZE（维持现状）", "retrain": "RETRAIN（重训升级）",
             "copy": "COPY（直迁）", "refresh": "REFRESH（蒸馏重训）",
             "inconclusive": "INCONCLUSIVE（未决）"}
VERDICT_ZH = {"unresolved": "证据未决", "equivalence": "等价确证",
              "gain-established": "增益确证", "no-reference": "无参考",
              "point-only": "点估计口径", "": ""}


def _sign(x):
    return f"+{x}" if isinstance(x, (int, float)) and x >= 0 else f"{x}"


def evidence_rows(ej, lang):
    """(item, value, reading) rows -- the section-4 master table."""
    zh = lang == "zh"
    ev, ms = ej["evidence"], ej["measurements"]
    r = []

    def add(item_zh, item_en, value, read_zh, read_en):
        r.append((item_zh if zh else item_en, value,
                  read_zh if zh else read_en))

    if ms.get("freeze_score") is not None:
        add(f"现役 specialist（门控半集 n={ms['gate_set_size']}）",
            f"serving specialist (gate half, n={ms['gate_set_size']})",
            f"{ms['freeze_score']:.4f}",
            "当前线上系统的实测水平", "measured level of the live system")
    if ms.get("adopt_floor") is not None:
        add("候选基座采用地板（零/少样本）",
            "candidate adoption floor (zero/few-shot)",
            f"{ms['adopt_floor']:.4f}",
            "不训练直接用新模型的水平——与现役的差距就是训练数据的护城河",
            "the new model used bare; the gap to serving is your data moat")
    if ms.get("reference_score") is not None:
        opp = ev.get("opportunity_pp")
        add("候选基座重训参考（同配方同数据）",
            "retrained reference (same recipe, same data)",
            f"{ms['reference_score']:.4f}"
            + (f"（机会差 {_sign(opp)}pp）" if zh and opp is not None
               else (f" (opportunity {_sign(opp)}pp)"
                     if opp is not None else "")),
            "真实训练并实测，非估算" if not ms.get("reference_is_estimate")
            else "β 投影估算值",
            "actually trained and measured, not estimated"
            if not ms.get("reference_is_estimate") else "beta-projected")
    pe = ev.get("paired_evidence")
    if pe:
        add("池化配对证据（val+test 全部）", "pooled paired evidence (val+test)",
            (f"n={pe['n']}：新系统修好 {pe['reference_fixes']} 题、"
             f"改错 {pe['reference_breaks']} 题") if zh else
            (f"n={pe['n']}: fixes {pe['reference_fixes']}, "
             f"breaks {pe['reference_breaks']}"),
            "v2 判定使用的全部证据；旧版只用 n≈100 的碎片",
            "everything the verdict judges on (the old core saw one "
            "n~100 fragment)")
    ci = ev.get("opportunity_ci_pooled_pp")
    if ci:
        add("池化 95% 置信区间", "pooled 95% confidence interval",
            f"[{_sign(ci[0])}, {_sign(ci[1])}]pp",
            f"真实差距的可信范围；数据已排除 >{ev.get('excluded_gain_above_pp')}pp 的增益",
            f"credible range of the true gap; gains above "
            f"{ev.get('excluded_gain_above_pp')}pp are excluded by the data")
    po = ev.get("posterior")
    if po:
        add("增益后验（论文 193 格先验）", "gain posterior (193-cell corpus prior)",
            (f"均值 {_sign(po['post_mu_pp'])}pp；P(增益>ε)="
             f"{po['p_gain_above_eps']:.0%}，P(倒退)="
             f"{po['p_loss_below_neg_eps']:.0%}") if zh else
            (f"mean {_sign(po['post_mu_pp'])}pp; P(gain>eps)="
             f"{po['p_gain_above_eps']:.0%}, P(regression)="
             f"{po['p_loss_below_neg_eps']:.0%}"),
            "结合公开实测语料对小样本借力",
            "borrows strength from the published measured corpus")
    if ev.get("opportunity_rer") is not None:
        add("错误率视角（RER）", "error-scale view (RER)",
            (f"相对错误消除 {ev['opportunity_rer']:+.0%}"
             f"（冻结错误 {ev.get('freeze_errors_on_gate')} 条）") if zh else
            (f"relative error reduction {ev['opportunity_rer']:+.0%} "
             f"({ev.get('freeze_errors_on_gate')} frozen errors)"),
            "天花板附近比绝对百分点更敏感的口径",
            "the decision-relevant scale near the accuracy ceiling")
    g = ej.get("genealogy", {})
    if g:
        cont = g.get("continuation_tokens")
        add("谱系裁决", "genealogy verdict",
            f"{g.get('edge_type')} ({g.get('confidence')})"
            + (f", continuation {float(cont)/1e9:.0f}B tokens" if cont else ""),
            "决定能否直迁 adapter：非续训一律禁止",
            "governs adapter copying: forbidden off documented continuations")
    rci = ev.get("opportunity_ci_pp")
    if rci:
        add("统计层（报告半集，与门控隔离）", "statistics (report half, gate-isolated)",
            f"CI [{_sign(rci[0])}, {_sign(rci[1])}]pp, "
            f"McNemar p={ev.get('opportunity_mcnemar_p')}",
            "门控从未见过这些题——无偏报告",
            "items the gates never saw -- unbiased reporting")
    nll = ev.get("nll_ref_minus_freeze")
    if nll:
        add("置信层：配对 log-loss（参考−现役）",
            "confidence layer: paired log-loss (ref - serving)",
            f"{_sign(nll[0])}, CI [{_sign(nll[1])}, {_sign(nll[2])}]",
            "负值偏参考：0/1 准确率看不见的置信质量差异" if nll[0] < 0
            else "现役的置信质量不落下风",
            "negative favors the reference: quality 0/1 accuracy cannot see"
            if nll[0] < 0 else "the serving system's confidence holds up")
    if ev.get("ece"):
        e = ev["ece"]
        add("置信层：校准误差 ECE", "confidence layer: calibration ECE",
            f"{'现役' if zh else 'serving'} {e['freeze']} / "
            f"{'参考' if zh else 'reference'} {e['reference']}",
            "越低越好；影响“低置信转人工”的可靠性",
            "lower is better; matters for confidence-based routing")
    if ev.get("aurc"):
        a2 = ev["aurc"]
        add("置信层：选择性风险 AURC", "confidence layer: risk-coverage AURC",
            f"{'现役' if zh else 'serving'} {a2['freeze']} / "
            f"{'参考' if zh else 'reference'} {a2['reference']}",
            "越低越好；路由型部署的运维口径",
            "lower is better; the selective-routing operating metric")
    rb = ev.get("robustness")
    if rb and "robustness_delta_pp" in rb:
        d = rb["robustness_delta_pp"]
        add("鲁棒层：扰动重测", "robustness layer: perturbed re-test",
            (f"现役 {rb['freeze_perturbed']} / 参考 "
             f"{rb['reference_perturbed']}（Δ {_sign(d)}pp）") if zh else
            (f"serving {rb['freeze_perturbed']} / reference "
             f"{rb['reference_perturbed']} (delta {_sign(d)}pp)"),
            "新基座在噪声输入下略有优势" if d > 0.5
            else "新基座未表现出额外抗干扰优势（负结果如实记录）",
            "a small edge to the newer base under noise" if d > 0.5
            else "no extra robustness from the newer base (negative result, "
            "reported as such)")
    dg = ev.get("disagreement")
    if dg:
        add("分歧集（COLLECT 的对象）", "disagreement set (what COLLECT labels)",
            (f"{dg['n_disagreements']} 条（占 {dg['disagreement_rate']:.1%}），"
             f"符号检验 p={dg['sign_test_p']}") if zh else
            (f"{dg['n_disagreements']} items ({dg['disagreement_rate']:.1%}),"
             f" sign test p={dg['sign_test_p']}"),
            "唯一携带决策信息的题目清单，已导出待标注",
            "the only items carrying decision information; exported for "
            "labeling")
        plan = dg.get("collection_plan")
        if plan:
            add("分歧标注收敛定价", "labeling convergence pricing",
                ", ".join(f"+{p['label_k_more']}: "
                          f"{p['p_direction_settles']:.0%}" for p in plan),
                "再标 k 条分歧后方向定案的概率",
                "chance the direction settles after k more labels")
    lm = ev.get("label_metrics")
    if lm:
        f1 = {k: v.get("macro_f1") for k, v in lm.items()}
        add("Macro-F1（类平衡口径）", "macro-F1 (class-balanced)",
            " / ".join(f"{k} {v}" for k, v in f1.items()),
            "类不平衡下的稳健对照", "robust to class imbalance")
        inv = {k: v.get("invalid_rate", 0) for k, v in lm.items()}
        add("无效输出率", "invalid-output rate",
            ("全部 0.00%" if zh else "all 0.00%")
            if all(x == 0 for x in inv.values())
            else " / ".join(f"{k} {v:.2%}" for k, v in inv.items()),
            "预测是否落在标签清单之外——格式风险",
            "predictions outside the label inventory -- format risk")
    led = ev.get("ledger")
    if led:
        add("任务台账", "task ledger",
            (f"{led.get('episodes')} episode；训练 "
             f"{led.get('train_gpu_minutes')} GPU 分钟；标注 "
             f"{led.get('gold_labels_consumed', 0)} 条") if zh else
            (f"{led.get('episodes')} episode(s); "
             f"{led.get('train_gpu_minutes')} train GPU-min; "
             f"{led.get('gold_labels_consumed', 0)} gold labels"),
            "本任务的累计资产与开销", "cumulative assets and spend")
    if ev.get("economic_epsilon_pp") is not None:
        add("经济 ε（盈亏平衡增益）", "economic epsilon (break-even gain)",
            f"{ev['economic_epsilon_pp']}pp",
            "按请求量×错误单价×摊销折算的“值得”门槛",
            "the 'worth it' bar from volume, error cost, amortization")
    return r


def render_dossier(cfg, ej, brief_md, tech_md, lang="en"):
    zh = lang == "zh"
    L = []
    a = L.append
    name = cfg.get("task_name", ej.get("task", "task"))
    tshort = str(ej.get("target", "")).replace("\\", "/").rstrip("/").split("/")[-1]
    act = ACTION_ZH.get(ej["action"], ej["action"].upper()) if zh \
        else ej["action"].upper()
    ver = VERDICT_ZH.get(ej.get("verdict", ""), ej.get("verdict", "")) if zh \
        else ej.get("verdict", "")

    a(("# 基座模型升级决策纪要：" if zh else "# Upgrade decision dossier: ")
      + f"{name} -> {tshort}")
    a("")

    # -- decision card --
    a("## " + ("决策卡" if zh else "Decision card"))
    a(f"**{act}**" + (f"（{ver}）" if zh else f" (verdict: {ver})"))
    headline = next((x for x in brief_md.splitlines()
                     if x.strip().startswith("【") or
                     x.strip().startswith("**")), "")
    if headline:
        a(headline.strip())
    pe = ej["evidence"].get("paired_evidence")
    if pe:
        a(("依据：" if zh else "Basis: ")
          + (f"{pe['n']} 条真实数据逐题对比，修好 {pe['reference_fixes']} 题 / "
             f"改错 {pe['reference_breaks']} 题" if zh else
             f"{pe['n']} real records head-to-head; "
             f"{pe['reference_fixes']} fixes / {pe['reference_breaks']} "
             "breaks"))
    a("")

    # -- 1 background --
    a("## " + ("一、背景与评估动机" if zh else "1. Background and motivation"))
    bg = cfg.get("case_background") or []
    if bg:
        for p in bg:
            a(p)
            a("")
    else:
        a("（在配置 yaml 的 `case_background` 键填写公司与任务背景段落）"
          if zh else
          "(fill the `case_background` key in the config yaml with the "
          "company/task narrative)")
        a("")

    # -- 2 assets --
    a("## " + ("二、数据与系统资产" if zh else "2. Data and system assets"))
    a("| " + ("项目 | 内容" if zh else "item | value") + " |")
    a("|---|---|")
    rows = [
        (("训练/验证/测试数据" if zh else "train/val/test data"),
         f"{cfg.get('train_set', '—')} / {cfg.get('val_set', '—')} / "
         f"{cfg.get('test_set', '—')}"),
        (("现役系统" if zh else "serving system"),
         f"{cfg.get('source_base', '—')} + LoRA ({cfg.get('adapter', '—')})"),
        (("候选基座" if zh else "candidate base"), ej.get("target", "—")),
        (("评估配置" if zh else "evaluation config"),
         f"flip budget {cfg.get('flip_budget', 0.03):.0%}; "
         f"ε={ej.get('epsilon', 0.01)*100:.0f}pp"
         + ("" if ej["measurements"].get("economic_epsilon") is None else
            (f"；经济 ε={ej['measurements']['economic_epsilon']*100:.2f}pp"
             if zh else
             f"; economic ε={ej['measurements']['economic_epsilon']*100:.2f}pp"))),
    ]
    for k, v in rows:
        a(f"| {k} | {v} |")
    a("")

    # -- 3 process --
    a("## " + ("三、评估过程与开销" if zh else "3. Process and spend"))
    led = ej["evidence"].get("ledger", {})
    a(("- 累计：" if zh else "- cumulative: ")
      + (f"{led.get('episodes', '—')} episode；训练 "
         f"{led.get('train_gpu_minutes', '—')} GPU 分钟；评测 "
         f"{led.get('eval_gpu_minutes', '—')} GPU 分钟；金标 "
         f"{led.get('gold_labels_consumed', 0)} 条" if zh else
         f"{led.get('episodes', '—')} episode(s); "
         f"{led.get('train_gpu_minutes', '—')} train GPU-min; "
         f"{led.get('eval_gpu_minutes', '—')} eval GPU-min; "
         f"{led.get('gold_labels_consumed', 0)} gold labels"))
    a("- " + ("本轮探针（置信+鲁棒）约 5 GPU 分钟；分歧提取与重判零 GPU 秒级"
              if zh else
              "this round's probes (confidence + robustness) ~5 GPU-min; "
              "disagreement extraction and re-verdict are zero-GPU seconds"))
    a("")

    # -- 4 evidence master table --
    a("## " + (f"四、系统判定（v2）：{act} —— {ver}" if zh else
               f"4. Verdict (v2 core): {act} -- {ver}"))
    a(("以下为工具输出的全部证据（未加筛选），解读列为附注：" if zh else
       "The complete, unfiltered evidence; the reading column is annotation:"))
    a("")
    a("| " + ("证据项 | 数值 | 解读" if zh else "evidence | value | reading")
      + " |")
    a("|---|---|---|")
    for item, value, reading in evidence_rows(ej, lang):
        a(f"| {item} | {value} | {reading} |")
    a("")
    if ej.get("reasons"):
        a(("**系统判定理由（原文）**" if zh else "**Reasons (verbatim)**"))
        for x in ej["reasons"]:
            a(f"- {x}")
        a("")
    if ej.get("warnings"):
        a(("**系统警告**" if zh else "**Warnings**"))
        for x in ej["warnings"]:
            a(f"- {x}")
        a("")

    # -- 5 executive brief --
    a("## " + ("五、决策书（给管理层，工具自动生成）" if zh else
               "5. Executive brief (auto-generated)"))
    body = brief_md.split("\n", 1)[1] if brief_md.startswith("#") else brief_md
    a(body.strip())
    a("")

    # -- 6 notes --
    a("## " + ("六、对照与讨论" if zh else "6. Discussion"))
    notes = cfg.get("case_notes") or []
    if notes:
        for p in notes:
            a(f"- {p}")
    else:
        a("（在配置 yaml 的 `case_notes` 键填写与上一版判定的对照或业务讨论）"
          if zh else
          "(fill the `case_notes` key in the config yaml with discussion "
          "points, e.g. contrast with the previous verdict)")
    a("")

    # -- 7 technical appendix --
    a("## " + ("七、技术附录：完整统计报告" if zh else
               "7. Technical appendix: full statistical report"))
    a("```")
    a(tech_md.strip())
    a("```")
    return "\n".join(L)


def build(workdir, cfg, lang="both"):
    """Assemble dossiers from the episode's artifacts. Returns paths."""
    ej = json.load(open(os.path.join(workdir, "evidence.json"),
                        encoding="utf-8"))
    tech = open(os.path.join(workdir, "recommendation.md"),
                encoding="utf-8").read()
    out = {}
    for lg in (("en", "zh") if lang == "both" else (lang,)):
        suffix = "" if lg == "en" else f"_{lg}"
        bp = os.path.join(workdir, f"decision_brief{suffix}.md")
        brief = open(bp, encoding="utf-8").read() if os.path.exists(bp) else ""
        md = render_dossier(cfg, ej, brief, tech, lang=lg)
        p = os.path.join(workdir, f"dossier{suffix}.md")
        with open(p, "w", encoding="utf-8") as f:
            f.write(md)
        out[lg] = p
    return out
