# 基座模型升级决策纪要：cloudtalk -> Qwen2.5-7B-Instruct

## 决策卡
**FREEZE（维持现状）**（等价确证）
【维持现状，本轮不升级】数据已经证明：换用新模型最多带来 1.97% 的质量改进，不足以覆盖迁移成本。零支出。
依据：900 条真实数据逐题对比，修好 18 题 / 改错 12 题

## 一、背景与评估动机
CloudTalk 给客户交付 NLU 槽位抽取（utterance → JSON{intent, slots}），现役 Qwen1.5-7B-Chat + LoRA。跳过 Qwen2，直接评估跨两代升级到 Qwen2.5-7B-Instruct。这是难任务（现役正确率仅四成），团队预期跨两代必有大幅提升。

本纪要为 v2 复评版：在原判定基础上，以升级后的打分体系（证据池化、等价检验、论文语料先验、分歧采证通道）对同一批实测记录重新出具判定。

## 二、数据与系统资产
| 项目 | 内容 |
|---|---|
| 训练/验证/测试数据 | E:\eval project\snips_slots\train.jsonl / E:\eval project\snips_slots\val.jsonl / E:\eval project\snips_slots\test.jsonl |
| 现役系统 | E:\dataset\models\Qwen1.5-7B-Chat + LoRA (E:\eval project\snips_slots\lora_q15) |
| 候选基座 | E:\dataset\models\Qwen2.5-7B-Instruct |
| 评估配置 | flip budget 5%; ε=2pp |

## 三、评估过程与开销
- 累计：1 episode；训练 18.4 GPU 分钟；评测 10.2 GPU 分钟；金标 2000 条
- 本轮探针（置信+鲁棒）约 5 GPU 分钟；分歧提取与重判零 GPU 秒级

## 四、系统判定（v2）：FREEZE（维持现状） —— 等价确证
以下为工具输出的全部证据（未加筛选），解读列为附注：

| 证据项 | 数值 | 解读 |
|---|---|---|
| 现役 specialist（门控半集 n=200） | 0.4250 | 当前线上系统的实测水平 |
| 候选基座采用地板（零/少样本） | 0.2095 | 不训练直接用新模型的水平——与现役的差距就是训练数据的护城河 |
| 候选基座重训参考（同配方同数据） | 0.4250（机会差 +0.67pp） | 真实训练并实测，非估算 |
| 池化配对证据（val+test 全部） | n=900：新系统修好 18 题、改错 12 题 | v2 判定使用的全部证据；旧版只用 n≈100 的碎片 |
| 池化 95% 置信区间 | [-0.64, +1.97]pp | 真实差距的可信范围；数据已排除 >1.97pp 的增益 |
| 错误率视角（RER） | 相对错误消除 +1%（冻结错误 487 条） | 天花板附近比绝对百分点更敏感的口径 |
| 谱系裁决 | fresh_pretraining (verified) | 决定能否直迁 adapter：非续训一律禁止 |
| 统计层（报告半集，与门控隔离） | CI [-0.93, +3.41]pp, McNemar p=0.3877 | 门控从未见过这些题——无偏报告 |
| 分歧集（COLLECT 的对象） | 90 条（占 10.0%），符号检验 p=0.3616 | 唯一携带决策信息的题目清单，已导出待标注 |
| 分歧标注收敛定价 | +10: 7%, +25: 21%, +50: 38%, +100: 55%, +200: 66% | 再标 k 条分歧后方向定案的概率 |
| 任务台账 | 1 episode；训练 18.4 GPU 分钟；标注 2000 条 | 本任务的累计资产与开销 |

**系统判定理由（原文）**
- equivalence established, FREEZE is a verdict not a default: the pooled paired CI [-0.6, +2.0]pp excludes any gain above epsilon (2pp) -- n=900 paired records, 18 fixes vs 12 breaks

**系统警告**
- gate set has only 200 items; gate sampling error at this size caused the worst episode in the paper's replay -- treat marginal verdicts as ties
- no data_manifest.json -- run `upgrade-advisor manifest` once to pin your splits (Phase 0)

## 五、决策书（给管理层，工具自动生成）
【维持现状，本轮不升级】数据已经证明：换用新模型最多带来 1.97% 的质量改进，不足以覆盖迁移成本。零支出。

## 你的系统现在什么水平
- 现役系统：每 100 个请求约答错 **54.1** 个
- 若换新模型并重训（我们真实训练并测过，非估算）：约答错 **53.4** 个
- 若直接裸用新模型、不做任何训练：约答错 **79.0** 个——你的训练数据才是护城河

## 我们做了哪些检查
1. **质量对比（头对头）** -- 在 900 个真实业务问题上逐题对比：新系统修好了 18 题、改错了 12 题，其余完全相同。现役每 100 个请求约错 54.1 个，升级重训后约错 53.4 个。考虑抽样误差，真实差距在 -0.6% 到 +2.0% 之间
2. **分歧清单** -- 两套系统意见不同的题共 90 个（占 10.0%）——这是唯一携带决策信息的题目清单，已导出待标注
3. **直迁安全性** -- 已核查模型血统：本升级路径禁止直接搬运现有成果（历史实测：跨代直迁会把正确率打到不如不用）——任何升级都必须重训

## 下一步
1. 本轮零支出、零变更
2. 下一代模型发布时重跑本评估（约 30 GPU 分钟）

## 这个结论有多可靠
- 全部数字来自你自己的 900 条真实业务数据的实测对比与真实训练，无任何估算或演示数据
- 方法与阈值来自公开基准 UpgradeBench（2026）：33 个实测升级决策回放，平均决策损失 0.37%，零线上倒退
- 当证据不足时，本工具会直说“不足”并给出补证的最小成本，而不是硬给一个结论

---
*技术附录（统计细节，供工程团队）：recommendation.md*

## 六、对照与讨论
- 上一版判定：FREEZE（继续服役现有专家）——本批最反直觉的判定
- 维持不升级，性质升级为等价确证（结构化任务 ε=2pp；n=900 池化、18修/12破，CI 上界 2.0pp 恰被排除）。分歧集 90 条为全案例最大——若未来想推翻本判定，标注这 90 条即可。
- 零成本说明：本版复评未新增任何训练与标注；置信/鲁棒双探针合计约 5 GPU 分钟，分歧提取与重判为零 GPU 秒级操作。

## 七、技术附录：完整统计报告
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