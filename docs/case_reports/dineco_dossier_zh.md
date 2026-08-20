# 基座模型升级决策纪要：dineco -> Qwen2-7B-Instruct

## 决策卡
**WAIT（跳过本代）**（证据未决）
【跳过这一代，等下一个版本】综合你的数据和 193 个公开实测案例的经验，这次升级划算的可能性只有 5%。不值得再花验证成本，维持现状，下一代发布时再评估。
依据：360 条真实数据逐题对比，修好 3 题 / 改错 4 题

## 一、背景与评估动机
DineCo 用 Qwen1.5-7B-Chat（2024 年初老栈）+ LoRA 做 15 类餐饮服务意图（订位、菜谱、营养、外卖等）。Qwen2-7B-Instruct 发布后评估。本案例把 REFRESH 路径全流程实测（教师重标 600 条 → 学生训练 → 入门控），是判定瀑布四个动作首次全部有实测数据在场。

本纪要为 v2 复评版：在原判定基础上，以升级后的打分体系（证据池化、等价检验、论文语料先验、分歧采证通道）对同一批实测记录重新出具判定。

## 二、数据与系统资产
| 项目 | 内容 |
|---|---|
| 训练/验证/测试数据 | E:\eval project\cases\dineco_dining\train.jsonl / E:\eval project\cases\dineco_dining\val.jsonl / E:\eval project\cases\dineco_dining\test.jsonl |
| 现役系统 | E:\dataset\models\Qwen1.5-7B-Chat + LoRA (E:\eval project\cases\dineco_dining\lora_src) |
| 候选基座 | E:\dataset\models\Qwen2-7B-Instruct |
| 评估配置 | flip budget 3%; ε=1pp |

## 三、评估过程与开销
- 累计：1 episode；训练 5.0 GPU 分钟；评测 2.4 GPU 分钟；金标 600 条
- 本轮探针（置信+鲁棒）约 5 GPU 分钟；分歧提取与重判零 GPU 秒级

## 四、系统判定（v2）：WAIT（跳过本代） —— 证据未决
以下为工具输出的全部证据（未加筛选），解读列为附注：

| 证据项 | 数值 | 解读 |
|---|---|---|
| 现役 specialist（门控半集 n=60） | 0.9667 | 当前线上系统的实测水平 |
| 候选基座采用地板（零/少样本） | 0.8098 | 不训练直接用新模型的水平——与现役的差距就是训练数据的护城河 |
| 候选基座重训参考（同配方同数据） | 0.9667（机会差 -0.28pp） | 真实训练并实测，非估算 |
| 池化配对证据（val+test 全部） | n=360：新系统修好 3 题、改错 4 题 | v2 判定使用的全部证据；旧版只用 n≈100 的碎片 |
| 池化 95% 置信区间 | [-2.0, +1.44]pp | 真实差距的可信范围；数据已排除 >1.44pp 的增益 |
| 增益后验（论文 193 格先验） | 均值 -0.18pp；P(增益>ε)=5%，P(倒退)=13% | 结合公开实测语料对小样本借力 |
| 错误率视角（RER） | 相对错误消除 -7%（冻结错误 15 条） | 天花板附近比绝对百分点更敏感的口径 |
| 谱系裁决 | fresh_pretraining (inferred) | 决定能否直迁 adapter：非续训一律禁止 |
| 统计层（报告半集，与门控隔离） | CI [-2.19, +2.19]pp, McNemar p=1.0 | 门控从未见过这些题——无偏报告 |
| 置信层：配对 log-loss（参考−现役） | +0.052, CI [-0.0346, +0.1491] | 现役的置信质量不落下风 |
| 置信层：校准误差 ECE | 现役 0.0228 / 参考 0.0318 | 越低越好；影响“低置信转人工”的可靠性 |
| 置信层：选择性风险 AURC | 现役 0.0078 / 参考 0.0076 | 越低越好；路由型部署的运维口径 |
| 鲁棒层：扰动重测 | 现役 0.9533 / 参考 0.9533（Δ +0.0pp） | 新基座未表现出额外抗干扰优势（负结果如实记录） |
| 分歧集（COLLECT 的对象） | 11 条（占 3.1%），符号检验 p=1.0 | 唯一携带决策信息的题目清单，已导出待标注 |
| 分歧标注收敛定价 | +10: 10%, +25: 21%, +50: 41%, +100: 56%, +200: 69% | 再标 k 条分歧后方向定案的概率 |
| Macro-F1（类平衡口径） | freeze 0.9568 / adopt 0.7498 / reference 0.9543 / refresh 0.9576 | 类不平衡下的稳健对照 |
| 无效输出率 | freeze 0.00% / adopt 0.00% / reference 0.00% / refresh 0.33% | 预测是否落在标签清单之外——格式风险 |
| 任务台账 | 1 episode；训练 5.0 GPU 分钟；标注 600 条 | 本任务的累计资产与开销 |

**系统判定理由（原文）**
- the pooled evidence cannot resolve epsilon: CI [-2.0, +1.4]pp straddles 1pp (n=360, 3 fixes vs 4 breaks; gains above 1.4pp are already excluded; leaning: lean-freeze). Under the UpgradeBench corpus prior the posterior gives the gain a 5% chance of clearing the decision epsilon (1.00pp) -- more evidence is unlikely to change the call, so hold the frozen specialist and revisit at the next release

**系统警告**
- gate set has only 60 items; gate sampling error at this size caused the worst episode in the paper's replay -- treat marginal verdicts as ties
- EVAL-SATURATED: the frozen specialist makes only 15 error(s) on the pooled evidence -- any upgrade comparison rests on that many items. Harvest hard/tail examples (e.g. production misroutes) before trusting an upgrade verdict here
- the gate passed but the report-half CI for the upgrade opportunity includes zero -- the gain is not statistically established; consider staying frozen until the next release or enlarging the gate set
- no data_manifest.json -- run `upgrade-advisor manifest` once to pin your splits (Phase 0)

## 五、决策书（给管理层，工具自动生成）
【跳过这一代，等下一个版本】综合你的数据和 193 个公开实测案例的经验，这次升级划算的可能性只有 5%。不值得再花验证成本，维持现状，下一代发布时再评估。

## 你的系统现在什么水平
- 现役系统：每 100 个请求约答错 **4.2** 个
- 若换新模型并重训（我们真实训练并测过，非估算）：约答错 **4.4** 个
- 若直接裸用新模型、不做任何训练：约答错 **19.0** 个——你的训练数据才是护城河

## 我们做了哪些检查
1. **质量对比（头对头）** -- 在 360 个真实业务问题上逐题对比：新系统修好了 3 题、改错了 4 题，其余完全相同。现役每 100 个请求约错 4.2 个，升级重训后约错 4.4 个。考虑抽样误差，真实差距在 -2.0% 到 +1.4% 之间
2. **分歧清单** -- 两套系统意见不同的题共 11 个（占 3.1%）——这是唯一携带决策信息的题目清单，已导出待标注
3. **置信度质量** -- 现役系统的置信度质量不落下风（对需要“低置信转人工”的场景有参考价值，本轮差异未达统计显著）
4. **抗干扰能力** -- 给输入加入错字、大小写混乱、口语填充词后重测：新旧系统的差距为 +0.00%——新系统未表现出额外的抗干扰优势
5. **直迁安全性** -- 已核查模型血统：本升级路径禁止直接搬运现有成果（历史实测：跨代直迁会把正确率打到不如不用）——任何升级都必须重训

## 值不值得：一句话的账
- 综合你的数据与 193 个公开实测升级案例：这次升级带来足够收益的可能性约 **5%**，造成倒退的可能性约 13%

## 下一步
1. 本轮不投入任何升级/验证成本
2. 把下一代基座模型的发布设为重评触发点；届时一次评估约需 30 GPU 分钟、零新标注
3. 若业务数据分布发生明显变化（新品类、新话术），提前重评

## 这个结论有多可靠
- 全部数字来自你自己的 360 条真实业务数据的实测对比与真实训练，无任何估算或演示数据
- 方法与阈值来自公开基准 UpgradeBench（2026）：33 个实测升级决策回放，平均决策损失 0.37%，零线上倒退
- 当证据不足时，本工具会直说“不足”并给出补证的最小成本，而不是硬给一个结论

---
*技术附录（统计细节，供工程团队）：recommendation.md*

## 六、对照与讨论
- 上一版判定：FREEZE（继续服役现有专家）
- 由 FREEZE 转 WAIT：未决但先验下增益概率仅 5%，采证性价比低。
- 零成本说明：本版复评未新增任何训练与标注；置信/鲁棒双探针合计约 5 GPU 分钟，分歧提取与重判为零 GPU 秒级操作。

## 七、技术附录：完整统计报告
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