# -*- coding: utf-8 -*-
"""Robustness probe (theory-review fix #5): rule-based perturbations of the
test inputs with gold labels unchanged. Newer bases often differ most under
distribution shift (effective robustness, Taori et al. 2020); a clean test
set cannot see that. Deterministic (seeded), zero new annotation.

Perturbation menu (applied per item, seeded by item id):
  typo     : swap two adjacent chars in one word; drop one char
  casing   : random word-level upper/lower flips
  filler   : insert spoken fillers ("um", "uh", "please", "so")
  punct    : strip punctuation, collapse whitespace
"""
import json
import os
import random
import re

FILLERS = ["um", "uh", "please", "so", "like", "hey"]


def _typo(text, rng):
    words = text.split()
    cand = [i for i, w in enumerate(words) if len(w) >= 4]
    if not cand:
        return text
    i = rng.choice(cand)
    w = list(words[i])
    j = rng.randrange(len(w) - 1)
    if rng.random() < 0.5:
        w[j], w[j + 1] = w[j + 1], w[j]
    else:
        del w[j]
    words[i] = "".join(w)
    return " ".join(words)


def _casing(text, rng):
    return " ".join(w.upper() if rng.random() < 0.25 else w.lower()
                    for w in text.split())


def _filler(text, rng):
    words = text.split()
    for _ in range(1 + rng.randrange(2)):
        words.insert(rng.randrange(len(words) + 1), rng.choice(FILLERS))
    return " ".join(words)


def _punct(text, rng):
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", text)).strip()


MENU = [_typo, _casing, _filler, _punct]


def perturb_file(src_path: str, out_path: str, seed: int = 42) -> dict:
    """Write a perturbed copy of a jsonl eval file (text/user field mutated,
    gold unchanged). Each item gets one perturbation, chosen round-robin so
    the mix is balanced and reproducible."""
    rows = [json.loads(l) for l in open(src_path, encoding="utf-8")]
    out = []
    for k, r in enumerate(rows):
        rng = random.Random(f"{seed}:{r.get('id', k)}")
        fn = MENU[k % len(MENU)]
        r = dict(r)
        field = "user" if "user" in r else "text"
        r[field] = fn(r[field], rng)
        r["perturbation"] = fn.__name__.lstrip("_")
        out.append(r)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return {"n": len(out), "out": out_path,
            "menu": [fn.__name__.lstrip("_") for fn in MENU]}
