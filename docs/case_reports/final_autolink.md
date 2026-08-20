# Upgrade recommendation: `autolink` -> `E:\dataset\models\OLMo-1.7-7B`

## Action: **FREEZE** (verdict: equivalence)

## Evidence
- frozen specialist (gate half, n=80): **1.0000**
- target adoption floor: **0.7791**
- retraining reference: **1.0000** (opportunity -1.05pp, epsilon 1pp)
- genealogy: fresh_pretraining (verified); distance unknown
  - model card states trained from scratch; measured copy at or below the no-adapter floor

## Statistics (report half only; gates never see these items)
- reference - frozen: 95% CI [-3.65, +0.00]pp, exact McNemar p = 0.5
- pooled paired evidence (val+test): n=380, reference fixes 1 frozen error(s) and breaks 5 frozen pass(es); 95% CI [-2.6, +0.5]pp -- gains above 0.5pp are excluded by the data
- error-scale view: relative error reduction -133% (3 frozen errors on gate)

## Confidence layer (proper scoring; more power than accuracy)
- paired log-loss, reference - frozen: +0.0475 (95% CI [-0.0001, +0.1072]; negative favors reference)
- calibration ECE: frozen 0.0093, reference 0.0174
- risk-coverage AURC (lower = better selective routing): frozen 0.0002, reference 0.0021

## Disagreement set (COLLECT channel: label these, not more i.i.d. samples)
- 6 disagreement item(s) (1.6% of pooled pairs); exact sign test on labeled outcomes p = 0.2188
- probability the direction settles after labeling k more disagreements -- +10: 56%, +25: 73%, +50: 82%, +100: 87%, +200: 91%

## Robustness under perturbation (typo/casing/filler/punct; gold unchanged)
- frozen: 0.98; reference: 0.9733 (delta -0.67pp)

## Label metrics (macro-F1: class-imbalance-robust; invalid rate: prediction outside the label inventory)
- freeze: macro-F1 **0.9899**, invalid outputs 0.00% (15 classes)
- adopt: macro-F1 **0.7409**, invalid outputs 4.33% (15 classes)
- reference: macro-F1 **0.9775**, invalid outputs 0.67% (15 classes)

## Task ledger: 1 episode(s), 2.6 train GPU-min, 4.1 eval GPU-min, 600 gold labels, 0 teacher queries, 160 validation items accumulated

## Reasoning
- equivalence established, FREEZE is a verdict not a default: the pooled paired CI [-2.6, +0.5]pp excludes any gain above epsilon (1pp) -- n=380 paired records, 1 fixes vs 5 breaks

## Warnings
- gate set has only 80 items; gate sampling error at this size caused the worst episode in the paper's replay -- treat marginal verdicts as ties
- EVAL-SATURATED: the frozen specialist makes only 3 error(s) on the pooled evidence -- any upgrade comparison rests on that many items. Harvest hard/tail examples (e.g. production misroutes) before trusting an upgrade verdict here
- no data_manifest.json -- run `upgrade-advisor manifest` once to pin your splits (Phase 0)

## Before serving
- run `upgrade-advisor gate` for the candidate against the serving records (reporting half only); block on negative-flip budget 3%
- log GPU-minutes and labels consumed for this episode so the amortized decision improves with each release

*Policy and margins from UpgradeBench (2026); validated over 33 measured upgrade episodes (0.37pp mean regret, zero regressions, split-half gating). Negative-flip rate follows Yan et al., Positive-Congruent Training, CVPR 2021. Scope: LoRA-class adapters, 1.5-8B open-weight models.*