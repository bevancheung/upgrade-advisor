# -*- coding: utf-8 -*-
"""Markdown evidence report for a recommendation."""


def render_report(cfg, target, verdict, m, rec):
    lines = []
    a = lines.append
    a(f"# Upgrade recommendation: `{cfg['task_name']}` -> `{target}`")
    a("")
    a(f"## Action: **{rec.action.value.upper()}**")
    a("")
    a("## Evidence")
    a(f"- frozen specialist (gate half, n={m.gate_set_size}): "
      f"**{m.freeze_score:.4f}**")
    a(f"- target adoption floor: **{m.adopt_floor:.4f}**")
    if m.reference_score is not None:
        tag = " (beta estimate)" if m.reference_is_estimate else ""
        a(f"- retraining reference{tag}: **{m.reference_score:.4f}** "
          f"(opportunity {rec.evidence.get('opportunity_pp', 0):+.2f}pp, "
          f"epsilon {rec.epsilon*100:.0f}pp)")
    if m.copy_score is not None:
        a(f"- copied adapter: **{m.copy_score:.4f}** "
          f"(NFR vs serving: {m.copy_negative_flip_rate:.2%})")
    if m.refresh_score is not None:
        a(f"- refresh student: **{m.refresh_score:.4f}**")
    a(f"- genealogy: {verdict.edge_type} "
      f"({verdict.confidence}); "
      + (f"continuation {float(verdict.continuation_tokens)/1e9:.0f}B tokens"
         if verdict.continuation_tokens else "distance unknown"))
    if verdict.note:
        a(f"  - {verdict.note}")
    ev = rec.evidence
    if any(k in ev for k in ("opportunity_ci_pp", "copy_vs_reference_ci_pp",
                             "refresh_vs_reference_ci_pp")):
        a("")
        a("## Statistics (report half only; gates never see these items)")
        if "opportunity_ci_pp" in ev:
            lo, hi = ev["opportunity_ci_pp"]
            a(f"- reference - frozen: 95% CI [{lo:+.2f}, {hi:+.2f}]pp, "
              f"exact McNemar p = {ev['opportunity_mcnemar_p']}")
        for tag in ("copy", "refresh"):
            k = f"{tag}_vs_reference_ci_pp"
            if k in ev:
                lo, hi = ev[k]
                a(f"- {tag} - reference: 95% CI [{lo:+.2f}, {hi:+.2f}]pp, "
                  f"p = {ev[f'{tag}_vs_reference_p']}")
    if "ledger" in ev:
        led = ev["ledger"]
        a("")
        a(f"## Task ledger: {led['episodes']} episode(s), "
          f"{led['train_gpu_minutes']} train GPU-min, "
          f"{led['eval_gpu_minutes']} eval GPU-min, "
          f"{led.get('gold_labels_consumed', 0)} gold labels, "
          f"{led.get('teacher_queries', 0)} teacher queries, "
          f"{led.get('validation_items', 0)} validation items accumulated")
    a("")
    a("## Reasoning")
    for x in rec.reasons:
        a(f"- {x}")
    if rec.warnings:
        a("")
        a("## Warnings")
        for x in rec.warnings:
            a(f"- {x}")
    a("")
    a("## Before serving")
    a("- run `upgrade-advisor gate` for the candidate against the serving "
      "records (reporting half only); block on negative-flip budget "
      f"{cfg.get('flip_budget', 0.03):.0%}")
    a("- log GPU-minutes and labels consumed for this episode so the "
      "amortized decision improves with each release")
    a("")
    a("*Policy and margins from UpgradeBench (2026); validated over 33 "
      "measured upgrade episodes (0.37pp mean regret, zero regressions, "
      "split-half gating). Scope: LoRA-class adapters, 1.5-8B open-weight "
      "models.*")
    return "\n".join(lines)
