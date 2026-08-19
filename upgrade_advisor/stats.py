# -*- coding: utf-8 -*-
"""Statistics layer (Playbook Phase 0: bootstrap CIs, paired McNemar).

Ported from the UpgradeBench harness: exact McNemar on discordant pairs,
percentile bootstrap on per-example records. Pure python + stdlib.
"""
import json
import math
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


def paired_counts(a: Dict[str, bool], b: Dict[str, bool]
                  ) -> Tuple[int, int, int]:
    """(n, n01, n10) over common ids: n01 = items a gets wrong and b fixes,
    n10 = items a gets right and b breaks. The decision-relevant evidence
    lives entirely in these discordant pairs."""
    ids = sorted(set(a) & set(b))
    n01 = sum(1 for i in ids if not a[i] and b[i])
    n10 = sum(1 for i in ids if a[i] and not b[i])
    return len(ids), n01, n10


def paired_gain_ci(n: int, n01: int, n10: int, z: float = 1.96
                   ) -> Tuple[float, float]:
    """95% CI for the paired accuracy difference (b - a) from discordant
    counts, with a continuity correction. Zero discordance is itself strong
    evidence: the rule-of-three bound |diff| <= 3.69/n (95%, two-sided via
    one-sided 97.5% on the discordance rate) replaces a degenerate CI."""
    if n <= 0:
        return -1.0, 1.0
    nd = n01 + n10
    if nd == 0:
        b = 3.69 / n
        return -b, b
    d = (n01 - n10) / n
    se = ((nd - (n01 - n10) ** 2 / n) ** 0.5) / n
    half = z * se + 1.0 / n
    return d - half, d + half


def normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def posterior_gain(n: int, n01: int, n10: int, prior_mu: float,
                   prior_sd: float, sigma_seed: float = 0.0
                   ) -> Tuple[float, float]:
    """Empirical-Bayes posterior over the true upgrade gain (normal-normal
    conjugate). Likelihood: observed paired difference with variance =
    sampling variance of the discordant counts (continuity-corrected so
    zero discordance stays finite) + seed-to-seed training variance (the
    reference is one draw of a stochastic training run). Prior: the
    UpgradeBench corpus distribution of specialist-score deltas for this
    edge kind. Returns (posterior mean, posterior sd) on the accuracy
    scale."""
    d_hat = (n01 - n10) / n
    se2 = (n01 + n10 + 0.5) / n ** 2 + sigma_seed ** 2
    tau2 = max(prior_sd, 1e-6) ** 2
    w = 1.0 / se2 + 1.0 / tau2
    mu = (d_hat / se2 + prior_mu / tau2) / w
    return mu, (1.0 / w) ** 0.5


def gain_probabilities(mu: float, sd: float, eps: float) -> dict:
    """P(gain > eps), P(gain < -eps), P(|gain| <= eps) under N(mu, sd)."""
    p_up = 1.0 - normal_cdf((eps - mu) / sd)
    p_down = normal_cdf((-eps - mu) / sd)
    return {"p_gain_above_eps": round(p_up, 3),
            "p_loss_below_neg_eps": round(p_down, 3),
            "p_within_band": round(1.0 - p_up - p_down, 3)}


def sign_test_p(n01: int, n10: int) -> float:
    """Exact two-sided binomial sign test on the discordant pairs (the
    McNemar exact test, taking counts directly)."""
    n = n01 + n10
    if n == 0:
        return 1.0
    tail = sum(comb(n, j) for j in range(0, min(n01, n10) + 1))
    p = 2 * tail * Fraction(1, 2 ** n)
    return min(1.0, float(p))


# ---------------- Power layer (theory-review fix #2) ----------------

def discordant_rate(a: Dict[str, bool], b: Dict[str, bool]) -> float:
    """Fraction of common items on which the two systems disagree."""
    ids = sorted(set(a) & set(b))
    if not ids:
        return 0.0
    return sum(1 for i in ids if a[i] != b[i]) / len(ids)


def mde(pi: float, n: int, alpha_z: float = 1.96, power_z: float = 0.84
        ) -> float:
    """Minimal detectable accuracy difference (paired, two-sided alpha=.05,
    power 80%): sqrt((z_a+z_b)^2 * pi / n). pi = discordant rate."""
    if n <= 0:
        return 1.0
    return ((alpha_z + power_z) ** 2 * pi / n) ** 0.5


def required_n(pi: float, target_diff: float, alpha_z: float = 1.96,
               power_z: float = 0.84) -> int:
    """Gate-set size needed to resolve target_diff at 80% power."""
    if target_diff <= 0:
        return 0
    return int(round((alpha_z + power_z) ** 2 * pi / target_diff ** 2))


# -------- Confidence layer (theory-review fix #4: proper scoring) --------

def _load_lp(records_path: str) -> List[dict]:
    return [json.loads(l) for l in open(records_path, encoding="utf-8")]


def paired_nll_ci(a_path: str, b_path: str, n_resamples: int = 10000,
                  seed: int = 42) -> Tuple[float, float, float]:
    """Mean NLL difference (a - b; negative = a better) with 95% paired
    bootstrap CI, over common ids. NLL is label-set-normalized negative
    log-likelihood of gold (proper scoring rule: more power than 0/1)."""
    A = {str(r["id"]): r["nll"] for r in _load_lp(a_path)}
    B = {str(r["id"]): r["nll"] for r in _load_lp(b_path)}
    ids = sorted(set(A) & set(B))
    diffs = [A[i] - B[i] for i in ids]
    m = len(diffs)
    mean = sum(diffs) / m
    rng = random.Random(seed)
    means = []
    for _ in range(n_resamples):
        t = 0.0
        for _ in range(m):
            t += diffs[rng.randrange(m)]
        means.append(t / m)
    means.sort()
    return (mean, means[int(0.025 * n_resamples)],
            means[int(0.975 * n_resamples) - 1])


def ece(records_path: str, n_bins: int = 10) -> float:
    """Expected calibration error (Guo et al. 2017) from per-item
    (conf, correct)."""
    rows = _load_lp(records_path)
    bins = [[] for _ in range(n_bins)]
    for r in rows:
        k = min(n_bins - 1, int(r["conf"] * n_bins))
        bins[k].append(r)
    total = len(rows)
    e = 0.0
    for bucket in bins:
        if not bucket:
            continue
        acc = sum(1 for r in bucket if r["correct"]) / len(bucket)
        conf = sum(r["conf"] for r in bucket) / len(bucket)
        e += len(bucket) / total * abs(acc - conf)
    return round(e, 4)


def aurc(records_path: str) -> float:
    """Area under the risk-coverage curve (selective prediction,
    Geifman & El-Yaniv 2017). Lower is better: risk when deferring
    low-confidence items to a human."""
    rows = sorted(_load_lp(records_path), key=lambda r: -r["conf"])
    n = len(rows)
    errs = 0
    area = 0.0
    for i, r in enumerate(rows, 1):
        errs += 0 if r["correct"] else 1
        area += errs / i
    return round(area / n, 4)
