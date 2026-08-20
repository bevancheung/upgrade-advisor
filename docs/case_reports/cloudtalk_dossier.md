# Upgrade decision dossier: cloudtalk -> Qwen2.5-7B-Instruct

## Decision card
**FREEZE** (verdict: equivalence)
**Stay put -- do not upgrade this round.** The data proves the new model would improve quality by at most 1.97%, which does not cover the cost of migrating. Zero spend.
Basis: 900 real records head-to-head; 18 fixes / 12 breaks

## 1. Background and motivation
CloudTalk 给客户交付 NLU 槽位抽取（utterance → JSON{intent, slots}），现役 Qwen1.5-7B-Chat + LoRA。跳过 Qwen2，直接评估跨两代升级到 Qwen2.5-7B-Instruct。这是难任务（现役正确率仅四成），团队预期跨两代必有大幅提升。

本纪要为 v2 复评版：在原判定基础上，以升级后的打分体系（证据池化、等价检验、论文语料先验、分歧采证通道）对同一批实测记录重新出具判定。

## 2. Data and system assets
| item | value |
|---|---|
| train/val/test data | E:\eval project\snips_slots\train.jsonl / E:\eval project\snips_slots\val.jsonl / E:\eval project\snips_slots\test.jsonl |
| serving system | E:\dataset\models\Qwen1.5-7B-Chat + LoRA (E:\eval project\snips_slots\lora_q15) |
| candidate base | E:\dataset\models\Qwen2.5-7B-Instruct |
| evaluation config | flip budget 5%; ε=2pp |

## 3. Process and spend
- cumulative: 1 episode(s); 18.4 train GPU-min; 10.2 eval GPU-min; 2000 gold labels
- this round's probes (confidence + robustness) ~5 GPU-min; disagreement extraction and re-verdict are zero-GPU seconds

## 4. Verdict (v2 core): FREEZE -- equivalence
The complete, unfiltered evidence; the reading column is annotation:

| evidence | value | reading |
|---|---|---|
| serving specialist (gate half, n=200) | 0.4250 | measured level of the live system |
| candidate adoption floor (zero/few-shot) | 0.2095 | the new model used bare; the gap to serving is your data moat |
| retrained reference (same recipe, same data) | 0.4250 (opportunity +0.67pp) | actually trained and measured, not estimated |
| pooled paired evidence (val+test) | n=900: fixes 18, breaks 12 | everything the verdict judges on (the old core saw one n~100 fragment) |
| pooled 95% confidence interval | [-0.64, +1.97]pp | credible range of the true gap; gains above 1.97pp are excluded by the data |
| error-scale view (RER) | relative error reduction +1% (487 frozen errors) | the decision-relevant scale near the accuracy ceiling |
| genealogy verdict | fresh_pretraining (verified) | governs adapter copying: forbidden off documented continuations |
| statistics (report half, gate-isolated) | CI [-0.93, +3.41]pp, McNemar p=0.3877 | items the gates never saw -- unbiased reporting |
| disagreement set (what COLLECT labels) | 90 items (10.0%), sign test p=0.3616 | the only items carrying decision information; exported for labeling |
| labeling convergence pricing | +10: 7%, +25: 21%, +50: 38%, +100: 55%, +200: 66% | chance the direction settles after k more labels |
| task ledger | 1 episode(s); 18.4 train GPU-min; 2000 gold labels | cumulative assets and spend |

**Reasons (verbatim)**
- equivalence established, FREEZE is a verdict not a default: the pooled paired CI [-0.6, +2.0]pp excludes any gain above epsilon (2pp) -- n=900 paired records, 18 fixes vs 12 breaks

**Warnings**
- gate set has only 200 items; gate sampling error at this size caused the worst episode in the paper's replay -- treat marginal verdicts as ties
- no data_manifest.json -- run `upgrade-advisor manifest` once to pin your splits (Phase 0)

## 5. Executive brief (auto-generated)
**Stay put -- do not upgrade this round.** The data proves the new model would improve quality by at most 1.97%, which does not cover the cost of migrating. Zero spend.

## Where you stand
- current system: about **54.1** wrong per 100 requests
- retrained on the new model (actually trained and measured, not estimated): about **53.4** wrong per 100
- the new model used bare, with no training: about **79.0** wrong per 100 -- your training data is the moat

## What we checked
1. **Quality, head-to-head** -- head-to-head on 900 real business questions: the new system fixed 18 and broke 12; everything else identical. Today you get ~54.1 wrong per 100 requests; retrained on the new model, ~53.4. Allowing for sampling error, the true gap is between -0.6% and +2.0%
2. **Disagreement list** -- 90 questions (10.0% of the set) where the two systems answer differently -- the only items that carry decision information; exported for labeling
3. **Transfer safety** -- model lineage checked: this path does NOT permit moving your existing work as-is (measured: cross-generation transfer can score worse than no system at all) -- any upgrade means retraining

## Next steps
1. zero spend, zero change this round
2. re-run this evaluation at the next model release (~30 GPU-minutes)

## How much to trust this
- every number comes from measured runs on your own 900 real business records; nothing is estimated or demo data
- method and thresholds follow the published UpgradeBench (2026) benchmark: 33 replayed upgrade decisions, 0.37% mean decision loss, zero serving regressions
- when the evidence is insufficient, this tool says so and prices the cheapest way to settle it, rather than forcing a verdict

---
*Technical appendix (full statistics, for the engineering team): recommendation.md*

## 6. Discussion
- 上一版判定：FREEZE（继续服役现有专家）——本批最反直觉的判定
- 维持不升级，性质升级为等价确证（结构化任务 ε=2pp；n=900 池化、18修/12破，CI 上界 2.0pp 恰被排除）。分歧集 90 条为全案例最大——若未来想推翻本判定，标注这 90 条即可。
- 零成本说明：本版复评未新增任何训练与标注；置信/鲁棒双探针合计约 5 GPU 分钟，分歧提取与重判为零 GPU 秒级操作。

## 7. Technical appendix: full statistical report
```
# Upgrade recommendation: `cloudtalk` -> `E:\dataset\models\Qwen2.5-7B-Instruct`

## Action: **FREEZE** (verdict: equivalence)

## Evidence
- frozen specialist (gate half, n=200): **0.4250**
- target adoption floor: **0.2095**
- retraining reference: **0.4250** (opportunity +0.67pp, epsilon 2pp)
- genealogy: fresh_pretraining (verified); distance unknown
  - path exists but crosses a non-continuation edge (anneal/soup/fresh): copying is not licensed

## Statistics (report half only; gates never see these items)
- reference - frozen: 95% CI [-0.93, +3.41]pp, exact McNemar p = 0.3877
- pooled paired evidence (val+test): n=900, reference fixes 18 frozen error(s) and breaks 12 frozen pass(es); 95% CI [-0.6, +2.0]pp -- gains above 2.0pp are excluded by the data
- error-scale view: relative error reduction +1% (487 frozen errors on gate)

## Disagreement set (COLLECT channel: label these, not more i.i.d. samples)
- 90 disagreement item(s) (10.0% of pooled pairs); exact sign test on labeled outcomes p = 0.3616
- probability the direction settles after labeling k more disagreements -- +10: 7%, +25: 21%, +50: 38%, +100: 55%, +200: 66%

## Task ledger: 1 episode(s), 18.4 train GPU-min, 10.2 eval GPU-min, 2000 gold labels, 0 teacher queries, 400 validation items accumulated

## Reasoning
- equivalence established, FREEZE is a verdict not a default: the pooled paired CI [-0.6, +2.0]pp excludes any gain above epsilon (2pp) -- n=900 paired records, 18 fixes vs 12 breaks

## Warnings
- gate set has only 200 items; gate sampling error at this size caused the worst episode in the paper's replay -- treat marginal verdicts as ties
- no data_manifest.json -- run `upgrade-advisor manifest` once to pin your splits (Phase 0)

## Before serving
- run `upgrade-advisor gate` for the candidate against the serving records (reporting half only); block on negative-flip budget 5%
- log GPU-minutes and labels consumed for this episode so the amortized decision improves with each release

*Policy and margins from UpgradeBench (2026); validated over 33 measured upgrade episodes (0.37pp mean regret, zero regressions, split-half gating). Negative-flip rate follows Yan et al., Positive-Congruent Training, CVPR 2021. Scope: LoRA-class adapters, 1.5-8B open-weight models.*
```