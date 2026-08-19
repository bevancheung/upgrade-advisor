# Upgrade recommendation: `workdesk` -> `E:\dataset\models\Qwen3-8B`

## Action: **WAIT** (verdict: unresolved)

## Evidence
- frozen specialist (gate half, n=100): **0.9700**
- target adoption floor: **0.9509**
- retraining reference: **0.9700** (opportunity +0.00pp, epsilon 1pp)
- genealogy: fresh_pretraining (verified); distance unknown
  - path exists but crosses a non-continuation edge (anneal/soup/fresh): copying is not licensed

## Statistics (report half only; gates never see these items)
- reference - frozen: 95% CI [-3.65, +1.46]pp, exact McNemar p = 1.0
- posterior over the true gain (UpgradeBench-corpus prior + paired evidence): mean +0.04pp, sd 0.53pp; P(gain > decision epsilon) = 4%, P(regression beyond epsilon) = 2%, P(within band) = 94%
- pooled paired evidence (val+test): n=400, reference fixes 2 frozen error(s) and breaks 2 frozen pass(es); 95% CI [-1.2, +1.2]pp -- gains above 1.2pp are excluded by the data
- error-scale view: relative error reduction +0% (6 frozen errors on gate)

## Confidence layer (proper scoring; more power than accuracy)
- paired log-loss, reference - frozen: -0.0139 (95% CI [-0.0726, +0.0371]; negative favors reference)
- calibration ECE: frozen 0.0099, reference 0.0108
- risk-coverage AURC (lower = better selective routing): frozen 0.0006, reference 0.0004

## Disagreement set (COLLECT channel: label these, not more i.i.d. samples)
- 5 disagreement item(s) (1.2% of pooled pairs); exact sign test on labeled outcomes p = 1.0
- probability the direction settles after labeling k more disagreements -- +10: 4%, +25: 29%, +50: 50%, +100: 63%, +200: 74%

## Robustness under perturbation (typo/casing/filler/punct; gold unchanged)
- frozen: 0.98; reference: 0.98 (delta +0.00pp)

## Label metrics (macro-F1: class-imbalance-robust; invalid rate: prediction outside the label inventory)
- freeze: macro-F1 **0.9897**, invalid outputs 0.00% (15 classes)
- adopt: macro-F1 **0.8717**, invalid outputs 0.00% (15 classes)
- reference: macro-F1 **0.9898**, invalid outputs 0.00% (15 classes)

## Task ledger: 1 episode(s), 3.2 train GPU-min, 3.6 eval GPU-min, 600 gold labels, 0 teacher queries, 200 validation items accumulated

## Reasoning
- the pooled evidence cannot resolve epsilon: CI [-1.2, +1.2]pp straddles 1pp (n=400, 2 fixes vs 2 breaks; gains above 1.2pp are already excluded; leaning: lean-freeze). Under the UpgradeBench corpus prior the posterior gives the gain a 4% chance of clearing the decision epsilon (1.00pp) -- more evidence is unlikely to change the call, so hold the frozen specialist and revisit at the next release

## Warnings
- gate set has only 100 items; gate sampling error at this size caused the worst episode in the paper's replay -- treat marginal verdicts as ties
- EVAL-SATURATED: the frozen specialist makes only 6 error(s) on the pooled evidence -- any upgrade comparison rests on that many items. Harvest hard/tail examples (e.g. production misroutes) before trusting an upgrade verdict here
- the gate passed but the report-half CI for the upgrade opportunity includes zero -- the gain is not statistically established; consider staying frozen until the next release or enlarging the gate set
- no data_manifest.json -- run `upgrade-advisor manifest` once to pin your splits (Phase 0)

## Before serving
- run `upgrade-advisor gate` for the candidate against the serving records (reporting half only); block on negative-flip budget 3%
- log GPU-minutes and labels consumed for this episode so the amortized decision improves with each release

*Policy and margins from UpgradeBench (2026); validated over 33 measured upgrade episodes (0.37pp mean regret, zero regressions, split-half gating). Negative-flip rate follows Yan et al., Positive-Congruent Training, CVPR 2021. Scope: LoRA-class adapters, 1.5-8B open-weight models.*

[report written to E:\eval project\cases\workdesk_it\episodes\E__dataset__models__Qwen3-8B\recommendation.md]
