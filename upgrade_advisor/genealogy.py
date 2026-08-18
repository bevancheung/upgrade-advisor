# -*- coding: utf-8 -*-
"""Release-genealogy lookup: is (source, target) a documented continuation,
and how far? Falls back to an explicit questionnaire for unknown pairs --
never to shape compatibility, which the paper showed is the wrong gate.
"""
import os
from dataclasses import dataclass
from typing import Optional

import yaml

REGISTRY = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "registry", "release_graph.yaml")


@dataclass
class GenealogyVerdict:
    documented_continuation: bool
    continuation_tokens: Optional[float]
    edge_type: str            # continuation|fresh_pretraining|anneal|soup|unknown
    confidence: str           # verified|inferred|user_supplied|unknown
    note: str = ""


def _tok(v):
    """YAML 的 2.0e10（无+号）会被解析成字符串；统一转 float。"""
    return None if v is None else float(v)


def _load(path: str = REGISTRY) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def lookup(source: str, target: str, registry_path: str = REGISTRY
           ) -> GenealogyVerdict:
    """Direct edge lookup; multi-hop paths are resolved only if every hop is
    a continuation (distances sum). Any fresh/soup hop breaks the license."""
    g = _load(registry_path)
    edges = g.get("edges", [])
    def norm(x):
        # allow local paths: match registry ids by basename as fallback
        return x.replace("\\", "/").rstrip("/").split("/")[-1].lower()

    def eq(a, b):
        return a == b or norm(a) == norm(b)

    direct = [e for e in edges
              if eq(e["source"], source) and eq(e["target"], target)]
    if direct:
        e = direct[0]
        return GenealogyVerdict(
            documented_continuation=(e["type"] == "continuation"),
            continuation_tokens=_tok(e.get("continuation_tokens")),
            edge_type=e["type"], confidence=e.get("confidence", "inferred"),
            note=e.get("note", ""))
    # single-intermediate path search (covers e.g. 237k -> soup via anneal)
    by_src = {}
    for e in edges:
        by_src.setdefault(e["source"], []).append(e)
    src_key = next((k for k in by_src if eq(k, source)), source)
    for e1 in by_src.get(src_key, []):
        for e2 in by_src.get(e1["target"], []):
            if not eq(e2["target"], target):
                continue
            types = {e1["type"], e2["type"]}
            if types == {"continuation"}:
                return GenealogyVerdict(
                    True,
                    (_tok(e1.get("continuation_tokens")) or 0)
                    + (_tok(e2.get("continuation_tokens")) or 0),
                    "continuation", "verified", "two-hop continuation path")
            return GenealogyVerdict(
                False, None, "+".join(sorted(types)), "verified",
                "path exists but crosses a non-continuation edge "
                "(anneal/soup/fresh): copying is not licensed")
    return GenealogyVerdict(False, None, "unknown", "unknown",
                            "pair not in registry")


def questionnaire() -> GenealogyVerdict:
    """Interactive fallback for pairs outside the registry. Two questions,
    straight from the paper's criterion."""
    print("This pair is not in the release-genealogy registry.")
    print("Q1. Does the provider's documentation state the target was")
    print("    trained by CONTINUING from your exact source weights")
    print("    (not retrained, not merged/souped)? [y/N] ", end="")
    a1 = input().strip().lower() == "y"
    if not a1:
        return GenealogyVerdict(False, None, "unknown", "user_supplied",
                                "no documented descent -- treat as fresh run")
    print("Q2. Roughly how many tokens of continued pretraining separate")
    print("    them? Enter a number like 20e9, or 'unknown': ", end="")
    a2 = input().strip().lower()
    try:
        tok = float(a2)
    except ValueError:
        return GenealogyVerdict(True, None, "continuation", "user_supplied",
                                "distance unknown -- copy not licensed "
                                "(paper: retention is a distance budget)")
    return GenealogyVerdict(True, tok, "continuation", "user_supplied", "")
