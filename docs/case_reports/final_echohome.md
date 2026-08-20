# Upgrade recommendation: `echohome` -> `E:\dataset\models\Qwen2.5-7B-Instruct`

## Action: **COLLECT** (verdict: unresolved)

## Evidence
- frozen specialist (gate half, n=60): **1.0000**
- target adoption floor: **0.9509**
- retraining reference: **1.0000** (opportunity +1.39pp, epsilon 1pp)
- genealogy: fresh_pretraining (inferred); distance unknown
  - shape-identical but independent run per release docs; measured copy retention -0.60..0.78

## Statistics (report half only; gates never see these items)
- reference - frozen: 95% CI [-2.19, +5.11]pp, exact McNemar p = 0.6875
- posterior over the true gain (UpgradeBench-corpus prior + paired evidence): mean +1.30pp, sd 0.94pp; P(gain > decision epsilon) = 62%, P(regression beyond epsilon) = 1%, P(within band) = 37%
- pooled paired evidence (val+test): n=360, reference fixes 9 frozen error(s) and breaks 4 frozen pass(es); 95% CI [-0.8, +3.6]pp -- gains above 3.6pp are excluded by the data
- error-scale view: relative error reduction +56% (9 frozen errors on gate)

## Confidence layer (proper scoring; more power than accuracy)
- paired log-loss, reference - frozen: -0.0702 (95% CI [-0.2219, +0.0517]; negative favors reference)
- calibration ECE: frozen 0.022, reference 0.0093
- risk-coverage AURC (lower = better selective routing): frozen 0.0125, reference 0.0011

## Disagreement set (COLLECT channel: label these, not more i.i.d. samples)
- 13 disagreement item(s) (3.6% of pooled pairs); exact sign test on labeled outcomes p = 0.2668
- probability the direction settles after labeling k more disagreements -- +10: 36%, +25: 54%, +50: 68%, +100: 76%, +200: 83%

## Robustness under perturbation (typo/casing/filler/punct; gold unchanged)
- frozen: 0.9633; reference: 0.9667 (delta +0.34pp)

## Label metrics (macro-F1: class-imbalance-robust; invalid rate: prediction outside the label inventory)
- freeze: macro-F1 **0.9696**, invalid outputs 0.33% (15 classes)
- adopt: macro-F1 **0.8198**, invalid outputs 0.33% (15 classes)
- reference: macro-F1 **0.9866**, invalid outputs 0.00% (15 classes)

## Task ledger: 1 episode(s), 2.4 train GPU-min, 2.3 eval GPU-min, 600 gold labels, 0 teacher queries, 120 validation items accumulated

## Reasoning
- the pooled evidence cannot resolve epsilon: CI [-0.8, +3.6]pp straddles 1pp (n=360, 9 fixes vs 4 breaks; gains above 3.6pp are already excluded; leaning: lean-upgrade); posterior chance the gain clears the decision epsilon: 62%. Cheapest resolution: label the disagreement set (`upgrade-advisor probe-disagree` writes it with a priced convergence plan); resolving by i.i.d. sampling would need roughly n=2831. Keep serving the frozen specialist while collecting

## Warnings
- gate set has only 60 items; gate sampling error at this size caused the worst episode in the paper's replay -- treat marginal verdicts as ties
- EVAL-SATURATED: the frozen specialist makes only 9 error(s) on the pooled evidence -- any upgrade comparison rests on that many items. Harvest hard/tail examples (e.g. production misroutes) before trusting an upgrade verdict here
- the gate passed but the report-half CI for the upgrade opportunity includes zero -- the gain is not statistically established; consider staying frozen until the next release or enlarging the gate set
- no data_manifest.json -- run `upgrade-advisor manifest` once to pin your splits (Phase 0)

## Before serving
- run `upgrade-advisor gate` for the candidate against the serving records (reporting half only); block on negative-flip budget 3%
- log GPU-minutes and labels consumed for this episode so the amortized decision improves with each release

*Policy and margins from UpgradeBench (2026); validated over 33 measured upgrade episodes (0.37pp mean regret, zero regressions, split-half gating). Negative-flip rate follows Yan et al., Positive-Congruent Training, CVPR 2021. Scope: LoRA-class adapters, 1.5-8B open-weight models.*