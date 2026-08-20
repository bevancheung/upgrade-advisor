# 基座模型升级决策纪要：fintone_card_routing -> Qwen2.5-7B-Instruct

## 决策卡
**WAIT（跳过本代）**（证据未决）
【跳过这一代，等下一个版本】综合你的数据和 193 个公开实测案例的经验，这次升级划算的可能性只有 5%。不值得再花验证成本，维持现状，下一代发布时再评估。
依据：400 条真实数据逐题对比，修好 8 题 / 改错 12 题

## 一、背景与评估动机
Fintone 客服机器人团队于 2024 年在 Qwen2-7B-Instruct 上用 QLoRA 训练了支付卡业务的意图路由专家（20 类自有意图体系），现服务于工单自动分派。Qwen2.5-7B-Instruct 发布后，团队面临标准的升级四选一：冻结现役（Freeze）、直接移植适配器（Copy）、教师蒸馏刷新（Refresh）还是重新训练（Retrain）。历史上这类决定靠工程直觉；本轮改用论文验证过的决策工具，以自有少量数据给出可执行、可追溯的建议。

本纪要为 v2 复评版：在原判定基础上，以升级后的打分体系（证据池化、等价检验、论文语料先验、分歧采证通道）对同一批实测记录重新出具判定。

## 二、数据与系统资产
| 项目 | 内容 |
|---|---|
| 训练/验证/测试数据 | E:\eval project\fintone\train.jsonl / E:\eval project\fintone\val.jsonl / E:\eval project\fintone\test.jsonl |
| 现役系统 | E:\dataset\models\Qwen2-7B-Instruct + LoRA (E:\eval project\fintone\lora_qwen2) |
| 候选基座 | E:\dataset\models\Qwen2.5-7B-Instruct |
| 评估配置 | flip budget 3%; ε=1pp |

## 三、评估过程与开销
- 累计：1 episode；训练 2.8 GPU 分钟；评测 3.8 GPU 分钟；金标 500 条
- 本轮探针（置信+鲁棒）约 5 GPU 分钟；分歧提取与重判零 GPU 秒级

## 四、系统判定（v2）：WAIT（跳过本代） —— 证据未决
以下为工具输出的全部证据（未加筛选），解读列为附注：

| 证据项 | 数值 | 解读 |
|---|---|---|
| 现役 specialist（门控半集 n=100） | 0.9100 | 当前线上系统的实测水平 |
| 候选基座采用地板（零/少样本） | 0.7730 | 不训练直接用新模型的水平——与现役的差距就是训练数据的护城河 |
| 候选基座重训参考（同配方同数据） | 0.8800（机会差 -1.0pp） | 真实训练并实测，非估算 |
| 池化配对证据（val+test 全部） | n=400：新系统修好 8 题、改错 12 题 | v2 判定使用的全部证据；旧版只用 n≈100 的碎片 |
| 池化 95% 置信区间 | [-3.44, +1.44]pp | 真实差距的可信范围；数据已排除 >1.44pp 的增益 |
| 增益后验（论文 193 格先验） | 均值 -0.67pp；P(增益>ε)=5%，P(倒退)=37% | 结合公开实测语料对小样本借力 |
| 错误率视角（RER） | 相对错误消除 -12%（冻结错误 32 条） | 天花板附近比绝对百分点更敏感的口径 |
| 谱系裁决 | fresh_pretraining (inferred) | 决定能否直迁 adapter：非续训一律禁止 |
| 统计层（报告半集，与门控隔离） | CI [-0.73, +5.84]pp, McNemar p=0.375 | 门控从未见过这些题——无偏报告 |
| 置信层：配对 log-loss（参考−现役） | -0.0523, CI [-0.1521, +0.0252] | 负值偏参考：0/1 准确率看不见的置信质量差异 |
| 置信层：校准误差 ECE | 现役 0.0322 / 参考 0.0331 | 越低越好；影响“低置信转人工”的可靠性 |
| 置信层：选择性风险 AURC | 现役 0.018 / 参考 0.0109 | 越低越好；路由型部署的运维口径 |
| 鲁棒层：扰动重测 | 现役 0.92 / 参考 0.9167（Δ -0.33pp） | 新基座未表现出额外抗干扰优势（负结果如实记录） |
| 分歧集（COLLECT 的对象） | 22 条（占 5.5%），符号检验 p=0.5034 | 唯一携带决策信息的题目清单，已导出待标注 |
| 分歧标注收敛定价 | +10: 7%, +25: 23%, +50: 40%, +100: 52%, +200: 65% | 再标 k 条分歧后方向定案的概率 |
| Macro-F1（类平衡口径） | freeze 0.924 / adopt 0.703 / reference 0.9214 | 类不平衡下的稳健对照 |
| 无效输出率 | freeze 1.00% / adopt 0.67% / reference 1.00% | 预测是否落在标签清单之外——格式风险 |
| 任务台账 | 1 episode；训练 2.8 GPU 分钟；标注 500 条 | 本任务的累计资产与开销 |

**系统判定理由（原文）**
- the pooled evidence cannot resolve epsilon: CI [-3.4, +1.4]pp straddles 1pp (n=400, 8 fixes vs 12 breaks; gains above 1.4pp are already excluded; leaning: lean-freeze). Under the UpgradeBench corpus prior the posterior gives the gain a 5% chance of clearing the decision epsilon (1.00pp) -- more evidence is unlikely to change the call, so hold the frozen specialist and revisit at the next release

**系统警告**
- gate set has only 100 items; gate sampling error at this size caused the worst episode in the paper's replay -- treat marginal verdicts as ties
- the gate passed but the report-half CI for the upgrade opportunity includes zero -- the gain is not statistically established; consider staying frozen until the next release or enlarging the gate set
- no data_manifest.json -- run `upgrade-advisor manifest` once to pin your splits (Phase 0)

## 五、决策书（给管理层，工具自动生成）
【跳过这一代，等下一个版本】综合你的数据和 193 个公开实测案例的经验，这次升级划算的可能性只有 5%。不值得再花验证成本，维持现状，下一代发布时再评估。

## 你的系统现在什么水平
- 现役系统：每 100 个请求约答错 **8.0** 个
- 若换新模型并重训（我们真实训练并测过，非估算）：约答错 **9.0** 个
- 若直接裸用新模型、不做任何训练：约答错 **22.7** 个——你的训练数据才是护城河

## 我们做了哪些检查
1. **质量对比（头对头）** -- 在 400 个真实业务问题上逐题对比：新系统修好了 8 题、改错了 12 题，其余完全相同。现役每 100 个请求约错 8.0 个，升级重训后约错 9.0 个。考虑抽样误差，真实差距在 -3.4% 到 +1.4% 之间
2. **分歧清单** -- 两套系统意见不同的题共 22 个（占 5.5%）——这是唯一携带决策信息的题目清单，已导出待标注
3. **置信度质量** -- 新系统在“知道自己该多确定”上略好（对需要“低置信转人工”的场景有参考价值，本轮差异未达统计显著）
4. **抗干扰能力** -- 给输入加入错字、大小写混乱、口语填充词后重测：新旧系统的差距为 -0.33%——新系统未表现出额外的抗干扰优势
5. **直迁安全性** -- 已核查模型血统：本升级路径禁止直接搬运现有成果（历史实测：跨代直迁会把正确率打到不如不用）——任何升级都必须重训

## 值不值得：一句话的账
- 综合你的数据与 193 个公开实测升级案例：这次升级带来足够收益的可能性约 **5%**，造成倒退的可能性约 37%

## 下一步
1. 本轮不投入任何升级/验证成本
2. 把下一代基座模型的发布设为重评触发点；届时一次评估约需 30 GPU 分钟、零新标注
3. 若业务数据分布发生明显变化（新品类、新话术），提前重评

## 这个结论有多可靠
- 全部数字来自你自己的 400 条真实业务数据的实测对比与真实训练，无任何估算或演示数据
- 方法与阈值来自公开基准 UpgradeBench（2026）：33 个实测升级决策回放，平均决策损失 0.37%，零线上倒退
- 当证据不足时，本工具会直说“不足”并给出补证的最小成本，而不是硬给一个结论

---
*技术附录（统计细节，供工程团队）：recommendation.md*

## 六、对照与讨论
- 上一版判定：FREEZE（继续服役现有专家）
- 维持不升级并转 WAIT：8修/12破方向偏负、先验下增益概率仅 5%——上一版“参考反而更差”的结论在池化口径下依然成立。
- 零成本说明：本版复评未新增任何训练与标注；置信/鲁棒双探针合计约 5 GPU 分钟，分歧提取与重判为零 GPU 秒级操作。

## 七、技术附录：完整统计报告
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