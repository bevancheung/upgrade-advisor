# Upgrade decision dossier: newsdesk -> Qwen2.5-7B-Instruct-1M

## Decision card
**FREEZE** (verdict: equivalence)
**Stay put -- do not upgrade this round.** The data proves the new model would improve quality by at most 0.76%, which does not cover the cost of migrating. Zero spend.
Basis: 500 real records head-to-head; 2 fixes / 4 breaks

## 1. Background and motivation
NewsDesk 编辑部用 Qwen2.5-7B-Instruct + LoRA 做稿件四大栏目（时政/体育/财经/科技）自动分栏。厂商发布长上下文版 Qwen2.5-7B-Instruct-1M——注册表记录其为同一权重的文档化延续（约 20B token）。这是五案例中唯一 Copy 被谱系许可并实测的一例。

本纪要为 v2 复评版：在原判定基础上，以升级后的打分体系（证据池化、等价检验、论文语料先验、分歧采证通道）对同一批实测记录重新出具判定。

## 2. Data and system assets
| item | value |
|---|---|
| train/val/test data | E:\eval project\cases\newsdesk_agnews\train.jsonl / E:\eval project\cases\newsdesk_agnews\val.jsonl / E:\eval project\cases\newsdesk_agnews\test.jsonl |
| serving system | E:\dataset\models\Qwen2.5-7B-Instruct + LoRA (E:\eval project\cases\newsdesk_agnews\lora_src) |
| candidate base | E:\dataset\models\Qwen2.5-7B-Instruct-1M |
| evaluation config | flip budget 3%; ε=1pp |

## 3. Process and spend
- cumulative: 1 episode(s); 5.4 train GPU-min; 3.4 eval GPU-min; 800 gold labels
- this round's probes (confidence + robustness) ~5 GPU-min; disagreement extraction and re-verdict are zero-GPU seconds

## 4. Verdict (v2 core): FREEZE -- equivalence
The complete, unfiltered evidence; the reading column is annotation:

| evidence | value | reading |
|---|---|---|
| serving specialist (gate half, n=100) | 0.9000 | measured level of the live system |
| candidate adoption floor (zero/few-shot) | 0.8465 | the new model used bare; the gap to serving is your data moat |
| retrained reference (same recipe, same data) | 0.9000 (opportunity -0.4pp) | actually trained and measured, not estimated |
| pooled paired evidence (val+test) | n=500: fixes 2, breaks 4 | everything the verdict judges on (the old core saw one n~100 fragment) |
| pooled 95% confidence interval | [-1.56, +0.76]pp | credible range of the true gap; gains above 0.76pp are excluded by the data |
| error-scale view (RER) | relative error reduction -5% (39 frozen errors) | the decision-relevant scale near the accuracy ceiling |
| genealogy verdict | continuation (inferred), continuation 20B tokens | governs adapter copying: forbidden off documented continuations |
| statistics (report half, gate-isolated) | CI [-1.62, +1.62]pp, McNemar p=1.0 | items the gates never saw -- unbiased reporting |
| confidence layer: paired log-loss (ref - serving) | -0.0163, CI [-0.0368, +0.0028] | negative favors the reference: quality 0/1 accuracy cannot see |
| confidence layer: calibration ECE | serving 0.0533 / reference 0.0382 | lower is better; matters for confidence-based routing |
| confidence layer: risk-coverage AURC | serving 0.0431 / reference 0.0347 | lower is better; the selective-routing operating metric |
| robustness layer: perturbed re-test | serving 0.9275 / reference 0.9225 (delta -0.5pp) | no extra robustness from the newer base (negative result, reported as such) |
| disagreement set (what COLLECT labels) | 7 items (1.4%), sign test p=0.6875 | the only items carrying decision information; exported for labeling |
| labeling convergence pricing | +10: 16%, +25: 39%, +50: 57%, +100: 68%, +200: 77% | chance the direction settles after k more labels |
| macro-F1 (class-balanced) | freeze 0.9257 / adopt 0.8297 / reference 0.9209 / copy 0.9132 | robust to class imbalance |
| invalid-output rate | all 0.00% | predictions outside the label inventory -- format risk |
| task ledger | 1 episode(s); 5.4 train GPU-min; 800 gold labels | cumulative assets and spend |

**Reasons (verbatim)**
- equivalence established, FREEZE is a verdict not a default: the pooled paired CI [-1.6, +0.8]pp excludes any gain above epsilon (1pp) -- n=500 paired records, 2 fixes vs 4 breaks

**Warnings**
- gate set has only 100 items; gate sampling error at this size caused the worst episode in the paper's replay -- treat marginal verdicts as ties
- no data_manifest.json -- run `upgrade-advisor manifest` once to pin your splits (Phase 0)

## 5. Executive brief (auto-generated)
**Stay put -- do not upgrade this round.** The data proves the new model would improve quality by at most 0.76%, which does not cover the cost of migrating. Zero spend.

## Where you stand
- current system: about **7.8** wrong per 100 requests
- retrained on the new model (actually trained and measured, not estimated): about **8.2** wrong per 100
- the new model used bare, with no training: about **15.3** wrong per 100 -- your training data is the moat

## What we checked
1. **Quality, head-to-head** -- head-to-head on 500 real business questions: the new system fixed 2 and broke 4; everything else identical. Today you get ~7.8 wrong per 100 requests; retrained on the new model, ~8.2. Allowing for sampling error, the true gap is between -1.6% and +0.8%
2. **Disagreement list** -- 7 questions (1.4% of the set) where the two systems answer differently -- the only items that carry decision information; exported for labeling
3. **Confidence quality** -- the new system is slightly better at knowing how sure to be (relevant if you route low-confidence cases to humans; not statistically significant here)
4. **Noise tolerance** -- re-tested with typos, casing noise and filler words injected: gap of -0.50% -- no extra robustness from the newer model
5. **Transfer safety** -- model lineage checked: this path permits moving your existing work as-is

## Next steps
1. zero spend, zero change this round
2. re-run this evaluation at the next model release (~30 GPU-minutes)

## How much to trust this
- every number comes from measured runs on your own 500 real business records; nothing is estimated or demo data
- method and thresholds follow the published UpgradeBench (2026) benchmark: 33 replayed upgrade decisions, 0.37% mean decision loss, zero serving regressions
- when the evidence is insufficient, this tool says so and prices the cheapest way to settle it, rather than forcing a verdict

---
*Technical appendix (full statistics, for the engineering team): recommendation.md*

## 6. Discussion
- 上一版判定：FREEZE（继续服役现有专家）
- 维持不升级，性质升级为等价确证（排除 >0.8pp 增益）。注意本案血统为 20B 续训、copy 本可许可，但机会门未开，许可无用武之地。
- 零成本说明：本版复评未新增任何训练与标注；置信/鲁棒双探针合计约 5 GPU 分钟，分歧提取与重判为零 GPU 秒级操作。

## 7. Technical appendix: full statistical report
```
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
```