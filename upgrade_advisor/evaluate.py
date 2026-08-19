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


def build_prompt(tok, item, system_default, plain, shots=None):
    """shots: optional few-shot exemplars [{user/text, assistant/label}, ...],
    fixed across all items and models for comparability."""
    system = item.get("system") or system_default
    user = item.get("user") or item.get("text")
    shots = shots or []
    if plain:
        parts = [system, ""]
        for sh in shots:
            parts.append((sh.get("user") or sh.get("text"))
                         + "\nAnswer: " + (sh.get("assistant") or sh.get("label")))
            parts.append("")
        parts.append(user + "\nAnswer: ")
        return "\n".join(parts)
    msgs = [{"role": "system", "content": system}]
    for sh in shots:
        msgs.append({"role": "user", "content": sh.get("user") or sh.get("text")})
        msgs.append({"role": "assistant",
                     "content": sh.get("assistant") or sh.get("label")})
    msgs.append({"role": "user", "content": user})
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
             max_new=32, limit=0, comparator=None, quant4bit=True,
             shots=None):
    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
    import torch
    from transformers import (AutoModelForCausalLM, AutoTokenizer,
                              BitsAndBytesConfig)
    from transformers.utils import logging as hf_logging
    hf_logging.set_verbosity_error()
    hf_logging.disable_progress_bar()

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

    prompts = [build_prompt(tok, it, system_default, plain, shots)
               for it in items]
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


def label_score(model_path, data_path, labels, out_records,
                adapter=None, system_default="You are a task specialist. "
                "Answer with the required output only.", plain=False,
                bs=32, quant4bit=True):
    """Confidence-layer scoring (theory-review fix #4): for each item,
    the total log-probability of every candidate label completion
    (teacher forcing), softmax-normalized over the label set. Emits
    per-item records with pred / correct / conf / nll -- inputs to the
    paired log-loss test, ECE, and risk-coverage AUC. Proper scoring
    rules carry more statistical power than 0/1 accuracy at the same n.
    Classification tasks only."""
    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
    import math

    import torch
    from transformers import (AutoModelForCausalLM, AutoTokenizer,
                              BitsAndBytesConfig)
    from transformers.utils import logging as hf_logging
    hf_logging.set_verbosity_error()

    items = load_jsonl(data_path)
    tok = AutoTokenizer.from_pretrained(model_path, padding_side="right")
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

    # Score label + eos so candidate events are disjoint: a bare prefix
    # label ("insurance" vs "insurance_change") would otherwise absorb the
    # probability mass of every longer continuation and win on sum-logprob.
    lab_ids = {lb: tok(lb, add_special_tokens=False)["input_ids"]
               + [tok.eos_token_id] for lb in labels}
    recs = []
    t0 = time.time()
    for it in items:
        prompt = build_prompt(tok, it, system_default, plain)
        p_ids = tok(prompt, add_special_tokens=False)["input_ids"]
        # 一个 batch 内给同一条目打所有候选标签
        seqs = [p_ids + lab_ids[lb] for lb in labels]
        maxlen = max(len(x) for x in seqs)
        inp = torch.full((len(seqs), maxlen), tok.pad_token_id,
                         dtype=torch.long)
        att = torch.zeros((len(seqs), maxlen), dtype=torch.long)
        for r_i, x in enumerate(seqs):
            inp[r_i, :len(x)] = torch.tensor(x)
            att[r_i, :len(x)] = 1
        inp, att = inp.to(model.device), att.to(model.device)
        scores = []
        with torch.no_grad():
            for b0 in range(0, len(seqs), bs):
                out = model(input_ids=inp[b0:b0 + bs],
                            attention_mask=att[b0:b0 + bs])
                logp = torch.log_softmax(out.logits.float(), dim=-1)
                for r_i in range(out.logits.shape[0]):
                    li = lab_ids[labels[b0 + r_i]]
                    start = len(p_ids)
                    tot = 0.0
                    for k, tid in enumerate(li):
                        tot += logp[r_i, start + k - 1, tid].item()
                    scores.append(tot)
        mx = max(scores)
        exps = [math.exp(x - mx) for x in scores]
        z = sum(exps)
        probs = [e / z for e in exps]
        best = max(range(len(labels)), key=lambda i: probs[i])
        gold = (it.get("assistant") or it.get("label"))
        gold_i = labels.index(gold) if gold in labels else None
        nll = (-math.log(max(probs[gold_i], 1e-12))
               if gold_i is not None else float("inf"))
        recs.append({"id": it["id"], "gold": gold, "pred": labels[best],
                     "correct": labels[best] == gold,
                     "conf": round(probs[best], 5), "nll": round(nll, 5)})
    os.makedirs(os.path.dirname(out_records) or ".", exist_ok=True)
    with open(out_records, "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    summary = {"model": model_path, "adapter": adapter, "n": len(recs),
               "accuracy": round(sum(r["correct"] for r in recs) / len(recs), 4),
               "mean_nll": round(sum(r["nll"] for r in recs) / len(recs), 4),
               "minutes": round((time.time() - t0) / 60, 1)}
    with open(out_records.replace(".jsonl", ".summary.json"), "w",
              encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    return summary
