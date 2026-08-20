# Upgrade decision dossier: autolink -> OLMo-1.7-7B

## Decision card
**FREEZE** (verdict: equivalence)
**Stay put -- do not upgrade this round.** The data proves the new model would improve quality by at most 0.47%, which does not cover the cost of migrating. Zero spend.
Basis: 380 real records head-to-head; 1 fixes / 5 breaks

## 1. Background and motivation
AutoLink 因整车厂审计要求（训练数据与全流程可审计），NLU 模块只允许使用全开源模型，现役为 OLMo-1-7B（base 模型，plain 提示格式）+ LoRA，15 类车载意图（导航、油量、胎压、保养、路况等）。OLMo-1.7-7B 发布后评估升级。模型卡明确记载 1.7 为从零重训——正是论文验证过“复制必然崩溃”的那类对。

本纪要为 v2 复评版：在原判定基础上，以升级后的打分体系（证据池化、等价检验、论文语料先验、分歧采证通道）对同一批实测记录重新出具判定。

## 2. Data and system assets
| item | value |
|---|---|
| train/val/test data | E:\eval project\cases\autolink_auto\train.jsonl / E:\eval project\cases\autolink_auto\val.jsonl / E:\eval project\cases\autolink_auto\test.jsonl |
| serving system | E:\dataset\models\OLMo-1-7B + LoRA (E:\eval project\cases\autolink_auto\lora_src) |
| candidate base | E:\dataset\models\OLMo-1.7-7B |
| evaluation config | flip budget 3%; ε=1pp |

## 3. Process and spend
- cumulative: 1 episode(s); 2.6 train GPU-min; 4.1 eval GPU-min; 600 gold labels
- this round's probes (confidence + robustness) ~5 GPU-min; disagreement extraction and re-verdict are zero-GPU seconds

## 4. Verdict (v2 core): FREEZE -- equivalence
The complete, unfiltered evidence; the reading column is annotation:

| evidence | value | reading |
|---|---|---|
| serving specialist (gate half, n=80) | 1.0000 | measured level of the live system |
| candidate adoption floor (zero/few-shot) | 0.7791 | the new model used bare; the gap to serving is your data moat |
| retrained reference (same recipe, same data) | 1.0000 (opportunity -1.05pp) | actually trained and measured, not estimated |
| pooled paired evidence (val+test) | n=380: fixes 1, breaks 5 | everything the verdict judges on (the old core saw one n~100 fragment) |
| pooled 95% confidence interval | [-2.57, +0.47]pp | credible range of the true gap; gains above 0.47pp are excluded by the data |
| error-scale view (RER) | relative error reduction -133% (3 frozen errors) | the decision-relevant scale near the accuracy ceiling |
| genealogy verdict | fresh_pretraining (verified) | governs adapter copying: forbidden off documented continuations |
| statistics (report half, gate-isolated) | CI [-3.65, +0.0]pp, McNemar p=0.5 | items the gates never saw -- unbiased reporting |
| confidence layer: paired log-loss (ref - serving) | +0.0475, CI [-0.0001, +0.1072] | the serving system's confidence holds up |
| confidence layer: calibration ECE | serving 0.0093 / reference 0.0174 | lower is better; matters for confidence-based routing |
| confidence layer: risk-coverage AURC | serving 0.0002 / reference 0.0021 | lower is better; the selective-routing operating metric |
| robustness layer: perturbed re-test | serving 0.98 / reference 0.9733 (delta -0.67pp) | no extra robustness from the newer base (negative result, reported as such) |
| disagreement set (what COLLECT labels) | 6 items (1.6%), sign test p=0.2188 | the only items carrying decision information; exported for labeling |
| labeling convergence pricing | +10: 56%, +25: 73%, +50: 82%, +100: 87%, +200: 91% | chance the direction settles after k more labels |
| macro-F1 (class-balanced) | freeze 0.9899 / adopt 0.7409 / reference 0.9775 | robust to class imbalance |
| invalid-output rate | freeze 0.00% / adopt 4.33% / reference 0.67% | predictions outside the label inventory -- format risk |
| task ledger | 1 episode(s); 2.6 train GPU-min; 600 gold labels | cumulative assets and spend |

**Reasons (verbatim)**
- equivalence established, FREEZE is a verdict not a default: the pooled paired CI [-2.6, +0.5]pp excludes any gain above epsilon (1pp) -- n=380 paired records, 1 fixes vs 5 breaks

**Warnings**
- gate set has only 80 items; gate sampling error at this size caused the worst episode in the paper's replay -- treat marginal verdicts as ties
- EVAL-SATURATED: the frozen specialist makes only 3 error(s) on the pooled evidence -- any upgrade comparison rests on that many items. Harvest hard/tail examples (e.g. production misroutes) before trusting an upgrade verdict here
- no data_manifest.json -- run `upgrade-advisor manifest` once to pin your splits (Phase 0)

## 5. Executive brief (auto-generated)
**Stay put -- do not upgrade this round.** The data proves the new model would improve quality by at most 0.47%, which does not cover the cost of migrating. Zero spend.

## Where you stand
- current system: about **0.8** wrong per 100 requests
- retrained on the new model (actually trained and measured, not estimated): about **1.8** wrong per 100
- the new model used bare, with no training: about **22.1** wrong per 100 -- your training data is the moat

## What we checked
1. **Quality, head-to-head** -- head-to-head on 380 real business questions: the new system fixed 1 and broke 5; everything else identical. Today you get ~0.8 wrong per 100 requests; retrained on the new model, ~1.8. Allowing for sampling error, the true gap is between -2.6% and +0.5%
2. **Disagreement list** -- 6 questions (1.6% of the set) where the two systems answer differently -- the only items that carry decision information; exported for labeling
3. **Confidence quality** -- the current system's confidence quality holds up (relevant if you route low-confidence cases to humans; not statistically significant here)
4. **Noise tolerance** -- re-tested with typos, casing noise and filler words injected: gap of -0.67% -- no extra robustness from the newer model
5. **Transfer safety** -- model lineage checked: this path does NOT permit moving your existing work as-is (measured: cross-generation transfer can score worse than no system at all) -- any upgrade means retraining

## Next steps
1. zero spend, zero change this round
2. re-run this evaluation at the next model release (~30 GPU-minutes)

## How much to trust this
- every number comes from measured runs on your own 380 real business records; nothing is estimated or demo data
- method and thresholds follow the published UpgradeBench (2026) benchmark: 33 replayed upgrade decisions, 0.37% mean decision loss, zero serving regressions
- when the evidence is insufficient, this tool says so and prices the cheapest way to settle it, rather than forcing a verdict

---
*Technical appendix (full statistics, for the engineering team): recommendation.md*

## 6. Discussion
- 上一版判定：FREEZE（继续服役现有专家）
- 维持不升级，性质升级为等价确证（排除 >0.5pp 增益；1修/5破，方向偏负）。
- 零成本说明：本版复评未新增任何训练与标注；置信/鲁棒双探针合计约 5 GPU 分钟，分歧提取与重判为零 GPU 秒级操作。

## 7. Technical appendix: full statistical report
```
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
```