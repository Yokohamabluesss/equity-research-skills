# Stability: same input, same output? TSEM FY26 Q2 (2026-11-23)

[English](#english) | [中文](#中文)

<a id="english"></a>

**Question.** If the current skills run several times on the same input, do they give the same structure, the same judgments and the same facts?

**Short answer.** Yes for structure and judgment; mostly for facts. All six runs pass their validators. The three digests give the same tag and the same five marks. The three call logs split the business the same way, quote the transcript word for word, and differ mainly in which supporting numbers they pick.

## Setup

| | earnings-call-reader | earnings-digest |
|---|---|---|
| version | v1.6.0 | v1.6.0 |
| input | TSEM FY26 Q2 transcript (local file) | TSEM call log (FY26 Q2 the latest quarter) |
| runs | 3, each in a fresh session | 3, each in a fresh session |
| output | a new call log (Chinese) | a digest of the latest quarter (Chinese) |

Metrics: [`evaluation/stability.py`](../stability.py) (definitions in the [README](../README.md#stability-metrics-stabilitypy)). Before/after comparison with the earlier skills was not part of this run.

## Results

| skill | runs | valid | same tag | same marks | same sections | number overlap | quotes verbatim | numbers traceable | length cv |
|---|---|---|---|---|---|---|---|---|---|
| earnings-call-reader | 3 | 100% | — | — | 97% | 89% | 99% | 89% | 0.02 |
| earnings-digest | 3 | 100% | 100% | 100% | — | 78% | 100% | 100% | 0.06 |

## Findings

- **The validators do their job.** All three digests first carried too many numbers in the Financials line; the validator warned, and each run cut them back to a few anchors before finishing. All call logs passed on the first try.
- **Judgment is stable.** Every digest tagged the quarter "beat · beat-raise" and gave the same marks: Financials ✅️, Sub-industry ⚠️, Orders ⚠️, Customers ⚠️, Momentum ✅️. This bears on the open Orders question in the [skill-vs-human report](2026-11-22_skill-vs-human.md): the skill's ⚠️ on Orders is a consistent reading, not noise, so the disagreement with the analyst is a rule question.
- **The business split is stable; the nesting is not quite.** All three logs used the same segments. One log placed silicon photonics and SiGe directly at the top level, while the other two put them under RF Infrastructure; that is the 97%. It is one company, so by the tuning rules it is recorded, not acted on.
- **Facts are traceable.** Quotes are almost all verbatim. The call-log numbers that could not be found in the transcript are mostly dates, sums the log computed and labelled (e.g. a segment mix adding to 87%), and number formats the parser does not match. The digests' numbers all come from the call log.
- **Runs differ in which supporting numbers they cite** (number overlap 78–89%), not in what they conclude. Length barely varies.

## Limits

One company, one quarter, three runs per skill, one model. Repeating this on COHR and FORM, and adding the earlier skill versions as a second group, would turn it into a before/after comparison.

---

<a id="中文"></a>

# 稳定性：同样输入，同样输出？TSEM FY26 Q2（2026-11-23）

**问题。** 当前版本的 skill 在同一份输入上运行多次，结构、判断和事实是否一样？

**简短结论。** 结构和判断一样，事实基本一样。六次运行全部通过校验。三份速读的标签和五个标记完全相同。三份电话会日志的业务拆分相同、引用与原文逐字一致，差别主要在挑了哪些辅助数字。

## 设置

| | earnings-call-reader | earnings-digest |
|---|---|---|
| 版本 | v1.6.0 | v1.6.0 |
| 输入 | TSEM FY26 Q2 电话会 transcript（本地文件） | TSEM 电话会日志（最新一季为 FY26 Q2） |
| 运行 | 3 次，每次都在新会话里 | 3 次，每次都在新会话里 |
| 输出 | 新建的电话会日志（中文） | 最新一季的速读（中文） |

指标：[`evaluation/stability.py`](../stability.py)（定义见 [README](../README.md#稳定性指标stabilitypy)）。这次没有做与旧版 skill 的前后对比。

## 结果

| skill | 运行 | 通过校验 | 标签相同 | 标记相同 | 板块相同 | 数字重叠 | 引用逐字可查 | 数字可溯源 | 篇幅波动 |
|---|---|---|---|---|---|---|---|---|---|
| earnings-call-reader | 3 | 100% | — | — | 97% | 89% | 99% | 89% | 0.02 |
| earnings-digest | 3 | 100% | 100% | 100% | — | 78% | 100% | 100% | 0.06 |

## 结论

- **校验脚本起了作用。** 三份速读一开始财务维的数字都过多，校验脚本给出警告，每次运行都在结束前删到只剩几个锚点。电话会日志都一次通过。
- **判断稳定。** 三份速读都把这一季标为"超预期·beat-raise"，五个标记完全相同：财务 ✅️、细分产业 ⚠️、订单 ⚠️、客户 ⚠️、业绩节奏 ✅️。这和 [skill vs 人的报告](2026-11-22_skill-vs-human.md)里悬而未决的订单维问题有关：skill 在订单维给 ⚠️ 是稳定的读法，不是随机波动，所以与分析师的分歧是规则问题。
- **业务拆分稳定，层级略有差别。** 三份日志用的分部相同。其中一份把硅光和 SiGe 直接放在顶层，另外两份放在 RF 基础设施之下，这就是 97% 的来源。只有一家公司，按调整规则只记录、不改规则。
- **事实可溯源。** 引用几乎全部逐字可查。电话会日志里在 transcript 中找不到的数字，大多是日期、日志自己计算并注明的合计（例如分部占比合计 87%），以及解析器没能匹配的数字写法。速读的数字全部来自电话会日志。
- **几次运行的差别在于引用了哪些辅助数字**（数字重叠 78–89%），而不是结论。篇幅几乎不变。

## 局限

一家公司、一个季度、每个 skill 跑三次、同一个模型。在 COHR 和 FORM 上重复，再加上旧版 skill 作为第二组，就能变成前后对比。
