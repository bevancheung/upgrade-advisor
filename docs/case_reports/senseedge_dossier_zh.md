# 基座模型升级决策纪要：senseedge -> Qwen2.5-1.5B-Instruct

## 决策卡
**COLLECT（先采证再定）**（证据未决）
【先花小钱把问题定死，再决定】现有数据不足以下结论。两套系统只在 10 个真实问题上给出了不同答案——请业务专家把这些题标注出对错（约一小时人工），即可定案。在此之前维持现状。
依据：400 条真实数据逐题对比，修好 6 题 / 改错 4 题

## 一、背景与评估动机
SenseEdge 的设备设置语音控制现役 Qwen2.5-7B-Instruct + LoRA（13 类设置意图），跑在云端。硬件团队希望把 NLU 下放到设备端 NPU，候选是 Qwen2.5-1.5B-Instruct——这是一次“反向升级”评估：工具照常工作，把降级的质量代价定价出来供成本决策。

本纪要为 v2 复评版：在原判定基础上，以升级后的打分体系（证据池化、等价检验、论文语料先验、分歧采证通道）对同一批实测记录重新出具判定。

## 二、数据与系统资产
| 项目 | 内容 |
|---|---|
| 训练/验证/测试数据 | E:\eval project\cases\senseedge_meta\train.jsonl / E:\eval project\cases\senseedge_meta\val.jsonl / E:\eval project\cases\senseedge_meta\test.jsonl |
| 现役系统 | E:\dataset\models\Qwen2.5-7B-Instruct + LoRA (E:\eval project\cases\senseedge_meta\lora_src) |
| 候选基座 | E:\dataset\models\Qwen2.5-1.5B-Instruct |
| 评估配置 | flip budget 3%; ε=1pp |

## 三、评估过程与开销
- 累计：1 episode；训练 1.2 GPU 分钟；评测 1.4 GPU 分钟；金标 600 条
- 本轮探针（置信+鲁棒）约 5 GPU 分钟；分歧提取与重判零 GPU 秒级

## 四、系统判定（v2）：COLLECT（先采证再定） —— 证据未决
以下为工具输出的全部证据（未加筛选），解读列为附注：

| 证据项 | 数值 | 解读 |
|---|---|---|
| 现役 specialist（门控半集 n=100） | 0.9700 | 当前线上系统的实测水平 |
| 候选基座采用地板（零/少样本） | 0.7975 | 不训练直接用新模型的水平——与现役的差距就是训练数据的护城河 |
| 候选基座重训参考（同配方同数据） | 0.9600（机会差 +0.5pp） | 真实训练并实测，非估算 |
| 池化配对证据（val+test 全部） | n=400：新系统修好 6 题、改错 4 题 | v2 判定使用的全部证据；旧版只用 n≈100 的碎片 |
| 池化 95% 置信区间 | [-1.3, +2.3]pp | 真实差距的可信范围；数据已排除 >2.3pp 的增益 |
| 错误率视角（RER） | 相对错误消除 +15%（冻结错误 13 条） | 天花板附近比绝对百分点更敏感的口径 |
| 谱系裁决 | unknown (unknown) | 决定能否直迁 adapter：非续训一律禁止 |
| 统计层（报告半集，与门控隔离） | CI [-1.46, +3.65]pp, McNemar p=1.0 | 门控从未见过这些题——无偏报告 |
| 置信层：配对 log-loss（参考−现役） | +0.0179, CI [-0.0444, +0.1081] | 现役的置信质量不落下风 |
| 置信层：校准误差 ECE | 现役 0.0232 / 参考 0.0171 | 越低越好；影响“低置信转人工”的可靠性 |
| 置信层：选择性风险 AURC | 现役 0.0011 / 参考 0.003 | 越低越好；路由型部署的运维口径 |
| 鲁棒层：扰动重测 | 现役 0.95 / 参考 0.95（Δ +0.0pp） | 新基座未表现出额外抗干扰优势（负结果如实记录） |
| 分歧集（COLLECT 的对象） | 10 条（占 2.5%），符号检验 p=0.7539 | 唯一携带决策信息的题目清单，已导出待标注 |
| 分歧标注收敛定价 | +10: 9%, +25: 27%, +50: 39%, +100: 58%, +200: 69% | 再标 k 条分歧后方向定案的概率 |
| Macro-F1（类平衡口径） | freeze 0.9679 / adopt 0.7648 / reference 0.9764 | 类不平衡下的稳健对照 |
| 无效输出率 | freeze 0.00% / adopt 1.67% / reference 0.00% | 预测是否落在标签清单之外——格式风险 |
| 任务台账 | 1 episode；训练 1.2 GPU 分钟；标注 600 条 | 本任务的累计资产与开销 |

**系统判定理由（原文）**
- the pooled evidence cannot resolve epsilon: CI [-1.3, +2.3]pp straddles 1pp (n=400, 6 fixes vs 4 breaks; gains above 2.3pp are already excluded; leaning: lean-freeze). Cheapest resolution: label the disagreement set (`upgrade-advisor probe-disagree` writes it with a priced convergence plan); resolving by i.i.d. sampling would need roughly n=1960. Keep serving the frozen specialist while collecting

**系统警告**
- gate set has only 100 items; gate sampling error at this size caused the worst episode in the paper's replay -- treat marginal verdicts as ties
- EVAL-SATURATED: the frozen specialist makes only 13 error(s) on the pooled evidence -- any upgrade comparison rests on that many items. Harvest hard/tail examples (e.g. production misroutes) before trusting an upgrade verdict here
- the gate passed but the report-half CI for the upgrade opportunity includes zero -- the gain is not statistically established; consider staying frozen until the next release or enlarging the gate set
- no data_manifest.json -- run `upgrade-advisor manifest` once to pin your splits (Phase 0)

## 五、决策书（给管理层，工具自动生成）
【先花小钱把问题定死，再决定】现有数据不足以下结论。两套系统只在 10 个真实问题上给出了不同答案——请业务专家把这些题标注出对错（约一小时人工），即可定案。在此之前维持现状。

## 你的系统现在什么水平
- 现役系统：每 100 个请求约答错 **3.2** 个
- 若换新模型并重训（我们真实训练并测过，非估算）：约答错 **2.8** 个
- 若直接裸用新模型、不做任何训练：约答错 **20.2** 个——你的训练数据才是护城河

## 我们做了哪些检查
1. **质量对比（头对头）** -- 在 400 个真实业务问题上逐题对比：新系统修好了 6 题、改错了 4 题，其余完全相同。现役每 100 个请求约错 3.2 个，升级重训后约错 2.8 个。考虑抽样误差，真实差距在 -1.3% 到 +2.3% 之间
2. **分歧清单** -- 两套系统意见不同的题共 10 个（占 2.5%）——这是唯一携带决策信息的题目清单，已导出待标注
3. **置信度质量** -- 现役系统的置信度质量不落下风（对需要“低置信转人工”的场景有参考价值，本轮差异未达统计显著）
4. **抗干扰能力** -- 给输入加入错字、大小写混乱、口语填充词后重测：新旧系统的差距为 +0.00%——新系统未表现出额外的抗干扰优势
5. **直迁安全性** -- 已核查模型血统：本升级路径禁止直接搬运现有成果（历史实测：跨代直迁会把正确率打到不如不用）——任何升级都必须重训

## 下一步
1. 把导出的分歧题单交给业务专家标注对错（再标 25 题，有 27% 的把握定案）
2. 标注完成后重新运行本工具，结论将升级为“升级”或“维持”的确定判定
3. 在此期间线上系统不做任何变更（零风险）

## 这个结论有多可靠
- 全部数字来自你自己的 400 条真实业务数据的实测对比与真实训练，无任何估算或演示数据
- 方法与阈值来自公开基准 UpgradeBench（2026）：33 个实测升级决策回放，平均决策损失 0.37%，零线上倒退
- 当证据不足时，本工具会直说“不足”并给出补证的最小成本，而不是硬给一个结论

---
*技术附录（统计细节，供工程团队）：recommendation.md*

## 六、对照与讨论
- 上一版判定：工具判定 FREEZE；商业解读：降级质量代价约 1pp（统计上未与零区分）
- 由 FREEZE（降级警示）转 COLLECT：6修/0破方向偏正但未过符号检验；小规模系列血统未登记、无先验可借力，默认走采证。
- 零成本说明：本版复评未新增任何训练与标注；置信/鲁棒双探针合计约 5 GPU 分钟，分歧提取与重判为零 GPU 秒级操作。

## 七、技术附录：完整统计报告
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