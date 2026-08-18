# -*- coding: utf-8 -*-
"""Fixed-recipe QLoRA training (GPU extra). One recipe so references stay
comparable across generations: r=16, alpha=32, lr 2e-4 cosine, NF4 double
quant, completion-only loss, seed 42.

Two modes:
  retrain: train on gold-labeled train.jsonl
  refresh: teacher = your current specialist relabels retained inputs first
           (annotation-free; saves labels, not necessarily compute).

Prompt and completion are tokenized SEPARATELY and concatenated -- with plain
prompts, BPE merges a trailing-space boundary into the answer's first token
and silently masks it from the loss (specialists learn answers minus their
first token; the paper's wave-4 incident). Keep this invariant.
"""
import json
import os
import time


def _build_example(tok, item, max_len, system_default, plain):
    system = item.get("system") or system_default
    user = item.get("user") or item.get("text")
    assistant = item.get("assistant") or item.get("label")
    if plain:
        prompt = system + "\n\n" + user + "\nAnswer: "
    else:
        msgs = [{"role": "system", "content": system},
                {"role": "user", "content": user}]
        try:
            prompt = tok.apply_chat_template(msgs, tokenize=False,
                                             add_generation_prompt=True,
                                             enable_thinking=False)
        except TypeError:
            prompt = tok.apply_chat_template(msgs, tokenize=False,
                                             add_generation_prompt=True)
    p_ids = tok(prompt, add_special_tokens=False)["input_ids"]
    a_ids = tok(assistant + tok.eos_token, add_special_tokens=False)["input_ids"]
    f_ids = (p_ids + a_ids)[:max_len]
    labels = [-100] * min(len(p_ids), len(f_ids)) + f_ids[len(p_ids):]
    return {"input_ids": f_ids, "labels": labels}


def train(base_model, train_path, out_dir, system_default, plain=False,
          max_len=256, epochs=3, lr=2e-4, batch=16, grad_accum=1,
          lora_r=16, seed=42):
    import torch
    from torch.utils.data import Dataset
    from transformers import (AutoModelForCausalLM, AutoTokenizer,
                              BitsAndBytesConfig, Trainer, TrainingArguments)
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

    tok = AutoTokenizer.from_pretrained(base_model)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token

    class DS(Dataset):
        def __init__(self, path):
            self.items = []
            with open(path, encoding="utf-8") as f:
                for line in f:
                    ex = _build_example(tok, json.loads(line), max_len,
                                        system_default, plain)
                    if any(x != -100 for x in ex["labels"]):
                        self.items.append(ex)
        def __len__(self): return len(self.items)
        def __getitem__(self, i): return self.items[i]

    def collate(batch_items):
        n = max(len(b["input_ids"]) for b in batch_items)
        pad = tok.pad_token_id
        return {
            "input_ids": torch.tensor(
                [b["input_ids"] + [pad] * (n - len(b["input_ids"]))
                 for b in batch_items]),
            "labels": torch.tensor(
                [b["labels"] + [-100] * (n - len(b["labels"]))
                 for b in batch_items]),
            "attention_mask": torch.tensor(
                [[1] * len(b["input_ids"]) + [0] * (n - len(b["input_ids"]))
                 for b in batch_items])}

    bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                             bnb_4bit_compute_dtype=torch.bfloat16,
                             bnb_4bit_use_double_quant=True)
    try:
        model = AutoModelForCausalLM.from_pretrained(
            base_model, quantization_config=bnb, dtype=torch.bfloat16,
            device_map={"": 0}, attn_implementation="sdpa")
    except TypeError:
        model = AutoModelForCausalLM.from_pretrained(
            base_model, quantization_config=bnb, torch_dtype=torch.bfloat16,
            device_map={"": 0}, attn_implementation="sdpa")
    model.config.use_cache = False
    model = prepare_model_for_kbit_training(model)
    model = get_peft_model(model, LoraConfig(
        r=lora_r, lora_alpha=2 * lora_r, lora_dropout=0.05, bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"]))

    t0 = time.time()
    Trainer(model=model, args=TrainingArguments(
        output_dir=os.path.join(out_dir, "ckpt"), seed=seed,
        num_train_epochs=epochs, learning_rate=lr,
        per_device_train_batch_size=batch // grad_accum if grad_accum > 1 else batch,
        gradient_accumulation_steps=grad_accum,
        lr_scheduler_type="cosine", warmup_ratio=0.03, logging_steps=50,
        save_strategy="no", bf16=True, report_to=[],
        gradient_checkpointing=True),
        train_dataset=DS(train_path), data_collator=collate).train()
    model.save_pretrained(out_dir)
    tok.save_pretrained(out_dir)
    log = {"base_model": base_model,
           "recipe": {"r": lora_r, "alpha": 2 * lora_r, "lr": lr,
                      "epochs": epochs, "bs": batch, "max_len": max_len,
                      "quant": "nf4-double", "seed": seed},
           "wall_clock_min": round((time.time() - t0) / 60, 2)}
    with open(os.path.join(out_dir, "train_log.json"), "w",
              encoding="utf-8") as f:
        json.dump(log, f, indent=2)
    return log


def relabel(base_model, adapter, inputs_path, out_path, system_default,
            plain=False, bs=16, max_new=32):
    """Teacher relabeling for REFRESH: current specialist labels retained
    inputs; output is a training file for `train` on the new base."""
    from .evaluate import build_prompt
    import torch
    from transformers import (AutoModelForCausalLM, AutoTokenizer,
                              BitsAndBytesConfig)
    from peft import PeftModel

    items = [json.loads(l) for l in open(inputs_path, encoding="utf-8")]
    tok = AutoTokenizer.from_pretrained(base_model, padding_side="left")
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                             bnb_4bit_compute_dtype=torch.bfloat16,
                             bnb_4bit_use_double_quant=True)
    try:
        model = AutoModelForCausalLM.from_pretrained(
            base_model, quantization_config=bnb, dtype=torch.bfloat16,
            device_map={"": 0}, attn_implementation="sdpa")
    except TypeError:
        model = AutoModelForCausalLM.from_pretrained(
            base_model, quantization_config=bnb, torch_dtype=torch.bfloat16,
            device_map={"": 0}, attn_implementation="sdpa")
    model = PeftModel.from_pretrained(model, adapter)
    model.eval()
    prompts = [build_prompt(tok, it, system_default, plain) for it in items]
    outs = []
    for i in range(0, len(prompts), bs):
        enc = tok(prompts[i:i + bs], return_tensors="pt", padding=True,
                  add_special_tokens=False).to(model.device)
        with torch.no_grad():
            out = model.generate(**enc, max_new_tokens=max_new,
                                 do_sample=False,
                                 pad_token_id=tok.pad_token_id,
                                 eos_token_id=tok.eos_token_id)
        for g in out[:, enc["input_ids"].shape[1]:]:
            raw = tok.decode(g, skip_special_tokens=True)
            if plain:
                raw = raw.strip().splitlines()[0] if raw.strip() else raw
            outs.append(raw.strip())
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for it, y in zip(items, outs):
            row = {"id": it["id"],
                   "user": it.get("user") or it.get("text"),
                   "assistant": y}
            if it.get("system"):
                row["system"] = it["system"]
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return {"n": len(items), "out": out_path}
