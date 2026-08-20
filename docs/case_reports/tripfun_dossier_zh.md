# 基座模型升级决策纪要：tripfun -> Qwen2.5-1.5B-Instruct

## 决策卡
**FREEZE（维持现状）**（等价确证）
【维持现状，本轮不升级】数据已经证明：换用新模型最多带来 0.94% 的质量改进，不足以覆盖迁移成本。零支出。
依据：400 条真实数据逐题对比，修好 1 题 / 改错 1 题

## 一、背景与评估动机
TripFun 的旅行助手跑在用户手机端，用 Qwen2-1.5B-Instruct（小模型，端侧算力约束）+ LoRA 做 15 类旅行意图分类（订票、签证、时区、汇率、行李等）。Qwen2.5-1.5B-Instruct 发布后评估升级。两代 1.5B 架构逐维相同——工程团队原本想直接把 adapter 拷过去。

本纪要为 v2 复评版：在原判定基础上，以升级后的打分体系（证据池化、等价检验、论文语料先验、分歧采证通道）对同一批实测记录重新出具判定。

## 二、数据与系统资产
| 项目 | 内容 |
|---|---|
| 训练/验证/测试数据 | E:\eval project\cases\tripfun_travel\train.jsonl / E:\eval project\cases\tripfun_travel\val.jsonl / E:\eval project\cases\tripfun_travel\test.jsonl |
| 现役系统 | E:\dataset\models\Qwen2-1.5B-Instruct + LoRA (E:\eval project\cases\tripfun_travel\lora_src) |
| 候选基座 | E:\dataset\models\Qwen2.5-1.5B-Instruct |
| 评估配置 | flip budget 3%; ε=1pp |

## 三、评估过程与开销
- 累计：1 episode；训练 2.4 GPU 分钟；评测 1.6 GPU 分钟；金标 600 条
- 本轮探针（置信+鲁棒）约 5 GPU 分钟；分歧提取与重判零 GPU 秒级

## 四、系统判定（v2）：FREEZE（维持现状） —— 等价确证
以下为工具输出的全部证据（未加筛选），解读列为附注：

| 证据项 | 数值 | 解读 |
|---|---|---|
| 现役 specialist（门控半集 n=100） | 0.9900 | 当前线上系统的实测水平 |
| 候选基座采用地板（零/少样本） | 0.8712 | 不训练直接用新模型的水平——与现役的差距就是训练数据的护城河 |
| 候选基座重训参考（同配方同数据） | 1.0000（机会差 +0.0pp） | 真实训练并实测，非估算 |
| 池化配对证据（val+test 全部） | n=400：新系统修好 1 题、改错 1 题 | v2 判定使用的全部证据；旧版只用 n≈100 的碎片 |
| 池化 95% 置信区间 | [-0.94, +0.94]pp | 真实差距的可信范围；数据已排除 >0.94pp 的增益 |
| 错误率视角（RER） | 相对错误消除 +0%（冻结错误 2 条） | 天花板附近比绝对百分点更敏感的口径 |
| 谱系裁决 | fresh_pretraining (inferred) | 决定能否直迁 adapter：非续训一律禁止 |
| 统计层（报告半集，与门控隔离） | CI [+0.0, +0.0]pp, McNemar p=1.0 | 门控从未见过这些题——无偏报告 |
| 置信层：配对 log-loss（参考−现役） | +0.0315, CI [+0.0002, +0.087] | 现役的置信质量不落下风 |
| 置信层：校准误差 ECE | 现役 0.0018 / 参考 0.007 | 越低越好；影响“低置信转人工”的可靠性 |
| 置信层：选择性风险 AURC | 现役 0.0 / 参考 0.0001 | 越低越好；路由型部署的运维口径 |
| 鲁棒层：扰动重测 | 现役 1.0 / 参考 0.9833（Δ -1.67pp） | 新基座未表现出额外抗干扰优势（负结果如实记录） |
| 分歧集（COLLECT 的对象） | 2 条（占 0.5%），符号检验 p=1.0 | 唯一携带决策信息的题目清单，已导出待标注 |
| 分歧标注收敛定价 | +10: 22%, +25: 38%, +50: 58%, +100: 70%, +200: 79% | 再标 k 条分歧后方向定案的概率 |
| Macro-F1（类平衡口径） | freeze 0.9968 / adopt 0.8712 / reference 0.9938 | 类不平衡下的稳健对照 |
| 无效输出率 | freeze 0.00% / adopt 3.00% / reference 0.00% | 预测是否落在标签清单之外——格式风险 |
| 任务台账 | 1 episode；训练 2.4 GPU 分钟；标注 600 条 | 本任务的累计资产与开销 |

**系统判定理由（原文）**
- equivalence established, FREEZE is a verdict not a default: the pooled paired CI [-0.9, +0.9]pp excludes any gain above epsilon (1pp) -- n=400 paired records, 1 fixes vs 1 breaks

**系统警告**
- gate set has only 100 items; gate sampling error at this size caused the worst episode in the paper's replay -- treat marginal verdicts as ties
- EVAL-SATURATED: the frozen specialist makes only 2 error(s) on the pooled evidence -- any upgrade comparison rests on that many items. Harvest hard/tail examples (e.g. production misroutes) before trusting an upgrade verdict here
- no data_manifest.json -- run `upgrade-advisor manifest` once to pin your splits (Phase 0)

## 五、决策书（给管理层，工具自动生成）
【维持现状，本轮不升级】数据已经证明：换用新模型最多带来 0.94% 的质量改进，不足以覆盖迁移成本。零支出。

## 你的系统现在什么水平
- 现役系统：每 100 个请求约答错 **0.5** 个
- 若换新模型并重训（我们真实训练并测过，非估算）：约答错 **0.5** 个
- 若直接裸用新模型、不做任何训练：约答错 **12.9** 个——你的训练数据才是护城河

## 我们做了哪些检查
1. **质量对比（头对头）** -- 在 400 个真实业务问题上逐题对比：新系统修好了 1 题、改错了 1 题，其余完全相同。现役每 100 个请求约错 0.5 个，升级重训后约错 0.5 个。考虑抽样误差，真实差距在 -0.9% 到 +0.9% 之间
2. **分歧清单** -- 两套系统意见不同的题共 2 个（占 0.5%）——这是唯一携带决策信息的题目清单，已导出待标注
3. **置信度质量** -- 现役系统的置信度质量不落下风（对需要“低置信转人工”的场景有参考价值，本轮差异未达统计显著）
4. **抗干扰能力** -- 给输入加入错字、大小写混乱、口语填充词后重测：新旧系统的差距为 -1.67%——新系统未表现出额外的抗干扰优势
5. **直迁安全性** -- 已核查模型血统：本升级路径禁止直接搬运现有成果（历史实测：跨代直迁会把正确率打到不如不用）——任何升级都必须重训

## 下一步
1. 本轮零支出、零变更
2. 下一代模型发布时重跑本评估（约 30 GPU 分钟）

## 这个结论有多可靠
- 全部数字来自你自己的 400 条真实业务数据的实测对比与真实训练，无任何估算或演示数据
- 方法与阈值来自公开基准 UpgradeBench（2026）：33 个实测升级决策回放，平均决策损失 0.37%，零线上倒退
- 当证据不足时，本工具会直说“不足”并给出补证的最小成本，而不是硬给一个结论

---
*技术附录（统计细节，供工程团队）：recommendation.md*

## 六、对照与讨论
- 上一版判定：FREEZE（继续服役现有专家）
- 维持不升级，但性质升级：旧版是“无可测收益”的默认冻结；本版是等价确证——数据已排除 >0.9pp 的增益，附排除界的正式判定。
- 零成本说明：本版复评未新增任何训练与标注；置信/鲁棒双探针合计约 5 GPU 分钟，分歧提取与重判为零 GPU 秒级操作。

## 七、技术附录：完整统计报告
```
# Upgrade recommendation: `tripfun` -> `E:\dataset\models\Qwen2.5-1.5B-Instruct`

## Action: **FREEZE** (verdict: equivalence)

## Evidence
- frozen specialist (gate half, n=100): **0.9900**
- target adoption floor: **0.8712**
- retraining reference: **1.0000** (opportunity +0.00pp, epsilon 1pp)
- genealogy: fresh_pretraining (inferred); distance unknown
  - shape-identical independent run; paper measured copy retention -0.60..0.10 at this scale

## Statistics (report half only; gates never see these items)
- reference - frozen: 95% CI [+0.00, +0.00]pp, exact McNemar p = 1.0
- pooled paired evidence (val+test): n=400, reference fixes 1 frozen error(s) and breaks 1 frozen pass(es); 95% CI [-0.9, +0.9]pp -- gains above 0.9pp are excluded by the data
- error-scale view: relative error reduction +0% (2 frozen errors on gate)

## Confidence layer (proper scoring; more power than accuracy)
- paired log-loss, reference - frozen: +0.0315 (95% CI [+0.0002, +0.0870]; negative favors reference)
- calibration ECE: frozen 0.0018, reference 0.007
- risk-coverage AURC (lower = better selective routing): frozen 0.0, reference 0.0001

## Disagreement set (COLLECT channel: label these, not more i.i.d. samples)
- 2 disagreement item(s) (0.5% of pooled pairs); exact sign test on labeled outcomes p = 1.0
- probability the direction settles after labeling k more disagreements -- +10: 22%, +25: 38%, +50: 58%, +100: 70%, +200: 79%

## Robustness under perturbation (typo/casing/filler/punct; gold unchanged)
- frozen: 1.0; reference: 0.9833 (delta -1.67pp)

## Label metrics (macro-F1: class-imbalance-robust; invalid rate: prediction outside the label inventory)
- freeze: macro-F1 **0.9968**, invalid outputs 0.00% (15 classes)
- adopt: macro-F1 **0.8712**, invalid outputs 3.00% (15 classes)
- reference: macro-F1 **0.9938**, invalid outputs 0.00% (15 classes)

## Task ledger: 1 episode(s), 2.4 train GPU-min, 1.6 eval GPU-min, 600 gold labels, 0 teacher queries, 200 validation items accumulated

## Reasoning
- equivalence established, FREEZE is a verdict not a default: the pooled paired CI [-0.9, +0.9]pp excludes any gain above epsilon (1pp) -- n=400 paired records, 1 fixes vs 1 breaks

## Warnings
- gate set has only 100 items; gate sampling error at this size caused the worst episode in the paper's replay -- treat marginal verdicts as ties
- EVAL-SATURATED: the frozen specialist makes only 2 error(s) on the pooled evidence -- any upgrade comparison rests on that many items. Harvest hard/tail examples (e.g. production misroutes) before trusting an upgrade verdict here
- no data_manifest.json -- run `upgrade-advisor manifest` once to pin your splits (Phase 0)

## Before serving
- run `upgrade-advisor gate` for the candidate against the serving records (reporting half only); block on negative-flip budget 3%
- log GPU-minutes and labels consumed for this episode so the amortized decision improves with each release

*Policy and margins from UpgradeBench (2026); validated over 33 measured upgrade episodes (0.37pp mean regret, zero regressions, split-half gating). Negative-flip rate follows Yan et al., Positive-Congruent Training, CVPR 2021. Scope: LoRA-class adapters, 1.5-8B open-weight models.*
```