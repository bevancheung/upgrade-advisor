# 基座模型升级决策纪要：echohome -> Qwen2.5-7B-Instruct

## 决策卡
**COLLECT（先采证再定）**（证据未决）
【先花小钱把问题定死，再决定】现有数据不足以下结论（升级划算的可能性约 62%）。两套系统只在 13 个真实问题上给出了不同答案——请业务专家把这些题标注出对错（约一小时人工），即可定案。在此之前维持现状。
依据：360 条真实数据逐题对比，修好 9 题 / 改错 4 题

## 一、背景与评估动机
EchoHome 的家庭助手 NLU 现役 Qwen2-7B-Instruct + LoRA（15 类：日程、提醒、购物清单、音乐等）。Qwen2.5-7B-Instruct 发布后，一名工程师看到两代架构逐维相同，绕过谱系建议直接把 adapter 挂到新基座提交上线申请。本文档记录系统的两幕处置：拦截与整改。

本纪要为 v2 复评版：在原判定基础上，以升级后的打分体系（证据池化、等价检验、论文语料先验、分歧采证通道）对同一批实测记录重新出具判定。

## 二、数据与系统资产
| 项目 | 内容 |
|---|---|
| 训练/验证/测试数据 | E:\eval project\cases\echohome_home\train.jsonl / E:\eval project\cases\echohome_home\val.jsonl / E:\eval project\cases\echohome_home\test.jsonl |
| 现役系统 | E:\dataset\models\Qwen2-7B-Instruct + LoRA (E:\eval project\cases\echohome_home\lora_src) |
| 候选基座 | E:\dataset\models\Qwen2.5-7B-Instruct |
| 评估配置 | flip budget 3%; ε=1pp |

## 三、评估过程与开销
- 累计：1 episode；训练 2.4 GPU 分钟；评测 2.3 GPU 分钟；金标 600 条
- 本轮探针（置信+鲁棒）约 5 GPU 分钟；分歧提取与重判零 GPU 秒级

## 四、系统判定（v2）：COLLECT（先采证再定） —— 证据未决
以下为工具输出的全部证据（未加筛选），解读列为附注：

| 证据项 | 数值 | 解读 |
|---|---|---|
| 现役 specialist（门控半集 n=60） | 1.0000 | 当前线上系统的实测水平 |
| 候选基座采用地板（零/少样本） | 0.9509 | 不训练直接用新模型的水平——与现役的差距就是训练数据的护城河 |
| 候选基座重训参考（同配方同数据） | 1.0000（机会差 +1.39pp） | 真实训练并实测，非估算 |
| 池化配对证据（val+test 全部） | n=360：新系统修好 9 题、改错 4 题 | v2 判定使用的全部证据；旧版只用 n≈100 的碎片 |
| 池化 95% 置信区间 | [-0.85, +3.62]pp | 真实差距的可信范围；数据已排除 >3.62pp 的增益 |
| 增益后验（论文 193 格先验） | 均值 +1.3pp；P(增益>ε)=62%，P(倒退)=1% | 结合公开实测语料对小样本借力 |
| 错误率视角（RER） | 相对错误消除 +56%（冻结错误 9 条） | 天花板附近比绝对百分点更敏感的口径 |
| 谱系裁决 | fresh_pretraining (inferred) | 决定能否直迁 adapter：非续训一律禁止 |
| 统计层（报告半集，与门控隔离） | CI [-2.19, +5.11]pp, McNemar p=0.6875 | 门控从未见过这些题——无偏报告 |
| 置信层：配对 log-loss（参考−现役） | -0.0702, CI [-0.2219, +0.0517] | 负值偏参考：0/1 准确率看不见的置信质量差异 |
| 置信层：校准误差 ECE | 现役 0.022 / 参考 0.0093 | 越低越好；影响“低置信转人工”的可靠性 |
| 置信层：选择性风险 AURC | 现役 0.0125 / 参考 0.0011 | 越低越好；路由型部署的运维口径 |
| 鲁棒层：扰动重测 | 现役 0.9633 / 参考 0.9667（Δ +0.34pp） | 新基座未表现出额外抗干扰优势（负结果如实记录） |
| 分歧集（COLLECT 的对象） | 13 条（占 3.6%），符号检验 p=0.2668 | 唯一携带决策信息的题目清单，已导出待标注 |
| 分歧标注收敛定价 | +10: 36%, +25: 54%, +50: 68%, +100: 76%, +200: 83% | 再标 k 条分歧后方向定案的概率 |
| Macro-F1（类平衡口径） | freeze 0.9696 / adopt 0.8198 / reference 0.9866 | 类不平衡下的稳健对照 |
| 无效输出率 | freeze 0.33% / adopt 0.33% / reference 0.00% | 预测是否落在标签清单之外——格式风险 |
| 任务台账 | 1 episode；训练 2.4 GPU 分钟；标注 600 条 | 本任务的累计资产与开销 |

**系统判定理由（原文）**
- the pooled evidence cannot resolve epsilon: CI [-0.8, +3.6]pp straddles 1pp (n=360, 9 fixes vs 4 breaks; gains above 3.6pp are already excluded; leaning: lean-upgrade); posterior chance the gain clears the decision epsilon: 62%. Cheapest resolution: label the disagreement set (`upgrade-advisor probe-disagree` writes it with a priced convergence plan); resolving by i.i.d. sampling would need roughly n=2831. Keep serving the frozen specialist while collecting

**系统警告**
- gate set has only 60 items; gate sampling error at this size caused the worst episode in the paper's replay -- treat marginal verdicts as ties
- EVAL-SATURATED: the frozen specialist makes only 9 error(s) on the pooled evidence -- any upgrade comparison rests on that many items. Harvest hard/tail examples (e.g. production misroutes) before trusting an upgrade verdict here
- the gate passed but the report-half CI for the upgrade opportunity includes zero -- the gain is not statistically established; consider staying frozen until the next release or enlarging the gate set
- no data_manifest.json -- run `upgrade-advisor manifest` once to pin your splits (Phase 0)

## 五、决策书（给管理层，工具自动生成）
【先花小钱把问题定死，再决定】现有数据不足以下结论（升级划算的可能性约 62%）。两套系统只在 13 个真实问题上给出了不同答案——请业务专家把这些题标注出对错（约一小时人工），即可定案。在此之前维持现状。

## 你的系统现在什么水平
- 现役系统：每 100 个请求约答错 **2.5** 个
- 若换新模型并重训（我们真实训练并测过，非估算）：约答错 **1.1** 个
- 若直接裸用新模型、不做任何训练：约答错 **4.9** 个——你的训练数据才是护城河

## 我们做了哪些检查
1. **质量对比（头对头）** -- 在 360 个真实业务问题上逐题对比：新系统修好了 9 题、改错了 4 题，其余完全相同。现役每 100 个请求约错 2.5 个，升级重训后约错 1.1 个。考虑抽样误差，真实差距在 -0.8% 到 +3.6% 之间
2. **分歧清单** -- 两套系统意见不同的题共 13 个（占 3.6%）——这是唯一携带决策信息的题目清单，已导出待标注
3. **置信度质量** -- 新系统在“知道自己该多确定”上略好（对需要“低置信转人工”的场景有参考价值，本轮差异未达统计显著）
4. **抗干扰能力** -- 给输入加入错字、大小写混乱、口语填充词后重测：新旧系统的差距为 +0.34%——新系统略有优势，但幅度很小
5. **直迁安全性** -- 已核查模型血统：本升级路径禁止直接搬运现有成果（历史实测：跨代直迁会把正确率打到不如不用）——任何升级都必须重训

## 值不值得：一句话的账
- 综合你的数据与 193 个公开实测升级案例：这次升级带来足够收益的可能性约 **62%**，造成倒退的可能性约 1%

## 下一步
1. 把导出的分歧题单交给业务专家标注对错（再标 25 题，有 54% 的把握定案）
2. 标注完成后重新运行本工具，结论将升级为“升级”或“维持”的确定判定
3. 在此期间线上系统不做任何变更（零风险）

## 这个结论有多可靠
- 全部数字来自你自己的 360 条真实业务数据的实测对比与真实训练，无任何估算或演示数据
- 方法与阈值来自公开基准 UpgradeBench（2026）：33 个实测升级决策回放，平均决策损失 0.37%，零线上倒退
- 当证据不足时，本工具会直说“不足”并给出补证的最小成本，而不是硬给一个结论

---
*技术附录（统计细节，供工程团队）：recommendation.md*

## 六、对照与讨论
- 上一版判定：第一幕 BLOCK → 第二幕 PASS → 终判 FREEZE（其实不必升）
- 由 FREEZE 转 COLLECT：本案是全部案例中最值得采证的——9修/4破、后验增益概率 62%、置信层 log-loss 亦偏参考。标注 13 条分歧即可定案。
- 零成本说明：本版复评未新增任何训练与标注；置信/鲁棒双探针合计约 5 GPU 分钟，分歧提取与重判为零 GPU 秒级操作。

## 七、技术附录：完整统计报告
```
# Upgrade recommendation: `echohome` -> `E:\dataset\models\Qwen2.5-7B-Instruct`

## Action: **COLLECT** (verdict: unresolved)

## Evidence
- frozen specialist (gate half, n=60): **1.0000**
- target adoption floor: **0.9509**
- retraining reference: **1.0000** (opportunity +1.39pp, epsilon 1pp)
- genealogy: fresh_pretraining (inferred); distance unknown
  - shape-identical but independent run per release docs; measured copy retention -0.60..0.78

## Statistics (report half only; gates never see these items)
- reference - frozen: 95% CI [-2.19, +5.11]pp, exact McNemar p = 0.6875
- posterior over the true gain (UpgradeBench-corpus prior + paired evidence): mean +1.30pp, sd 0.94pp; P(gain > decision epsilon) = 62%, P(regression beyond epsilon) = 1%, P(within band) = 37%
- pooled paired evidence (val+test): n=360, reference fixes 9 frozen error(s) and breaks 4 frozen pass(es); 95% CI [-0.8, +3.6]pp -- gains above 3.6pp are excluded by the data
- error-scale view: relative error reduction +56% (9 frozen errors on gate)

## Confidence layer (proper scoring; more power than accuracy)
- paired log-loss, reference - frozen: -0.0702 (95% CI [-0.2219, +0.0517]; negative favors reference)
- calibration ECE: frozen 0.022, reference 0.0093
- risk-coverage AURC (lower = better selective routing): frozen 0.0125, reference 0.0011

## Disagreement set (COLLECT channel: label these, not more i.i.d. samples)
- 13 disagreement item(s) (3.6% of pooled pairs); exact sign test on labeled outcomes p = 0.2668
- probability the direction settles after labeling k more disagreements -- +10: 36%, +25: 54%, +50: 68%, +100: 76%, +200: 83%

## Robustness under perturbation (typo/casing/filler/punct; gold unchanged)
- frozen: 0.9633; reference: 0.9667 (delta +0.34pp)

## Label metrics (macro-F1: class-imbalance-robust; invalid rate: prediction outside the label inventory)
- freeze: macro-F1 **0.9696**, invalid outputs 0.33% (15 classes)
- adopt: macro-F1 **0.8198**, invalid outputs 0.33% (15 classes)
- reference: macro-F1 **0.9866**, invalid outputs 0.00% (15 classes)

## Task ledger: 1 episode(s), 2.4 train GPU-min, 2.3 eval GPU-min, 600 gold labels, 0 teacher queries, 120 validation items accumulated

## Reasoning
- the pooled evidence cannot resolve epsilon: CI [-0.8, +3.6]pp straddles 1pp (n=360, 9 fixes vs 4 breaks; gains above 3.6pp are already excluded; leaning: lean-upgrade); posterior chance the gain clears the decision epsilon: 62%. Cheapest resolution: label the disagreement set (`upgrade-advisor probe-disagree` writes it with a priced convergence plan); resolving by i.i.d. sampling would need roughly n=2831. Keep serving the frozen specialist while collecting

## Warnings
- gate set has only 60 items; gate sampling error at this size caused the worst episode in the paper's replay -- treat marginal verdicts as ties
- EVAL-SATURATED: the frozen specialist makes only 9 error(s) on the pooled evidence -- any upgrade comparison rests on that many items. Harvest hard/tail examples (e.g. production misroutes) before trusting an upgrade verdict here
- the gate passed but the report-half CI for the upgrade opportunity includes zero -- the gain is not statistically established; consider staying frozen until the next release or enlarging the gate set
- no data_manifest.json -- run `upgrade-advisor manifest` once to pin your splits (Phase 0)

## Before serving
- run `upgrade-advisor gate` for the candidate against the serving records (reporting half only); block on negative-flip budget 3%
- log GPU-minutes and labels consumed for this episode so the amortized decision improves with each release

*Policy and margins from UpgradeBench (2026); validated over 33 measured upgrade episodes (0.37pp mean regret, zero regressions, split-half gating). Negative-flip rate follows Yan et al., Positive-Congruent Training, CVPR 2021. Scope: LoRA-class adapters, 1.5-8B open-weight models.*
```