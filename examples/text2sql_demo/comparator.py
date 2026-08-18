# -*- coding: utf-8 -*-
"""Custom comparator for text-to-SQL: normalized string match by default;
swap in execution-based comparison against your own database for the real
metric (the paper used SQLite result-multiset equality with a 10s timeout).
"""
import re


def _norm(s):
    s = re.sub(r"<think>.*?</think>", "", s, flags=re.S).strip().strip("`")
    s = s.splitlines()[0].strip() if s else ""
    s = re.sub(r"\s+", " ", s).rstrip(";").lower()
    return s


def compare(pred, gold):
    return _norm(pred) == _norm(gold)
