# Upgrade decision dossier: fintone_card_routing -> Qwen2.5-7B-Instruct

## Decision card
**WAIT** (verdict: unresolved)
**Skip this generation.** Combining your data with 193 published measured cases, this upgrade has only a 5% chance of paying off. Not worth further verification spend; stay put and re-evaluate at the next release.
Basis: 400 real records head-to-head; 8 fixes / 12 breaks

## 1. Background and motivation
Fintone 客服机器人团队于 2024 年在 Qwen2-7B-Instruct 上用 QLoRA 训练了支付卡业务的意图路由专家（20 类自有意图体系），现服务于工单自动分派。Qwen2.5-7B-Instruct 发布后，团队面临标准的升级四选一：冻结现役（Freeze）、直接移植适配器（Copy）、教师蒸馏刷新（Refresh）还是重新训练（Retrain）。历史上这类决定靠工程直觉；本轮改用论文验证过的决策工具，以自有少量数据给出可执行、可追溯的建议。

本纪要为 v2 复评版：在原判定基础上，以升级后的打分体系（证据池化、等价检验、论文语料先验、分歧采证通道）对同一批实测记录重新出具判定。

## 2. Data and system assets
| item | value |
|---|---|
| train/val/test data | E:\eval project\fintone\train.jsonl / E:\eval project\fintone\val.jsonl / E:\eval project\fintone\test.jsonl |
| serving system | E:\dataset\models\Qwen2-7B-Instruct + LoRA (E:\eval project\fintone\lora_qwen2) |
| candidate base | E:\dataset\models\Qwen2.5-7B-Instruct |
| evaluation config | flip budget 3%; ε=1pp |

## 3. Process and spend
- cumulative: 1 episode(s); 2.8 train GPU-min; 3.8 eval GPU-min; 500 gold labels
- this round's probes (confidence + robustness) ~5 GPU-min; disagreement extraction and re-verdict are zero-GPU seconds

## 4. Verdict (v2 core): WAIT -- unresolved
The complete, unfiltered evidence; the reading column is annotation:

| evidence | value | reading |
|---|---|---|
| serving specialist (gate half, n=100) | 0.9100 | measured level of the live system |
| candidate adoption floor (zero/few-shot) | 0.7730 | the new model used bare; the gap to serving is your data moat |
| retrained reference (same recipe, same data) | 0.8800 (opportunity -1.0pp) | actually trained and measured, not estimated |
| pooled paired evidence (val+test) | n=400: fixes 8, breaks 12 | everything the verdict judges on (the old core saw one n~100 fragment) |
| pooled 95% confidence interval | [-3.44, +1.44]pp | credible range of the true gap; gains above 1.44pp are excluded by the data |
| gain posterior (193-cell corpus prior) | mean -0.67pp; P(gain>eps)=5%, P(regression)=37% | borrows strength from the published measured corpus |
| error-scale view (RER) | relative error reduction -12% (32 frozen errors) | the decision-relevant scale near the accuracy ceiling |
| genealogy verdict | fresh_pretraining (inferred) | governs adapter copying: forbidden off documented continuations |
| statistics (report half, gate-isolated) | CI [-0.73, +5.84]pp, McNemar p=0.375 | items the gates never saw -- unbiased reporting |
| confidence layer: paired log-loss (ref - serving) | -0.0523, CI [-0.1521, +0.0252] | negative favors the reference: quality 0/1 accuracy cannot see |
| confidence layer: calibration ECE | serving 0.0322 / reference 0.0331 | lower is better; matters for confidence-based routing |
| confidence layer: risk-coverage AURC | serving 0.018 / reference 0.0109 | lower is better; the selective-routing operating metric |
| robustness layer: perturbed re-test | serving 0.92 / reference 0.9167 (delta -0.33pp) | no extra robustness from the newer base (negative result, reported as such) |
| disagreement set (what COLLECT labels) | 22 items (5.5%), sign test p=0.5034 | the only items carrying decision information; exported for labeling |
| labeling convergence pricing | +10: 7%, +25: 23%, +50: 40%, +100: 52%, +200: 65% | chance the direction settles after k more labels |
| macro-F1 (class-balanced) | freeze 0.924 / adopt 0.703 / reference 0.9214 | robust to class imbalance |
| invalid-output rate | freeze 1.00% / adopt 0.67% / reference 1.00% | predictions outside the label inventory -- format risk |
| task ledger | 1 episode(s); 2.8 train GPU-min; 500 gold labels | cumulative assets and spend |

**Reasons (verbatim)**
- the pooled evidence cannot resolve epsilon: CI [-3.4, +1.4]pp straddles 1pp (n=400, 8 fixes vs 12 breaks; gains above 1.4pp are already excluded; leaning: lean-freeze). Under the UpgradeBench corpus prior the posterior gives the gain a 5% chance of clearing the decision epsilon (1.00pp) -- more evidence is unlikely to change the call, so hold the frozen specialist and revisit at the next release

**Warnings**
- gate set has only 100 items; gate sampling error at this size caused the worst episode in the paper's replay -- treat marginal verdicts as ties
- the gate passed but the report-half CI for the upgrade opportunity includes zero -- the gain is not statistically established; consider staying frozen until the next release or enlarging the gate set
- no data_manifest.json -- run `upgrade-advisor manifest` once to pin your splits (Phase 0)

## 5. Executive brief (auto-generated)
**Skip this generation.** Combining your data with 193 published measured cases, this upgrade has only a 5% chance of paying off. Not worth further verification spend; stay put and re-evaluate at the next release.

## Where you stand
- current system: about **8.0** wrong per 100 requests
- retrained on the new model (actually trained and measured, not estimated): about **9.0** wrong per 100
- the new model used bare, with no training: about **22.7** wrong per 100 -- your training data is the moat

## What we checked
1. **Quality, head-to-head** -- head-to-head on 400 real business questions: the new system fixed 8 and broke 12; everything else identical. Today you get ~8.0 wrong per 100 requests; retrained on the new model, ~9.0. Allowing for sampling error, the true gap is between -3.4% and +1.4%
2. **Disagreement list** -- 22 questions (5.5% of the set) where the two systems answer differently -- the only items that carry decision information; exported for labeling
3. **Confidence quality** -- the new system is slightly better at knowing how sure to be (relevant if you route low-confidence cases to humans; not statistically significant here)
4. **Noise tolerance** -- re-tested with typos, casing noise and filler words injected: gap of -0.33% -- no extra robustness from the newer model
5. **Transfer safety** -- model lineage checked: this path does NOT permit moving your existing work as-is (measured: cross-generation transfer can score worse than no system at all) -- any upgrade means retraining

## The money question
- combining your data with 193 published measured upgrade cases: roughly **5%** chance this upgrade pays off, 37% chance it regresses

## Next steps
1. spend nothing on upgrading or verifying this round
2. set the next base-model release as the re-evaluation trigger; that evaluation costs ~30 GPU-minutes and zero new labels
3. re-evaluate early if your traffic shifts (new product lines, new phrasing)

## How much to trust this
- every number comes from measured runs on your own 400 real business records; nothing is estimated or demo data
- method and thresholds follow the published UpgradeBench (2026) benchmark: 33 replayed upgrade decisions, 0.37% mean decision loss, zero serving regressions
- when the evidence is insufficient, this tool says so and prices the cheapest way to settle it, rather than forcing a verdict

---
*Technical appendix (full statistics, for the engineering team): recommendation.md*

## 6. Discussion
- 上一版判定：FREEZE（继续服役现有专家）
- 维持不升级并转 WAIT：8修/12破方向偏负、先验下增益概率仅 5%——上一版“参考反而更差”的结论在池化口径下依然成立。
- 零成本说明：本版复评未新增任何训练与标注；置信/鲁棒双探针合计约 5 GPU 分钟，分歧提取与重判为零 GPU 秒级操作。

## 7. Technical appendix: full statistical report
```
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
```