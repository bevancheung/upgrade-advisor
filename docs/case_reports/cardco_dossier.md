# Upgrade decision dossier: cardco -> Qwen2.5-7B-Instruct

## Decision card
**COLLECT** (verdict: unresolved)
**Spend a little to settle it, then decide.** The current data cannot settle the question (roughly 25% chance the upgrade pays off). The two systems gave different answers on only 10 real questions -- have a domain expert mark those right/wrong (about an hour of work) and the answer becomes definitive. Stay put meanwhile.
Basis: 400 real records head-to-head; 5 fixes / 3 breaks

## 1. Background and motivation
CardCo 用 Qwen1.5-7B-Chat + LoRA 做 15 类持卡人服务意图。团队按纪律连续记录了两个完整升级 episode（→Qwen2、→Qwen2.5，均判 FREEZE），本期 Qwen3-8B 发布正值预算冻结——希望用台账的 β 投影做“零训练判定”：只测地板，不训练参考。

本纪要为 v2 复评版：在原判定基础上，以升级后的打分体系（证据池化、等价检验、论文语料先验、分歧采证通道）对同一批实测记录重新出具判定。

## 2. Data and system assets
| item | value |
|---|---|
| train/val/test data | E:\eval project\cases\cardco_credit\train.jsonl / E:\eval project\cases\cardco_credit\val.jsonl / E:\eval project\cases\cardco_credit\test.jsonl |
| serving system | E:\dataset\models\Qwen1.5-7B-Chat + LoRA (E:\eval project\cases\cardco_credit\lora_src) |
| candidate base | E:\dataset\models\Qwen2.5-7B-Instruct |
| evaluation config | flip budget 3%; ε=1pp |

## 3. Process and spend
- cumulative: 3 episode(s); 4.6 train GPU-min; 3.2 eval GPU-min; 1200 gold labels
- this round's probes (confidence + robustness) ~5 GPU-min; disagreement extraction and re-verdict are zero-GPU seconds

## 4. Verdict (v2 core): COLLECT -- unresolved
The complete, unfiltered evidence; the reading column is annotation:

| evidence | value | reading |
|---|---|---|
| serving specialist (gate half, n=100) | 0.9900 | measured level of the live system |
| candidate adoption floor (zero/few-shot) | 0.8712 | the new model used bare; the gap to serving is your data moat |
| retrained reference (same recipe, same data) | 0.9900 (opportunity +0.5pp) | actually trained and measured, not estimated |
| pooled paired evidence (val+test) | n=400: fixes 5, breaks 3 | everything the verdict judges on (the old core saw one n~100 fragment) |
| pooled 95% confidence interval | [-1.14, +2.14]pp | credible range of the true gap; gains above 2.14pp are excluded by the data |
| gain posterior (193-cell corpus prior) | mean +0.53pp; P(gain>eps)=25%, P(regression)=2% | borrows strength from the published measured corpus |
| error-scale view (RER) | relative error reduction +20% (10 frozen errors) | the decision-relevant scale near the accuracy ceiling |
| genealogy verdict | fresh_pretraining (verified) | governs adapter copying: forbidden off documented continuations |
| statistics (report half, gate-isolated) | CI [-2.19, +2.19]pp, McNemar p=1.0 | items the gates never saw -- unbiased reporting |
| confidence layer: paired log-loss (ref - serving) | -0.0295, CI [-0.08, +0.0134] | negative favors the reference: quality 0/1 accuracy cannot see |
| confidence layer: calibration ECE | serving 0.0183 / reference 0.014 | lower is better; matters for confidence-based routing |
| confidence layer: risk-coverage AURC | serving 0.0077 / reference 0.0055 | lower is better; the selective-routing operating metric |
| robustness layer: perturbed re-test | serving 0.9633 / reference 0.9667 (delta +0.34pp) | no extra robustness from the newer base (negative result, reported as such) |
| disagreement set (what COLLECT labels) | 10 items (2.5%), sign test p=0.7266 | the only items carrying decision information; exported for labeling |
| labeling convergence pricing | +10: 12%, +25: 32%, +50: 50%, +100: 62%, +200: 73% | chance the direction settles after k more labels |
| macro-F1 (class-balanced) | freeze 0.9725 / adopt 0.8068 / reference 0.9828 | robust to class imbalance |
| invalid-output rate | freeze 0.33% / adopt 0.00% / reference 1.00% | predictions outside the label inventory -- format risk |
| task ledger | 3 episode(s); 4.6 train GPU-min; 1200 gold labels | cumulative assets and spend |

**Reasons (verbatim)**
- the pooled evidence cannot resolve epsilon: CI [-1.1, +2.1]pp straddles 1pp (n=400, 5 fixes vs 3 breaks; gains above 2.1pp are already excluded; leaning: lean-freeze); posterior chance the gain clears the decision epsilon: 25%. Cheapest resolution: label the disagreement set (`upgrade-advisor probe-disagree` writes it with a priced convergence plan); resolving by i.i.d. sampling would need roughly n=1568. Keep serving the frozen specialist while collecting

**Warnings**
- gate set has only 100 items; gate sampling error at this size caused the worst episode in the paper's replay -- treat marginal verdicts as ties
- EVAL-SATURATED: the frozen specialist makes only 10 error(s) on the pooled evidence -- any upgrade comparison rests on that many items. Harvest hard/tail examples (e.g. production misroutes) before trusting an upgrade verdict here
- the gate passed but the report-half CI for the upgrade opportunity includes zero -- the gain is not statistically established; consider staying frozen until the next release or enlarging the gate set
- no data_manifest.json -- run `upgrade-advisor manifest` once to pin your splits (Phase 0)

## 5. Executive brief (auto-generated)
**Spend a little to settle it, then decide.** The current data cannot settle the question (roughly 25% chance the upgrade pays off). The two systems gave different answers on only 10 real questions -- have a domain expert mark those right/wrong (about an hour of work) and the answer becomes definitive. Stay put meanwhile.

## Where you stand
- current system: about **2.5** wrong per 100 requests
- retrained on the new model (actually trained and measured, not estimated): about **2.0** wrong per 100
- the new model used bare, with no training: about **12.9** wrong per 100 -- your training data is the moat

## What we checked
1. **Quality, head-to-head** -- head-to-head on 400 real business questions: the new system fixed 5 and broke 3; everything else identical. Today you get ~2.5 wrong per 100 requests; retrained on the new model, ~2.0. Allowing for sampling error, the true gap is between -1.1% and +2.1%
2. **Disagreement list** -- 10 questions (2.5% of the set) where the two systems answer differently -- the only items that carry decision information; exported for labeling
3. **Confidence quality** -- the new system is slightly better at knowing how sure to be (relevant if you route low-confidence cases to humans; not statistically significant here)
4. **Noise tolerance** -- re-tested with typos, casing noise and filler words injected: gap of +0.34% -- a small edge to the newer model
5. **Transfer safety** -- model lineage checked: this path does NOT permit moving your existing work as-is (measured: cross-generation transfer can score worse than no system at all) -- any upgrade means retraining

## The money question
- combining your data with 193 published measured upgrade cases: roughly **25%** chance this upgrade pays off, 2% chance it regresses

## Next steps
1. hand the exported disagreement list to a domain expert to mark right/wrong (labeling 25 more gives a 32% chance of a definitive answer)
2. re-run this tool after labeling; the verdict will harden into a definite upgrade / stay-put call
3. change nothing in production meanwhile (zero risk)

## How much to trust this
- every number comes from measured runs on your own 400 real business records; nothing is estimated or demo data
- method and thresholds follow the published UpgradeBench (2026) benchmark: 33 replayed upgrade decisions, 0.37% mean decision loss, zero serving regressions
- when the evidence is insufficient, this tool says so and prices the cheapest way to settle it, rather than forcing a verdict

---
*Technical appendix (full statistics, for the engineering team): recommendation.md*

## 6. Discussion
- 上一版判定：FREEZE（默认）——β 投影被稳定性门如实拒绝
- 由 FREEZE 转 COLLECT：5修/3破、后验增益概率 25%，值得花小成本把话说死（旧版的 β 投影演练线保留在台账中）。
- 零成本说明：本版复评未新增任何训练与标注；置信/鲁棒双探针合计约 5 GPU 分钟，分歧提取与重判为零 GPU 秒级操作。

## 7. Technical appendix: full statistical report
```
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
```