# -*- coding: utf-8 -*-
"""Markdown evidence report for a recommendation."""


def render_report(cfg, target, verdict, m, rec):
    lines = []
    a = lines.append
    a(f"# Upgrade recommendation: `{cfg['task_name']}` -> `{target}`")
    a("")
    a(f"## Action: **{rec.action.value.upper()}**"
      + (f" (verdict: {rec.verdict})" if getattr(rec, "verdict", "") else ""))
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
    if "posterior" in ev:
        po = ev["posterior"]
        a(f"- posterior over the true gain (UpgradeBench-corpus prior + "
          f"paired evidence): mean {po['post_mu_pp']:+.2f}pp, sd "
          f"{po['post_sd_pp']:.2f}pp; P(gain > decision epsilon) = "
          f"{po['p_gain_above_eps']:.0%}, P(regression beyond epsilon) = "
          f"{po['p_loss_below_neg_eps']:.0%}, P(within band) = "
          f"{po['p_within_band']:.0%}")
    if "paired_evidence" in ev:
        pe = ev["paired_evidence"]
        ci = ev.get("opportunity_ci_pooled_pp")
        a(f"- pooled paired evidence (val+test): n={pe['n']}, reference "
          f"fixes {pe['reference_fixes']} frozen error(s) and breaks "
          f"{pe['reference_breaks']} frozen pass(es)"
          + (f"; 95% CI [{ci[0]:+.1f}, {ci[1]:+.1f}]pp -- gains above "
             f"{ev['excluded_gain_above_pp']:.1f}pp are excluded by the "
             "data" if ci else ""))
    if "mde_pp" in ev:
        a(f"- power: minimal detectable difference at this gate set = "
          f"{ev['mde_pp']}pp")
    if "opportunity_rer" in ev:
        a(f"- error-scale view: relative error reduction "
          f"{ev['opportunity_rer']:+.0%} "
          f"({ev.get('freeze_errors_on_gate', '?')} frozen errors on gate)")
    if "nll_ref_minus_freeze" in ev:
        dm, dlo, dhi = ev["nll_ref_minus_freeze"]
        a("")
        a("## Confidence layer (proper scoring; more power than accuracy)")
        a(f"- paired log-loss, reference - frozen: {dm:+.4f} "
          f"(95% CI [{dlo:+.4f}, {dhi:+.4f}]; negative favors reference)")
        a(f"- calibration ECE: frozen {ev['ece']['freeze']}, "
          f"reference {ev['ece']['reference']}")
        a(f"- risk-coverage AURC (lower = better selective routing): "
          f"frozen {ev['aurc']['freeze']}, "
          f"reference {ev['aurc']['reference']}")
    if "disagreement" in ev:
        dg = ev["disagreement"]
        a("")
        a("## Disagreement set (COLLECT channel: label these, not more "
          "i.i.d. samples)")
        a(f"- {dg['n_disagreements']} disagreement item(s) "
          f"({dg['disagreement_rate']:.1%} of pooled pairs); exact sign "
          f"test on labeled outcomes p = {dg['sign_test_p']}")
        if dg.get("collection_plan"):
            plan = ", ".join(
                f"+{p['label_k_more']}: {p['p_direction_settles']:.0%}"
                for p in dg["collection_plan"])
            a(f"- probability the direction settles after labeling k more "
              f"disagreements -- {plan}")
    if "robustness" in ev:
        rb = ev["robustness"]
        a("")
        a("## Robustness under perturbation (typo/casing/filler/punct; "
          "gold unchanged)")
        a(f"- frozen: {rb['freeze_perturbed']}"
          + (f"; reference: {rb['reference_perturbed']} "
             f"(delta {rb['robustness_delta_pp']:+.2f}pp)"
             if "reference_perturbed" in rb else ""))
    if "economic_epsilon_pp" in ev:
        a(f"- economic epsilon (break-even gain at stated volume/costs): "
          f"{ev['economic_epsilon_pp']}pp")
    if "label_metrics" in ev:
        a("")
        a("## Label metrics (macro-F1: class-imbalance-robust; "
          "invalid rate: prediction outside the label inventory)")
        for stem, d in ev["label_metrics"].items():
            a(f"- {stem}: macro-F1 **{d['macro_f1']}**, "
              f"invalid outputs {d['invalid_rate']:.2%} "
              f"({d['n_classes']} classes)")
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
      "split-half gating). Negative-flip rate follows Yan et al., "
      "Positive-Congruent Training, CVPR 2021. Scope: LoRA-class adapters, "
      "1.5-8B open-weight models.*")
    return "\n".join(lines)
