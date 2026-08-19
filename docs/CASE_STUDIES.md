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
