# Upgrade recommendation: `fintone_card_routing` -> `E:\dataset\models\Qwen2.5-7B-Instruct`

## Action: **WAIT** (verdict: unresolved)

## Evidence
- frozen specialist (gate half, n=100): **0.9100**
- target adoption floor: **0.7730**
- retraining reference: **0.8800** (opportunity -1.00pp, epsilon 1pp)
- genealogy: fresh_pretraining (inferred); distance unknown
  - shape-identical but independent run per release docs; measured copy retention -0.60..0.78

## Statistics (report half only; gates never see these items)
- reference - frozen: 95% CI [-0.73, +5.84]pp, exact McNemar p = 0.375
- posterior over the true gain (UpgradeBench-corpus prior + paired evidence): mean -0.67pp, sd 1.03pp; P(gain > decision epsilon) = 5%, P(regression beyond epsilon) = 37%, P(within band) = 57%
- pooled paired evidence (val+test): n=400, reference fixes 8 frozen error(s) and breaks 12 frozen pass(es); 95% CI [-3.4, +1.4]pp -- gains above 1.4pp are excluded by the data
- error-scale view: relative error reduction -12% (32 frozen errors on gate)

## Confidence layer (proper scoring; more power than accuracy)
- paired log-loss, reference - frozen: -0.0523 (95% CI [-0.1521, +0.0252]; negative favors reference)
- calibration ECE: frozen 0.0322, reference 0.0331
- risk-coverage AURC (lower = better selective routing): frozen 0.018, reference 0.0109

## Disagreement set (COLLECT channel: label these, not more i.i.d. samples)
- 22 disagreement item(s) (5.5% of pooled pairs); exact sign test on labeled outcomes p = 0.5034
- probability the direction settles after labeling k more disagreements -- +10: 7%, +25: 23%, +50: 40%, +100: 52%, +200: 65%

## Robustness under perturbation (typo/casing/filler/punct; gold unchanged)
- frozen: 0.92; reference: 0.9167 (delta -0.33pp)

## Label metrics (macro-F1: class-imbalance-robust; invalid rate: prediction outside the label inventory)
- freeze: macro-F1 **0.924**, invalid outputs 1.00% (20 classes)
- adopt: macro-F1 **0.703**, invalid outputs 0.67% (20 classes)
- reference: macro-F1 **0.9214**, invalid outputs 1.00% (20 classes)

## Task ledger: 1 episode(s), 2.8 train GPU-min, 3.8 eval GPU-min, 500 gold labels, 0 teacher queries, 200 validation items accumulated

## Reasoning
- the pooled evidence cannot resolve epsilon: CI [-3.4, +1.4]pp straddles 1pp (n=400, 8 fixes vs 12 breaks; gains above 1.4pp are already excluded; leaning: lean-freeze). Under the UpgradeBench corpus prior the posterior gives the gain a 5% chance of clearing the decision epsilon (1.00pp) -- more evidence is unlikely to change the call, so hold the frozen specialist and revisit at the next release

## Warnings
- gate set has only 100 items; gate sampling error at this size caused the worst episode in the paper's replay -- treat marginal verdicts as ties
- the gate passed but the report-half CI for the upgrade opportunity includes zero -- the gain is not statistically established; consider staying frozen until the next release or enlarging the gate set
- no data_manifest.json -- run `upgrade-advisor manifest` once to pin your splits (Phase 0)

## Before serving
- run `upgrade-advisor gate` for the candidate against the serving records (reporting half only); block on negative-flip budget 3%
- log GPU-minutes and labels consumed for this episode so the amortized decision improves with each release

*Policy and margins from UpgradeBench (2026); validated over 33 measured upgrade episodes (0.37pp mean regret, zero regressions, split-half gating). Negative-flip rate follows Yan et al., Positive-Congruent Training, CVPR 2021. Scope: LoRA-class adapters, 1.5-8B open-weight models.*

[report written to E:\eval project\fintone\episodes\E__dataset__models__Qwen2.5-7B-Instruct\recommendation.md]
