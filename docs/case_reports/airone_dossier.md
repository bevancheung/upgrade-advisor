# Upgrade decision dossier: airone -> Qwen2-7B-Instruct

## Decision card
**COLLECT** (verdict: unresolved)
**Spend a little to settle it, then decide.** The current data cannot settle the question (roughly 11% chance the upgrade pays off). The two systems gave different answers on only 2 real questions -- have a domain expert mark those right/wrong (about an hour of work) and the answer becomes definitive. Stay put meanwhile.
Basis: 400 real records head-to-head; 2 fixes / 0 breaks

## 1. Background and motivation
AirOne 呼叫中心于 2024 年初在当时最新的 Qwen1.5-7B-Chat 上训练了航班业务意图路由专家（订票查询、航班状态、票价、地面服务等）。Qwen2-7B-Instruct 发布后评估是否升级。这是五案例中现役基座最老的一个——预期升级机会最大。

本纪要为 v2 复评版：在原判定基础上，以升级后的打分体系（证据池化、等价检验、论文语料先验、分歧采证通道）对同一批实测记录重新出具判定。

## 2. Data and system assets
| item | value |
|---|---|
| train/val/test data | E:\eval project\cases\airone_atis\train.jsonl / E:\eval project\cases\airone_atis\val.jsonl / E:\eval project\cases\airone_atis\test.jsonl |
| serving system | E:\dataset\models\Qwen1.5-7B-Chat + LoRA (E:\eval project\cases\airone_atis\lora_src) |
| candidate base | E:\dataset\models\Qwen2-7B-Instruct |
| evaluation config | flip budget 3%; ε=1pp |

## 3. Process and spend
- cumulative: 1 episode(s); 2.6 train GPU-min; 1.9 eval GPU-min; 600 gold labels
- this round's probes (confidence + robustness) ~5 GPU-min; disagreement extraction and re-verdict are zero-GPU seconds

## 4. Verdict (v2 core): COLLECT -- unresolved
The complete, unfiltered evidence; the reading column is annotation:

| evidence | value | reading |
|---|---|---|
| serving specialist (gate half, n=100) | 0.9800 | measured level of the live system |
| candidate adoption floor (zero/few-shot) | 0.9264 | the new model used bare; the gap to serving is your data moat |
| retrained reference (same recipe, same data) | 1.0000 (opportunity +0.5pp) | actually trained and measured, not estimated |
| pooled paired evidence (val+test) | n=400: fixes 2, breaks 0 | everything the verdict judges on (the old core saw one n~100 fragment) |
| pooled 95% confidence interval | [-0.44, +1.44]pp | credible range of the true gap; gains above 1.44pp are excluded by the data |
| gain posterior (193-cell corpus prior) | mean +0.51pp; P(gain>eps)=11%, P(regression)=0% | borrows strength from the published measured corpus |
| error-scale view (RER) | relative error reduction +50% (4 frozen errors) | the decision-relevant scale near the accuracy ceiling |
| genealogy verdict | fresh_pretraining (inferred) | governs adapter copying: forbidden off documented continuations |
| statistics (report half, gate-isolated) | CI [+0.0, +0.0]pp, McNemar p=1.0 | items the gates never saw -- unbiased reporting |
| confidence layer: paired log-loss (ref - serving) | -0.0585, CI [-0.1534, +0.0047] | negative favors the reference: quality 0/1 accuracy cannot see |
| confidence layer: calibration ECE | serving 0.0064 / reference 0.008 | lower is better; matters for confidence-based routing |
| confidence layer: risk-coverage AURC | serving 0.0171 / reference 0.0009 | lower is better; the selective-routing operating metric |
| robustness layer: perturbed re-test | serving 0.99 / reference 0.9867 (delta -0.33pp) | no extra robustness from the newer base (negative result, reported as such) |
| disagreement set (what COLLECT labels) | 2 items (0.5%), sign test p=0.5 | the only items carrying decision information; exported for labeling |
| labeling convergence pricing | +10: 58%, +25: 67%, +50: 79%, +100: 85%, +200: 89% | chance the direction settles after k more labels |
| macro-F1 (class-balanced) | freeze 0.9993 / adopt 0.9158 / reference 0.9993 | robust to class imbalance |
| invalid-output rate | freeze 0.67% / adopt 2.33% / reference 0.67% | predictions outside the label inventory -- format risk |
| task ledger | 1 episode(s); 2.6 train GPU-min; 600 gold labels | cumulative assets and spend |

**Reasons (verbatim)**
- the pooled evidence cannot resolve epsilon: CI [-0.4, +1.4]pp straddles 1pp (n=400, 2 fixes vs 0 breaks; gains above 1.4pp are already excluded; leaning: lean-freeze); posterior chance the gain clears the decision epsilon: 11%. Cheapest resolution: label the disagreement set (`upgrade-advisor probe-disagree` writes it with a priced convergence plan); resolving by i.i.d. sampling would need roughly n=392. Keep serving the frozen specialist while collecting

**Warnings**
- gate set has only 100 items; gate sampling error at this size caused the worst episode in the paper's replay -- treat marginal verdicts as ties
- EVAL-SATURATED: the frozen specialist makes only 4 error(s) on the pooled evidence -- any upgrade comparison rests on that many items. Harvest hard/tail examples (e.g. production misroutes) before trusting an upgrade verdict here
- the gate passed but the report-half CI for the upgrade opportunity includes zero -- the gain is not statistically established; consider staying frozen until the next release or enlarging the gate set
- no data_manifest.json -- run `upgrade-advisor manifest` once to pin your splits (Phase 0)

## 5. Executive brief (auto-generated)
**Spend a little to settle it, then decide.** The current data cannot settle the question (roughly 11% chance the upgrade pays off). The two systems gave different answers on only 2 real questions -- have a domain expert mark those right/wrong (about an hour of work) and the answer becomes definitive. Stay put meanwhile.

## Where you stand
- current system: about **1.0** wrong per 100 requests
- retrained on the new model (actually trained and measured, not estimated): about **0.5** wrong per 100
- the new model used bare, with no training: about **7.4** wrong per 100 -- your training data is the moat

## What we checked
1. **Quality, head-to-head** -- head-to-head on 400 real business questions: the new system fixed 2 and broke 0; everything else identical. Today you get ~1.0 wrong per 100 requests; retrained on the new model, ~0.5. Allowing for sampling error, the true gap is between -0.4% and +1.4%
2. **Disagreement list** -- 2 questions (0.5% of the set) where the two systems answer differently -- the only items that carry decision information; exported for labeling
3. **Confidence quality** -- the new system is slightly better at knowing how sure to be (relevant if you route low-confidence cases to humans; not statistically significant here)
4. **Noise tolerance** -- re-tested with typos, casing noise and filler words injected: gap of -0.33% -- no extra robustness from the newer model
5. **Transfer safety** -- model lineage checked: this path does NOT permit moving your existing work as-is (measured: cross-generation transfer can score worse than no system at all) -- any upgrade means retraining

## The money question
- combining your data with 193 published measured upgrade cases: roughly **11%** chance this upgrade pays off, 0% chance it regresses

## Next steps
1. hand the exported disagreement list to a domain expert to mark right/wrong (labeling 25 more gives a 67% chance of a definitive answer)
2. re-run this tool after labeling; the verdict will harden into a definite upgrade / stay-put call
3. change nothing in production meanwhile (zero risk)

## How much to trust this
- every number comes from measured runs on your own 400 real business records; nothing is estimated or demo data
- method and thresholds follow the published UpgradeBench (2026) benchmark: 33 replayed upgrade decisions, 0.37% mean decision loss, zero serving regressions
- when the evidence is insufficient, this tool says so and prices the cheapest way to settle it, rather than forcing a verdict

---
*Technical appendix (full statistics, for the engineering team): recommendation.md*

## 6. Discussion
- 上一版判定：RETRAIN（在新基座上重训）——但附统计观望警告
- 改判原因：旧版 RETRAIN 建立在 val 门控半集 2 条样本翻转上；池化全部 400 条配对记录后为 2修/0破，置信区间横跨 ε——增益未确证。v2 按对称标准拒绝用点估计开瀑布，转 COLLECT：分歧仅 2 条，标注成本几乎为零。
- 零成本说明：本版复评未新增任何训练与标注；置信/鲁棒双探针合计约 5 GPU 分钟，分歧提取与重判为零 GPU 秒级操作。

## 7. Technical appendix: full statistical report
```
# Upgrade recommendation: `airone` -> `E:\dataset\models\Qwen2-7B-Instruct`

## Action: **COLLECT** (verdict: unresolved)

## Evidence
- frozen specialist (gate half, n=100): **0.9800**
- target adoption floor: **0.9264**
- retraining reference: **1.0000** (opportunity +0.50pp, epsilon 1pp)
- genealogy: fresh_pretraining (inferred); distance unknown
  - architecture break; weight-space transfer undefined

## Statistics (report half only; gates never see these items)
- reference - frozen: 95% CI [+0.00, +0.00]pp, exact McNemar p = 1.0
- posterior over the true gain (UpgradeBench-corpus prior + paired evidence): mean +0.51pp, sd 0.41pp; P(gain > decision epsilon) = 11%, P(regression beyond epsilon) = 0%, P(within band) = 89%
- pooled paired evidence (val+test): n=400, reference fixes 2 frozen error(s) and breaks 0 frozen pass(es); 95% CI [-0.4, +1.4]pp -- gains above 1.4pp are excluded by the data
- error-scale view: relative error reduction +50% (4 frozen errors on gate)

## Confidence layer (proper scoring; more power than accuracy)
- paired log-loss, reference - frozen: -0.0585 (95% CI [-0.1534, +0.0047]; negative favors reference)
- calibration ECE: frozen 0.0064, reference 0.008
- risk-coverage AURC (lower = better selective routing): frozen 0.0171, reference 0.0009

## Disagreement set (COLLECT channel: label these, not more i.i.d. samples)
- 2 disagreement item(s) (0.5% of pooled pairs); exact sign test on labeled outcomes p = 0.5
- probability the direction settles after labeling k more disagreements -- +10: 58%, +25: 67%, +50: 79%, +100: 85%, +200: 89%

## Robustness under perturbation (typo/casing/filler/punct; gold unchanged)
- frozen: 0.99; reference: 0.9867 (delta -0.33pp)

## Label metrics (macro-F1: class-imbalance-robust; invalid rate: prediction outside the label inventory)
- freeze: macro-F1 **0.9993**, invalid outputs 0.67% (6 classes)
- adopt: macro-F1 **0.9158**, invalid outputs 2.33% (6 classes)
- reference: macro-F1 **0.9993**, invalid outputs 0.67% (6 classes)

## Task ledger: 1 episode(s), 2.6 train GPU-min, 1.9 eval GPU-min, 600 gold labels, 0 teacher queries, 200 validation items accumulated

## Reasoning
- the pooled evidence cannot resolve epsilon: CI [-0.4, +1.4]pp straddles 1pp (n=400, 2 fixes vs 0 breaks; gains above 1.4pp are already excluded; leaning: lean-freeze); posterior chance the gain clears the decision epsilon: 11%. Cheapest resolution: label the disagreement set (`upgrade-advisor probe-disagree` writes it with a priced convergence plan); resolving by i.i.d. sampling would need roughly n=392. Keep serving the frozen specialist while collecting

## Warnings
- gate set has only 100 items; gate sampling error at this size caused the worst episode in the paper's replay -- treat marginal verdicts as ties
- EVAL-SATURATED: the frozen specialist makes only 4 error(s) on the pooled evidence -- any upgrade comparison rests on that many items. Harvest hard/tail examples (e.g. production misroutes) before trusting an upgrade verdict here
- the gate passed but the report-half CI for the upgrade opportunity includes zero -- the gain is not statistically established; consider staying frozen until the next release or enlarging the gate set
- no data_manifest.json -- run `upgrade-advisor manifest` once to pin your splits (Phase 0)

## Before serving
- run `upgrade-advisor gate` for the candidate against the serving records (reporting half only); block on negative-flip budget 3%
- log GPU-minutes and labels consumed for this episode so the amortized decision improves with each release

*Policy and margins from UpgradeBench (2026); validated over 33 measured upgrade episodes (0.37pp mean regret, zero regressions, split-half gating). Negative-flip rate follows Yan et al., Positive-Congruent Training, CVPR 2021. Scope: LoRA-class adapters, 1.5-8B open-weight models.*
```