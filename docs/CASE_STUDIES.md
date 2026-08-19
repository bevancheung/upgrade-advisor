# Validation case studies

Four end-to-end runs on a single RTX 4090, each executed as an external
user would (cold clone, README-only). Every defect found was fixed and
regression-tested; the fixes are part of this repository's history.

## 1. Paper cross-check (Banking77, 77 intents)

The paper's real Qwen2.5 adapter against Qwen3-8B. The tool's adoption
floor (.6683) matched the paper's independently implemented protocol
(.6594); genealogy correctly ruled Qwen2.5->Qwen3 a fresh pretraining run
and skipped copying; verdict FREEZE (opportunity -1.58pp <= 1pp), matching
the paper's conclusion for this task.

## 2. Cold-clone round: SNIPS intents (7 classes, 2,000 labels)

Two episodes. Qwen2->Qwen2.5 (fresh run): copy auto-skipped, measured
reference gave opportunity +0.53pp <= eps -> FREEZE. Qwen2.5->2.5-1M
(documented 20B-token continuation): copy licensed and measured at
retention ~1.05 with 0.27% negative flips -- a third independent task
landing in the paper's continuation band -- but the opportunity gate fired
first (-0.53pp) -> FREEZE: when upgrading buys nothing, even a free copy
is not worth serving-side churn.

## 3. Cold-clone round: slot-filling NLU (structured JSON, custom comparator)

A harder episode (frozen .425 / floor .157 / reference .445 on val).
Exercised: structured margins (2pp), yaml-loaded custom comparator,
full val-set gating, the copy quality-gate REJECT branch, the first
RETRAIN verdict, manifest drift warning (fires on a mutated test file,
clears on restore), and the gate command's BLOCK branch (zero-shot
candidate: 46.4% negative flips > 5% budget -> exit code 1).

## 4. Production scenario: "Fintone" card-support routing (500 labels)

A bank-style team with 20 intents and only 500 gold labels asks whether
to move its Qwen2-7B specialist to Qwen2.5. Total cost: ~25 GPU-minutes,
zero new annotation, zero API spend. Verdict FREEZE with three mutually
consistent readings: opportunity -3.0pp <= 1pp (reference .880 vs frozen
.910; floor .773); report-half CI [-0.73, +5.84]pp (p=0.375, treated as a
tie); macro-F1 .924 vs .921. Small data suffices because the decision
rests on paired comparisons on one fixed test set, not on absolute
scores -- and the report flags the small gate set explicitly.

## Defects found by these runs (all fixed in-tree)

- os.path.join hijack for absolute-path targets; path sanitizer regex
- adoption floors must carry full task instructions (adoption_system_prompt)
- PyYAML parses `2.0e10` as a string (registry distances; now schema-tested)
- statistics were computed but not rendered; now report-half-only by design
- ledger double-counting on re-runs; dual-basis floors for beta
- missing eos handling for base models; first-line cut for plain outputs

## 5. The v2 decision core, replayed over eleven industry episodes

After a theory review of the scoring layer (post-hoc-power fallacy;
evidence fragmentation; a 2-item flip deciding a RETRAIN), the opportunity
gate was rebuilt: pooled paired evidence, a TOST three-zone verdict, a
corpus prior from the paper's 193 cells, and a verdict/action split with
two new actions (COLLECT, WAIT). All eleven episodes were re-judged and
every probe layer was run on real GPUs; the full reports live in
`docs/case_reports/`.

| Episode | Action (verdict) | Pooled CI (pp) | P(gain>eps) |
|---|---|---|---|
| AirOne (ATIS) | COLLECT (unresolved) | [-0.4, +1.4] | 11% |
| TripFun | FREEZE (equivalence) | [-0.9, +0.9] | -- |
| NewsDesk | FREEZE (equivalence) | [-1.6, +0.8] | -- |
| WorkDesk | WAIT (unresolved) | [-1.2, +1.2] | 4% |
| AutoLink | FREEZE (equivalence) | [-2.6, +0.5] | -- |
| DineCo | WAIT (unresolved) | [-2.0, +1.4] | 5% |
| CardCo -> Qwen2.5 | COLLECT (unresolved) | [-1.1, +2.1] | 25% |
| CloudTalk (slots) | FREEZE (equivalence) | [-0.6, +2.0] | -- |
| EchoHome | COLLECT (unresolved) | [-0.8, +3.6] | 62% |
| SenseEdge | COLLECT (unresolved) | [-1.3, +2.3] | -- (lineage unknown) |
| Fintone | WAIT (unresolved) | [-3.4, +1.4] | 5% |

Notable outcomes, all from real records:
- **AirOne's old RETRAIN dissolves.** The original verdict rested on a
  2-item flip in one evidence fragment; pooling all 400 paired records
  shows 2 fixes / 0 breaks. The symmetric three-zone gate calls it
  unresolved and routes it to COLLECT.
- **FREEZE became a verdict, not a default.** Four episodes now carry an
  equivalence statement with an exclusion bound ("gains above 0.9pp are
  excluded by the data") instead of "no measurable gain".
- **The confidence layer sees what 0/1 accuracy cannot, sometimes.** In
  6 of 10 classification episodes the paired log-loss favors the
  reference (EchoHome -0.070), directionally consistent with the
  verdict leaning; none reach significance at these n.
- **A negative result, reported as such:** under rule-based perturbation
  (typo/casing/filler/punct) the newer bases are *not* more robust once
  fine-tuned on the same data (mean delta -0.28pp across episodes;
  TripFun -1.67pp). The "hidden robustness dividend of newer
  pretraining" did not survive same-recipe fine-tuning here.

Operating characteristics of the v2 core, validated by subsampling the
paper's own per-example corpus (21 real upgrade cells, leave-one-pair-out
prior, COLLECT played out on real disagreement labels): false-open rate
at n=100 drops from 17.9% (point-estimate gate) to 1.9%, at a stated cost
of ~0.1pp mean regret. See `docs/small_n_operating_curve.md`.
