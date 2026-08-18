# -*- coding: utf-8 -*-
"""Episode ledger (Playbook Phase 0-4 and Phase 3-2).

Append-only JSONL at <workdir>/ledger.jsonl. Each completed measurement or
recommendation appends one entry, so over releases the task accumulates:
floors, references, chosen actions, and costs. From two or more episodes
with (floor, reference) pairs the task's coupling beta = dReference/dFloor
is estimated and used to project the reference score for a new target
before anyone pays for retraining.
"""
import json
import os
import time
from typing import List, Optional, Tuple

FILENAME = "ledger.jsonl"


def _path(workdir: str) -> str:
    return os.path.join(workdir, FILENAME)


def append(workdir: str, entry: dict) -> None:
    os.makedirs(workdir, exist_ok=True)
    entry = dict(entry)
    entry.setdefault("ts", time.strftime("%Y-%m-%d %H:%M:%S"))
    with open(_path(workdir), "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def history(workdir: str) -> List[dict]:
    p = _path(workdir)
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def _floor_zs(e: dict):
    """beta uses the zero-shot floor consistently across episodes; falls back
    to legacy single-field entries."""
    return e.get("floor_zs", e.get("floor"))


def _episodes_with_pairs(entries: List[dict]) -> List[dict]:
    """Latest entry per target that carries both a zs floor and a measured
    reference."""
    by_target = {}
    for e in entries:
        if _floor_zs(e) is not None and e.get("reference") is not None:
            by_target[e["target"]] = e
    return sorted(by_target.values(), key=lambda e: e["ts"])


def beta_estimate(entries: List[dict]) -> Optional[Tuple[float, dict, dict]]:
    """(beta, older_episode, newer_episode) from the two most recent
    complete episodes, or None. Denominator-gated: |dFloor| must exceed
    2pp, mirroring the paper's elasticity stability rule."""
    eps = _episodes_with_pairs(entries)
    if len(eps) < 2:
        return None
    old, new = eps[-2], eps[-1]
    d_floor = _floor_zs(new) - _floor_zs(old)
    if abs(d_floor) < 0.02:
        return None
    beta = (new["reference"] - old["reference"]) / d_floor
    return beta, old, new


def project_reference(entries: List[dict], new_floor: float
                      ) -> Optional[dict]:
    """Project the reference score for a new target from beta and the most
    recent measured episode. Returns evidence dict or None."""
    est = beta_estimate(entries)
    if est is None:
        return None
    beta, old, new = est
    proj = new["reference"] + beta * (new_floor - _floor_zs(new))
    return {"projected_reference": max(0.0, min(1.0, proj)),
            "beta": round(beta, 3),
            "from_episodes": [old["target"], new["target"]],
            "note": ("beta-projected from ledger history; train the real "
                     "reference before committing compute-heavy actions")}


def costs_summary(entries: List[dict]) -> dict:
    tr = sum(e.get("train_minutes") or 0 for e in entries)
    ev = sum(e.get("eval_minutes") or 0 for e in entries)
    return {"episodes": len({e.get("target") for e in entries if e.get("target")}),
            "train_gpu_minutes": round(tr, 1),
            "eval_gpu_minutes": round(ev, 1)}
