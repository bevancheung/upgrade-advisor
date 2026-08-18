# -*- coding: utf-8 -*-
"""Generic evaluation with per-example records (GPU extra: pip install .[gpu]).

Two task kinds:
  classification: gold label match after normalization (optionally lenient)
  structured:     exact match after whitespace/number normalization; plug in
                  your own comparator for execution-based metrics.

Data format (JSONL): {"id": ..., "user": ..., "assistant": gold,
                      optional "system": ...}  or {"text":..., "label":...}

Lessons from the paper are baked in:
  - prompts and completions are tokenized separately in training (train.py),
    and evaluation prompts match that format token-for-token;
  - eos_token_id is passed explicitly (base models may lack a generation
    config and will otherwise run past the answer);
  - plain-format outputs are cut at the first newline;
  - long-prompt batches shrink automatically (MHA KV-cache spill guard).
"""
import json
import os
import re
import time


def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f]


def norm_label(s):
    s = re.sub(r"<think>.*?</think>", "", s, flags=re.S).strip().strip("\"'`.")
    s = s.splitlines()[0].strip() if s else ""
    return s.lower().replace(" ", "_").replace("-", "_")


def norm_structured(s):
    s = re.sub(r"<think>.*?</think>", "", s, flags=re.S).strip().strip("`")
    s = s.splitlines()[0].strip() if s else ""
    return re.sub(r"\s+", " ", s)


def build_prompt(tok, item, system_default, plain):
    system = item.get("system") or system_default
    user = item.get("user") or item.get("text")
    if plain:
        return system + "\n\n" + user + "\nAnswer: "
    msgs = [{"role": "system", "content": system},
            {"role": "user", "content": user}]
    try:
        return tok.apply_chat_template(msgs, tokenize=False,
                                       add_generation_prompt=True,
                                       enable_thinking=False)
    except TypeError:
        return tok.apply_chat_template(msgs, tokenize=False,
                                       add_generation_prompt=True)


def evaluate(model_path, data_path, out_records, task_kind="classification",
             adapter=None, system_default="You are a task specialist. "
             "Answer with the required output only.", plain=False, bs=16,
             max_new=32, limit=0, comparator=None, quant4bit=True):
    import torch
    from transformers import (AutoModelForCausalLM, AutoTokenizer,
                              BitsAndBytesConfig)

    items = load_jsonl(data_path)
    if limit:
        items = items[:limit]
    tok = AutoTokenizer.from_pretrained(model_path, padding_side="left")
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    kw = {}
    if quant4bit:
        kw["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True)
    try:
        model = AutoModelForCausalLM.from_pretrained(
            model_path, dtype=torch.bfloat16, device_map={"": 0},
            attn_implementation="sdpa", **kw)
    except TypeError:
        model = AutoModelForCausalLM.from_pretrained(
            model_path, torch_dtype=torch.bfloat16, device_map={"": 0},
            attn_implementation="sdpa", **kw)
    if adapter:
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, adapter)
    model.eval()

    prompts = [build_prompt(tok, it, system_default, plain) for it in items]
    if prompts and max(len(p) for p in prompts) > 2500 and bs > 8:
        bs = 8  # KV-cache spill guard (paper appendix, operational note 1)

    norm = norm_label if task_kind == "classification" else norm_structured
    cmp_fn = comparator or (lambda pred, gold: norm(pred) == norm(gold))
    recs, correct, t0 = [], 0, time.time()
    for i in range(0, len(prompts), bs):
        enc = tok(prompts[i:i + bs], return_tensors="pt", padding=True,
                  add_special_tokens=False).to(model.device)
        with torch.no_grad():
            out = model.generate(**enc, max_new_tokens=max_new,
                                 do_sample=False,
                                 pad_token_id=tok.pad_token_id,
                                 eos_token_id=tok.eos_token_id)
        for j, g in enumerate(out[:, enc["input_ids"].shape[1]:]):
            raw = tok.decode(g, skip_special_tokens=True)
            if plain:
                raw = raw.strip().splitlines()[0] if raw.strip() else raw
            it = items[i + j]
            gold = it.get("assistant") or it.get("label")
            ok = bool(cmp_fn(raw, gold))
            correct += ok
            recs.append({"id": it["id"], "gold": gold,
                         "pred": raw.strip()[:300], "correct": ok})
        print(f"{min(i+bs, len(items))}/{len(items)} "
              f"acc={correct/min(i+bs, len(items)):.4f}", flush=True)

    os.makedirs(os.path.dirname(out_records) or ".", exist_ok=True)
    with open(out_records, "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    summary = {"model": model_path, "adapter": adapter, "n": len(items),
               "accuracy": round(correct / len(items), 4),
               "minutes": round((time.time() - t0) / 60, 1)}
    with open(out_records.replace(".jsonl", ".summary.json"), "w",
              encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    return summary
