# 基座模型升级决策纪要：newsdesk -> Qwen2.5-7B-Instruct-1M

## 决策卡
**FREEZE（维持现状）**（等价确证）
【维持现状，本轮不升级】数据已经证明：换用新模型最多带来 0.76% 的质量改进，不足以覆盖迁移成本。零支出。
依据：500 条真实数据逐题对比，修好 2 题 / 改错 4 题

## 一、背景与评估动机
NewsDesk 编辑部用 Qwen2.5-7B-Instruct + LoRA 做稿件四大栏目（时政/体育/财经/科技）自动分栏。厂商发布长上下文版 Qwen2.5-7B-Instruct-1M——注册表记录其为同一权重的文档化延续（约 20B token）。这是五案例中唯一 Copy 被谱系许可并实测的一例。

本纪要为 v2 复评版：在原判定基础上，以升级后的打分体系（证据池化、等价检验、论文语料先验、分歧采证通道）对同一批实测记录重新出具判定。

## 二、数据与系统资产
| 项目 | 内容 |
|---|---|
| 训练/验证/测试数据 | E:\eval project\cases\newsdesk_agnews\train.jsonl / E:\eval project\cases\newsdesk_agnews\val.jsonl / E:\eval project\cases\newsdesk_agnews\test.jsonl |
| 现役系统 | E:\dataset\models\Qwen2.5-7B-Instruct + LoRA (E:\eval project\cases\newsdesk_agnews\lora_src) |
| 候选基座 | E:\dataset\models\Qwen2.5-7B-Instruct-1M |
| 评估配置 | flip budget 3%; ε=1pp |

## 三、评估过程与开销
- 累计：1 episode；训练 5.4 GPU 分钟；评测 3.4 GPU 分钟；金标 800 条
- 本轮探针（置信+鲁棒）约 5 GPU 分钟；分歧提取与重判零 GPU 秒级

## 四、系统判定（v2）：FREEZE（维持现状） —— 等价确证
以下为工具输出的全部证据（未加筛选），解读列为附注：

| 证据项 | 数值 | 解读 |
|---|---|---|
| 现役 specialist（门控半集 n=100） | 0.9000 | 当前线上系统的实测水平 |
| 候选基座采用地板（零/少样本） | 0.8465 | 不训练直接用新模型的水平——与现役的差距就是训练数据的护城河 |
| 候选基座重训参考（同配方同数据） | 0.9000（机会差 -0.4pp） | 真实训练并实测，非估算 |
| 池化配对证据（val+test 全部） | n=500：新系统修好 2 题、改错 4 题 | v2 判定使用的全部证据；旧版只用 n≈100 的碎片 |
| 池化 95% 置信区间 | [-1.56, +0.76]pp | 真实差距的可信范围；数据已排除 >0.76pp 的增益 |
| 错误率视角（RER） | 相对错误消除 -5%（冻结错误 39 条） | 天花板附近比绝对百分点更敏感的口径 |
| 谱系裁决 | continuation (inferred), continuation 20B tokens | 决定能否直迁 adapter：非续训一律禁止 |
| 统计层（报告半集，与门控隔离） | CI [-1.62, +1.62]pp, McNemar p=1.0 | 门控从未见过这些题——无偏报告 |
| 置信层：配对 log-loss（参考−现役） | -0.0163, CI [-0.0368, +0.0028] | 负值偏参考：0/1 准确率看不见的置信质量差异 |
| 置信层：校准误差 ECE | 现役 0.0533 / 参考 0.0382 | 越低越好；影响“低置信转人工”的可靠性 |
| 置信层：选择性风险 AURC | 现役 0.0431 / 参考 0.0347 | 越低越好；路由型部署的运维口径 |
| 鲁棒层：扰动重测 | 现役 0.9275 / 参考 0.9225（Δ -0.5pp） | 新基座未表现出额外抗干扰优势（负结果如实记录） |
| 分歧集（COLLECT 的对象） | 7 条（占 1.4%），符号检验 p=0.6875 | 唯一携带决策信息的题目清单，已导出待标注 |
| 分歧标注收敛定价 | +10: 16%, +25: 39%, +50: 57%, +100: 68%, +200: 77% | 再标 k 条分歧后方向定案的概率 |
| Macro-F1（类平衡口径） | freeze 0.9257 / adopt 0.8297 / reference 0.9209 / copy 0.9132 | 类不平衡下的稳健对照 |
| 无效输出率 | 全部 0.00% | 预测是否落在标签清单之外——格式风险 |
| 任务台账 | 1 episode；训练 5.4 GPU 分钟；标注 800 条 | 本任务的累计资产与开销 |

**系统判定理由（原文）**
- equivalence established, FREEZE is a verdict not a default: the pooled paired CI [-1.6, +0.8]pp excludes any gain above epsilon (1pp) -- n=500 paired records, 2 fixes vs 4 breaks

**系统警告**
- gate set has only 100 items; gate sampling error at this size caused the worst episode in the paper's replay -- treat marginal verdicts as ties
- no data_manifest.json -- run `upgrade-advisor manifest` once to pin your splits (Phase 0)

## 五、决策书（给管理层，工具自动生成）
【维持现状，本轮不升级】数据已经证明：换用新模型最多带来 0.76% 的质量改进，不足以覆盖迁移成本。零支出。

## 你的系统现在什么水平
- 现役系统：每 100 个请求约答错 **7.8** 个
- 若换新模型并重训（我们真实训练并测过，非估算）：约答错 **8.2** 个
- 若直接裸用新模型、不做任何训练：约答错 **15.3** 个——你的训练数据才是护城河

## 我们做了哪些检查
1. **质量对比（头对头）** -- 在 500 个真实业务问题上逐题对比：新系统修好了 2 题、改错了 4 题，其余完全相同。现役每 100 个请求约错 7.8 个，升级重训后约错 8.2 个。考虑抽样误差，真实差距在 -1.6% 到 +0.8% 之间
2. **分歧清单** -- 两套系统意见不同的题共 7 个（占 1.4%）——这是唯一携带决策信息的题目清单，已导出待标注
3. **置信度质量** -- 新系统在“知道自己该多确定”上略好（对需要“低置信转人工”的场景有参考价值，本轮差异未达统计显著）
4. **抗干扰能力** -- 给输入加入错字、大小写混乱、口语填充词后重测：新旧系统的差距为 -0.50%——新系统未表现出额外的抗干扰优势
5. **直迁安全性** -- 已核查模型血统：本升级路径允许直接搬运现有成果

## 下一步
1. 本轮零支出、零变更
2. 下一代模型发布时重跑本评估（约 30 GPU 分钟）

## 这个结论有多可靠
- 全部数字来自你自己的 500 条真实业务数据的实测对比与真实训练，无任何估算或演示数据
- 方法与阈值来自公开基准 UpgradeBench（2026）：33 个实测升级决策回放，平均决策损失 0.37%，零线上倒退
- 当证据不足时，本工具会直说“不足”并给出补证的最小成本，而不是硬给一个结论

---
*技术附录（统计细节，供工程团队）：recommendation.md*

## 六、对照与讨论
- 上一版判定：FREEZE（继续服役现有专家）
- 维持不升级，性质升级为等价确证（排除 >0.8pp 增益）。注意本案血统为 20B 续训、copy 本可许可，但机会门未开，许可无用武之地。
- 零成本说明：本版复评未新增任何训练与标注；置信/鲁棒双探针合计约 5 GPU 分钟，分歧提取与重判为零 GPU 秒级操作。

## 七、技术附录：完整统计报告
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