# Upgrade decision dossier: workdesk -> Qwen3-8B

## Decision card
**WAIT** (verdict: unresolved)
**Skip this generation.** Combining your data with 193 published measured cases, this upgrade has only a 4% chance of paying off. Not worth further verification spend; stay put and re-evaluate at the next release.
Basis: 400 real records head-to-head; 2 fixes / 2 breaks

## 1. Background and motivation
WorkDesk 为大型企业运营 HR/IT 服务台，用 Qwen2-7B-Instruct + LoRA 做 15 类员工请求路由（休假、报销、保险、会议、工资单等）。跳过 Qwen2.5 一代后，评估直接升级到 Qwen3-8B（跨两代）。

本纪要为 v2 复评版：在原判定基础上，以升级后的打分体系（证据池化、等价检验、论文语料先验、分歧采证通道）对同一批实测记录重新出具判定。

## 2. Data and system assets
| item | value |
|---|---|
| train/val/test data | E:\eval project\cases\workdesk_it\train.jsonl / E:\eval project\cases\workdesk_it\val.jsonl / E:\eval project\cases\workdesk_it\test.jsonl |
| serving system | E:\dataset\models\Qwen2-7B-Instruct + LoRA (E:\eval project\cases\workdesk_it\lora_src) |
| candidate base | E:\dataset\models\Qwen3-8B |
| evaluation config | flip budget 3%; ε=1pp |

## 3. Process and spend
- cumulative: 1 episode(s); 3.2 train GPU-min; 3.6 eval GPU-min; 600 gold labels
- this round's probes (confidence + robustness) ~5 GPU-min; disagreement extraction and re-verdict are zero-GPU seconds

## 4. Verdict (v2 core): WAIT -- unresolved
The complete, unfiltered evidence; the reading column is annotation:

| evidence | value | reading |
|---|---|---|
| serving specialist (gate half, n=100) | 0.9700 | measured level of the live system |
| candidate adoption floor (zero/few-shot) | 0.9509 | the new model used bare; the gap to serving is your data moat |
| retrained reference (same recipe, same data) | 0.9700 (opportunity +0.0pp) | actually trained and measured, not estimated |
| pooled paired evidence (val+test) | n=400: fixes 2, breaks 2 | everything the verdict judges on (the old core saw one n~100 fragment) |
| pooled 95% confidence interval | [-1.23, +1.23]pp | credible range of the true gap; gains above 1.23pp are excluded by the data |
| gain posterior (193-cell corpus prior) | mean +0.04pp; P(gain>eps)=4%, P(regression)=2% | borrows strength from the published measured corpus |
| error-scale view (RER) | relative error reduction +0% (6 frozen errors) | the decision-relevant scale near the accuracy ceiling |
| genealogy verdict | fresh_pretraining (verified) | governs adapter copying: forbidden off documented continuations |
| statistics (report half, gate-isolated) | CI [-3.65, +1.46]pp, McNemar p=1.0 | items the gates never saw -- unbiased reporting |
| confidence layer: paired log-loss (ref - serving) | -0.0139, CI [-0.0726, +0.0371] | negative favors the reference: quality 0/1 accuracy cannot see |
| confidence layer: calibration ECE | serving 0.0099 / reference 0.0108 | lower is better; matters for confidence-based routing |
| confidence layer: risk-coverage AURC | serving 0.0006 / reference 0.0004 | lower is better; the selective-routing operating metric |
| robustness layer: perturbed re-test | serving 0.98 / reference 0.98 (delta +0.0pp) | no extra robustness from the newer base (negative result, reported as such) |
| disagreement set (what COLLECT labels) | 5 items (1.2%), sign test p=1.0 | the only items carrying decision information; exported for labeling |
| labeling convergence pricing | +10: 4%, +25: 29%, +50: 50%, +100: 63%, +200: 74% | chance the direction settles after k more labels |
| macro-F1 (class-balanced) | freeze 0.9897 / adopt 0.8717 / reference 0.9898 | robust to class imbalance |
| invalid-output rate | all 0.00% | predictions outside the label inventory -- format risk |
| task ledger | 1 episode(s); 3.2 train GPU-min; 600 gold labels | cumulative assets and spend |

**Reasons (verbatim)**
- the pooled evidence cannot resolve epsilon: CI [-1.2, +1.2]pp straddles 1pp (n=400, 2 fixes vs 2 breaks; gains above 1.2pp are already excluded; leaning: lean-freeze). Under the UpgradeBench corpus prior the posterior gives the gain a 4% chance of clearing the decision epsilon (1.00pp) -- more evidence is unlikely to change the call, so hold the frozen specialist and revisit at the next release

**Warnings**
- gate set has only 100 items; gate sampling error at this size caused the worst episode in the paper's replay -- treat marginal verdicts as ties
- EVAL-SATURATED: the frozen specialist makes only 6 error(s) on the pooled evidence -- any upgrade comparison rests on that many items. Harvest hard/tail examples (e.g. production misroutes) before trusting an upgrade verdict here
- the gate passed but the report-half CI for the upgrade opportunity includes zero -- the gain is not statistically established; consider staying frozen until the next release or enlarging the gate set
- no data_manifest.json -- run `upgrade-advisor manifest` once to pin your splits (Phase 0)

## 5. Executive brief (auto-generated)
**Skip this generation.** Combining your data with 193 published measured cases, this upgrade has only a 4% chance of paying off. Not worth further verification spend; stay put and re-evaluate at the next release.

## Where you stand
- current system: about **1.5** wrong per 100 requests
- retrained on the new model (actually trained and measured, not estimated): about **1.5** wrong per 100
- the new model used bare, with no training: about **4.9** wrong per 100 -- your training data is the moat

## What we checked
1. **Quality, head-to-head** -- head-to-head on 400 real business questions: the new system fixed 2 and broke 2; everything else identical. Today you get ~1.5 wrong per 100 requests; retrained on the new model, ~1.5. Allowing for sampling error, the true gap is between -1.2% and +1.2%
2. **Disagreement list** -- 5 questions (1.2% of the set) where the two systems answer differently -- the only items that carry decision information; exported for labeling
3. **Confidence quality** -- the new system is slightly better at knowing how sure to be (relevant if you route low-confidence cases to humans; not statistically significant here)
4. **Noise tolerance** -- re-tested with typos, casing noise and filler words injected: gap of +0.00% -- no extra robustness from the newer model
5. **Transfer safety** -- model lineage checked: this path does NOT permit moving your existing work as-is (measured: cross-generation transfer can score worse than no system at all) -- any upgrade means retraining

## The money question
- combining your data with 193 published measured upgrade cases: roughly **4%** chance this upgrade pays off, 2% chance it regresses

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
- 由 FREEZE 转 WAIT：池化证据未决（CI 横跨 ε），且论文先验下增益概率仅 4%——不值得花标注去验证，等下一代基座更划算。
- 零成本说明：本版复评未新增任何训练与标注；置信/鲁棒双探针合计约 5 GPU 分钟，分歧提取与重判为零 GPU 秒级操作。

## 7. Technical appendix: full statistical report
```
# Upgrade recommendation: `workdesk` -> `E:\dataset\models\Qwen3-8B`

## Action: **WAIT** (verdict: unresolved)

## Evidence
- frozen specialist (gate half, n=100): **0.9700**
- target adoption floor: **0.9509**
- retraining reference: **0.9700** (opportunity +0.00pp, epsilon 1pp)
- genealogy: fresh_pretraining (verified); distance unknown
  - path exists but crosses a non-continuation edge (anneal/soup/fresh): copying is not licensed

## Statistics (report half only; gates never see these items)
- reference - frozen: 95% CI [-3.65, +1.46]pp, exact McNemar p = 1.0
- posterior over the true gain (UpgradeBench-corpus prior + paired evidence): mean +0.04pp, sd 0.53pp; P(gain > decision epsilon) = 4%, P(regression beyond epsilon) = 2%, P(within band) = 94%
- pooled paired evidence (val+test): n=400, reference fixes 2 frozen error(s) and breaks 2 frozen pass(es); 95% CI [-1.2, +1.2]pp -- gains above 1.2pp are excluded by the data
- error-scale view: relative error reduction +0% (6 frozen errors on gate)

## Confidence layer (proper scoring; more power than accuracy)
- paired log-loss, reference - frozen: -0.0139 (95% CI [-0.0726, +0.0371]; negative favors reference)
- calibration ECE: frozen 0.0099, reference 0.0108
- risk-coverage AURC (lower = better selective routing): frozen 0.0006, reference 0.0004

## Disagreement set (COLLECT channel: label these, not more i.i.d. samples)
- 5 disagreement item(s) (1.2% of pooled pairs); exact sign test on labeled outcomes p = 1.0
- probability the direction settles after labeling k more disagreements -- +10: 4%, +25: 29%, +50: 50%, +100: 63%, +200: 74%

## Robustness under perturbation (typo/casing/filler/punct; gold unchanged)
- frozen: 0.98; reference: 0.98 (delta +0.00pp)

## Label metrics (macro-F1: class-imbalance-robust; invalid rate: prediction outside the label inventory)
- freeze: macro-F1 **0.9897**, invalid outputs 0.00% (15 classes)
- adopt: macro-F1 **0.8717**, invalid outputs 0.00% (15 classes)
- reference: macro-F1 **0.9898**, invalid outputs 0.00% (15 classes)

## Task ledger: 1 episode(s), 3.2 train GPU-min, 3.6 eval GPU-min, 600 gold labels, 0 teacher queries, 200 validation items accumulated

## Reasoning
- the pooled evidence cannot resolve epsilon: CI [-1.2, +1.2]pp straddles 1pp (n=400, 2 fixes vs 2 breaks; gains above 1.2pp are already excluded; leaning: lean-freeze). Under the UpgradeBench corpus prior the posterior gives the gain a 4% chance of clearing the decision epsilon (1.00pp) -- more evidence is unlikely to change the call, so hold the frozen specialist and revisit at the next release

## Warnings
- gate set has only 100 items; gate sampling error at this size caused the worst episode in the paper's replay -- treat marginal verdicts as ties
- EVAL-SATURATED: the frozen specialist makes only 6 error(s) on the pooled evidence -- any upgrade comparison rests on that many items. Harvest hard/tail examples (e.g. production misroutes) before trusting an upgrade verdict here
- the gate passed but the report-half CI for the upgrade opportunity includes zero -- the gain is not statistically established; consider staying frozen until the next release or enlarging the gate set
- no data_manifest.json -- run `upgrade-advisor manifest` once to pin your splits (Phase 0)

## Before serving
- run `upgrade-advisor gate` for the candidate against the serving records (reporting half only); block on negative-flip budget 3%
- log GPU-minutes and labels consumed for this episode so the amortized decision improves with each release

*Policy and margins from UpgradeBench (2026); validated over 33 measured upgrade episodes (0.37pp mean regret, zero regressions, split-half gating). Negative-flip rate follows Yan et al., Positive-Congruent Training, CVPR 2021. Scope: LoRA-class adapters, 1.5-8B open-weight models.*
```