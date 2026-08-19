# Upgrade recommendation: `newsdesk` -> `E:\dataset\models\Qwen2.5-7B-Instruct-1M`

## Action: **FREEZE** (verdict: equivalence)

## Evidence
- frozen specialist (gate half, n=100): **0.9000**
- target adoption floor: **0.8465**
- retraining reference: **0.9000** (opportunity -0.40pp, epsilon 1pp)
- copied adapter: **0.9100** (NFR vs serving: 1.86%)
- genealogy: continuation (inferred); continuation 20B tokens
  - long-context extension of the same weights; measured copy retention 0.82-1.45

## Statistics (report half only; gates never see these items)
- reference - frozen: 95% CI [-1.62, +1.62]pp, exact McNemar p = 1.0
- copy - reference: 95% CI [-2.70, +1.08]pp, p = 1.0
- pooled paired evidence (val+test): n=500, reference fixes 2 frozen error(s) and breaks 4 frozen pass(es); 95% CI [-1.6, +0.8]pp -- gains above 0.8pp are excluded by the data
- error-scale view: relative error reduction -5% (39 frozen errors on gate)

## Confidence layer (proper scoring; more power than accuracy)
- paired log-loss, reference - frozen: -0.0163 (95% CI [-0.0368, +0.0028]; negative favors reference)
- calibration ECE: frozen 0.0533, reference 0.0382
- risk-coverage AURC (lower = better selective routing): frozen 0.0431, reference 0.0347

## Disagreement set (COLLECT channel: label these, not more i.i.d. samples)
- 7 disagreement item(s) (1.4% of pooled pairs); exact sign test on labeled outcomes p = 0.6875
- probability the direction settles after labeling k more disagreements -- +10: 16%, +25: 39%, +50: 57%, +100: 68%, +200: 77%

## Robustness under perturbation (typo/casing/filler/punct; gold unchanged)
- frozen: 0.9275; reference: 0.9225 (delta -0.50pp)

## Label metrics (macro-F1: class-imbalance-robust; invalid rate: prediction outside the label inventory)
- freeze: macro-F1 **0.9257**, invalid outputs 0.00% (4 classes)
- adopt: macro-F1 **0.8297**, invalid outputs 0.00% (4 classes)
- reference: macro-F1 **0.9209**, invalid outputs 0.00% (4 classes)
- copy: macro-F1 **0.9132**, invalid outputs 0.00% (4 classes)

## Task ledger: 1 episode(s), 5.4 train GPU-min, 3.4 eval GPU-min, 800 gold labels, 0 teacher queries, 200 validation items accumulated

## Reasoning
- equivalence established, FREEZE is a verdict not a default: the pooled paired CI [-1.6, +0.8]pp excludes any gain above epsilon (1pp) -- n=500 paired records, 2 fixes vs 4 breaks

## Warnings
- gate set has only 100 items; gate sampling error at this size caused the worst episode in the paper's replay -- treat marginal verdicts as ties
- no data_manifest.json -- run `upgrade-advisor manifest` once to pin your splits (Phase 0)

## Before serving
- run `upgrade-advisor gate` for the candidate against the serving records (reporting half only); block on negative-flip budget 3%
- log GPU-minutes and labels consumed for this episode so the amortized decision improves with each release

*Policy and margins from UpgradeBench (2026); validated over 33 measured upgrade episodes (0.37pp mean regret, zero regressions, split-half gating). Negative-flip rate follows Yan et al., Positive-Congruent Training, CVPR 2021. Scope: LoRA-class adapters, 1.5-8B open-weight models.*

[report written to E:\eval project\cases\newsdesk_agnews\episodes\E__dataset__models__Qwen2.5-7B-Instruct-1M\recommendation.md]
