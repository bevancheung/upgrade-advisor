# Upgrade recommendation: `tripfun` -> `E:\dataset\models\Qwen2.5-1.5B-Instruct`

## Action: **FREEZE** (verdict: equivalence)

## Evidence
- frozen specialist (gate half, n=100): **0.9900**
- target adoption floor: **0.8712**
- retraining reference: **1.0000** (opportunity +0.00pp, epsilon 1pp)
- genealogy: fresh_pretraining (inferred); distance unknown
  - shape-identical independent run; paper measured copy retention -0.60..0.10 at this scale

## Statistics (report half only; gates never see these items)
- reference - frozen: 95% CI [+0.00, +0.00]pp, exact McNemar p = 1.0
- pooled paired evidence (val+test): n=400, reference fixes 1 frozen error(s) and breaks 1 frozen pass(es); 95% CI [-0.9, +0.9]pp -- gains above 0.9pp are excluded by the data
- error-scale view: relative error reduction +0% (2 frozen errors on gate)

## Confidence layer (proper scoring; more power than accuracy)
- paired log-loss, reference - frozen: +0.0315 (95% CI [+0.0002, +0.0870]; negative favors reference)
- calibration ECE: frozen 0.0018, reference 0.007
- risk-coverage AURC (lower = better selective routing): frozen 0.0, reference 0.0001

## Disagreement set (COLLECT channel: label these, not more i.i.d. samples)
- 2 disagreement item(s) (0.5% of pooled pairs); exact sign test on labeled outcomes p = 1.0
- probability the direction settles after labeling k more disagreements -- +10: 22%, +25: 38%, +50: 58%, +100: 70%, +200: 79%

## Robustness under perturbation (typo/casing/filler/punct; gold unchanged)
- frozen: 1.0; reference: 0.9833 (delta -1.67pp)

## Label metrics (macro-F1: class-imbalance-robust; invalid rate: prediction outside the label inventory)
- freeze: macro-F1 **0.9968**, invalid outputs 0.00% (15 classes)
- adopt: macro-F1 **0.8712**, invalid outputs 3.00% (15 classes)
- reference: macro-F1 **0.9938**, invalid outputs 0.00% (15 classes)

## Task ledger: 1 episode(s), 2.4 train GPU-min, 1.6 eval GPU-min, 600 gold labels, 0 teacher queries, 200 validation items accumulated

## Reasoning
- equivalence established, FREEZE is a verdict not a default: the pooled paired CI [-0.9, +0.9]pp excludes any gain above epsilon (1pp) -- n=400 paired records, 1 fixes vs 1 breaks

## Warnings
- gate set has only 100 items; gate sampling error at this size caused the worst episode in the paper's replay -- treat marginal verdicts as ties
- EVAL-SATURATED: the frozen specialist makes only 2 error(s) on the pooled evidence -- any upgrade comparison rests on that many items. Harvest hard/tail examples (e.g. production misroutes) before trusting an upgrade verdict here
- no data_manifest.json -- run `upgrade-advisor manifest` once to pin your splits (Phase 0)

## Before serving
- run `upgrade-advisor gate` for the candidate against the serving records (reporting half only); block on negative-flip budget 3%
- log GPU-minutes and labels consumed for this episode so the amortized decision improves with each release

*Policy and margins from UpgradeBench (2026); validated over 33 measured upgrade episodes (0.37pp mean regret, zero regressions, split-half gating). Negative-flip rate follows Yan et al., Positive-Congruent Training, CVPR 2021. Scope: LoRA-class adapters, 1.5-8B open-weight models.*

[report written to E:\eval project\cases\tripfun_travel\episodes\E__dataset__models__Qwen2.5-1.5B-Instruct\recommendation.md]
