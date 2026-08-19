# upgrade-advisor

**An executable recommendation for one question: your base model just got a new
release — what should happen to your fine-tuned specialist?**

`upgrade-advisor` turns the measured decision policy from *UpgradeBench: A
Decision-Centric Benchmark for Upgrading Fine-Tuned LLM Specialists* into a
tool an ML platform team can run on **its own task data**. You provide a small
amount of your data (a held-out test set, your current adapter, the candidate
base); the tool measures what the decision needs, applies the policy the paper
validated over 33 upgrade episodes (mean regret 0.37pp, zero behavioral
regressions, at one third of always-retrain compute and labels), and emits one
of four actions with the evidence attached:

| Action | When the policy picks it |
|---|---|
| **FREEZE** | *Equivalence established*: the pooled paired CI excludes any gain above ε (1pp classification / 2pp structured) — a verdict with an exclusion bound, not a default |
| **COPY** | Adapter loads without mapping **and** target is a documented *short* continuation of your exact base weights **and** the copy passes a regression gate |
| **REFRESH** | Retraining is worthwhile, gold labels are expensive, and you retained task inputs — your current specialist relabels them (annotation-free; paper: retention 0.96–1.05 vs. gold retraining) |
| **RETRAIN** | *Gain established* (CI above ε, or ≥30% of frozen errors removed with the direction settled by exact sign test) and no cheaper path passes its gates |
| **COLLECT** | The evidence cannot resolve ε yet and the posterior leaves the gain live — label the disagreement set (`probe-disagree` writes it with a priced convergence plan) |
| **WAIT** | The evidence cannot resolve ε and the corpus-prior posterior gives the gain <10% chance of clearing your decision ε — hold until the next release |

Every recommendation separates the **epistemic verdict** (gain-established /
equivalence / unresolved) from the **operational action**, judges on the
*pooled* paired records (every val+test pair the episode holds), and — when
the verdict is unresolved — reports a posterior over the true gain under an
empirical-Bayes prior extracted from the paper's own 193 measured cells
(`registry/gain_prior.json`, rebuilt by `scripts/build_gain_prior.py`).

**Why this matters at enterprise evidence sizes** (n=100–600): replayed over
21 real upgrade cells from the paper corpus
(`docs/small_n_operating_curve.md`), the naive point-estimate gate falsely
opens the upgrade waterfall on **17.9%** of ground-truth-null episodes at
n=100; this core holds that at **1.9%** while its equivalence verdicts are
wrong ≤0.5% of the time, at a stated cost of ~0.1pp mean regret. And when the
verdict is unresolved, 25 labeled *disagreements* resolve the direction more
often than 100 labeled i.i.d. samples — annotation complexity is
O(#disagreements), not O(n).

## Why not just copy the adapter when shapes match?

Because that is the single most dangerous habit the paper measured. Between
architecturally identical checkpoints from *independent* pretraining runs,
copying collapsed a 92.8% classifier to 42.9% — below the 60.7% the bare
target base scores with no adapter, negatively flipping half the test set.
Portability is governed by *documented continued-training distance*, not by
`config.json`: retention was 0.88–0.99 at a 46B-token continuation and zero at
2.9T tokens, with annealing and model souping adding no further damage. The
`copy-if-shape` rule scored 17pp mean regret and 14 regression episodes in
replay; the policy here scored 0.37pp and zero.

## Install

```bash
pip install -e .            # core: policy engine, genealogy, flips, report (no GPU)
pip install -e ".[gpu]"     # + evaluation/probe/training (torch, transformers, peft)
pip install -e ".[dev]" && pytest tests/   # run the test suite
```

Training-class commands (`retrain`, `refresh`, and `measure` on large
test sets) run for 10+ minutes -- launch them under `nohup`/a job
runner rather than an interactive shell with a timeout.

## Quickstart

```bash
# 1. Describe your episode (task, data paths, models, margins) once:
upgrade-advisor init my_task.yaml

# 2. When a new base releases — measure the cheap facts (~1–2 GPU-hours):
upgrade-advisor measure my_task.yaml --target Qwen/Qwen3-8B

# 3. Get the recommendation + evidence report:
upgrade-advisor recommend my_task.yaml --target Qwen/Qwen3-8B

# 4. Before serving whatever you built — behavioral regression gate:
upgrade-advisor gate my_task.yaml --candidate outputs/new_adapter

# supporting commands:
upgrade-advisor manifest my_task.yaml    # pin split hashes (Phase 0)
upgrade-advisor retrain  my_task.yaml --target ...   # reference on target
upgrade-advisor refresh  my_task.yaml --target ...   # annotation-free student

# evidence probes (each feeds new sections into `recommend`):
upgrade-advisor probe-disagree my_task.yaml --target ...  # zero GPU: the
#   disagreement set + a priced labeling plan; --inputs FILE scans unlabeled
#   traffic with both systems (disagreement needs no gold labels)
upgrade-advisor probe-conf   my_task.yaml --target ...    # confidence layer:
#   label-logprob scoring -> paired log-loss, ECE, risk-coverage AURC
upgrade-advisor probe-robust my_task.yaml --target ...    # robustness layer:
#   typo/casing/filler/punct perturbations, gold unchanged
```

Reports carry paired bootstrap CIs and exact McNemar p-values for every
measured comparison, and each episode appends to a per-task ledger
(floors, references, costs); after two-plus releases the ledger estimates
the task coupling (beta) and projects the reference for a new target
before you pay for retraining.

`recommend` never deploys anything. It prints the action, the measured
evidence behind it (floors, margins, genealogy verdict, flip rates, paired
CIs and McNemar p-values on the held-out report half), plus the task's
cumulative episode costs from the ledger, and writes a Markdown report you
can put in a design review.

## What you need to provide

- **Test set** (JSONL, gold-labeled, fixed split) — a few hundred to a few
  thousand items. This is the only hard requirement.
- **Your current specialist** (base checkpoint id + LoRA adapter dir).
- Optional: a validation set (used for gates, so the test set stays clean),
  retained training inputs (enables REFRESH), gold training labels (enables
  RETRAIN cost estimates).

## What the tool knows that you don't have to

- A **release-genealogy registry** (`registry/release_graph.yaml`) seeded with
  the checkpoints the paper verified (Qwen 1.5→2→2.5→3 series, Qwen2.5-1M
  continuation, the OLMo documented trajectory including its anneal and soup
  edges). For unknown checkpoints it walks you through the two questions that
  matter — documented descent, and continuation distance — instead of letting
  shape compatibility decide.
- The paper's **fixed training recipe** (QLoRA r=16, α=32, lr 2e-4, NF4) so
  your retrained references stay comparable across generations.
- **Per-example bookkeeping**: every evaluation writes per-item records so
  negative-flip analysis and paired tests come free later.

## Scope and honesty

Validated for LoRA-class adapters on 1.5–8B open-weight models, English
tasks, one consumer GPU. If you run full fine-tuning, RLHF-style adaptation,
or much larger models, treat the recommendation as a starting hypothesis and
keep the regression gate. The policy's gates consume your validation data;
gate sampling error on small sets is real (the paper's worst replay episode
came from exactly that) — the report states the gate set size next to every
verdict. See [PLAYBOOK.md](PLAYBOOK.md) for the full non-technical recipe. Validation runs and the defects they caught are documented in [docs/CASE_STUDIES.md](docs/CASE_STUDIES.md).

## Repository layout

```
upgrade_advisor/    policy.py      the validated decision policy (pure python)
                    genealogy.py   release-graph lookup + questionnaire
                    flips.py       negative/positive-flip regression gate
                    evaluate.py    floors & specialist scoring (GPU extra)
                    probe.py       CKA/top-1/JSD base-pair probe (GPU extra)
                    train.py       fixed-recipe QLoRA retrain/refresh (GPU extra)
                    report.py      evidence report generation
registry/           release_graph.yaml   typed checkpoint genealogy
examples/           banking77_demo/      end-to-end walkthrough on public data
tests/              policy fixtures from the paper's 33 measured episodes
```

## Citation

If this tool informs a deployment decision or a paper, please cite
*UpgradeBench: A Decision-Centric Benchmark for Upgrading Fine-Tuned LLM
Specialists* (2026). License: Apache-2.0.
