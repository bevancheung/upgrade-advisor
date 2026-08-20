# Upgrade recommendation: `cardco` -> `E:\dataset\models\Qwen2.5-7B-Instruct`

## Action: **COLLECT** (verdict: unresolved)

## Evidence
- frozen specialist (gate half, n=100): **0.9900**
- target adoption floor: **0.8712**
- retraining reference: **0.9900** (opportunity +0.50pp, epsilon 1pp)
- genealogy: fresh_pretraining (verified); distance unknown
  - path exists but crosses a non-continuation edge (anneal/soup/fresh): copying is not licensed

## Statistics (report half only; gates never see these items)
- reference - frozen: 95% CI [-2.19, +2.19]pp, exact McNemar p = 1.0
- posterior over the true gain (UpgradeBench-corpus prior + paired evidence): mean +0.53pp, sd 0.71pp; P(gain > decision epsilon) = 25%, P(regression beyond epsilon) = 2%, P(within band) = 73%
- pooled paired evidence (val+test): n=400, reference fixes 5 frozen error(s) and breaks 3 frozen pass(es); 95% CI [-1.1, +2.1]pp -- gains above 2.1pp are excluded by the data
- error-scale view: relative error reduction +20% (10 frozen errors on gate)

## Confidence layer (proper scoring; more power than accuracy)
- paired log-loss, reference - frozen: -0.0295 (95% CI [-0.0800, +0.0134]; negative favors reference)
- calibration ECE: frozen 0.0183, reference 0.014
- risk-coverage AURC (lower = better selective routing): frozen 0.0077, reference 0.0055

## Disagreement set (COLLECT channel: label these, not more i.i.d. samples)
- 10 disagreement item(s) (2.5% of pooled pairs); exact sign test on labeled outcomes p = 0.7266
- probability the direction settles after labeling k more disagreements -- +10: 12%, +25: 32%, +50: 50%, +100: 62%, +200: 73%

## Robustness under perturbation (typo/casing/filler/punct; gold unchanged)
- frozen: 0.9633; reference: 0.9667 (delta +0.34pp)

## Label metrics (macro-F1: class-imbalance-robust; invalid rate: prediction outside the label inventory)
- freeze: macro-F1 **0.9725**, invalid outputs 0.33% (15 classes)
- adopt: macro-F1 **0.8068**, invalid outputs 0.00% (15 classes)
- reference: macro-F1 **0.9828**, invalid outputs 1.00% (15 classes)

## Task ledger: 3 episode(s), 4.6 train GPU-min, 3.2 eval GPU-min, 1200 gold labels, 0 teacher queries, 500 validation items accumulated

## Reasoning
- the pooled evidence cannot resolve epsilon: CI [-1.1, +2.1]pp straddles 1pp (n=400, 5 fixes vs 3 breaks; gains above 2.1pp are already excluded; leaning: lean-freeze); posterior chance the gain clears the decision epsilon: 25%. Cheapest resolution: label the disagreement set (`upgrade-advisor probe-disagree` writes it with a priced convergence plan); resolving by i.i.d. sampling would need roughly n=1568. Keep serving the frozen specialist while collecting

## Warnings
- gate set has only 100 items; gate sampling error at this size caused the worst episode in the paper's replay -- treat marginal verdicts as ties
- EVAL-SATURATED: the frozen specialist makes only 10 error(s) on the pooled evidence -- any upgrade comparison rests on that many items. Harvest hard/tail examples (e.g. production misroutes) before trusting an upgrade verdict here
- the gate passed but the report-half CI for the upgrade opportunity includes zero -- the gain is not statistically established; consider staying frozen until the next release or enlarging the gate set
- no data_manifest.json -- run `upgrade-advisor manifest` once to pin your splits (Phase 0)

## Before serving
- run `upgrade-advisor gate` for the candidate against the serving records (reporting half only); block on negative-flip budget 3%
- log GPU-minutes and labels consumed for this episode so the amortized decision improves with each release

*Policy and margins from UpgradeBench (2026); validated over 33 measured upgrade episodes (0.37pp mean regret, zero regressions, split-half gating). Negative-flip rate follows Yan et al., Positive-Congruent Training, CVPR 2021. Scope: LoRA-class adapters, 1.5-8B open-weight models.*