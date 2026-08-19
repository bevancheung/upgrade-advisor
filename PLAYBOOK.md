# The Playbook

*A non-technical yet executable recipe for maintaining fine-tuned
domain specialists across base-model releases, grounded in the
UpgradeBench measurements. `upgrade-advisor` automates Phases 1-3;
Phase 0 is organizational hygiene no tool can do for you.*


## Phase 0 — One-time setup (before any upgrade decision)

- Retain your task inputs, not just the model. The paper shows the durable assets are the training inputs, per-example test records, and the refresh pipeline — not frozen weights. Store: gold-labeled train/val/test sets with fixed splits, and unlabeled production inputs if labels are expensive.
- Build a fixed evaluation harness per task: held-out test set, deterministic decoding, per-example prediction logging (needed for negative-flip analysis later), bootstrap CIs, paired McNemar for comparisons.
- Standardize one training recipe (e.g., QLoRA r=16, fixed hyperparameters, fixed seed) so retrained references are comparable across generations.
- Measure and record each task's coupling. When a new base ships, log its zero-shot floor and, when you retrain, the reference score. Over 2–3 releases you can estimate β = Δreference/Δfloor per task. High β (like text-to-SQL, ~1.5) means base progress penetrates your fine-tune; near-zero β (label taxonomies, call formats) means your fine-tune is the ceiling.

## Phase 1 — When a new base releases (per task, ~1–2 GPU-hours of measurement)

- Measure the new base's cheap-adoption floor (zero-shot + few-shot with your full task instructions) on your test set.
- Evaluate your frozen specialist against that floor. If the specialist still leads by a comfortable margin and your task is low-β, you likely need to do nothing.
- Check release genealogy, not config.json. Ask two questions before considering adapter copying: (a) is the new checkpoint a documented continued-pretraining descendant of your current base (e.g., a long-context or continuation release)? (b) if yes, roughly how far — is the continuation short (tens of billions of tokens) or a large fraction of a full pretraining run? Shape compatibility means nothing: identical architecture from an independent run will likely destroy your adapter, sometimes below zero-shot performance.

## Phase 2 — Choose the action (the paper's validated policy)

- First separate what the evidence *establishes* from what to *do*. The opportunity gate judges the pooled paired records (every val+test pair) with a three-zone equivalence test: CI entirely above ε opens the waterfall; CI entirely below ε is FREEZE **as a verdict** (equivalence established, exclusion bound stated); a straddling CI is *unresolved* — never silently mapped to freeze.
- FREEZE when equivalence is established at ε = 1pp (classification) / 2pp (structured generation). This is the right call for most data-bound tasks — the paper found intent specialists retained 99–101% of attainable gain over 14 months.
- COLLECT when the verdict is unresolved and the corpus-prior posterior leaves the gain live: label the disagreement set (`probe-disagree` writes it with a priced convergence plan). Disagreement is visible without gold labels, and McNemar conditions on discordant pairs, so 25 disagreement labels typically outperform 100 i.i.d. labels on direction resolution.
- WAIT when the verdict is unresolved but the posterior gives the gain <10% chance of clearing your decision ε (set ε economically: migration cost ÷ monthly requests × amortization × error cost). Hold the frozen specialist and revisit at the next release instead of spending annotation.
- COPY only if all three hold: the adapter loads without mapping, the target is a documented short continuation of your exact base weights, and the copied adapter passes a regression gate on your validation set (both aggregate score and negative-flip rate). Never copy onto a new major generation, even if shapes match.
- REFRESH (teacher relabeling) if retraining looks worthwhile but new gold labels are expensive: have your current specialist relabel the retained inputs, then train a fresh adapter on the new base. The paper found this matches gold-label retraining (0.96–1.05 retention) with zero annotation cost. Note it does not always save compute — if you kept the original gold labels, plain retraining dominates.
- RETRAIN on gold labels only for high-β tasks where the new base's reference ceiling clearly rises, or when neither copying nor input retention is available. Don't bother with small label budgets on hard tasks — the paper found 256 labels bought nothing on text-to-SQL; 95% of the gain required >4,096.

## Phase 3 — Gate before serving

- Run a behavioral regression gate, not just an accuracy check. Compute the negative-flip rate against your currently-serving specialist on the fixed test set. Even quality-neutral retraining flipped 1–5% of previously-correct items in the paper; a copied adapter flipped 50%. Set a flip-rate budget appropriate to your SLA and block deployment above it.
- Log costs per episode (GPU-minutes, labels consumed, validation load) so the amortized decision — is upgrading worth it at your release cadence and traffic volume — becomes data-driven over time.

## Rules of thumb the evidence supports: data-bound specialists (taxonomies, formats) age very slowly — don't chase every release; base-bound specialists (compositional reasoning over unseen inputs) lose most of their margin within months even if they stay net-positive for a year; "wait for the next base" is not directionally safe because per-task zero-shot uplift can be negative; and the single most dangerous habit is copying adapters because the architecture matches.


## One caveat on scope: this recipe is validated for parameter-efficient (LoRA-class) adapters on 1.5–8B open-weight models with English tasks. If you're doing full fine-tuning, RLHF-style adaptation, or much larger models, treat it as a starting hypothesis to verify with your own harness rather than settled guidance.

