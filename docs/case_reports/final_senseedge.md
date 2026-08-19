# Upgrade recommendation: `senseedge` -> `E:\dataset\models\Qwen2.5-1.5B-Instruct`

## Action: **COLLECT** (verdict: unresolved)

## Evidence
- frozen specialist (gate half, n=100): **0.9700**
- target adoption floor: **0.7975**
- retraining reference: **0.9600** (opportunity +0.50pp, epsilon 1pp)
- genealogy: unknown (unknown); distance unknown
  - pair not in registry

## Statistics (report half only; gates never see these items)
- reference - frozen: 95% CI [-1.46, +3.65]pp, exact McNemar p = 1.0
- pooled paired evidence (val+test): n=400, reference fixes 6 frozen error(s) and breaks 4 frozen pass(es); 95% CI [-1.3, +2.3]pp -- gains above 2.3pp are excluded by the data
- error-scale view: relative error reduction +15% (13 frozen errors on gate)

## Confidence layer (proper scoring; more power than accuracy)
- paired log-loss, reference - frozen: +0.0179 (95% CI [-0.0444, +0.1081]; negative favors reference)
- calibration ECE: frozen 0.0232, reference 0.0171
- risk-coverage AURC (lower = better selective routing): frozen 0.0011, reference 0.003

## Disagreement set (COLLECT channel: label these, not more i.i.d. samples)
- 10 disagreement item(s) (2.5% of pooled pairs); exact sign test on labeled outcomes p = 0.7539
- probability the direction settles after labeling k more disagreements -- +10: 9%, +25: 27%, +50: 39%, +100: 58%, +200: 69%

## Robustness under perturbation (typo/casing/filler/punct; gold unchanged)
- frozen: 0.95; reference: 0.95 (delta +0.00pp)

## Label metrics (macro-F1: class-imbalance-robust; invalid rate: prediction outside the label inventory)
- freeze: macro-F1 **0.9679**, invalid outputs 0.00% (13 classes)
- adopt: macro-F1 **0.7648**, invalid outputs 1.67% (13 classes)
- reference: macro-F1 **0.9764**, invalid outputs 0.00% (13 classes)

## Task ledger: 1 episode(s), 1.2 train GPU-min, 1.4 eval GPU-min, 600 gold labels, 0 teacher queries, 200 validation items accumulated

## Reasoning
- the pooled evidence cannot resolve epsilon: CI [-1.3, +2.3]pp straddles 1pp (n=400, 6 fixes vs 4 breaks; gains above 2.3pp are already excluded; leaning: lean-freeze). Cheapest resolution: label the disagreement set (`upgrade-advisor probe-disagree` writes it with a priced convergence plan); resolving by i.i.d. sampling would need roughly n=1960. Keep serving the frozen specialist while collecting

## Warnings
- gate set has only 100 items; gate sampling error at this size caused the worst episode in the paper's replay -- treat marginal verdicts as ties
- EVAL-SATURATED: the frozen specialist makes only 13 error(s) on the pooled evidence -- any upgrade comparison rests on that many items. Harvest hard/tail examples (e.g. production misroutes) before trusting an upgrade verdict here
- the gate passed but the report-half CI for the upgrade opportunity includes zero -- the gain is not statistically established; consider staying frozen until the next release or enlarging the gate set
- no data_manifest.json -- run `upgrade-advisor manifest` once to pin your splits (Phase 0)

## Before serving
- run `upgrade-advisor gate` for the candidate against the serving records (reporting half only); block on negative-flip budget 3%
- log GPU-minutes and labels consumed for this episode so the amortized decision improves with each release

*Policy and margins from UpgradeBench (2026); validated over 33 measured upgrade episodes (0.37pp mean regret, zero regressions, split-half gating). Negative-flip rate follows Yan et al., Positive-Congruent Training, CVPR 2021. Scope: LoRA-class adapters, 1.5-8B open-weight models.*

[report written to E:\eval project\cases\senseedge_meta\episodes\E__dataset__models__Qwen2.5-1.5B-Instruct\recommendation.md]
