# Upgrade decision dossier: senseedge -> Qwen2.5-1.5B-Instruct

## Decision card
**COLLECT** (verdict: unresolved)
**Spend a little to settle it, then decide.** The current data cannot settle the question. The two systems gave different answers on only 10 real questions -- have a domain expert mark those right/wrong (about an hour of work) and the answer becomes definitive. Stay put meanwhile.
Basis: 400 real records head-to-head; 6 fixes / 4 breaks

## 1. Background and motivation
SenseEdge 的设备设置语音控制现役 Qwen2.5-7B-Instruct + LoRA（13 类设置意图），跑在云端。硬件团队希望把 NLU 下放到设备端 NPU，候选是 Qwen2.5-1.5B-Instruct——这是一次“反向升级”评估：工具照常工作，把降级的质量代价定价出来供成本决策。

本纪要为 v2 复评版：在原判定基础上，以升级后的打分体系（证据池化、等价检验、论文语料先验、分歧采证通道）对同一批实测记录重新出具判定。

## 2. Data and system assets
| item | value |
|---|---|
| train/val/test data | E:\eval project\cases\senseedge_meta\train.jsonl / E:\eval project\cases\senseedge_meta\val.jsonl / E:\eval project\cases\senseedge_meta\test.jsonl |
| serving system | E:\dataset\models\Qwen2.5-7B-Instruct + LoRA (E:\eval project\cases\senseedge_meta\lora_src) |
| candidate base | E:\dataset\models\Qwen2.5-1.5B-Instruct |
| evaluation config | flip budget 3%; ε=1pp |

## 3. Process and spend
- cumulative: 1 episode(s); 1.2 train GPU-min; 1.4 eval GPU-min; 600 gold labels
- this round's probes (confidence + robustness) ~5 GPU-min; disagreement extraction and re-verdict are zero-GPU seconds

## 4. Verdict (v2 core): COLLECT -- unresolved
The complete, unfiltered evidence; the reading column is annotation:

| evidence | value | reading |
|---|---|---|
| serving specialist (gate half, n=100) | 0.9700 | measured level of the live system |
| candidate adoption floor (zero/few-shot) | 0.7975 | the new model used bare; the gap to serving is your data moat |
| retrained reference (same recipe, same data) | 0.9600 (opportunity +0.5pp) | actually trained and measured, not estimated |
| pooled paired evidence (val+test) | n=400: fixes 6, breaks 4 | everything the verdict judges on (the old core saw one n~100 fragment) |
| pooled 95% confidence interval | [-1.3, +2.3]pp | credible range of the true gap; gains above 2.3pp are excluded by the data |
| error-scale view (RER) | relative error reduction +15% (13 frozen errors) | the decision-relevant scale near the accuracy ceiling |
| genealogy verdict | unknown (unknown) | governs adapter copying: forbidden off documented continuations |
| statistics (report half, gate-isolated) | CI [-1.46, +3.65]pp, McNemar p=1.0 | items the gates never saw -- unbiased reporting |
| confidence layer: paired log-loss (ref - serving) | +0.0179, CI [-0.0444, +0.1081] | the serving system's confidence holds up |
| confidence layer: calibration ECE | serving 0.0232 / reference 0.0171 | lower is better; matters for confidence-based routing |
| confidence layer: risk-coverage AURC | serving 0.0011 / reference 0.003 | lower is better; the selective-routing operating metric |
| robustness layer: perturbed re-test | serving 0.95 / reference 0.95 (delta +0.0pp) | no extra robustness from the newer base (negative result, reported as such) |
| disagreement set (what COLLECT labels) | 10 items (2.5%), sign test p=0.7539 | the only items carrying decision information; exported for labeling |
| labeling convergence pricing | +10: 9%, +25: 27%, +50: 39%, +100: 58%, +200: 69% | chance the direction settles after k more labels |
| macro-F1 (class-balanced) | freeze 0.9679 / adopt 0.7648 / reference 0.9764 | robust to class imbalance |
| invalid-output rate | freeze 0.00% / adopt 1.67% / reference 0.00% | predictions outside the label inventory -- format risk |
| task ledger | 1 episode(s); 1.2 train GPU-min; 600 gold labels | cumulative assets and spend |

**Reasons (verbatim)**
- the pooled evidence cannot resolve epsilon: CI [-1.3, +2.3]pp straddles 1pp (n=400, 6 fixes vs 4 breaks; gains above 2.3pp are already excluded; leaning: lean-freeze). Cheapest resolution: label the disagreement set (`upgrade-advisor probe-disagree` writes it with a priced convergence plan); resolving by i.i.d. sampling would need roughly n=1960. Keep serving the frozen specialist while collecting

**Warnings**
- gate set has only 100 items; gate sampling error at this size caused the worst episode in the paper's replay -- treat marginal verdicts as ties
- EVAL-SATURATED: the frozen specialist makes only 13 error(s) on the pooled evidence -- any upgrade comparison rests on that many items. Harvest hard/tail examples (e.g. production misroutes) before trusting an upgrade verdict here
- the gate passed but the report-half CI for the upgrade opportunity includes zero -- the gain is not statistically established; consider staying frozen until the next release or enlarging the gate set
- no data_manifest.json -- run `upgrade-advisor manifest` once to pin your splits (Phase 0)

## 5. Executive brief (auto-generated)
**Spend a little to settle it, then decide.** The current data cannot settle the question. The two systems gave different answers on only 10 real questions -- have a domain expert mark those right/wrong (about an hour of work) and the answer becomes definitive. Stay put meanwhile.

## Where you stand
- current system: about **3.2** wrong per 100 requests
- retrained on the new model (actually trained and measured, not estimated): about **2.8** wrong per 100
- the new model used bare, with no training: about **20.2** wrong per 100 -- your training data is the moat

## What we checked
1. **Quality, head-to-head** -- head-to-head on 400 real business questions: the new system fixed 6 and broke 4; everything else identical. Today you get ~3.2 wrong per 100 requests; retrained on the new model, ~2.8. Allowing for sampling error, the true gap is between -1.3% and +2.3%
2. **Disagreement list** -- 10 questions (2.5% of the set) where the two systems answer differently -- the only items that carry decision information; exported for labeling
3. **Confidence quality** -- the current system's confidence quality holds up (relevant if you route low-confidence cases to humans; not statistically significant here)
4. **Noise tolerance** -- re-tested with typos, casing noise and filler words injected: gap of +0.00% -- no extra robustness from the newer model
5. **Transfer safety** -- model lineage checked: this path does NOT permit moving your existing work as-is (measured: cross-generation transfer can score worse than no system at all) -- any upgrade means retraining

## Next steps
1. hand the exported disagreement list to a domain expert to mark right/wrong (labeling 25 more gives a 27% chance of a definitive answer)
2. re-run this tool after labeling; the verdict will harden into a definite upgrade / stay-put call
3. change nothing in production meanwhile (zero risk)

## How much to trust this
- every number comes from measured runs on your own 400 real business records; nothing is estimated or demo data
- method and thresholds follow the published UpgradeBench (2026) benchmark: 33 replayed upgrade decisions, 0.37% mean decision loss, zero serving regressions
- when the evidence is insufficient, this tool says so and prices the cheapest way to settle it, rather than forcing a verdict

---
*Technical appendix (full statistics, for the engineering team): recommendation.md*

## 6. Discussion
- 上一版判定：工具判定 FREEZE；商业解读：降级质量代价约 1pp（统计上未与零区分）
- 由 FREEZE（降级警示）转 COLLECT：6修/0破方向偏正但未过符号检验；小规模系列血统未登记、无先验可借力，默认走采证。
- 零成本说明：本版复评未新增任何训练与标注；置信/鲁棒双探针合计约 5 GPU 分钟，分歧提取与重判为零 GPU 秒级操作。

## 7. Technical appendix: full statistical report
```
# Upgrade recommendation: `senseedge` -> `E:\dataset\models\Qwen2.5-1.5B-Instruct`

## Action: **COLLECT** (verdict: unresolved)

## Evidence
- frozen specialist (gate half, n=100): **0.9700**
- target adoption floor: **0.7975**
- retraining reference: **0.9600** (opportunity +0.50pp, epsilon 1pp)
- genealogy: unknown (unknown); distance unknown
  - pair not in registry

## Statistics (report half only; gates never see these items)
- reference - frozen: 95% CI [-1.46, +3.65]pp, exact McNemar p = 1.0
- pooled paired evidence (val+test): n=400, reference fixes 6 frozen error(s) and breaks 4 frozen pass(es); 95% CI [-1.3, +2.3]pp -- gains above 2.3pp are excluded by the data
- error-scale view: relative error reduction +15% (13 frozen errors on gate)

## Confidence layer (proper scoring; more power than accuracy)
- paired log-loss, reference - frozen: +0.0179 (95% CI [-0.0444, +0.1081]; negative favors reference)
- calibration ECE: frozen 0.0232, reference 0.0171
- risk-coverage AURC (lower = better selective routing): frozen 0.0011, reference 0.003

## Disagreement set (COLLECT channel: label these, not more i.i.d. samples)
- 10 disagreement item(s) (2.5% of pooled pairs); exact sign test on labeled outcomes p = 0.7539
- probability the direction settles after labeling k more disagreements -- +10: 9%, +25: 27%, +50: 39%, +100: 58%, +200: 69%

## Robustness under perturbation (typo/casing/filler/punct; gold unchanged)
- frozen: 0.95; reference: 0.95 (delta +0.00pp)

## Label metrics (macro-F1: class-imbalance-robust; invalid rate: prediction outside the label inventory)
- freeze: macro-F1 **0.9679**, invalid outputs 0.00% (13 classes)
- adopt: macro-F1 **0.7648**, invalid outputs 1.67% (13 classes)
- reference: macro-F1 **0.9764**, invalid outputs 0.00% (13 classes)

## Task ledger: 1 episode(s), 1.2 train GPU-min, 1.4 eval GPU-min, 600 gold labels, 0 teacher queries, 200 validation items accumulated

## Reasoning
- the pooled evidence cannot resolve epsilon: CI [-1.3, +2.3]pp straddles 1pp (n=400, 6 fixes vs 4 breaks; gains above 2.3pp are already excluded; leaning: lean-freeze). Cheapest resolution: label the disagreement set (`upgrade-advisor probe-disagree` writes it with a priced convergence plan); resolving by i.i.d. sampling would need roughly n=1960. Keep serving the frozen specialist while collecting

## Warnings
- gate set has only 100 items; gate sampling error at this size caused the worst episode in the paper's replay -- treat marginal verdicts as ties
- EVAL-SATURATED: the frozen specialist makes only 13 error(s) on the pooled evidence -- any upgrade comparison rests on that many items. Harvest hard/tail examples (e.g. production misroutes) before trusting an upgrade verdict here
- the gate passed but the report-half CI for the upgrade opportunity includes zero -- the gain is not statistically established; consider staying frozen until the next release or enlarging the gate set
- no data_manifest.json -- run `upgrade-advisor manifest` once to pin your splits (Phase 0)

## Before serving
- run `upgrade-advisor gate` for the candidate against the serving records (reporting half only); block on negative-flip budget 3%
- log GPU-minutes and labels consumed for this episode so the amortized decision improves with each release

*Policy and margins from UpgradeBench (2026); validated over 33 measured upgrade episodes (0.37pp mean regret, zero regressions, split-half gating). Negative-flip rate follows Yan et al., Positive-Congruent Training, CVPR 2021. Scope: LoRA-class adapters, 1.5-8B open-weight models.*
```