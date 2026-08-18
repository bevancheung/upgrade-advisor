# -*- coding: utf-8 -*-
"""Base-pair portability probe (GPU extra): one forward pass per prompt on
each checkpoint -> layer-wise linear CKA, next-token top-1 agreement, JSD.
CKA rank-correlated with mean R(Copy) at Spearman 0.74 over the paper's
eight pairs (n=8: exploratory signal, not a decision rule -- keep the
regression gate).

Usage:
    from upgrade_advisor.probe import probe_pair
    r = probe_pair("Qwen/Qwen2.5-7B-Instruct", "Qwen/Qwen3-8B",
                   prompts=[...])   # 128-512 task prompts
"""
import json
import torch
from transformers import (AutoModelForCausalLM, AutoTokenizer,
                          BitsAndBytesConfig)

def load(path):
    tok = AutoTokenizer.from_pretrained(path, padding_side="left")
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                             bnb_4bit_compute_dtype=torch.bfloat16,
                             bnb_4bit_use_double_quant=True)
    try:
        m = AutoModelForCausalLM.from_pretrained(
            path, quantization_config=bnb, dtype=torch.bfloat16,
            device_map={"": 0}, attn_implementation="sdpa")
    except TypeError:
        m = AutoModelForCausalLM.from_pretrained(
            path, quantization_config=bnb, torch_dtype=torch.bfloat16,
            device_map={"": 0}, attn_implementation="sdpa")
    m.eval()
    return tok, m


def last_token_states(model, tok, prompts, bs=8):
    """返回 [层, 样本, 维度] 的最后位置隐状态（float32, CPU）与 next-token logits。"""
    hs_all, lg_all = None, []
    for i in range(0, len(prompts), bs):
        enc = tok(prompts[i:i + bs], return_tensors="pt", padding=True,
                  truncation=True, max_length=1024,
                  add_special_tokens=False).to(model.device)
        with torch.no_grad():
            o = model(**enc, output_hidden_states=True)
        hs = torch.stack([h[:, -1, :].float().cpu() for h in o.hidden_states])
        hs_all = hs if hs_all is None else torch.cat([hs_all, hs], dim=1)
        lg_all.append(o.logits[:, -1, :].float().cpu())
        del o
        torch.cuda.empty_cache()
    return hs_all, torch.cat(lg_all, 0)


def cka(x, y):
    """线性 CKA（样本 × 维度，维度可不同）。"""
    x = x - x.mean(0, keepdim=True)
    y = y - y.mean(0, keepdim=True)
    xy = (x.T @ y).norm("fro") ** 2
    xx = (x.T @ x).norm("fro")
    yy = (y.T @ y).norm("fro")
    return float(xy / (xx * yy + 1e-12))


def probe_pair(source, target, prompts, bs=8):
    """Return dict(cka_mean, cka_last, top1_agree, jsd) for one base pair."""
    import torch
    tok_s, ms = load(source)
    hs_s, lg_s = last_token_states(ms, tok_s, prompts, bs=bs)
    del ms
    torch.cuda.empty_cache()
    tok_t, mt = load(target)
    hs_t, lg_t = last_token_states(mt, tok_t, prompts, bs=bs)
    del mt
    torch.cuda.empty_cache()
    L = min(hs_s.shape[0], hs_t.shape[0])
    idx = [round(k * (L - 1) / 8) for k in range(9)]
    ckas = [cka(hs_s[i], hs_t[i]) for i in idx]
    V = min(lg_s.shape[1], lg_t.shape[1])
    ps = torch.softmax(lg_s[:, :V], -1)
    pt = torch.softmax(lg_t[:, :V], -1)
    m_ = 0.5 * (ps + pt)
    kl = lambda a, b: (a * (a.clamp_min(1e-12).log()
                            - b.clamp_min(1e-12).log())).sum(-1)
    return dict(
        cka_mean=round(sum(ckas) / len(ckas), 4),
        cka_last=round(ckas[-1], 4),
        top1_agree=round(float((lg_s[:, :V].argmax(-1)
                                == lg_t[:, :V].argmax(-1)).float().mean()), 4),
        jsd=round(float((0.5 * kl(ps, m_) + 0.5 * kl(pt, m_)).mean()), 4),
        n_prompts=len(prompts))
