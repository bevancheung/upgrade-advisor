# -*- coding: utf-8 -*-
"""Behavioral regression gate: negative/positive flips between the serving
system and a candidate, from per-example records. Averages hide regressions;
the paper found quality-neutral retraining flips 1-5% of previously-correct
items and a bad copy flips 50%.
"""
import hashlib
import json
from dataclasses import dataclass
from typing import Dict


def load_records(path: str) -> Dict[str, bool]:
    out = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            out[str(r["id"])] = bool(r["correct"])
    return out


def load_records_gold(path: str) -> Dict[str, tuple]:
    """id -> (correct, gold) for severity-weighted flips."""
    out = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            out[str(r["id"])] = (bool(r["correct"]), str(r.get("gold", "")))
    return out


def weighted_flips(serving_path: str, candidate_path: str,
                   class_weights: dict, half: str = "all") -> "FlipReport":
    """Severity-weighted negative/positive flips: each item weighted by
    its gold-label weight (default 1.0). NFR budgets then reflect that
    breaking a high-severity class costs more (cost-sensitive evaluation)."""
    A = load_records_gold(serving_path)
    B = load_records_gold(candidate_path)
    ids = sorted(set(A) & set(B))
    if half == "gate":
        ids = [i for i in ids if gate_half(i)]
    elif half == "report":
        ids = [i for i in ids if not gate_half(i)]
    w = lambda i: float(class_weights.get(A[i][1], 1.0))
    tot = sum(w(i) for i in ids)
    nf = sum(w(i) for i in ids if A[i][0] and not B[i][0])
    pf = sum(w(i) for i in ids if not A[i][0] and B[i][0])
    return FlipReport(n=len(ids), negative_flips=round(nf, 2),
                      positive_flips=round(pf, 2),
                      nfr=nf / tot if tot else 0.0,
                      pfr=pf / tot if tot else 0.0,
                      net_pp=((pf - nf) / tot * 100) if tot else 0.0)


def gate_half(item_id: str) -> bool:
    """True -> gate half; False -> reporting half. Stable id hash, so gates
    and reported scores never share items (paper §6, split-half replay)."""
    return int(hashlib.md5(str(item_id).encode()).hexdigest(), 16) % 2 == 0


@dataclass
class FlipReport:
    n: int
    negative_flips: int
    positive_flips: int
    nfr: float
    pfr: float
    net_pp: float

    def as_dict(self):
        return dict(n=self.n, negative_flips=self.negative_flips,
                    positive_flips=self.positive_flips,
                    nfr=round(self.nfr, 4), pfr=round(self.pfr, 4),
                    net_pp=round(self.net_pp, 2))


def flips(serving: Dict[str, bool], candidate: Dict[str, bool],
          half: str = "all") -> FlipReport:
    ids = sorted(set(serving) & set(candidate))
    if half == "gate":
        ids = [i for i in ids if gate_half(i)]
    elif half == "report":
        ids = [i for i in ids if not gate_half(i)]
    nf = sum(1 for i in ids if serving[i] and not candidate[i])
    pf = sum(1 for i in ids if not serving[i] and candidate[i])
    n = len(ids)
    return FlipReport(n=n, negative_flips=nf, positive_flips=pf,
                      nfr=nf / n if n else 0.0, pfr=pf / n if n else 0.0,
                      net_pp=((pf - nf) / n * 100) if n else 0.0)


def passes(report: FlipReport, budget: float) -> bool:
    return report.nfr <= budget
