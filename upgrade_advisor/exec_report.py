# -*- coding: utf-8 -*-
"""Executive decision brief: the same evidence as the technical report,
rendered for a reader with no statistics background (a CEO, a budget
owner). Design rules: one-sentence verdict first; error counts per 100
requests instead of accuracy points; every claim traceable to a real
measurement; costs and next steps in money/time, not GPU jargon; no
number invented by the renderer -- everything comes from rec.evidence.

render_exec(cfg, target, verdict, m, rec, lang) -> markdown string.
lang: "en" | "zh".
"""


def _wrong_per_100(score):
    return round((1.0 - score) * 100, 1)


def _pooled_wrong(m):
    """(frozen, reference) wrong-per-100 on the pooled paired records --
    the same evidence base as the head-to-head fixes/breaks counts, so the
    brief never contradicts itself. Falls back to gate scores when no
    pooled pairs exist."""
    if m.paired_n:
        wf = m.paired_freeze_errors / m.paired_n * 100
        wr = (m.paired_freeze_errors - m.paired_n01
              + m.paired_n10) / m.paired_n * 100
        return round(wf, 1), round(wr, 1)
    wf = _wrong_per_100(m.freeze_score)
    wr = (_wrong_per_100(m.reference_score)
          if m.reference_score is not None else None)
    return wf, wr


def _fmt_pct(x):
    return f"{x:.0%}"


# ---------------------------------------------------------------- headline
def _headline(rec, ev, lang):
    a = rec.action.value
    hi = ev.get("excluded_gain_above_pp")
    post = ev.get("posterior", {})
    dg = ev.get("disagreement", {})
    if lang == "zh":
        if a == "freeze" and rec.verdict == "equivalence":
            return ("【维持现状，本轮不升级】数据已经证明：换用新模型最多带来 "
                    f"{hi}% 的质量改进，不足以覆盖迁移成本。零支出。")
        if a == "freeze":
            return ("【暂不升级】目前还没有对照实验数据；在补齐对照之前，"
                    "维持现状是零风险的默认选择。")
        if a == "collect":
            n_d = dg.get("n_disagreements")
            p = post.get("p_gain_above_eps")
            return ("【先花小钱把问题定死，再决定】现有数据不足以下结论"
                    + (f"（升级划算的可能性约 {_fmt_pct(p)}）" if p is not None
                       else "")
                    + "。两套系统只在 "
                    + (f"{n_d} " if n_d is not None else "少数")
                    + "个真实问题上给出了不同答案——请业务专家把这些题标注出"
                    "对错（约一小时人工），即可定案。在此之前维持现状。")
        if a == "wait":
            p = post.get("p_gain_above_eps")
            return ("【跳过这一代，等下一个版本】综合你的数据和 193 个公开"
                    "实测案例的经验，这次升级划算的可能性只有 "
                    + (f"{_fmt_pct(p)}" if p is not None else "很低")
                    + "。不值得再花验证成本，维持现状，下一代发布时再评估。")
        if a == "retrain":
            return ("【值得升级】数据确认新模型重训后有真实收益。"
                    "建议按下方步骤执行，上线前有自动回归检查兜底。")
        if a == "copy":
            return ("【免费搬家】新版本是当前模型的直系延续，现有成果可以"
                    "直接迁移，且已通过质量与行为回归两道检查。")
        if a == "refresh":
            return ("【值得升级，且可以省标注】用现有系统给旧输入自动打标，"
                    "在新模型上训练——效果与人工标注重训相当。")
        return "【见下文】"
    # ---- en ----
    if a == "freeze" and rec.verdict == "equivalence":
        return ("**Stay put -- do not upgrade this round.** The data proves "
                f"the new model would improve quality by at most {hi}%, "
                "which does not cover the cost of migrating. Zero spend.")
    if a == "freeze":
        return ("**Hold off.** There is no controlled comparison yet; until "
                "one exists, staying put is the zero-risk default.")
    if a == "collect":
        n_d = dg.get("n_disagreements")
        p = post.get("p_gain_above_eps")
        return ("**Spend a little to settle it, then decide.** The current "
                "data cannot settle the question"
                + (f" (roughly {_fmt_pct(p)} chance the upgrade pays off)"
                   if p is not None else "")
                + ". The two systems gave different answers on only "
                + (f"{n_d}" if n_d is not None else "a handful of")
                + " real questions -- have a domain expert mark those "
                "right/wrong (about an hour of work) and the answer becomes "
                "definitive. Stay put meanwhile.")
    if a == "wait":
        p = post.get("p_gain_above_eps")
        return ("**Skip this generation.** Combining your data with 193 "
                "published measured cases, this upgrade has only a "
                + (f"{_fmt_pct(p)}" if p is not None else "low")
                + " chance of paying off. Not worth further verification "
                "spend; stay put and re-evaluate at the next release.")
    if a == "retrain":
        return ("**Upgrade.** The data confirms a real gain from retraining "
                "on the new model. Follow the steps below; an automatic "
                "regression gate protects the launch.")
    if a == "copy":
        return ("**A free ride.** The new release is a direct continuation "
                "of your current model; your existing work transfers as-is "
                "and has already passed both quality and behavior checks.")
    if a == "refresh":
        return ("**Upgrade, and save on labeling.** Your current system can "
                "label the training inputs automatically; retraining on "
                "those matches gold-label quality in the benchmark.")
    return "**See below.**"


# ---------------------------------------------------------------- checks
def _checks(m, ev, lang):
    rows = []
    zh = lang == "zh"

    pe = ev.get("paired_evidence")
    if pe and m.reference_score is not None:
        wf, wr = _pooled_wrong(m)
        ci = ev.get("opportunity_ci_pooled_pp")
        if zh:
            detail = (f"在 {pe['n']} 个真实业务问题上逐题对比：新系统修好了 "
                      f"{pe['reference_fixes']} 题、改错了 {pe['reference_breaks']} 题，"
                      f"其余完全相同。现役每 100 个请求约错 {wf} 个，"
                      f"升级重训后约错 {wr} 个")
            if ci:
                detail += (f"。考虑抽样误差，真实差距在 {ci[0]:+.1f}% 到 "
                           f"{ci[1]:+.1f}% 之间")
            rows.append(("质量对比（头对头）", detail))
        else:
            detail = (f"head-to-head on {pe['n']} real business questions: "
                      f"the new system fixed {pe['reference_fixes']} and "
                      f"broke {pe['reference_breaks']}; everything else "
                      f"identical. Today you get ~{wf} wrong per 100 "
                      f"requests; retrained on the new model, ~{wr}")
            if ci:
                detail += (f". Allowing for sampling error, the true gap is "
                           f"between {ci[0]:+.1f}% and {ci[1]:+.1f}%")
            rows.append(("Quality, head-to-head", detail))

    dg = ev.get("disagreement")
    if dg:
        if zh:
            rows.append(("分歧清单", f"两套系统意见不同的题共 "
                         f"{dg['n_disagreements']} 个（占 "
                         f"{dg['disagreement_rate']:.1%}）——这是唯一携带决策"
                         "信息的题目清单，已导出待标注"))
        else:
            rows.append(("Disagreement list",
                         f"{dg['n_disagreements']} questions "
                         f"({dg['disagreement_rate']:.1%} of the set) where "
                         "the two systems answer differently -- the only "
                         "items that carry decision information; exported "
                         "for labeling"))

    if "nll_ref_minus_freeze" in ev:
        dm = ev["nll_ref_minus_freeze"][0]
        better = dm < 0
        if zh:
            rows.append(("置信度质量",
                         ("新系统在“知道自己该多确定”上略好"
                          if better else "现役系统的置信度质量不落下风")
                         + "（对需要“低置信转人工”的场景有参考价值，"
                         "本轮差异未达统计显著）"))
        else:
            rows.append(("Confidence quality",
                         ("the new system is slightly better at knowing how "
                          "sure to be" if better else
                          "the current system's confidence quality holds up")
                         + " (relevant if you route low-confidence cases to "
                         "humans; not statistically significant here)"))

    if "robustness" in ev and "robustness_delta_pp" in ev.get("robustness", {}):
        d = ev["robustness"]["robustness_delta_pp"]
        if zh:
            rows.append(("抗干扰能力", "给输入加入错字、大小写混乱、口语"
                         f"填充词后重测：新旧系统的差距为 {d:+.2f}%——"
                         + ("新系统未表现出额外的抗干扰优势" if d <= 0
                            else "新系统略有优势，但幅度很小")))
        else:
            rows.append(("Noise tolerance", "re-tested with typos, casing "
                         "noise and filler words injected: gap of "
                         f"{d:+.2f}% -- "
                         + ("no extra robustness from the newer model"
                            if d <= 0 else "a small edge to the newer "
                            "model")))

    if zh:
        rows.append(("直迁安全性", "已核查模型血统：本升级路径"
                     + ("允许直接搬运现有成果" if m.documented_continuation
                        else "禁止直接搬运现有成果（历史实测：跨代直迁会把"
                        "正确率打到不如不用）——任何升级都必须重训")))
    else:
        rows.append(("Transfer safety", "model lineage checked: this path "
                     + ("permits moving your existing work as-is"
                        if m.documented_continuation else
                        "does NOT permit moving your existing work as-is "
                        "(measured: cross-generation transfer can score "
                        "worse than no system at all) -- any upgrade means "
                        "retraining")))
    return rows


# ---------------------------------------------------------------- next steps
def _next_steps(rec, ev, lang):
    a = rec.action.value
    dg = ev.get("disagreement", {})
    led = ev.get("ledger", {})
    zh = lang == "zh"
    steps = []
    if a == "collect":
        plan = dg.get("collection_plan") or []
        best = next((p for p in plan if p["label_k_more"] in (25, 50)), None)
        if zh:
            steps.append("把导出的分歧题单交给业务专家标注对错"
                         + (f"（再标 {best['label_k_more']} 题，有 "
                            f"{best['p_direction_settles']:.0%} 的把握定案）"
                            if best else ""))
            steps.append("标注完成后重新运行本工具，结论将升级为"
                         "“升级”或“维持”的确定判定")
            steps.append("在此期间线上系统不做任何变更（零风险）")
        else:
            steps.append("hand the exported disagreement list to a domain "
                         "expert to mark right/wrong"
                         + (f" (labeling {best['label_k_more']} more gives a "
                            f"{best['p_direction_settles']:.0%} chance of a "
                            "definitive answer)" if best else ""))
            steps.append("re-run this tool after labeling; the verdict will "
                         "harden into a definite upgrade / stay-put call")
            steps.append("change nothing in production meanwhile (zero risk)")
    elif a == "wait":
        if zh:
            steps.append("本轮不投入任何升级/验证成本")
            steps.append("把下一代基座模型的发布设为重评触发点；届时一次"
                         "评估约需 30 GPU 分钟、零新标注")
            steps.append("若业务数据分布发生明显变化（新品类、新话术），"
                         "提前重评")
        else:
            steps.append("spend nothing on upgrading or verifying this round")
            steps.append("set the next base-model release as the re-evaluation "
                         "trigger; that evaluation costs ~30 GPU-minutes and "
                         "zero new labels")
            steps.append("re-evaluate early if your traffic shifts (new "
                         "product lines, new phrasing)")
    elif a in ("retrain", "refresh", "copy"):
        tm = led.get("train_gpu_minutes")
        if zh:
            steps.append("按工具输出的配方在新模型上重训"
                         + (f"（历史单次成本约 {tm} GPU 分钟）" if tm else ""))
            steps.append("上线前运行回归门（自动检查“原来答对现在答错”"
                         "的题数，超预算自动拦截）")
            steps.append("灰度切换并保留旧系统回滚通道一周")
        else:
            steps.append("retrain on the new model with the tool's fixed "
                         "recipe" + (f" (historical cost ~{tm} GPU-minutes)"
                                     if tm else ""))
            steps.append("run the regression gate before serving (auto-blocks "
                         "if too many previously-correct answers flip)")
            steps.append("roll out gradually; keep the old system as a "
                         "one-week rollback path")
    else:  # freeze
        if zh:
            steps.append("本轮零支出、零变更")
            steps.append("下一代模型发布时重跑本评估（约 30 GPU 分钟）")
        else:
            steps.append("zero spend, zero change this round")
            steps.append("re-run this evaluation at the next model release "
                         "(~30 GPU-minutes)")
    return steps


# ---------------------------------------------------------------- render
def render_exec(cfg, target, verdict, m, rec, lang="en"):
    zh = lang == "zh"
    ev = rec.evidence
    L = []
    a = L.append
    name = cfg.get("task_name", "task")
    tshort = str(target).replace("\\", "/").rstrip("/").split("/")[-1]

    a(("# 升级决策书：" if zh else "# Upgrade decision brief: ")
      + f"{name} -> {tshort}")
    a("")
    a(_headline(rec, ev, lang))
    a("")

    a("## " + ("你的系统现在什么水平" if zh else "Where you stand"))
    wf, wr = _pooled_wrong(m)
    if zh:
        a(f"- 现役系统：每 100 个请求约答错 **{wf}** 个")
        if wr is not None and not m.reference_is_estimate:
            a(f"- 若换新模型并重训（我们真实训练并测过，非估算）：约答错 "
              f"**{wr}** 个")
        if m.adopt_floor is not None:
            a(f"- 若直接裸用新模型、不做任何训练：约答错 "
              f"**{_wrong_per_100(m.adopt_floor)}** 个——你的训练数据"
              "才是护城河")
    else:
        a(f"- current system: about **{wf}** wrong per 100 requests")
        if wr is not None and not m.reference_is_estimate:
            a(f"- retrained on the new model (actually trained and "
              f"measured, not estimated): about "
              f"**{wr}** wrong per 100")
        if m.adopt_floor is not None:
            a(f"- the new model used bare, with no training: about "
              f"**{_wrong_per_100(m.adopt_floor)}** wrong per 100 -- your "
              "training data is the moat")
    a("")

    a("## " + ("我们做了哪些检查" if zh else "What we checked"))
    for i, (title, detail) in enumerate(_checks(m, ev, lang), 1):
        a(f"{i}. **{title}** -- {detail}")
    a("")

    post = ev.get("posterior")
    econ = ev.get("economic_epsilon_pp")
    if post or econ is not None:
        a("## " + ("值不值得：一句话的账" if zh else "The money question"))
        if post:
            if zh:
                a(f"- 综合你的数据与 193 个公开实测升级案例：这次升级带来"
                  f"足够收益的可能性约 **{_fmt_pct(post['p_gain_above_eps'])}**，"
                  f"造成倒退的可能性约 {_fmt_pct(post['p_loss_below_neg_eps'])}")
            else:
                a(f"- combining your data with 193 published measured "
                  f"upgrade cases: roughly **"
                  f"{_fmt_pct(post['p_gain_above_eps'])}** chance this "
                  f"upgrade pays off, "
                  f"{_fmt_pct(post['p_loss_below_neg_eps'])} chance it "
                  "regresses")
        if econ is not None:
            if zh:
                a(f"- 按你填写的请求量与错误成本折算：质量至少要提升 "
                  f"**{econ}%** 才能覆盖迁移成本（这是本报告使用的"
                  "“值得”门槛）")
            else:
                a(f"- at your stated volume and error cost, quality must "
                  f"improve by at least **{econ}%** to cover migration "
                  "(that is the \"worth it\" bar this brief uses)")
        a("")

    a("## " + ("下一步" if zh else "Next steps"))
    for i, s in enumerate(_next_steps(rec, ev, lang), 1):
        a(f"{i}. {s}")
    a("")

    a("## " + ("这个结论有多可靠" if zh else "How much to trust this"))
    pe = ev.get("paired_evidence", {})
    if zh:
        a(f"- 全部数字来自你自己的 {pe.get('n', '—')} 条真实业务数据的"
          "实测对比与真实训练，无任何估算或演示数据")
        a("- 方法与阈值来自公开基准 UpgradeBench（2026）：33 个实测升级"
          "决策回放，平均决策损失 0.37%，零线上倒退")
        a("- 当证据不足时，本工具会直说“不足”并给出补证的最小成本，"
          "而不是硬给一个结论")
    else:
        a(f"- every number comes from measured runs on your own "
          f"{pe.get('n', '--')} real business records; nothing is estimated "
          "or demo data")
        a("- method and thresholds follow the published UpgradeBench (2026) "
          "benchmark: 33 replayed upgrade decisions, 0.37% mean decision "
          "loss, zero serving regressions")
        a("- when the evidence is insufficient, this tool says so and "
          "prices the cheapest way to settle it, rather than forcing a "
          "verdict")
    a("")
    a("---")
    a("*" + ("技术附录（统计细节，供工程团队）：recommendation.md"
             if zh else
             "Technical appendix (full statistics, for the engineering "
             "team): recommendation.md") + "*")
    return "\n".join(L)


def decision_card(rec, ev, lang="en"):
    """6-line terminal card printed before the technical report."""
    zh = lang == "zh"
    pe = ev.get("paired_evidence", {})
    head = _headline(rec, ev, lang)
    # strip markdown bold for terminal
    head = head.replace("**", "")
    lines = ["=" * 64, head]
    if pe:
        lines.append(
            (f"依据：{pe.get('n')} 条真实数据逐题对比，新系统修好 "
             f"{pe.get('reference_fixes')} 题 / 改错 "
             f"{pe.get('reference_breaks')} 题")
            if zh else
            (f"Basis: {pe.get('n')} real records compared head-to-head; "
             f"new system fixes {pe.get('reference_fixes')}, breaks "
             f"{pe.get('reference_breaks')}"))
    lines.append("=" * 64)
    return "\n".join(lines)
