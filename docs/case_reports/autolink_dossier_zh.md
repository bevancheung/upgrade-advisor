# 基座模型升级决策纪要：autolink -> OLMo-1.7-7B

## 决策卡
**FREEZE（维持现状）**（等价确证）
【维持现状，本轮不升级】数据已经证明：换用新模型最多带来 0.47% 的质量改进，不足以覆盖迁移成本。零支出。
依据：380 条真实数据逐题对比，修好 1 题 / 改错 5 题

## 一、背景与评估动机
AutoLink 因整车厂审计要求（训练数据与全流程可审计），NLU 模块只允许使用全开源模型，现役为 OLMo-1-7B（base 模型，plain 提示格式）+ LoRA，15 类车载意图（导航、油量、胎压、保养、路况等）。OLMo-1.7-7B 发布后评估升级。模型卡明确记载 1.7 为从零重训——正是论文验证过“复制必然崩溃”的那类对。

本纪要为 v2 复评版：在原判定基础上，以升级后的打分体系（证据池化、等价检验、论文语料先验、分歧采证通道）对同一批实测记录重新出具判定。

## 二、数据与系统资产
| 项目 | 内容 |
|---|---|
| 训练/验证/测试数据 | E:\eval project\cases\autolink_auto\train.jsonl / E:\eval project\cases\autolink_auto\val.jsonl / E:\eval project\cases\autolink_auto\test.jsonl |
| 现役系统 | E:\dataset\models\OLMo-1-7B + LoRA (E:\eval project\cases\autolink_auto\lora_src) |
| 候选基座 | E:\dataset\models\OLMo-1.7-7B |
| 评估配置 | flip budget 3%; ε=1pp |

## 三、评估过程与开销
- 累计：1 episode；训练 2.6 GPU 分钟；评测 4.1 GPU 分钟；金标 600 条
- 本轮探针（置信+鲁棒）约 5 GPU 分钟；分歧提取与重判零 GPU 秒级

## 四、系统判定（v2）：FREEZE（维持现状） —— 等价确证
以下为工具输出的全部证据（未加筛选），解读列为附注：

| 证据项 | 数值 | 解读 |
|---|---|---|
| 现役 specialist（门控半集 n=80） | 1.0000 | 当前线上系统的实测水平 |
| 候选基座采用地板（零/少样本） | 0.7791 | 不训练直接用新模型的水平——与现役的差距就是训练数据的护城河 |
| 候选基座重训参考（同配方同数据） | 1.0000（机会差 -1.05pp） | 真实训练并实测，非估算 |
| 池化配对证据（val+test 全部） | n=380：新系统修好 1 题、改错 5 题 | v2 判定使用的全部证据；旧版只用 n≈100 的碎片 |
| 池化 95% 置信区间 | [-2.57, +0.47]pp | 真实差距的可信范围；数据已排除 >0.47pp 的增益 |
| 错误率视角（RER） | 相对错误消除 -133%（冻结错误 3 条） | 天花板附近比绝对百分点更敏感的口径 |
| 谱系裁决 | fresh_pretraining (verified) | 决定能否直迁 adapter：非续训一律禁止 |
| 统计层（报告半集，与门控隔离） | CI [-3.65, +0.0]pp, McNemar p=0.5 | 门控从未见过这些题——无偏报告 |
| 置信层：配对 log-loss（参考−现役） | +0.0475, CI [-0.0001, +0.1072] | 现役的置信质量不落下风 |
| 置信层：校准误差 ECE | 现役 0.0093 / 参考 0.0174 | 越低越好；影响“低置信转人工”的可靠性 |
| 置信层：选择性风险 AURC | 现役 0.0002 / 参考 0.0021 | 越低越好；路由型部署的运维口径 |
| 鲁棒层：扰动重测 | 现役 0.98 / 参考 0.9733（Δ -0.67pp） | 新基座未表现出额外抗干扰优势（负结果如实记录） |
| 分歧集（COLLECT 的对象） | 6 条（占 1.6%），符号检验 p=0.2188 | 唯一携带决策信息的题目清单，已导出待标注 |
| 分歧标注收敛定价 | +10: 56%, +25: 73%, +50: 82%, +100: 87%, +200: 91% | 再标 k 条分歧后方向定案的概率 |
| Macro-F1（类平衡口径） | freeze 0.9899 / adopt 0.7409 / reference 0.9775 | 类不平衡下的稳健对照 |
| 无效输出率 | freeze 0.00% / adopt 4.33% / reference 0.67% | 预测是否落在标签清单之外——格式风险 |
| 任务台账 | 1 episode；训练 2.6 GPU 分钟；标注 600 条 | 本任务的累计资产与开销 |

**系统判定理由（原文）**
- equivalence established, FREEZE is a verdict not a default: the pooled paired CI [-2.6, +0.5]pp excludes any gain above epsilon (1pp) -- n=380 paired records, 1 fixes vs 5 breaks

**系统警告**
- gate set has only 80 items; gate sampling error at this size caused the worst episode in the paper's replay -- treat marginal verdicts as ties
- EVAL-SATURATED: the frozen specialist makes only 3 error(s) on the pooled evidence -- any upgrade comparison rests on that many items. Harvest hard/tail examples (e.g. production misroutes) before trusting an upgrade verdict here
- no data_manifest.json -- run `upgrade-advisor manifest` once to pin your splits (Phase 0)

## 五、决策书（给管理层，工具自动生成）
【维持现状，本轮不升级】数据已经证明：换用新模型最多带来 0.47% 的质量改进，不足以覆盖迁移成本。零支出。

## 你的系统现在什么水平
- 现役系统：每 100 个请求约答错 **0.8** 个
- 若换新模型并重训（我们真实训练并测过，非估算）：约答错 **1.8** 个
- 若直接裸用新模型、不做任何训练：约答错 **22.1** 个——你的训练数据才是护城河

## 我们做了哪些检查
1. **质量对比（头对头）** -- 在 380 个真实业务问题上逐题对比：新系统修好了 1 题、改错了 5 题，其余完全相同。现役每 100 个请求约错 0.8 个，升级重训后约错 1.8 个。考虑抽样误差，真实差距在 -2.6% 到 +0.5% 之间
2. **分歧清单** -- 两套系统意见不同的题共 6 个（占 1.6%）——这是唯一携带决策信息的题目清单，已导出待标注
3. **置信度质量** -- 现役系统的置信度质量不落下风（对需要“低置信转人工”的场景有参考价值，本轮差异未达统计显著）
4. **抗干扰能力** -- 给输入加入错字、大小写混乱、口语填充词后重测：新旧系统的差距为 -0.67%——新系统未表现出额外的抗干扰优势
5. **直迁安全性** -- 已核查模型血统：本升级路径禁止直接搬运现有成果（历史实测：跨代直迁会把正确率打到不如不用）——任何升级都必须重训

## 下一步
1. 本轮零支出、零变更
2. 下一代模型发布时重跑本评估（约 30 GPU 分钟）

## 这个结论有多可靠
- 全部数字来自你自己的 380 条真实业务数据的实测对比与真实训练，无任何估算或演示数据
- 方法与阈值来自公开基准 UpgradeBench（2026）：33 个实测升级决策回放，平均决策损失 0.37%，零线上倒退
- 当证据不足时，本工具会直说“不足”并给出补证的最小成本，而不是硬给一个结论

---
*技术附录（统计细节，供工程团队）：recommendation.md*

## 六、对照与讨论
- 上一版判定：FREEZE（继续服役现有专家）
- 维持不升级，性质升级为等价确证（排除 >0.5pp 增益；1修/5破，方向偏负）。
- 零成本说明：本版复评未新增任何训练与标注；置信/鲁棒双探针合计约 5 GPU 分钟，分歧提取与重判为零 GPU 秒级操作。

## 七、技术附录：完整统计报告
```
# Upgrade recommendation: `autolink` -> `E:\dataset\models\OLMo-1.7-7B`

## Action: **FREEZE** (verdict: equivalence)

## Evidence
- frozen specialist (gate half, n=80): **1.0000**
- target adoption floor: **0.7791**
- retraining reference: **1.0000** (opportunity -1.05pp, epsilon 1pp)
- genealogy: fresh_pretraining (verified); distance unknown
  - model card states trained from scratch; measured copy at or below the no-adapter floor

## Statistics (report half only; gates never see these items)
- reference - frozen: 95% CI [-3.65, +0.00]pp, exact McNemar p = 0.5
- pooled paired evidence (val+test): n=380, reference fixes 1 frozen error(s) and breaks 5 frozen pass(es); 95% CI [-2.6, +0.5]pp -- gains above 0.5pp are excluded by the data
- error-scale view: relative error reduction -133% (3 frozen errors on gate)

## Confidence layer (proper scoring; more power than accuracy)
- paired log-loss, reference - frozen: +0.0475 (95% CI [-0.0001, +0.1072]; negative favors reference)
- calibration ECE: frozen 0.0093, reference 0.0174
- risk-coverage AURC (lower = better selective routing): frozen 0.0002, reference 0.0021

## Disagreement set (COLLECT channel: label these, not more i.i.d. samples)
- 6 disagreement item(s) (1.6% of pooled pairs); exact sign test on labeled outcomes p = 0.2188
- probability the direction settles after labeling k more disagreements -- +10: 56%, +25: 73%, +50: 82%, +100: 87%, +200: 91%

## Robustness under perturbation (typo/casing/filler/punct; gold unchanged)
- frozen: 0.98; reference: 0.9733 (delta -0.67pp)

## Label metrics (macro-F1: class-imbalance-robust; invalid rate: prediction outside the label inventory)
- freeze: macro-F1 **0.9899**, invalid outputs 0.00% (15 classes)
- adopt: macro-F1 **0.7409**, invalid outputs 4.33% (15 classes)
- reference: macro-F1 **0.9775**, invalid outputs 0.67% (15 classes)

## Task ledger: 1 episode(s), 2.6 train GPU-min, 4.1 eval GPU-min, 600 gold labels, 0 teacher queries, 160 validation items accumulated

## Reasoning
- equivalence established, FREEZE is a verdict not a default: the pooled paired CI [-2.6, +0.5]pp excludes any gain above epsilon (1pp) -- n=380 paired records, 1 fixes vs 5 breaks

## Warnings
- gate set has only 80 items; gate sampling error at this size caused the worst episode in the paper's replay -- treat marginal verdicts as ties
- EVAL-SATURATED: the frozen specialist makes only 3 error(s) on the pooled evidence -- any upgrade comparison rests on that many items. Harvest hard/tail examples (e.g. production misroutes) before trusting an upgrade verdict here
- no data_manifest.json -- run `upgrade-advisor manifest` once to pin your splits (Phase 0)

## Before serving
- run `upgrade-advisor gate` for the candidate against the serving records (reporting half only); block on negative-flip budget 3%
- log GPU-minutes and labels consumed for this episode so the amortized decision improves with each release

*Policy and margins from UpgradeBench (2026); validated over 33 measured upgrade episodes (0.37pp mean regret, zero regressions, split-half gating). Negative-flip rate follows Yan et al., Positive-Congruent Training, CVPR 2021. Scope: LoRA-class adapters, 1.5-8B open-weight models.*
```