# -*- coding: utf-8 -*-
"""COLLECT channel (review-2 fix: evidence design). On saturated tasks the
decision-relevant information lives entirely in the items where the two
systems disagree -- and disagreement is observable WITHOUT gold labels.
McNemar's test conditions on the discordant pairs, so labeling only
disagreements buys the same inference as i.i.d. labeling at a fraction of
the annotation cost: O(#disagreements), not O(n).

Two modes:
- record mode (zero GPU): pull the disagreement set out of existing paired
  records (pred fields), with gold outcomes where already labeled;
- unlabeled mode (GPU, via cli): run both systems over unlabeled traffic,
  emit the disagreement set for annotation.

`convergence_forecast` prices the information: the probability that
labeling k more disagreements settles the direction (exact sign test),
under the Beta posterior implied by the disagreements labeled so far.
"""
import json
import math
import os
from typing import Dict, Optional


def load_preds(path: str) -> Dict[str, dict]:
    out = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            out[str(r["id"])] = r
    return out


def disagreement_set(freeze_recs: Dict[str, dict],
                     ref_recs: Dict[str, dict]) -> list:
    """Items where the two systems' predictions differ, with gold where
    present. Sorted by id for reproducibility."""
    rows = []
    for i in sorted(set(freeze_recs) & set(ref_recs)):
        f, r = freeze_recs[i], ref_recs[i]
        pf = f.get("pred", f.get("pred_sql", f.get("pred_raw")))
        pr = r.get("pred", r.get("pred_sql", r.get("pred_raw")))
        if pf == pr:
            continue
        row = {"id": i, "pred_frozen": pf, "pred_reference": pr}
        if "gold" in f and f["gold"] not in (None, ""):
            row["gold"] = f["gold"]
            row["outcome"] = ("reference_fixes" if r.get("correct")
                              and not f.get("correct") else
                              "reference_breaks" if f.get("correct")
                              and not r.get("correct") else "both_wrong")
        rows.append(row)
    return rows


def _log_beta(a: float, b: float) -> float:
    return math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)


def _beta_binom_pmf(x: int, k: int, a: float, b: float) -> float:
    return math.exp(math.lgamma(k + 1) - math.lgamma(x + 1)
                    - math.lgamma(k - x + 1)
                    + _log_beta(x + a, k - x + b) - _log_beta(a, b))


def _sign_p(n01: int, n10: int) -> float:
    n = n01 + n10
    if n == 0:
        return 1.0
    lo = min(n01, n10)
    tail = sum(math.comb(n, j) for j in range(lo + 1))
    return min(1.0, 2 * tail / 2 ** n)


def convergence_forecast(n01: int, n10: int, k: int) -> float:
    """P(direction settles) after labeling k more disagreements: the exact
    sign test over all labeled disagreements goes below 0.05, with the k
    new outcomes drawn Beta-Binomial from the posterior
    theta ~ Beta(n01+1, n10+1) over the current fix/break split."""
    if k <= 0:
        return 1.0 if _sign_p(n01, n10) < 0.05 else 0.0
    a, b = n01 + 1, n10 + 1
    p = 0.0
    for x in range(k + 1):
        if _sign_p(n01 + x, n10 + k - x) < 0.05:
            p += _beta_binom_pmf(x, k, a, b)
    return p


def collection_plan(n01: int, n10: int,
                    budgets=(10, 25, 50, 100, 200)) -> list:
    """Convergence probability at each labeling budget -- the concrete
    'label this many disagreements' plan an INCONCLUSIVE verdict points to."""
    return [{"label_k_more": k,
             "p_direction_settles": round(convergence_forecast(n01, n10, k), 3)}
            for k in budgets]


def summarize(workdir: str, freeze_stem: str = "freeze",
              ref_stem: str = "reference",
              out_name: str = "disagreements.jsonl") -> Optional[dict]:
    """Record mode: pool val+test records, write the disagreement set, and
    return the summary (rate, labeled outcomes, collection plan)."""
    pool_f, pool_r = {}, {}
    for suf in ("", "_val"):
        fp = os.path.join(workdir, f"{freeze_stem}{suf}.jsonl")
        rp = os.path.join(workdir, f"{ref_stem}{suf}.jsonl")
        if os.path.exists(fp) and os.path.exists(rp):
            for i, r in load_preds(fp).items():
                pool_f[f"{suf}:{i}"] = r
            for i, r in load_preds(rp).items():
                pool_r[f"{suf}:{i}"] = r
    if not pool_f or not pool_r:
        return None
    rows = disagreement_set(pool_f, pool_r)
    n_common = len(set(pool_f) & set(pool_r))
    out_path = os.path.join(workdir, out_name)
    with open(out_path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    n01 = sum(1 for r in rows if r.get("outcome") == "reference_fixes")
    n10 = sum(1 for r in rows if r.get("outcome") == "reference_breaks")
    summary = {
        "n_paired": n_common,
        "n_disagreements": len(rows),
        "disagreement_rate": round(len(rows) / n_common, 4) if n_common else 0,
        "labeled_outcomes": {
            "reference_fixes": n01, "reference_breaks": n10,
            "both_wrong": sum(1 for r in rows
                              if r.get("outcome") == "both_wrong"),
            "unlabeled": sum(1 for r in rows if "outcome" not in r)},
        "sign_test_p": round(_sign_p(n01, n10), 4),
        "collection_plan": collection_plan(n01, n10),
        "disagreements_file": out_path,
    }
    with open(os.path.join(workdir, "disagree_summary.json"), "w",
              encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    return summary
