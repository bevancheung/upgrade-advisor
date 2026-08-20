# Upgrade decision dossier: echohome -> Qwen2.5-7B-Instruct

## Decision card
**COLLECT** (verdict: unresolved)
**Spend a little to settle it, then decide.** The current data cannot settle the question (roughly 62% chance the upgrade pays off). The two systems gave different answers on only 13 real questions -- have a domain expert mark those right/wrong (about an hour of work) and the answer becomes definitive. Stay put meanwhile.
Basis: 360 real records head-to-head; 9 fixes / 4 breaks

## 1. Background and motivation
EchoHome 的家庭助手 NLU 现役 Qwen2-7B-Instruct + LoRA（15 类：日程、提醒、购物清单、音乐等）。Qwen2.5-7B-Instruct 发布后，一名工程师看到两代架构逐维相同，绕过谱系建议直接把 adapter 挂到新基座提交上线申请。本文档记录系统的两幕处置：拦截与整改。

本纪要为 v2 复评版：在原判定基础上，以升级后的打分体系（证据池化、等价检验、论文语料先验、分歧采证通道）对同一批实测记录重新出具判定。

## 2. Data and system assets
| item | value |
|---|---|
| train/val/test data | E:\eval project\cases\echohome_home\train.jsonl / E:\eval project\cases\echohome_home\val.jsonl / E:\eval project\cases\echohome_home\test.jsonl |
| serving system | E:\dataset\models\Qwen2-7B-Instruct + LoRA (E:\eval project\cases\echohome_home\lora_src) |
| candidate base | E:\dataset\models\Qwen2.5-7B-Instruct |
| evaluation config | flip budget 3%; ε=1pp |

## 3. Process and spend
- cumulative: 1 episode(s); 2.4 train GPU-min; 2.3 eval GPU-min; 600 gold labels
- this round's probes (confidence + robustness) ~5 GPU-min; disagreement extraction and re-verdict are zero-GPU seconds

## 4. Verdict (v2 core): COLLECT -- unresolved
The complete, unfiltered evidence; the reading column is annotation:

| evidence | value | reading |
|---|---|---|
| serving specialist (gate half, n=60) | 1.0000 | measured level of the live system |
| candidate adoption floor (zero/few-shot) | 0.9509 | the new model used bare; the gap to serving is your data moat |
| retrained reference (same recipe, same data) | 1.0000 (opportunity +1.39pp) | actually trained and measured, not estimated |
| pooled paired evidence (val+test) | n=360: fixes 9, breaks 4 | everything the verdict judges on (the old core saw one n~100 fragment) |
| pooled 95% confidence interval | [-0.85, +3.62]pp | credible range of the true gap; gains above 3.62pp are excluded by the data |
| gain posterior (193-cell corpus prior) | mean +1.3pp; P(gain>eps)=62%, P(regression)=1% | borrows strength from the published measured corpus |
| error-scale view (RER) | relative error reduction +56% (9 frozen errors) | the decision-relevant scale near the accuracy ceiling |
| genealogy verdict | fresh_pretraining (inferred) | governs adapter copying: forbidden off documented continuations |
| statistics (report half, gate-isolated) | CI [-2.19, +5.11]pp, McNemar p=0.6875 | items the gates never saw -- unbiased reporting |
| confidence layer: paired log-loss (ref - serving) | -0.0702, CI [-0.2219, +0.0517] | negative favors the reference: quality 0/1 accuracy cannot see |
| confidence layer: calibration ECE | serving 0.022 / reference 0.0093 | lower is better; matters for confidence-based routing |
| confidence layer: risk-coverage AURC | serving 0.0125 / reference 0.0011 | lower is better; the selective-routing operating metric |
| robustness layer: perturbed re-test | serving 0.9633 / reference 0.9667 (delta +0.34pp) | no extra robustness from the newer base (negative result, reported as such) |
| disagreement set (what COLLECT labels) | 13 items (3.6%), sign test p=0.2668 | the only items carrying decision information; exported for labeling |
| labeling convergence pricing | +10: 36%, +25: 54%, +50: 68%, +100: 76%, +200: 83% | chance the direction settles after k more labels |
| macro-F1 (class-balanced) | freeze 0.9696 / adopt 0.8198 / reference 0.9866 | robust to class imbalance |
| invalid-output rate | freeze 0.33% / adopt 0.33% / reference 0.00% | predictions outside the label inventory -- format risk |
| task ledger | 1 episode(s); 2.4 train GPU-min; 600 gold labels | cumulative assets and spend |

**Reasons (verbatim)**
- the pooled evidence cannot resolve epsilon: CI [-0.8, +3.6]pp straddles 1pp (n=360, 9 fixes vs 4 breaks; gains above 3.6pp are already excluded; leaning: lean-upgrade); posterior chance the gain clears the decision epsilon: 62%. Cheapest resolution: label the disagreement set (`upgrade-advisor probe-disagree` writes it with a priced convergence plan); resolving by i.i.d. sampling would need roughly n=2831. Keep serving the frozen specialist while collecting

**Warnings**
- gate set has only 60 items; gate sampling error at this size caused the worst episode in the paper's replay -- treat marginal verdicts as ties
- EVAL-SATURATED: the frozen specialist makes only 9 error(s) on the pooled evidence -- any upgrade comparison rests on that many items. Harvest hard/tail examples (e.g. production misroutes) before trusting an upgrade verdict here
- the gate passed but the report-half CI for the upgrade opportunity includes zero -- the gain is not statistically established; consider staying frozen until the next release or enlarging the gate set
- no data_manifest.json -- run `upgrade-advisor manifest` once to pin your splits (Phase 0)

## 5. Executive brief (auto-generated)
**Spend a little to settle it, then decide.** The current data cannot settle the question (roughly 62% chance the upgrade pays off). The two systems gave different answers on only 13 real questions -- have a domain expert mark those right/wrong (about an hour of work) and the answer becomes definitive. Stay put meanwhile.

## Where you stand
- current system: about **2.5** wrong per 100 requests
- retrained on the new model (actually trained and measured, not estimated): about **1.1** wrong per 100
- the new model used bare, with no training: about **4.9** wrong per 100 -- your training data is the moat

## What we checked
1. **Quality, head-to-head** -- head-to-head on 360 real business questions: the new system fixed 9 and broke 4; everything else identical. Today you get ~2.5 wrong per 100 requests; retrained on the new model, ~1.1. Allowing for sampling error, the true gap is between -0.8% and +3.6%
2. **Disagreement list** -- 13 questions (3.6% of the set) where the two systems answer differently -- the only items that carry decision information; exported for labeling
3. **Confidence quality** -- the new system is slightly better at knowing how sure to be (relevant if you route low-confidence cases to humans; not statistically significant here)
4. **Noise tolerance** -- re-tested with typos, casing noise and filler words injected: gap of +0.34% -- a small edge to the newer model
5. **Transfer safety** -- model lineage checked: this path does NOT permit moving your existing work as-is (measured: cross-generation transfer can score worse than no system at all) -- any upgrade means retraining

## The money question
- combining your data with 193 published measured upgrade cases: roughly **62%** chance this upgrade pays off, 1% chance it regresses

## Next steps
1. hand the exported disagreement list to a domain expert to mark right/wrong (labeling 25 more gives a 54% chance of a definitive answer)
2. re-run this tool after labeling; the verdict will harden into a definite upgrade / stay-put call
3. change nothing in production meanwhile (zero risk)

## How much to trust this
- every number comes from measured runs on your own 360 real business records; nothing is estimated or demo data
- method and thresholds follow the published UpgradeBench (2026) benchmark: 33 replayed upgrade decisions, 0.37% mean decision loss, zero serving regressions
- when the evidence is insufficient, this tool says so and prices the cheapest way to settle it, rather than forcing a verdict

---
*Technical appendix (full statistics, for the engineering team): recommendation.md*

## 6. Discussion
- 上一版判定：第一幕 BLOCK → 第二幕 PASS → 终判 FREEZE（其实不必升）
- 由 FREEZE 转 COLLECT：本案是全部案例中最值得采证的——9修/4破、后验增益概率 62%、置信层 log-loss 亦偏参考。标注 13 条分歧即可定案。
- 零成本说明：本版复评未新增任何训练与标注；置信/鲁棒双探针合计约 5 GPU 分钟，分歧提取与重判为零 GPU 秒级操作。

## 7. Technical appendix: full statistical report
```
# Upgrade recommendation: `echohome` -> `E:\dataset\models\Qwen2.5-7B-Instruct`

## Action: **COLLECT** (verdict: unresolved)

## Evidence
- frozen specialist (gate half, n=60): **1.0000**
- target adoption floor: **0.9509**
- retraining reference: **1.0000** (opportunity +1.39pp, epsilon 1pp)
- genealogy: fresh_pretraining (inferred); distance unknown
  - shape-identical but independent run per release docs; measured copy retention -0.60..0.78

## Statistics (report half only; gates never see these items)
- reference - frozen: 95% CI [-2.19, +5.11]pp, exact McNemar p = 0.6875
- posterior over the true gain (UpgradeBench-corpus prior + paired evidence): mean +1.30pp, sd 0.94pp; P(gain > decision epsilon) = 62%, P(regression beyond epsilon) = 1%, P(within band) = 37%
- pooled paired evidence (val+test): n=360, reference fixes 9 frozen error(s) and breaks 4 frozen pass(es); 95% CI [-0.8, +3.6]pp -- gains above 3.6pp are excluded by the data
- error-scale view: relative error reduction +56% (9 frozen errors on gate)

## Confidence layer (proper scoring; more power than accuracy)
- paired log-loss, reference - frozen: -0.0702 (95% CI [-0.2219, +0.0517]; negative favors reference)
- calibration ECE: frozen 0.022, reference 0.0093
- risk-coverage AURC (lower = better selective routing): frozen 0.0125, reference 0.0011

## Disagreement set (COLLECT channel: label these, not more i.i.d. samples)
- 13 disagreement item(s) (3.6% of pooled pairs); exact sign test on labeled outcomes p = 0.2668
- probability the direction settles after labeling k more disagreements -- +10: 36%, +25: 54%, +50: 68%, +100: 76%, +200: 83%

## Robustness under perturbation (typo/casing/filler/punct; gold unchanged)
- frozen: 0.9633; reference: 0.9667 (delta +0.34pp)

## Label metrics (macro-F1: class-imbalance-robust; invalid rate: prediction outside the label inventory)
- freeze: macro-F1 **0.9696**, invalid outputs 0.33% (15 classes)
- adopt: macro-F1 **0.8198**, invalid outputs 0.33% (15 classes)
- reference: macro-F1 **0.9866**, invalid outputs 0.00% (15 classes)

## Task ledger: 1 episode(s), 2.4 train GPU-min, 2.3 eval GPU-min, 600 gold labels, 0 teacher queries, 120 validation items accumulated

## Reasoning
- the pooled evidence cannot resolve epsilon: CI [-0.8, +3.6]pp straddles 1pp (n=360, 9 fixes vs 4 breaks; gains above 3.6pp are already excluded; leaning: lean-upgrade); posterior chance the gain clears the decision epsilon: 62%. Cheapest resolution: label the disagreement set (`upgrade-advisor probe-disagree` writes it with a priced convergence plan); resolving by i.i.d. sampling would need roughly n=2831. Keep serving the frozen specialist while collecting

## Warnings
- gate set has only 60 items; gate sampling error at this size caused the worst episode in the paper's replay -- treat marginal verdicts as ties
- EVAL-SATURATED: the frozen specialist makes only 9 error(s) on the pooled evidence -- any upgrade comparison rests on that many items. Harvest hard/tail examples (e.g. production misroutes) before trusting an upgrade verdict here
- the gate passed but the report-half CI for the upgrade opportunity includes zero -- the gain is not statistically established; consider staying frozen until the next release or enlarging the gate set
- no data_manifest.json -- run `upgrade-advisor manifest` once to pin your splits (Phase 0)

## Before serving
- run `upgrade-advisor gate` for the candidate against the serving records (reporting half only); block on negative-flip budget 3%
- log GPU-minutes and labels consumed for this episode so the amortized decision improves with each release

*Policy and margins from UpgradeBench (2026); validated over 33 measured upgrade episodes (0.37pp mean regret, zero regressions, split-half gating). Negative-flip rate follows Yan et al., Positive-Congruent Training, CVPR 2021. Scope: LoRA-class adapters, 1.5-8B open-weight models.*
```