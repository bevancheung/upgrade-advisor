# -*- coding: utf-8 -*-
"""upgrade-advisor CLI.

  init       write an episode config template
  measure    score floor / specialist / (copy) on your gate+report halves
  recommend  run the validated policy on the measurements -> action + report
  gate       negative-flip regression gate for any candidate vs serving
"""
import argparse
import json
import os
import sys

import re

import yaml

import hashlib

from . import flips as F
from . import ledger as L
from . import stats as S
from . import genealogy as G
from . import policy as P
from .report import render_report

TEMPLATE = """\
# upgrade-advisor episode config
task_name: my_task
task_kind: classification        # classification | structured
test_set: data/test.jsonl        # gold-labeled, fixed split
train_set: data/train.jsonl      # used by `retrain`/`refresh`
val_set: null                    # optional; gates use test gate-half if null
system_prompt: "You are a task specialist. Answer with the required output only."
# adoption floor prompt MUST carry the full task instructions a newcomer needs
# (e.g. the complete label inventory) -- the specialist prompt usually does not:
adoption_system_prompt: null
source_base: Qwen/Qwen2.5-7B-Instruct
adapter: adapters/my_task_lora
plain_format: false              # true for base (non-instruct) checkpoints
inputs_retained: true            # unlabeled train inputs kept? (enables REFRESH)
gold_labels_retained: true
flip_budget: 0.03                # max negative-flip rate vs serving system
# economic epsilon (optional): break-even gain = migration_cost /
# (monthly_requests * amortization_months * cost_per_error)
monthly_requests: null
cost_per_error: null
migration_cost: null
amortization_months: 6
class_weights: {}                # e.g. {report_lost_card: 5.0}
fewshot_k: 5                     # adoption floor also measured few-shot
workdir: runs/my_task
"""


def _wd(cfg, target):
    # sanitize HF ids AND local paths (drive letters would hijack os.path.join)
    safe = re.sub(r"[\\/:]+", "__", target).strip("_")
    return os.path.join(cfg["workdir"], safe)


def _comparator(cfg, config_path):
    """Load optional custom comparator "file.py::func" (relative to config)."""
    spec = cfg.get("comparator")
    if not spec:
        return None
    import importlib.util
    fpath, fn = spec.split("::")
    if not os.path.isabs(fpath):
        fpath = os.path.join(os.path.dirname(os.path.abspath(config_path)),
                             fpath)
    mod_spec = importlib.util.spec_from_file_location("episode_comparator",
                                                      fpath)
    mod = importlib.util.module_from_spec(mod_spec)
    mod_spec.loader.exec_module(mod)
    return getattr(mod, fn)


def _shots(cfg, k):
    """k exemplars stride-sampled across the whole train file (deterministic,
    robust to label-sorted files)."""
    if not k or not cfg.get("train_set"):
        return None
    import json as _json
    with open(cfg["train_set"], encoding="utf-8") as f:
        rows = [_json.loads(line) for line in f if line.strip()]
    if not rows:
        return None
    step = max(1, len(rows) // k)
    out = [rows[i * step] for i in range(min(k, len(rows)))]
    labels = {r.get("assistant") or r.get("label") for r in out}
    if cfg.get("task_kind") == "classification" and len(labels) < min(k, 3):
        print(f"[warn] few-shot exemplars cover only {len(labels)} distinct "
              "labels; consider a shuffled train file")
    return out


def _sum_eval_minutes(wd):
    import glob as _glob
    import json as _json
    tot = 0.0
    for p in _glob.glob(os.path.join(wd, "*.summary.json")):
        tot += _json.load(open(p, encoding="utf-8")).get("minutes") or 0
    return round(tot, 1)


def _train_minutes(wd):
    import glob as _glob
    import json as _json
    tot = 0.0
    for p in _glob.glob(os.path.join(wd, "*", "train_log.json")):
        tot += _json.load(open(p, encoding="utf-8")).get("wall_clock_min") or 0
    return round(tot, 1)


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _manifest_path(config_path):
    return os.path.join(os.path.dirname(os.path.abspath(config_path)),
                        "data_manifest.json")


def _check_manifest(c, config_path, warnings):
    mp = _manifest_path(config_path)
    if not os.path.exists(mp):
        warnings.append("no data_manifest.json -- run `upgrade-advisor "
                        "manifest` once to pin your splits (Phase 0)")
        return
    man = json.load(open(mp, encoding="utf-8"))
    for key in ("test_set", "train_set", "val_set"):
        f = c.get(key)
        if f and f in man and os.path.exists(f) and _sha(f) != man[f]["sha256"]:
            warnings.append(f"{key} changed since it was pinned in "
                            "data_manifest.json -- scores are no longer "
                            "comparable across episodes")


def _cfg(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _score(records_path, half):
    recs = F.load_records(records_path)
    ids = [i for i in recs if F.gate_half(i) == (half == "gate")]
    return sum(recs[i] for i in ids) / len(ids) if ids else 0.0, len(ids)


def cmd_init(args):
    if os.path.exists(args.config):
        sys.exit(f"{args.config} already exists")
    with open(args.config, "w", encoding="utf-8") as f:
        f.write(TEMPLATE)
    print(f"wrote {args.config}; edit paths, then run `upgrade-advisor "
          f"measure {args.config} --target <hf-id>`")


def cmd_measure(args):
    from .evaluate import evaluate  # GPU import deferred
    c = _cfg(args.config)
    wd = _wd(c, args.target)
    os.makedirs(wd, exist_ok=True)
    plain = c.get("plain_format", False)
    common = dict(data_path=c["test_set"], task_kind=c["task_kind"],
                  system_default=c["system_prompt"], plain=plain,
                  comparator=_comparator(c, args.config))
    print("[1/4] serving specialist on source base")
    evaluate(c["source_base"], adapter=c["adapter"],
             out_records=os.path.join(wd, "freeze.jsonl"), **common)
    print("[2/4] target adoption floor (zero-shot, full task instructions)")
    adopt_common = dict(common)
    adopt_common["system_default"] = (c.get("adoption_system_prompt")
                                      or c["system_prompt"])
    evaluate(args.target, adapter=None,
             out_records=os.path.join(wd, "adopt.jsonl"), **adopt_common)
    shots = _shots(c, c.get("fewshot_k", 0))
    if shots:
        print(f"[3/4] adoption floor, {len(shots)}-shot")
        evaluate(args.target, adapter=None, shots=shots,
                 out_records=os.path.join(wd, "adopt_fs.jsonl"),
                 **adopt_common)
    ver = G.lookup(c["source_base"], args.target)
    if ver.documented_continuation and not args.skip_copy:
        print("[4/4] documented continuation: measuring the copied adapter")
        evaluate(args.target, adapter=c["adapter"],
                 out_records=os.path.join(wd, "copy.jsonl"), **common)
    else:
        print("[4/4] copy not licensed by genealogy; skipped "
              f"({ver.edge_type}: {ver.note})")
    if c.get("val_set"):
        print("[val] scoring gate set (val_set) for the serving specialist")
        val_common = dict(common)
        val_common["data_path"] = c["val_set"]
        evaluate(c["source_base"], adapter=c["adapter"],
                 out_records=os.path.join(wd, "freeze_val.jsonl"),
                 **val_common)
        if os.path.exists(os.path.join(wd, "copy.jsonl")):
            evaluate(args.target, adapter=c["adapter"],
                     out_records=os.path.join(wd, "copy_val.jsonl"),
                     **val_common)
    print(f"measurements in {wd}; next: upgrade-advisor recommend "
          f"{args.config} --target {args.target}")


def cmd_recommend(args):
    c = _cfg(args.config)
    wd = _wd(c, args.target)
    ver = G.lookup(c["source_base"], args.target)
    if ver.edge_type == "unknown" and not args.non_interactive:
        ver = G.questionnaire()

    # val 只在"每个参与门控的条件都有 _val 记录"时启用；
    # 否则全部退回测试集门控半，绝不在同一比较里混用两个样本集。
    stems_present = [st for st in ("freeze", "reference", "copy", "refresh")
                     if os.path.exists(os.path.join(wd, st + ".jsonl"))]
    use_val = bool(c.get("val_set")) and all(
        os.path.exists(os.path.join(wd, st + "_val.jsonl"))
        for st in stems_present)

    def gate_score(stem):
        """Gate metrics: full val_set (if complete), else test gate-half."""
        if use_val:
            r = F.load_records(os.path.join(wd, stem + "_val.jsonl"))
            return sum(r.values()) / len(r), len(r)
        return _score(os.path.join(wd, stem + ".jsonl"), "gate")

    fz, n_gate = gate_score("freeze")
    ad_zs, _ = _score(os.path.join(wd, "adopt.jsonl"), "gate")
    ad, ad_fs = ad_zs, None
    fs_p = os.path.join(wd, "adopt_fs.jsonl")
    if os.path.exists(fs_p):
        ad_fs, _ = _score(fs_p, "gate")
        ad = max(ad, ad_fs)
    m = P.Measurements(
        task_kind=c["task_kind"], freeze_score=fz, adopt_floor=ad,
        inputs_retained=c.get("inputs_retained", False),
        gold_labels_retained=c.get("gold_labels_retained", False),
        gate_set_size=n_gate, shape_compatible=True,
        documented_continuation=ver.documented_continuation,
        continuation_tokens=ver.continuation_tokens)
    proj_note = None
    ref_p = os.path.join(wd, "reference.jsonl")
    if os.path.exists(ref_p):
        m.reference_score, _ = gate_score("reference")
        # 池化全部配对证据（review-2）：val 与 test 的每一条配对记录都进
        # 判定；suffix 前缀隔离两个样本集的 id 空间，配对只发生在同集合内。
        pool_f, pool_r = {}, {}
        for suf in ("", "_val"):
            fp2 = os.path.join(wd, f"freeze{suf}.jsonl")
            rp2 = os.path.join(wd, f"reference{suf}.jsonl")
            if os.path.exists(fp2) and os.path.exists(rp2):
                for i, v in F.load_records(fp2).items():
                    pool_f[f"{suf}:{i}"] = v
                for i, v in F.load_records(rp2).items():
                    pool_r[f"{suf}:{i}"] = v
        m.paired_n, m.paired_n01, m.paired_n10 = S.paired_counts(pool_f,
                                                                 pool_r)
        common = set(pool_f) & set(pool_r)
        m.paired_freeze_errors = sum(1 for i in common if not pool_f[i])
    elif args.reference_estimate is not None:
        m.reference_score = args.reference_estimate
        m.reference_is_estimate = True
    else:
        proj = L.project_reference(L.history(c["workdir"]), ad_zs)
        if proj:
            m.reference_score = proj["projected_reference"]
            m.reference_is_estimate = True
            proj_note = proj
    cp_p = os.path.join(wd, "copy.jsonl")
    if os.path.exists(cp_p):
        m.copy_score, _ = gate_score("copy")
        fr = F.flips(F.load_records(os.path.join(wd, "freeze.jsonl")),
                     F.load_records(cp_p), half="gate")
        m.copy_negative_flip_rate = fr.nfr
    rf_p = os.path.join(wd, "refresh.jsonl")
    if os.path.exists(rf_p):
        m.refresh_score, _ = gate_score("refresh")

    rec = P.recommend(m, flip_budget=c.get("flip_budget"))
    if proj_note:
        rec.reasons.append(
            f"reference was beta-projected (beta={proj_note['beta']}, from "
            f"episodes {proj_note['from_episodes']}); "
            + proj_note["note"])

    # 统计层：只用报告半集（门控读过的一半绝不参与这里的推断）
    def report_half(path):
        r = F.load_records(path)
        return {i: v for i, v in r.items() if not F.gate_half(i)}

    freeze_rec = report_half(os.path.join(wd, "freeze.jsonl"))
    if os.path.exists(ref_p):
        ref_rec = report_half(ref_p)
        mean, lo, hi = S.paired_diff_ci(ref_rec, freeze_rec)
        b01, c10, pv = S.mcnemar(ref_rec, freeze_rec)
        rec.evidence["opportunity_ci_pp"] = [round(lo, 2), round(hi, 2)]
        rec.evidence["opportunity_mcnemar_p"] = round(pv, 4)
        if rec.action.value != "freeze" and lo <= 0 <= hi:
            rec.warnings.append(
                "the gate passed but the report-half CI for the upgrade "
                "opportunity includes zero -- the gain is not statistically "
                "established; consider staying frozen until the next release "
                "or enlarging the gate set")
        for tag, path in [("copy", cp_p), ("refresh", rf_p)]:
            if os.path.exists(path):
                other = report_half(path)
                _, lo2, hi2 = S.paired_diff_ci(other, ref_rec)
                _, _, p2 = S.mcnemar(other, ref_rec)
                rec.evidence[f"{tag}_vs_reference_ci_pp"] = [round(lo2, 2),
                                                             round(hi2, 2)]
                rec.evidence[f"{tag}_vs_reference_p"] = round(p2, 4)

    # ---- confidence layer (fix #4), if probe-conf has run ----
    lp_f = os.path.join(wd, "freeze_lp.jsonl")
    lp_r = os.path.join(wd, "reference_lp.jsonl")
    if os.path.exists(lp_f) and os.path.exists(lp_r):
        dm, dlo, dhi = S.paired_nll_ci(lp_r, lp_f)
        rec.evidence["nll_ref_minus_freeze"] = [round(dm, 4),
                                                round(dlo, 4),
                                                round(dhi, 4)]
        rec.evidence["ece"] = {"freeze": S.ece(lp_f),
                               "reference": S.ece(lp_r)}
        rec.evidence["aurc"] = {"freeze": S.aurc(lp_f),
                                "reference": S.aurc(lp_r)}
        if dhi < 0:
            rec.warnings.append(
                "confidence layer: the reference has significantly lower "
                "log-loss than the frozen specialist even where accuracy "
                "ties -- an upgrade benefit the 0/1 metric cannot see; "
                "weigh it if selective routing (confidence thresholds) is "
                "part of serving")
    # ---- robustness layer (fix #5), if probe-robust has run ----
    rb = os.path.join(wd, "robust_summary.json")
    if os.path.exists(rb):
        rec.evidence["robustness"] = json.load(open(rb, encoding="utf-8"))
    # ---- economic epsilon (fix #6) ----
    if all(c.get(k) for k in ("monthly_requests", "cost_per_error",
                              "migration_cost")):
        months = c.get("amortization_months") or 6
        denom = c["monthly_requests"] * months * c["cost_per_error"]
        econ_eps = c["migration_cost"] / denom if denom else None
        if econ_eps is not None:
            rec.evidence["economic_epsilon_pp"] = round(econ_eps * 100, 3)
            gain_now = rec.evidence.get("opportunity_pp")
            if (gain_now is not None and gain_now / 100 > econ_eps
                    and rec.action.value in ("freeze", "inconclusive")):
                rec.warnings.append(
                    f"economic epsilon ({econ_eps*100:.3f}pp break-even at "
                    "your volume/costs) is below the statistical margin -- "
                    "the observed gain would already pay for migration if "
                    "it were statistically established; consider growing "
                    "the gate set rather than dismissing the upgrade")

    if c["task_kind"] == "classification":
        lm = {}
        for stem in ("freeze", "adopt", "reference", "copy", "refresh"):
            p = os.path.join(wd, stem + ".jsonl")
            if os.path.exists(p):
                lm[stem] = S.label_metrics(p)
        if lm:
            rec.evidence["label_metrics"] = lm

    _check_manifest(c, args.config, rec.warnings)
    L.append(c["workdir"], {
        "event": "recommend", "target": args.target,
        "task": c["task_name"], "action": rec.action.value,
        "freeze": round(fz, 4), "floor": round(ad, 4),
        "floor_zs": round(ad_zs, 4),
        "floor_fs": (round(ad_fs, 4) if ad_fs is not None else None),
        "reference": (round(m.reference_score, 4)
                      if m.reference_score is not None
                      and not m.reference_is_estimate else None),
        "reference_estimate": (round(m.reference_score, 4)
                               if m.reference_is_estimate else None),
        "copy": (round(m.copy_score, 4) if m.copy_score is not None else None),
        "train_minutes": _train_minutes(wd),
        "eval_minutes": _sum_eval_minutes(wd),
        "validation_items": n_gate})
    cs = L.costs_summary(L.history(c["workdir"]))
    rec.evidence["ledger"] = cs
    out = render_report(c, args.target, ver, m, rec)
    rpt = os.path.join(wd, "recommendation.md")
    with open(rpt, "w", encoding="utf-8") as f:
        f.write(out)
    print(out)
    print(f"\n[report written to {rpt}]")


def cmd_retrain(args):
    """Train the fixed-recipe reference on the target and score it into the
    episode workdir (reference.jsonl), unlocking the opportunity gate."""
    from .evaluate import evaluate
    from .train import train
    c = _cfg(args.config)
    wd = _wd(c, args.target)
    os.makedirs(wd, exist_ok=True)
    out_dir = args.out or os.path.join(wd, "reference_adapter")
    train(args.target, args.train_set or c.get("train_set"),
          out_dir, system_default=c["system_prompt"],
          plain=c.get("plain_format", False), max_len=args.max_len,
          epochs=args.epochs)
    evaluate(args.target, adapter=out_dir, data_path=c["test_set"],
             task_kind=c["task_kind"], system_default=c["system_prompt"],
             plain=c.get("plain_format", False),
             comparator=_comparator(c, args.config),
             out_records=os.path.join(wd, "reference.jsonl"))
    val_n = 0
    if c.get("val_set"):
        vs = evaluate(args.target, adapter=out_dir, data_path=c["val_set"],
                      task_kind=c["task_kind"],
                      system_default=c["system_prompt"],
                      plain=c.get("plain_format", False),
                      comparator=_comparator(c, args.config),
                      out_records=os.path.join(wd, "reference_val.jsonl"))
        val_n = vs["n"]
    tl = json.load(open(os.path.join(out_dir, "train_log.json"),
                        encoding="utf-8"))
    n_labels = sum(1 for _ in open(args.train_set or c.get("train_set"),
                                   encoding="utf-8"))
    L.append(c["workdir"], {
        "event": "retrain", "target": args.target, "task": c["task_name"],
        "train_minutes": tl.get("wall_clock_min"),
        "gold_labels_consumed": n_labels, "teacher_queries": 0,
        "validation_items": val_n})
    print(f"reference trained and scored; rerun `upgrade-advisor recommend`")


def cmd_refresh(args):
    """Annotation-free refresh: current specialist relabels retained inputs,
    a student trains on the target, and its records land in the workdir."""
    from .evaluate import evaluate
    from .train import relabel, train
    c = _cfg(args.config)
    wd = _wd(c, args.target)
    os.makedirs(wd, exist_ok=True)
    relabeled = os.path.join(wd, "refresh_train.jsonl")
    relabel(c["source_base"], c["adapter"],
            args.inputs or c.get("train_set"), relabeled,
            system_default=c["system_prompt"],
            plain=c.get("plain_format", False))
    out_dir = args.out or os.path.join(wd, "refresh_adapter")
    train(args.target, relabeled, out_dir,
          system_default=c["system_prompt"],
          plain=c.get("plain_format", False), max_len=args.max_len,
          epochs=args.epochs)
    evaluate(args.target, adapter=out_dir, data_path=c["test_set"],
             task_kind=c["task_kind"], system_default=c["system_prompt"],
             plain=c.get("plain_format", False),
             comparator=_comparator(c, args.config),
             out_records=os.path.join(wd, "refresh.jsonl"))
    val_n = 0
    if c.get("val_set"):
        vs = evaluate(args.target, adapter=out_dir, data_path=c["val_set"],
                      task_kind=c["task_kind"],
                      system_default=c["system_prompt"],
                      plain=c.get("plain_format", False),
                      comparator=_comparator(c, args.config),
                      out_records=os.path.join(wd, "refresh_val.jsonl"))
        val_n = vs["n"]
    tl = json.load(open(os.path.join(out_dir, "train_log.json"),
                        encoding="utf-8"))
    n_inputs = sum(1 for _ in open(args.inputs or c.get("train_set"),
                                   encoding="utf-8"))
    L.append(c["workdir"], {
        "event": "refresh", "target": args.target, "task": c["task_name"],
        "train_minutes": tl.get("wall_clock_min"),
        "gold_labels_consumed": 0, "teacher_queries": n_inputs,
        "validation_items": val_n})
    print(f"refresh student trained and scored; rerun `upgrade-advisor recommend`")


def cmd_manifest(args):
    """Pin the data splits (sha256 + row counts) next to the episode config;
    recommend warns whenever a pinned file changes (Phase 0 hygiene)."""
    c = _cfg(args.config)
    man = {}
    for key in ("test_set", "train_set", "val_set"):
        f = c.get(key)
        if f and os.path.exists(f):
            n = sum(1 for _ in open(f, encoding="utf-8"))
            man[f] = {"sha256": _sha(f), "n": n, "role": key}
    mp = _manifest_path(args.config)
    with open(mp, "w", encoding="utf-8") as fp:
        json.dump(man, fp, ensure_ascii=False, indent=2)
    print(f"pinned {len(man)} files in {mp}")


def cmd_probe_conf(args):
    """Confidence-layer probe (fix #4): label-logprob scoring of frozen and
    reference systems -> paired log-loss, ECE, risk-coverage inputs."""
    from .evaluate import label_score
    c = _cfg(args.config)
    wd = _wd(c, args.target)
    labels = [l for l in open(args.labels or os.path.join(
        os.path.dirname(c["test_set"]), "labels.txt"),
        encoding="utf-8").read().split("\n") if l.strip()]
    common = dict(data_path=c["test_set"], labels=labels,
                  system_default=c["system_prompt"],
                  plain=c.get("plain_format", False))
    print("[1/2] frozen specialist, label-logprob scoring")
    label_score(c["source_base"], adapter=c["adapter"],
                out_records=os.path.join(wd, "freeze_lp.jsonl"), **common)
    ref_ad = os.path.join(wd, "reference_adapter")
    if os.path.isdir(ref_ad):
        print("[2/2] reference, label-logprob scoring")
        label_score(args.target, adapter=ref_ad,
                    out_records=os.path.join(wd, "reference_lp.jsonl"),
                    **common)
    else:
        print("[2/2] no reference_adapter in workdir -- run `retrain` first")
    print("done; rerun `upgrade-advisor recommend` to fold these in")


def cmd_probe_robust(args):
    """Robustness probe (fix #5): perturbed inputs, unchanged gold; frozen
    vs reference accuracy under noise."""
    from .evaluate import evaluate
    from .perturb import perturb_file
    c = _cfg(args.config)
    wd = _wd(c, args.target)
    pert = os.path.join(wd, "test_perturbed.jsonl")
    info = perturb_file(c["test_set"], pert)
    print(f"perturbed {info['n']} items ({'/'.join(info['menu'])})")
    common = dict(data_path=pert, task_kind=c["task_kind"],
                  system_default=c["system_prompt"],
                  plain=c.get("plain_format", False),
                  comparator=_comparator(c, args.config))
    fz = evaluate(c["source_base"], adapter=c["adapter"],
                  out_records=os.path.join(wd, "freeze_perturbed.jsonl"),
                  **common)
    out = {"perturbations": info["menu"],
           "freeze_perturbed": fz["accuracy"]}
    ref_ad = os.path.join(wd, "reference_adapter")
    if os.path.isdir(ref_ad):
        rf = evaluate(args.target, adapter=ref_ad,
                      out_records=os.path.join(wd, "reference_perturbed.jsonl"),
                      **common)
        out["reference_perturbed"] = rf["accuracy"]
        out["robustness_delta_pp"] = round(
            (rf["accuracy"] - fz["accuracy"]) * 100, 2)
    with open(os.path.join(wd, "robust_summary.json"), "w",
              encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(json.dumps(out, ensure_ascii=False))
    print("rerun `upgrade-advisor recommend` to fold these in")


def cmd_gate(args):
    c = _cfg(args.config)
    serving = F.load_records(args.serving)
    cand = F.load_records(args.candidate)
    weights = c.get("class_weights") or {}
    if weights:
        rep = F.weighted_flips(args.serving, args.candidate, weights,
                               half="report")
        print("[severity-weighted flips]")
    else:
        rep = F.flips(serving, cand, half="report")
    budget = c.get("flip_budget", 0.03)
    ok = F.passes(rep, budget)
    print(json.dumps(rep.as_dict(), indent=2))
    print(f"negative-flip budget {budget:.2%}: "
          f"{'PASS' if ok else 'BLOCK DEPLOYMENT'}")
    sys.exit(0 if ok else 1)


def main():
    ap = argparse.ArgumentParser(prog="upgrade-advisor")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("init"); p.add_argument("config"); p.set_defaults(f=cmd_init)
    p = sub.add_parser("measure"); p.add_argument("config")
    p.add_argument("--target", required=True)
    p.add_argument("--skip-copy", action="store_true")
    p.set_defaults(f=cmd_measure)
    p = sub.add_parser("recommend"); p.add_argument("config")
    p.add_argument("--target", required=True)
    p.add_argument("--reference-estimate", type=float, default=None,
                   help="beta-projected reference score if not trained yet")
    p.add_argument("--non-interactive", action="store_true")
    p.set_defaults(f=cmd_recommend)
    for name, fn in [("retrain", cmd_retrain), ("refresh", cmd_refresh)]:
        p = sub.add_parser(name); p.add_argument("config")
        p.add_argument("--target", required=True)
        p.add_argument("--train-set", dest="train_set", default=None,
                       help="gold train jsonl (retrain) ")
        p.add_argument("--inputs", default=None,
                       help="retained inputs jsonl (refresh)")
        p.add_argument("--out", default=None)
        p.add_argument("--max-len", dest="max_len", type=int, default=256)
        p.add_argument("--epochs", type=float, default=3)
        p.set_defaults(f=fn)
    p = sub.add_parser("manifest"); p.add_argument("config")
    p.set_defaults(f=cmd_manifest)
    p = sub.add_parser("probe-conf"); p.add_argument("config")
    p.add_argument("--target", required=True)
    p.add_argument("--labels", default=None)
    p.set_defaults(f=cmd_probe_conf)
    p = sub.add_parser("probe-robust"); p.add_argument("config")
    p.add_argument("--target", required=True)
    p.set_defaults(f=cmd_probe_robust)
    p = sub.add_parser("gate"); p.add_argument("config")
    p.add_argument("--serving", required=True, help="records jsonl of serving system")
    p.add_argument("--candidate", required=True)
    p.set_defaults(f=cmd_gate)
    args = ap.parse_args()
    args.f(args)


if __name__ == "__main__":
    main()
