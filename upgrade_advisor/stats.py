# -*- coding: utf-8 -*-
"""Statistics layer (Playbook Phase 0: bootstrap CIs, paired McNemar).

Ported from the UpgradeBench harness: exact McNemar on discordant pairs,
percentile bootstrap on per-example records. Pure python + stdlib.
"""
import random
from fractions import Fraction
from math import comb
from typing import Dict, List, Tuple


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
