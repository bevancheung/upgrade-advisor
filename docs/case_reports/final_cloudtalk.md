# Upgrade recommendation: `cloudtalk` -> `E:\dataset\models\Qwen2.5-7B-Instruct`

## Action: **FREEZE** (verdict: equivalence)

## Evidence
- frozen specialist (gate half, n=200): **0.4250**
- target adoption floor: **0.2095**
- retraining reference: **0.4250** (opportunity +0.67pp, epsilon 2pp)
- genealogy: fresh_pretraining (verified); distance unknown
  - path exists but crosses a non-continuation edge (anneal/soup/fresh): copying is not licensed

## Statistics (report half only; gates never see these items)
- reference - frozen: 95% CI [-0.93, +3.41]pp, exact McNemar p = 0.3877
- pooled paired evidence (val+test): n=900, reference fixes 18 frozen error(s) and breaks 12 frozen pass(es); 95% CI [-0.6, +2.0]pp -- gains above 2.0pp are excluded by the data
- error-scale view: relative error reduction +1% (487 frozen errors on gate)

## Disagreement set (COLLECT channel: label these, not more i.i.d. samples)
- 90 disagreement item(s) (10.0% of pooled pairs); exact sign test on labeled outcomes p = 0.3616
- probability the direction settles after labeling k more disagreements -- +10: 7%, +25: 21%, +50: 38%, +100: 55%, +200: 66%

## Task ledger: 1 episode(s), 18.4 train GPU-min, 10.2 eval GPU-min, 2000 gold labels, 0 teacher queries, 400 validation items accumulated

## Reasoning
- equivalence established, FREEZE is a verdict not a default: the pooled paired CI [-0.6, +2.0]pp excludes any gain above epsilon (2pp) -- n=900 paired records, 18 fixes vs 12 breaks

## Warnings
- gate set has only 200 items; gate sampling error at this size caused the worst episode in the paper's replay -- treat marginal verdicts as ties
- no data_manifest.json -- run `upgrade-advisor manifest` once to pin your splits (Phase 0)

## Before serving
- run `upgrade-advisor gate` for the candidate against the serving records (reporting half only); block on negative-flip budget 5%
- log GPU-minutes and labels consumed for this episode so the amortized decision improves with each release

*Policy and margins from UpgradeBench (2026); validated over 33 measured upgrade episodes (0.37pp mean regret, zero regressions, split-half gating). Negative-flip rate follows Yan et al., Positive-Congruent Training, CVPR 2021. Scope: LoRA-class adapters, 1.5-8B open-weight models.*

[report written to E:\eval project\snips_slots\episodes_cloudtalk\E__dataset__models__Qwen2.5-7B-Instruct\recommendation.md]
