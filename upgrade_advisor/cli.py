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

from . import flips as F
from . import genealogy as G
from . import policy as P
from .report import render_report

TEMPLATE = """\
# upgrade-advisor episode config
task_name: my_task
task_kind: classification        # classification | structured
test_set: data/test.jsonl        # gold-labeled, fixed split
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
workdir: runs/my_task
"""


def _wd(cfg, target):
    # sanitize HF ids AND local paths (drive letters would hijack os.path.join)
    safe = re.sub(r"[\\/:]+", "__", target).strip("_")
    return os.path.join(cfg["workdir"], safe)


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
                  system_default=c["system_prompt"], plain=plain)
    print("[1/3] serving specialist on source base")
    evaluate(c["source_base"], adapter=c["adapter"],
             out_records=os.path.join(wd, "freeze.jsonl"), **common)
    print("[2/3] target adoption floor (zero-shot, full task instructions)")
    adopt_common = dict(common)
    adopt_common["system_default"] = c.get("adoption_system_prompt")         or c["system_prompt"]
    evaluate(args.target, adapter=None,
             out_records=os.path.join(wd, "adopt.jsonl"), **adopt_common)
    ver = G.lookup(c["source_base"], args.target)
    if ver.documented_continuation and not args.skip_copy:
        print("[3/3] documented continuation: measuring the copied adapter")
        evaluate(args.target, adapter=c["adapter"],
                 out_records=os.path.join(wd, "copy.jsonl"), **common)
    else:
        print("[3/3] copy not licensed by genealogy; skipped "
              f"({ver.edge_type}: {ver.note})")
    print(f"measurements in {wd}; next: upgrade-advisor recommend "
          f"{args.config} --target {args.target}")


def cmd_recommend(args):
    c = _cfg(args.config)
    wd = _wd(c, args.target)
    ver = G.lookup(c["source_base"], args.target)
    if ver.edge_type == "unknown" and not args.non_interactive:
        ver = G.questionnaire()

    fz, n_gate = _score(os.path.join(wd, "freeze.jsonl"), "gate")
    ad, _ = _score(os.path.join(wd, "adopt.jsonl"), "gate")
    m = P.Measurements(
        task_kind=c["task_kind"], freeze_score=fz, adopt_floor=ad,
        inputs_retained=c.get("inputs_retained", False),
        gold_labels_retained=c.get("gold_labels_retained", False),
        gate_set_size=n_gate, shape_compatible=True,
        documented_continuation=ver.documented_continuation,
        continuation_tokens=ver.continuation_tokens)
    ref_p = os.path.join(wd, "reference.jsonl")
    if os.path.exists(ref_p):
        m.reference_score, _ = _score(ref_p, "gate")
    elif args.reference_estimate is not None:
        m.reference_score = args.reference_estimate
        m.reference_is_estimate = True
    cp_p = os.path.join(wd, "copy.jsonl")
    if os.path.exists(cp_p):
        m.copy_score, _ = _score(cp_p, "gate")
        fr = F.flips(F.load_records(os.path.join(wd, "freeze.jsonl")),
                     F.load_records(cp_p), half="gate")
        m.copy_negative_flip_rate = fr.nfr
    rf_p = os.path.join(wd, "refresh.jsonl")
    if os.path.exists(rf_p):
        m.refresh_score, _ = _score(rf_p, "gate")

    rec = P.recommend(m, flip_budget=c.get("flip_budget"))
    out = render_report(c, args.target, ver, m, rec)
    rpt = os.path.join(wd, "recommendation.md")
    with open(rpt, "w", encoding="utf-8") as f:
        f.write(out)
    print(out)
    print(f"\n[report written to {rpt}]")


def cmd_gate(args):
    c = _cfg(args.config)
    serving = F.load_records(args.serving)
    cand = F.load_records(args.candidate)
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
    p = sub.add_parser("gate"); p.add_argument("config")
    p.add_argument("--serving", required=True, help="records jsonl of serving system")
    p.add_argument("--candidate", required=True)
    p.set_defaults(f=cmd_gate)
    args = ap.parse_args()
    args.f(args)


if __name__ == "__main__":
    main()
