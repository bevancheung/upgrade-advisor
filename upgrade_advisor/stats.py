# -*- coding: utf-8 -*-
"""Statistics layer (Playbook Phase 0: bootstrap CIs, paired McNemar).

Ported from the UpgradeBench harness: exact McNemar on discordant pairs,
percentile bootstrap on per-example records. Pure python + stdlib.
"""
import json
import random
import re
from fractions import Fraction
from math import comb
from typing import Dict, List, Tuple


def _norm_label(s: str) -> str:
    s = re.sub(r"<think>.*?</think>", "", s, flags=re.S).strip().strip("\"'`.")
    s = s.splitlines()[0].strip() if s else ""
    return s.lower().replace(" ", "_").replace("-", "_")


def label_metrics(records_path: str) -> dict:
    """Macro-F1 over the gold label set (standard class-imbalance-robust
    metric) and invalid-output rate (prediction outside the label
    inventory; format-reliability in the function-calling literature).
    Computed from per-example records; classification tasks only."""
    rows = [json.loads(l) for l in open(records_path, encoding="utf-8")]
    golds = [_norm_label(r["gold"]) for r in rows]
    preds = [_norm_label(r["pred"]) for r in rows]
    labels = sorted(set(golds))
    label_set = set(labels)
    f1s = []
    for lb in labels:
        tp = sum(1 for g, p in zip(golds, preds) if g == lb and p == lb)
        fp = sum(1 for g, p in zip(golds, preds) if g != lb and p == lb)
        fn = sum(1 for g, p in zip(golds, preds) if g == lb and p != lb)
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1s.append(2 * prec * rec / (prec + rec) if prec + rec else 0.0)
    invalid = sum(1 for p in preds if p not in label_set)
    return {"macro_f1": round(sum(f1s) / len(f1s), 4) if f1s else None,
            "invalid_rate": round(invalid / len(rows), 4) if rows else None,
            "n_classes": len(labels)}


def bootstrap_ci(correct: List[bool], n_resamples: int = 10000,
                 seed: int = 42) -> Tuple[float, float]:
    """95% percentile CI for a single accuracy."""
    rng = random.Random(seed)
    m = len(correct)
    vals = [1.0 if c else 0.0 for c in correct]
    means = []
    for _ in range(n_resamples):
        s = 0.0
        for _ in range(m):
            s += vals[rng.randrange(m)]
        means.append(s / m)
    means.sort()
    return (means[int(0.025 * n_resamples)],
            means[int(0.975 * n_resamples) - 1])


def paired_diff_ci(a: Dict[str, bool], b: Dict[str, bool],
                   n_resamples: int = 10000, seed: int = 42
                   ) -> Tuple[float, float, float]:
    """Mean of (a - b) in pp with a 95% paired bootstrap CI, over common ids."""
    ids = sorted(set(a) & set(b))
    diffs = [(1.0 if a[i] else 0.0) - (1.0 if b[i] else 0.0) for i in ids]
    m = len(diffs)
    mean = sum(diffs) / m * 100
    rng = random.Random(seed)
    means = []
    for _ in range(n_resamples):
        s = 0.0
        for _ in range(m):
            s += diffs[rng.randrange(m)]
        means.append(s / m * 100)
    means.sort()
    return (mean, means[int(0.025 * n_resamples)],
            means[int(0.975 * n_resamples) - 1])


def mcnemar(a: Dict[str, bool], b: Dict[str, bool]
            ) -> Tuple[int, int, float]:
    """Exact two-sided McNemar on discordant pairs; returns (b01, c10, p)."""
    ids = sorted(set(a) & set(b))
    b01 = sum(1 for i in ids if a[i] and not b[i])
    c10 = sum(1 for i in ids if not a[i] and b[i])
    n = b01 + c10
    if n == 0:
        return b01, c10, 1.0
    tail = sum(comb(n, j) for j in range(0, min(b01, c10) + 1))
    p = 2 * tail * Fraction(1, 2 ** n)
    return b01, c10, min(1.0, float(p))
