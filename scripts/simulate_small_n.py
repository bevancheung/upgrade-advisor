# -*- coding: utf-8 -*-
"""Small-evidence operating characteristics of the decision core, validated
on the UpgradeBench per-example corpus (review-2, paper addition A).

The paper validated the policy at n=1034-5500; enterprises run it at
n=100-600. This script closes that external-validity gap by simulation on
real records: for every documented upgrade pair with per-example records,
subsample enterprise-sized gate sets, run the v2 decision core, and score
it against the full-n ground truth.

Experiment 1 (operating curve): action distribution, false-open rate,
false-equivalence rate, and mean regret vs n -- v2 core (TOST + corpus
prior, leave-one-pair-out to avoid self-priming) against the old
point-estimate rule.

Experiment 2 (annotation efficiency): labels needed to settle the
direction -- i.i.d. labeling vs disagreement-first labeling (scan
unlabeled traffic with both systems, label only disagreements).

Every record is a real eval row from E:\\dataset\\records; nothing is
synthesized.
"""
import json
import math
import os
import random
import statistics
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from upgrade_advisor import policy as P            # noqa: E402
from upgrade_advisor import stats as S             # noqa: E402

REC = r"E:\dataset\records"
PRIOR = os.path.join(os.path.dirname(__file__), "..", "registry",
                     "gain_prior.json")
OUT_JSON = os.path.join(os.path.dirname(__file__), "..", "docs",
                        "small_n_simulation.json")
OUT_MD = os.path.join(os.path.dirname(__file__), "..", "docs",
                      "small_n_operating_curve.md")

TASK_KIND = {"banking77": "classification", "clinc150": "classification",
             "spider": "structured", "xlam": "structured",
             "glaive_v2": "structured", "finqa": "structured"}
PREFIX = {"banking77": "", "clinc150": "clinc150_", "spider": "sp_",
          "xlam": "xl_", "glaive_v2": "glv2_", "finqa": "finqa_"}
PAIRS = [
    ("q15", "q2", "fresh"), ("q2", "q25", "fresh"), ("q25", "q3", "fresh"),
    ("q15", "q25", "fresh"), ("q2", "q3", "fresh"), ("q15", "q3", "fresh"),
    ("olmo1", "olmo17", "fresh"),
    ("q25", "q1m", "continuation"),
]
NS = [100, 200, 300, 600, 1000]
REPS = 300
SEED = 20260819


def load_correct(path):
    out = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            out[str(r["id"])] = bool(r["correct"])
    return out


def find_records(task, model):
    p = os.path.join(REC, task, f"{PREFIX[task]}{model}_expert_test.jsonl")
    return p if os.path.exists(p) else None


def collect_pairs():
    """(task, src, tgt, kind) -> paired outcome vectors on common ids."""
    out = []
    for task in TASK_KIND:
        for src, tgt, kind in PAIRS:
            ps, pt = find_records(task, src), find_records(task, tgt)
            if not ps or not pt:
                continue
            a, b = load_correct(ps), load_correct(pt)
            ids = sorted(set(a) & set(b))
            if len(ids) < 800:
                continue
            out.append({"task": task, "kind": kind,
                        "pair": f"{src}->{tgt}",
                        "frozen": [a[i] for i in ids],
                        "ref": [b[i] for i in ids]})
    return out


def loo_prior(prior, kind, task, pair):
    """Leave the evaluated (task, pair) sample out of its own prior."""
    rows = [s for s in prior["buckets"][kind]["samples"]
            if not (s["task"] == task and s["pair"] == pair)]
    ds = [s["delta_pp"] / 100 for s in rows]
    if len(ds) < 3:
        return None
    return (statistics.mean(ds), statistics.stdev(ds))


def decide_v2(fr, rf, prior_mu, prior_sd, sigma_seed, eps):
    n = len(fr)
    n01 = sum(1 for f, r in zip(fr, rf) if not f and r)
    n10 = sum(1 for f, r in zip(fr, rf) if f and not r)
    m = P.Measurements(
        task_kind="classification" if eps == 0.01 else "structured",
        freeze_score=sum(fr) / n, adopt_floor=0.0,
        reference_score=sum(rf) / n, gate_set_size=n,
        paired_n=n, paired_n01=n01, paired_n10=n10,
        paired_freeze_errors=sum(1 for f in fr if not f),
        prior_mu=prior_mu, prior_sd=prior_sd, sigma_seed=sigma_seed)
    return P.recommend(m)


def main():
    rng = random.Random(SEED)
    prior = json.load(open(PRIOR, encoding="utf-8"))
    pairs = collect_pairs()
    print(f"{len(pairs)} (task, pair) cells with full per-example records")

    results = []
    for cell in pairs:
        fr_full, rf_full = cell["frozen"], cell["ref"]
        n_full = len(fr_full)
        eps = 0.01 if TASK_KIND[cell["task"]] == "classification" else 0.02
        delta_full = (sum(rf_full) - sum(fr_full)) / n_full
        best_is_upgrade = delta_full > eps
        lp = loo_prior(prior, cell["kind"], cell["task"], cell["pair"])
        sseed = (prior["sigma_seed"]["by_task_kind"]
                 .get(TASK_KIND[cell["task"]], {})
                 .get("median_sd_pp", 0)) / 100
        row = {"task": cell["task"], "pair": cell["pair"],
               "kind": cell["kind"], "n_full": n_full,
               "delta_full_pp": round(delta_full * 100, 2),
               "epsilon_pp": eps * 100, "curve": {}}
        idx = list(range(n_full))
        for n in NS:
            if n > n_full:
                continue
            tally = {"v2": {}, "old": {}}
            regret = {"v2": 0.0, "old": 0.0}
            false_open = {"v2": 0, "old": 0}
            false_equiv = 0
            dis_all = [i for i in idx if fr_full[i] != rf_full[i]]
            for _ in range(REPS):
                sub = rng.sample(idx, n)
                fr = [fr_full[i] for i in sub]
                rf = [rf_full[i] for i in sub]
                rec = decide_v2(fr, rf,
                                lp[0] if lp else None,
                                lp[1] if lp else None, sseed, eps)
                act = rec.action.value
                if rec.verdict == "gain-established":
                    a_v2 = "open"
                elif rec.verdict == "equivalence":
                    a_v2 = "equivalence"
                    if best_is_upgrade:
                        false_equiv += 1
                else:
                    a_v2 = act        # collect / wait
                tally["v2"][a_v2] = tally["v2"].get(a_v2, 0) + 1
                serve_ref = a_v2 == "open"
                # stage 2: COLLECT is not terminal -- label up to 50
                # disagreements (real records) and re-judge the direction
                if a_v2 == "collect" and dis_all:
                    subd = rng.sample(dis_all, min(50, len(dis_all)))
                    d01 = sum(1 for i in subd
                              if not fr_full[i] and rf_full[i])
                    d10 = len(subd) - d01
                    if S.sign_test_p(d01, d10) < 0.05 and d01 > d10:
                        serve_ref = True
                if serve_ref and not best_is_upgrade:
                    false_open["v2"] += 1
                regret["v2"] += (max(0.0, -delta_full) if serve_ref
                                 else max(0.0, delta_full))
                # old rule: point estimate through the gate
                gain_pt = (sum(rf) - sum(fr)) / n
                a_old = "open" if gain_pt > eps + 1e-9 else "freeze"
                tally["old"][a_old] = tally["old"].get(a_old, 0) + 1
                if a_old == "open" and not best_is_upgrade:
                    false_open["old"] += 1
                regret["old"] += (max(0.0, -delta_full) if a_old == "open"
                                  else max(0.0, delta_full))
            row["curve"][n] = {
                "v2_actions": {k: round(v / REPS, 3)
                               for k, v in sorted(tally["v2"].items())},
                "old_actions": {k: round(v / REPS, 3)
                                for k, v in sorted(tally["old"].items())},
                "v2_false_open_after_collect": round(false_open["v2"] / REPS, 3),
                "old_false_open": round(false_open["old"] / REPS, 3),
                "v2_false_equivalence": round(false_equiv / REPS, 3),
                "v2_mean_regret_pp_after_collect": round(regret["v2"] / REPS * 100, 3),
                "old_mean_regret_pp": round(regret["old"] / REPS * 100, 3),
            }
        results.append(row)
        print(f"  {cell['task']:<10} {cell['pair']:<12} "
              f"delta_full={row['delta_full_pp']:+.2f}pp done")

    # ---- Experiment 2: annotation efficiency ----
    eff = []
    for cell in pairs:
        fr_full, rf_full = cell["frozen"], cell["ref"]
        n_full = len(fr_full)
        eps = 0.01 if TASK_KIND[cell["task"]] == "classification" else 0.02
        delta_full = (sum(rf_full) - sum(fr_full)) / n_full
        dis_idx = [i for i in range(n_full) if fr_full[i] != rf_full[i]]
        true_dir = 1 if delta_full > 0 else (-1 if delta_full < 0 else 0)
        if true_dir == 0 or len(dis_idx) < 6:
            continue
        budgets = [10, 25, 50, 100, 200, 400]
        row = {"task": cell["task"], "pair": cell["pair"],
               "delta_full_pp": round(delta_full * 100, 2),
               "disagreement_rate": round(len(dis_idx) / n_full, 4),
               "iid": {}, "disagree_first": {}}
        for b in budgets:
            hit_iid = hit_dis = 0
            for _ in range(REPS):
                # i.i.d.: label b random items, infer from their pairs
                sub = rng.sample(range(n_full), min(b, n_full))
                n01 = sum(1 for i in sub if not fr_full[i] and rf_full[i])
                n10 = sum(1 for i in sub if fr_full[i] and not rf_full[i])
                if S.sign_test_p(n01, n10) < 0.05 and \
                        (1 if n01 > n10 else -1) == true_dir:
                    hit_iid += 1
                # disagreement-first: scan all unlabeled with both systems
                # (zero labels), label b of the disagreements
                subd = rng.sample(dis_idx, min(b, len(dis_idx)))
                d01 = sum(1 for i in subd if not fr_full[i] and rf_full[i])
                d10 = len(subd) - d01
                if S.sign_test_p(d01, d10) < 0.05 and \
                        (1 if d01 > d10 else -1) == true_dir:
                    hit_dis += 1
            row["iid"][b] = round(hit_iid / REPS, 3)
            row["disagree_first"][b] = round(hit_dis / REPS, 3)
        eff.append(row)

    out = {"provenance": {
               "records": REC, "reps": REPS, "seed": SEED,
               "prior": "leave-one-pair-out from registry/gain_prior.json",
               "old_rule": "point-estimate gain > epsilon opens"},
           "experiment1_operating_curve": results,
           "experiment2_annotation_efficiency": eff}
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"wrote {OUT_JSON}")


if __name__ == "__main__":
    main()
