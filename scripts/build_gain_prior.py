# -*- coding: utf-8 -*-
"""Build registry/gain_prior.json from the UpgradeBench per-cell corpus.

The paper's 193 measured eval cells are an empirical-Bayes prior for the
platform: for each documented upgrade relation (release_graph.yaml) we
collect the specialist-score delta (target expert - source expert) on the
same task, bucketed by edge kind (fresh_pretraining vs continuation). The
across-(task,pair) spread of those deltas plus the seed-to-seed training
variance (multi-seed waves) gives the prior variance a small gate set
borrows strength from.

Every number is read from E:\\dataset\\records\\summary_all.json (the
paper's audited registry); nothing is assumed.

Usage: python scripts/build_gain_prior.py [SUMMARY_JSON] [OUT_JSON]
"""
import json
import statistics
import sys

SUMMARY = (sys.argv[1] if len(sys.argv) > 1
           else r"E:\dataset\records\summary_all.json")
OUT = (sys.argv[2] if len(sys.argv) > 2
       else r"D:\in UTD\Dropbox\AI research\AI papers\organizational AI"
            r"\P1-UpgradeBench\platform plan\upgrade-advisor\registry"
            r"\gain_prior.json")

TASK_KIND = {"banking77": "classification", "clinc150": "classification",
             "spider": "structured", "xlam": "structured",
             "glaive": "structured", "glaive_v2": "structured",
             "finqa": "structured"}

# Upgrade pairs, keyed by the model tokens used in cell tags. Kinds follow
# registry/release_graph.yaml: Qwen generations and OLMo-1->1.7 are fresh
# pretrainings (composed generation skips stay fresh); Qwen2.5->1M is a
# documented 20B continuation; the OLMo-2 stage-1 checkpoints are documented
# continuations of each other (46B / 2.9T).
PAIRS = [
    ("q15", "q2", "fresh"), ("q2", "q25", "fresh"), ("q25", "q3", "fresh"),
    ("q15", "q25", "fresh"), ("q2", "q3", "fresh"), ("q15", "q3", "fresh"),
    ("olmo1", "olmo17", "fresh"), ("olmo17", "o2main", "fresh"),
    ("q25", "q1m", "continuation"),
    ("o2s237", "o2s248", "continuation"),
    ("o2s237", "o2s928", "continuation"),
    ("o2s248", "o2s928", "continuation"),
]


def main():
    evals = json.load(open(SUMMARY, encoding="utf-8"))["evals"]
    # task -> model token -> expert score (primary rows: no seed suffix,
    # no _constr variant; expert recipe only)
    expert = {}
    for key, v in evals.items():
        task, tag = key.split("/", 1)
        t = tag[len(task) + 1:] if tag.startswith(task + "_") else tag
        parts = t.split("_")
        if len(parts) != 2 or parts[1] != "expert":
            continue
        expert.setdefault(task, {})[parts[0]] = v["score"]

    buckets = {"fresh": [], "continuation": []}
    for src, tgt, kind in PAIRS:
        for task, models in expert.items():
            if src in models and tgt in models:
                delta = models[tgt] - models[src]
                buckets[kind].append({
                    "task": task, "task_kind": TASK_KIND[task],
                    "pair": f"{src}->{tgt}",
                    "delta_pp": round(delta * 100, 2)})

    def _agg(rows):
        ds = [r["delta_pp"] for r in rows]
        return {"n_samples": len(ds),
                "mu_pp": round(statistics.mean(ds), 2),
                "sd_pp": round(statistics.stdev(ds), 2) if len(ds) > 1
                else None,
                "samples": rows}

    # seed-to-seed training variance: families tagged _s43/_s44 alongside
    # the primary run, per (task, model, recipe)
    fams = {}
    for key, v in evals.items():
        task, tag = key.split("/", 1)
        t = tag[len(task) + 1:] if tag.startswith(task + "_") else tag
        if t.endswith("_s43") or t.endswith("_s44"):
            base = t[:-4]
        else:
            base = t
        fams.setdefault((task, base), {})[t] = v["score"]
    seed_rows = []
    for (task, base), runs in fams.items():
        if len(runs) >= 3:      # primary + two seeds
            scores = list(runs.values())
            seed_rows.append({
                "task": task, "task_kind": TASK_KIND[task], "family": base,
                "n_seeds": len(scores),
                "sd_pp": round(statistics.stdev(scores) * 100, 2),
                "spread_pp": round((max(scores) - min(scores)) * 100, 2)})
    by_kind = {}
    for r in seed_rows:
        by_kind.setdefault(r["task_kind"], []).append(r["sd_pp"])
    sigma_seed = {k: {"n_families": len(v),
                      "median_sd_pp": round(statistics.median(v), 2),
                      "mean_sd_pp": round(statistics.mean(v), 2)}
                  for k, v in by_kind.items()}

    out = {
        "provenance": {
            "source": SUMMARY,
            "rule": "delta = expert(target) - expert(source), same task, "
                    "primary rows (no seed suffix, no _constr); pairs per "
                    "registry/release_graph.yaml edge kinds",
            "paper": "UpgradeBench (2026), 193 measured eval cells"},
        "buckets": {k: _agg(v) for k, v in buckets.items()},
        "sigma_seed": {"per_family": seed_rows, "by_task_kind": sigma_seed},
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"wrote {OUT}")
    for k, v in out["buckets"].items():
        print(f"  {k}: n={v['n_samples']} mu={v['mu_pp']}pp sd={v['sd_pp']}pp")
    print(f"  sigma_seed: {sigma_seed}")


if __name__ == "__main__":
    main()
