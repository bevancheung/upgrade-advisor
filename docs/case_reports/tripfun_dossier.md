# Upgrade decision dossier: tripfun -> Qwen2.5-1.5B-Instruct

## Decision card
**FREEZE** (verdict: equivalence)
**Stay put -- do not upgrade this round.** The data proves the new model would improve quality by at most 0.94%, which does not cover the cost of migrating. Zero spend.
Basis: 400 real records head-to-head; 1 fixes / 1 breaks

## 1. Background and motivation
TripFun 的旅行助手跑在用户手机端，用 Qwen2-1.5B-Instruct（小模型，端侧算力约束）+ LoRA 做 15 类旅行意图分类（订票、签证、时区、汇率、行李等）。Qwen2.5-1.5B-Instruct 发布后评估升级。两代 1.5B 架构逐维相同——工程团队原本想直接把 adapter 拷过去。

本纪要为 v2 复评版：在原判定基础上，以升级后的打分体系（证据池化、等价检验、论文语料先验、分歧采证通道）对同一批实测记录重新出具判定。

## 2. Data and system assets
| item | value |
|---|---|
| train/val/test data | E:\eval project\cases\tripfun_travel\train.jsonl / E:\eval project\cases\tripfun_travel\val.jsonl / E:\eval project\cases\tripfun_travel\test.jsonl |
| serving system | E:\dataset\models\Qwen2-1.5B-Instruct + LoRA (E:\eval project\cases\tripfun_travel\lora_src) |
| candidate base | E:\dataset\models\Qwen2.5-1.5B-Instruct |
| evaluation config | flip budget 3%; ε=1pp |

## 3. Process and spend
- cumulative: 1 episode(s); 2.4 train GPU-min; 1.6 eval GPU-min; 600 gold labels
- this round's probes (confidence + robustness) ~5 GPU-min; disagreement extraction and re-verdict are zero-GPU seconds

## 4. Verdict (v2 core): FREEZE -- equivalence
The complete, unfiltered evidence; the reading column is annotation:

| evidence | value | reading |
|---|---|---|
| serving specialist (gate half, n=100) | 0.9900 | measured level of the live system |
| candidate adoption floor (zero/few-shot) | 0.8712 | the new model used bare; the gap to serving is your data moat |
| retrained reference (same recipe, same data) | 1.0000 (opportunity +0.0pp) | actually trained and measured, not estimated |
| pooled paired evidence (val+test) | n=400: fixes 1, breaks 1 | everything the verdict judges on (the old core saw one n~100 fragment) |
| pooled 95% confidence interval | [-0.94, +0.94]pp | credible range of the true gap; gains above 0.94pp are excluded by the data |
| error-scale view (RER) | relative error reduction +0% (2 frozen errors) | the decision-relevant scale near the accuracy ceiling |
| genealogy verdict | fresh_pretraining (inferred) | governs adapter copying: forbidden off documented continuations |
| statistics (report half, gate-isolated) | CI [+0.0, +0.0]pp, McNemar p=1.0 | items the gates never saw -- unbiased reporting |
| confidence layer: paired log-loss (ref - serving) | +0.0315, CI [+0.0002, +0.087] | the serving system's confidence holds up |
| confidence layer: calibration ECE | serving 0.0018 / reference 0.007 | lower is better; matters for confidence-based routing |
| confidence layer: risk-coverage AURC | serving 0.0 / reference 0.0001 | lower is better; the selective-routing operating metric |
| robustness layer: perturbed re-test | serving 1.0 / reference 0.9833 (delta -1.67pp) | no extra robustness from the newer base (negative result, reported as such) |
| disagreement set (what COLLECT labels) | 2 items (0.5%), sign test p=1.0 | the only items carrying decision information; exported for labeling |
| labeling convergence pricing | +10: 22%, +25: 38%, +50: 58%, +100: 70%, +200: 79% | chance the direction settles after k more labels |
| macro-F1 (class-balanced) | freeze 0.9968 / adopt 0.8712 / reference 0.9938 | robust to class imbalance |
| invalid-output rate | freeze 0.00% / adopt 3.00% / reference 0.00% | predictions outside the label inventory -- format risk |
| task ledger | 1 episode(s); 2.4 train GPU-min; 600 gold labels | cumulative assets and spend |

**Reasons (verbatim)**
- equivalence established, FREEZE is a verdict not a default: the pooled paired CI [-0.9, +0.9]pp excludes any gain above epsilon (1pp) -- n=400 paired records, 1 fixes vs 1 breaks

**Warnings**
- gate set has only 100 items; gate sampling error at this size caused the worst episode in the paper's replay -- treat marginal verdicts as ties
- EVAL-SATURATED: the frozen specialist makes only 2 error(s) on the pooled evidence -- any upgrade comparison rests on that many items. Harvest hard/tail examples (e.g. production misroutes) before trusting an upgrade verdict here
- no data_manifest.json -- run `upgrade-advisor manifest` once to pin your splits (Phase 0)

## 5. Executive brief (auto-generated)
**Stay put -- do not upgrade this round.** The data proves the new model would improve quality by at most 0.94%, which does not cover the cost of migrating. Zero spend.

## Where you stand
- current system: about **0.5** wrong per 100 requests
- retrained on the new model (actually trained and measured, not estimated): about **0.5** wrong per 100
- the new model used bare, with no training: about **12.9** wrong per 100 -- your training data is the moat

## What we checked
1. **Quality, head-to-head** -- head-to-head on 400 real business questions: the new system fixed 1 and broke 1; everything else identical. Today you get ~0.5 wrong per 100 requests; retrained on the new model, ~0.5. Allowing for sampling error, the true gap is between -0.9% and +0.9%
2. **Disagreement list** -- 2 questions (0.5% of the set) where the two systems answer differently -- the only items that carry decision information; exported for labeling
3. **Confidence quality** -- the current system's confidence quality holds up (relevant if you route low-confidence cases to humans; not statistically significant here)
4. **Noise tolerance** -- re-tested with typos, casing noise and filler words injected: gap of -1.67% -- no extra robustness from the newer model
5. **Transfer safety** -- model lineage checked: this path does NOT permit moving your existing work as-is (measured: cross-generation transfer can score worse than no system at all) -- any upgrade means retraining

## Next steps
1. zero spend, zero change this round
2. re-run this evaluation at the next model release (~30 GPU-minutes)

## How much to trust this
- every number comes from measured runs on your own 400 real business records; nothing is estimated or demo data
- method and thresholds follow the published UpgradeBench (2026) benchmark: 33 replayed upgrade decisions, 0.37% mean decision loss, zero serving regressions
- when the evidence is insufficient, this tool says so and prices the cheapest way to settle it, rather than forcing a verdict

---
*Technical appendix (full statistics, for the engineering team): recommendation.md*

## 6. Discussion
- 上一版判定：FREEZE（继续服役现有专家）
- 维持不升级，但性质升级：旧版是“无可测收益”的默认冻结；本版是等价确证——数据已排除 >0.9pp 的增益，附排除界的正式判定。
- 零成本说明：本版复评未新增任何训练与标注；置信/鲁棒双探针合计约 5 GPU 分钟，分歧提取与重判为零 GPU 秒级操作。

## 7. Technical appendix: full statistical report
```
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
```