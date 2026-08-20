# Upgrade decision dossier: dineco -> Qwen2-7B-Instruct

## Decision card
**WAIT** (verdict: unresolved)
**Skip this generation.** Combining your data with 193 published measured cases, this upgrade has only a 5% chance of paying off. Not worth further verification spend; stay put and re-evaluate at the next release.
Basis: 360 real records head-to-head; 3 fixes / 4 breaks

## 1. Background and motivation
DineCo 用 Qwen1.5-7B-Chat（2024 年初老栈）+ LoRA 做 15 类餐饮服务意图（订位、菜谱、营养、外卖等）。Qwen2-7B-Instruct 发布后评估。本案例把 REFRESH 路径全流程实测（教师重标 600 条 → 学生训练 → 入门控），是判定瀑布四个动作首次全部有实测数据在场。

本纪要为 v2 复评版：在原判定基础上，以升级后的打分体系（证据池化、等价检验、论文语料先验、分歧采证通道）对同一批实测记录重新出具判定。

## 2. Data and system assets
| item | value |
|---|---|
| train/val/test data | E:\eval project\cases\dineco_dining\train.jsonl / E:\eval project\cases\dineco_dining\val.jsonl / E:\eval project\cases\dineco_dining\test.jsonl |
| serving system | E:\dataset\models\Qwen1.5-7B-Chat + LoRA (E:\eval project\cases\dineco_dining\lora_src) |
| candidate base | E:\dataset\models\Qwen2-7B-Instruct |
| evaluation config | flip budget 3%; ε=1pp |

## 3. Process and spend
- cumulative: 1 episode(s); 5.0 train GPU-min; 2.4 eval GPU-min; 600 gold labels
- this round's probes (confidence + robustness) ~5 GPU-min; disagreement extraction and re-verdict are zero-GPU seconds

## 4. Verdict (v2 core): WAIT -- unresolved
The complete, unfiltered evidence; the reading column is annotation:

| evidence | value | reading |
|---|---|---|
| serving specialist (gate half, n=60) | 0.9667 | measured level of the live system |
| candidate adoption floor (zero/few-shot) | 0.8098 | the new model used bare; the gap to serving is your data moat |
| retrained reference (same recipe, same data) | 0.9667 (opportunity -0.28pp) | actually trained and measured, not estimated |
| pooled paired evidence (val+test) | n=360: fixes 3, breaks 4 | everything the verdict judges on (the old core saw one n~100 fragment) |
| pooled 95% confidence interval | [-2.0, +1.44]pp | credible range of the true gap; gains above 1.44pp are excluded by the data |
| gain posterior (193-cell corpus prior) | mean -0.18pp; P(gain>eps)=5%, P(regression)=13% | borrows strength from the published measured corpus |
| error-scale view (RER) | relative error reduction -7% (15 frozen errors) | the decision-relevant scale near the accuracy ceiling |
| genealogy verdict | fresh_pretraining (inferred) | governs adapter copying: forbidden off documented continuations |
| statistics (report half, gate-isolated) | CI [-2.19, +2.19]pp, McNemar p=1.0 | items the gates never saw -- unbiased reporting |
| confidence layer: paired log-loss (ref - serving) | +0.052, CI [-0.0346, +0.1491] | the serving system's confidence holds up |
| confidence layer: calibration ECE | serving 0.0228 / reference 0.0318 | lower is better; matters for confidence-based routing |
| confidence layer: risk-coverage AURC | serving 0.0078 / reference 0.0076 | lower is better; the selective-routing operating metric |
| robustness layer: perturbed re-test | serving 0.9533 / reference 0.9533 (delta +0.0pp) | no extra robustness from the newer base (negative result, reported as such) |
| disagreement set (what COLLECT labels) | 11 items (3.1%), sign test p=1.0 | the only items carrying decision information; exported for labeling |
| labeling convergence pricing | +10: 10%, +25: 21%, +50: 41%, +100: 56%, +200: 69% | chance the direction settles after k more labels |
| macro-F1 (class-balanced) | freeze 0.9568 / adopt 0.7498 / reference 0.9543 / refresh 0.9576 | robust to class imbalance |
| invalid-output rate | freeze 0.00% / adopt 0.00% / reference 0.00% / refresh 0.33% | predictions outside the label inventory -- format risk |
| task ledger | 1 episode(s); 5.0 train GPU-min; 600 gold labels | cumulative assets and spend |

**Reasons (verbatim)**
- the pooled evidence cannot resolve epsilon: CI [-2.0, +1.4]pp straddles 1pp (n=360, 3 fixes vs 4 breaks; gains above 1.4pp are already excluded; leaning: lean-freeze). Under the UpgradeBench corpus prior the posterior gives the gain a 5% chance of clearing the decision epsilon (1.00pp) -- more evidence is unlikely to change the call, so hold the frozen specialist and revisit at the next release

**Warnings**
- gate set has only 60 items; gate sampling error at this size caused the worst episode in the paper's replay -- treat marginal verdicts as ties
- EVAL-SATURATED: the frozen specialist makes only 15 error(s) on the pooled evidence -- any upgrade comparison rests on that many items. Harvest hard/tail examples (e.g. production misroutes) before trusting an upgrade verdict here
- the gate passed but the report-half CI for the upgrade opportunity includes zero -- the gain is not statistically established; consider staying frozen until the next release or enlarging the gate set
- no data_manifest.json -- run `upgrade-advisor manifest` once to pin your splits (Phase 0)

## 5. Executive brief (auto-generated)
**Skip this generation.** Combining your data with 193 published measured cases, this upgrade has only a 5% chance of paying off. Not worth further verification spend; stay put and re-evaluate at the next release.

## Where you stand
- current system: about **4.2** wrong per 100 requests
- retrained on the new model (actually trained and measured, not estimated): about **4.4** wrong per 100
- the new model used bare, with no training: about **19.0** wrong per 100 -- your training data is the moat

## What we checked
1. **Quality, head-to-head** -- head-to-head on 360 real business questions: the new system fixed 3 and broke 4; everything else identical. Today you get ~4.2 wrong per 100 requests; retrained on the new model, ~4.4. Allowing for sampling error, the true gap is between -2.0% and +1.4%
2. **Disagreement list** -- 11 questions (3.1% of the set) where the two systems answer differently -- the only items that carry decision information; exported for labeling
3. **Confidence quality** -- the current system's confidence quality holds up (relevant if you route low-confidence cases to humans; not statistically significant here)
4. **Noise tolerance** -- re-tested with typos, casing noise and filler words injected: gap of +0.00% -- no extra robustness from the newer model
5. **Transfer safety** -- model lineage checked: this path does NOT permit moving your existing work as-is (measured: cross-generation transfer can score worse than no system at all) -- any upgrade means retraining

## The money question
- combining your data with 193 published measured upgrade cases: roughly **5%** chance this upgrade pays off, 13% chance it regresses

## Next steps
1. spend nothing on upgrading or verifying this round
2. set the next base-model release as the re-evaluation trigger; that evaluation costs ~30 GPU-minutes and zero new labels
3. re-evaluate early if your traffic shifts (new product lines, new phrasing)

## How much to trust this
- every number comes from measured runs on your own 360 real business records; nothing is estimated or demo data
- method and thresholds follow the published UpgradeBench (2026) benchmark: 33 replayed upgrade decisions, 0.37% mean decision loss, zero serving regressions
- when the evidence is insufficient, this tool says so and prices the cheapest way to settle it, rather than forcing a verdict

---
*Technical appendix (full statistics, for the engineering team): recommendation.md*

## 6. Discussion
- 上一版判定：FREEZE（继续服役现有专家）
- 由 FREEZE 转 WAIT：未决但先验下增益概率仅 5%，采证性价比低。
- 零成本说明：本版复评未新增任何训练与标注；置信/鲁棒双探针合计约 5 GPU 分钟，分歧提取与重判为零 GPU 秒级操作。

## 7. Technical appendix: full statistical report
```
# Upgrade recommendation: `dineco` -> `E:\dataset\models\Qwen2-7B-Instruct`

## Action: **WAIT** (verdict: unresolved)

## Evidence
- frozen specialist (gate half, n=60): **0.9667**
- target adoption floor: **0.8098**
- retraining reference: **0.9667** (opportunity -0.28pp, epsilon 1pp)
- refresh student: **0.9500**
- genealogy: fresh_pretraining (inferred); distance unknown
  - architecture break; weight-space transfer undefined

## Statistics (report half only; gates never see these items)
- reference - frozen: 95% CI [-2.19, +2.19]pp, exact McNemar p = 1.0
- refresh - reference: 95% CI [-2.92, +1.46]pp, p = 1.0
- posterior over the true gain (UpgradeBench-corpus prior + paired evidence): mean -0.18pp, sd 0.73pp; P(gain > decision epsilon) = 5%, P(regression beyond epsilon) = 13%, P(within band) = 82%
- pooled paired evidence (val+test): n=360, reference fixes 3 frozen error(s) and breaks 4 frozen pass(es); 95% CI [-2.0, +1.4]pp -- gains above 1.4pp are excluded by the data
- error-scale view: relative error reduction -7% (15 frozen errors on gate)

## Confidence layer (proper scoring; more power than accuracy)
- paired log-loss, reference - frozen: +0.0520 (95% CI [-0.0346, +0.1491]; negative favors reference)
- calibration ECE: frozen 0.0228, reference 0.0318
- risk-coverage AURC (lower = better selective routing): frozen 0.0078, reference 0.0076

## Disagreement set (COLLECT channel: label these, not more i.i.d. samples)
- 11 disagreement item(s) (3.1% of pooled pairs); exact sign test on labeled outcomes p = 1.0
- probability the direction settles after labeling k more disagreements -- +10: 10%, +25: 21%, +50: 41%, +100: 56%, +200: 69%

## Robustness under perturbation (typo/casing/filler/punct; gold unchanged)
- frozen: 0.9533; reference: 0.9533 (delta +0.00pp)

## Label metrics (macro-F1: class-imbalance-robust; invalid rate: prediction outside the label inventory)
- freeze: macro-F1 **0.9568**, invalid outputs 0.00% (15 classes)
- adopt: macro-F1 **0.7498**, invalid outputs 0.00% (15 classes)
- reference: macro-F1 **0.9543**, invalid outputs 0.00% (15 classes)
- refresh: macro-F1 **0.9576**, invalid outputs 0.33% (15 classes)

## Task ledger: 1 episode(s), 5.0 train GPU-min, 2.4 eval GPU-min, 600 gold labels, 600 teacher queries, 180 validation items accumulated

## Reasoning
- the pooled evidence cannot resolve epsilon: CI [-2.0, +1.4]pp straddles 1pp (n=360, 3 fixes vs 4 breaks; gains above 1.4pp are already excluded; leaning: lean-freeze). Under the UpgradeBench corpus prior the posterior gives the gain a 5% chance of clearing the decision epsilon (1.00pp) -- more evidence is unlikely to change the call, so hold the frozen specialist and revisit at the next release

## Warnings
- gate set has only 60 items; gate sampling error at this size caused the worst episode in the paper's replay -- treat marginal verdicts as ties
- EVAL-SATURATED: the frozen specialist makes only 15 error(s) on the pooled evidence -- any upgrade comparison rests on that many items. Harvest hard/tail examples (e.g. production misroutes) before trusting an upgrade verdict here
- the gate passed but the report-half CI for the upgrade opportunity includes zero -- the gain is not statistically established; consider staying frozen until the next release or enlarging the gate set
- no data_manifest.json -- run `upgrade-advisor manifest` once to pin your splits (Phase 0)

## Before serving
- run `upgrade-advisor gate` for the candidate against the serving records (reporting half only); block on negative-flip budget 3%
- log GPU-minutes and labels consumed for this episode so the amortized decision improves with each release

*Policy and margins from UpgradeBench (2026); validated over 33 measured upgrade episodes (0.37pp mean regret, zero regressions, split-half gating). Negative-flip rate follows Yan et al., Positive-Congruent Training, CVPR 2021. Scope: LoRA-class adapters, 1.5-8B open-weight models.*
```