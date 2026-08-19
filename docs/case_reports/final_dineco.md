# Upgrade recommendation: `dineco` -> `E:\dataset\models\Qwen2-7B-Instruct`

## Action: **WAIT** (verdict: unresolved)

## Evidence
- frozen specialist (gate half, n=60): **0.9667**
- target adoption floor: **0.8098**
- retraining reference: **0.9667** (opportunity -0.28pp, epsilon 1pp)
- refresh student: **0.9500**
- genealogy: fresh_pretraining (inferred); distance unknown
  - architecture break; weight-space transfer undefined

## Statistics (report half only; gates never see these items)
- reference - frozen: 95% CI [-2.19, +2.19]pp, exact McNemar p = 1.0
- refresh - reference: 95% CI [-2.92, +1.46]pp, p = 1.0
- posterior over the true gain (UpgradeBench-corpus prior + paired evidence): mean -0.18pp, sd 0.73pp; P(gain > decision epsilon) = 5%, P(regression beyond epsilon) = 13%, P(within band) = 82%
- pooled paired evidence (val+test): n=360, reference fixes 3 frozen error(s) and breaks 4 frozen pass(es); 95% CI [-2.0, +1.4]pp -- gains above 1.4pp are excluded by the data
- error-scale view: relative error reduction -7% (15 frozen errors on gate)

## Confidence layer (proper scoring; more power than accuracy)
- paired log-loss, reference - frozen: +0.0520 (95% CI [-0.0346, +0.1491]; negative favors reference)
- calibration ECE: frozen 0.0228, reference 0.0318
- risk-coverage AURC (lower = better selective routing): frozen 0.0078, reference 0.0076

## Disagreement set (COLLECT channel: label these, not more i.i.d. samples)
- 11 disagreement item(s) (3.1% of pooled pairs); exact sign test on labeled outcomes p = 1.0
- probability the direction settles after labeling k more disagreements -- +10: 10%, +25: 21%, +50: 41%, +100: 56%, +200: 69%

## Robustness under perturbation (typo/casing/filler/punct; gold unchanged)
- frozen: 0.9533; reference: 0.9533 (delta +0.00pp)

## Label metrics (macro-F1: class-imbalance-robust; invalid rate: prediction outside the label inventory)
- freeze: macro-F1 **0.9568**, invalid outputs 0.00% (15 classes)
- adopt: macro-F1 **0.7498**, invalid outputs 0.00% (15 classes)
- reference: macro-F1 **0.9543**, invalid outputs 0.00% (15 classes)
- refresh: macro-F1 **0.9576**, invalid outputs 0.33% (15 classes)

## Task ledger: 1 episode(s), 5.0 train GPU-min, 2.4 eval GPU-min, 600 gold labels, 600 teacher queries, 180 validation items accumulated

## Reasoning
- the pooled evidence cannot resolve epsilon: CI [-2.0, +1.4]pp straddles 1pp (n=360, 3 fixes vs 4 breaks; gains above 1.4pp are already excluded; leaning: lean-freeze). Under the UpgradeBench corpus prior the posterior gives the gain a 5% chance of clearing the decision epsilon (1.00pp) -- more evidence is unlikely to change the call, so hold the frozen specialist and revisit at the next release

## Warnings
- gate set has only 60 items; gate sampling error at this size caused the worst episode in the paper's replay -- treat marginal verdicts as ties
- EVAL-SATURATED: the frozen specialist makes only 15 error(s) on the pooled evidence -- any upgrade comparison rests on that many items. Harvest hard/tail examples (e.g. production misroutes) before trusting an upgrade verdict here
- the gate passed but the report-half CI for the upgrade opportunity includes zero -- the gain is not statistically established; consider staying frozen until the next release or enlarging the gate set
- no data_manifest.json -- run `upgrade-advisor manifest` once to pin your splits (Phase 0)

## Before serving
- run `upgrade-advisor gate` for the candidate against the serving records (reporting half only); block on negative-flip budget 3%
- log GPU-minutes and labels consumed for this episode so the amortized decision improves with each release

*Policy and margins from UpgradeBench (2026); validated over 33 measured upgrade episodes (0.37pp mean regret, zero regressions, split-half gating). Negative-flip rate follows Yan et al., Positive-Congruent Training, CVPR 2021. Scope: LoRA-class adapters, 1.5-8B open-weight models.*

[report written to E:\eval project\cases\dineco_dining\episodes\E__dataset__models__Qwen2-7B-Instruct\recommendation.md]
