# -*- coding: utf-8 -*-
"""Fetch Banking77 test split to data/test.jsonl (public, CC-BY-4.0)."""
import json, os, urllib.request, csv, io
URL = ("https://raw.githubusercontent.com/PolyAI-LDN/task-specific-datasets/"
       "master/banking_data/test.csv")
os.makedirs("data", exist_ok=True)
rows = list(csv.DictReader(io.StringIO(
    urllib.request.urlopen(URL).read().decode("utf-8"))))
with open("data/test.jsonl", "w", encoding="utf-8") as f:
    for i, r in enumerate(rows):
        f.write(json.dumps({"id": f"te-{i:05d}", "text": r["text"],
                            "label": r["category"]}, ensure_ascii=False) + "\n")
print(f"wrote data/test.jsonl ({len(rows)} items)")
