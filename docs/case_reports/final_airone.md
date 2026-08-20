# Upgrade recommendation: `airone` -> `E:\dataset\models\Qwen2-7B-Instruct`

## Action: **COLLECT** (verdict: unresolved)

## Evidence
- frozen specialist (gate half, n=100): **0.9800**
- target adoption floor: **0.9264**
- retraining reference: **1.0000** (opportunity +0.50pp, epsilon 1pp)
- genealogy: fresh_pretraining (inferred); distance unknown
  - architecture break; weight-space transfer undefined

## Statistics (report half only; gates never see these items)
- reference - frozen: 95% CI [+0.00, +0.00]pp, exact McNemar p = 1.0
- posterior over the true gain (UpgradeBench-corpus prior + paired evidence): mean +0.51pp, sd 0.41pp; P(gain > decision epsilon) = 11%, P(regression beyond epsilon) = 0%, P(within band) = 89%
- pooled paired evidence (val+test): n=400, reference fixes 2 frozen error(s) and breaks 0 frozen pass(es); 95% CI [-0.4, +1.4]pp -- gains above 1.4pp are excluded by the data
- error-scale view: relative error reduction +50% (4 frozen errors on gate)

## Confidence layer (proper scoring; more power than accuracy)
- paired log-loss, reference - frozen: -0.0585 (95% CI [-0.1534, +0.0047]; negative favors reference)
- calibration ECE: frozen 0.0064, reference 0.008
- risk-coverage AURC (lower = better selective routing): frozen 0.0171, reference 0.0009

## Disagreement set (COLLECT channel: label these, not more i.i.d. samples)
- 2 disagreement item(s) (0.5% of pooled pairs); exact sign test on labeled outcomes p = 0.5
- probability the direction settles after labeling k more disagreements -- +10: 58%, +25: 67%, +50: 79%, +100: 85%, +200: 89%

## Robustness under perturbation (typo/casing/filler/punct; gold unchanged)
- frozen: 0.99; reference: 0.9867 (delta -0.33pp)

## Label metrics (macro-F1: class-imbalance-robust; invalid rate: prediction outside the label inventory)
- freeze: macro-F1 **0.9993**, invalid outputs 0.67% (6 classes)
- adopt: macro-F1 **0.9158**, invalid outputs 2.33% (6 classes)
- reference: macro-F1 **0.9993**, invalid outputs 0.67% (6 classes)

## Task ledger: 1 episode(s), 2.6 train GPU-min, 1.9 eval GPU-min, 600 gold labels, 0 teacher queries, 200 validation items accumulated

## Reasoning
- the pooled evidence cannot resolve epsilon: CI [-0.4, +1.4]pp straddles 1pp (n=400, 2 fixes vs 0 breaks; gains above 1.4pp are already excluded; leaning: lean-freeze); posterior chance the gain clears the decision epsilon: 11%. Cheapest resolution: label the disagreement set (`upgrade-advisor probe-disagree` writes it with a priced convergence plan); resolving by i.i.d. sampling would need roughly n=392. Keep serving the frozen specialist while collecting

## Warnings
- gate set has only 100 items; gate sampling error at this size caused the worst episode in the paper's replay -- treat marginal verdicts as ties
- EVAL-SATURATED: the frozen specialist makes only 4 error(s) on the pooled evidence -- any upgrade comparison rests on that many items. Harvest hard/tail examples (e.g. production misroutes) before trusting an upgrade verdict here
- the gate passed but the report-half CI for the upgrade opportunity includes zero -- the gain is not statistically established; consider staying frozen until the next release or enlarging the gate set
- no data_manifest.json -- run `upgrade-advisor manifest` once to pin your splits (Phase 0)

## Before serving
- run `upgrade-advisor gate` for the candidate against the serving records (reporting half only); block on negative-flip budget 3%
- log GPU-minutes and labels consumed for this episode so the amortized decision improves with each release

*Policy and margins from UpgradeBench (2026); validated over 33 measured upgrade episodes (0.37pp mean regret, zero regressions, split-half gating). Negative-flip rate follows Yan et al., Positive-Congruent Training, CVPR 2021. Scope: LoRA-class adapters, 1.5-8B open-weight models.*