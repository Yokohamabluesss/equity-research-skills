# Stability on five companies: AEHR, CIEN, GLW, COHR, FORM (2026-11-25)

[English](#english) | [中文](#中文)

<a id="english"></a>

**Question.** The [TSEM stability test](2026-11-23_stability-tsem.md) found identical digest tags and marks across three runs. Does that hold on other companies, including three the rules were never tuned on?

**Short answer.** Structure and facts hold; judgment mostly holds. All 20 runs pass their validators, and every pair of digests gives the same headline tag. Across both runs, **20 of 25 dimension marks are identical**, against 15 of 15 on TSEM. Every flip is between ✅️ and ⚠️, never 🔻, and Customers flips most often. Call logs quote the transcript almost word for word and split the business the same way in 3 of 5 companies.

## Setup

| | earnings-call-reader | earnings-digest |
|---|---|---|
| version | v1.7.0 | v1.7.0 |
| input | the latest transcript per company: AEHR FY26 Q4, CIEN FY26 Q3, GLW FY26 Q2, COHR FY27 Q1, FORM FY26 Q3 | the company's existing call log (latest quarter: AEHR FY26 Q4, CIEN FY26 Q3, GLW FY26 Q2, COHR FY26 Q4, FORM FY26 Q2) |
| runs | 2 per company, each in a fresh session | 2 per company, each in a fresh session |
| output | a new call log (Chinese) | a digest of the latest quarter (Chinese) |

- **Two runs, not three.** The [cost report](../../cost-benefit/reports/2026-11-23_cost-vs-quality.md) found that two runs give the same verdict as three, at two thirds of the cost.
- AEHR, CIEN and GLW are held-out companies: the rules were never written or tuned on them. COHR and FORM are in-sample.
- Model: Opus. No web access; each run saw only its own folder.
- Metrics: [`evaluation/stability.py`](../stability.py) (definitions in the [README](../README.md#stability-metrics-stabilitypy)). "Same marks" is the per-dimension share of runs giving the most common mark, averaged; with two runs, one flip in five dimensions gives 90%.

## Results

| skill | company | runs | valid | same tag | same marks | same sections | number overlap | quotes verbatim | numbers traceable | length cv |
|---|---|---|---|---|---|---|---|---|---|---|
| earnings-call-reader | AEHR | 2 | 100% | — | — | 100% | 95% | 100% | 90% | 0.01 |
| | CIEN | 2 | 100% | — | — | 100% | 90% | 99% | 91% | 0.03 |
| | GLW | 2 | 100% | — | — | 93% | 90% | 99% | 89% | 0.04 |
| | COHR | 2 | 100% | — | — | 100% | 95% | 100% | 87% | 0.02 |
| | FORM | 2 | 100% | — | — | 100% | 87% | 100% | 90% | 0.05 |
| earnings-digest | AEHR | 2 | 100% | 100% | 90% | — | 77% | 100% | 99% | 0.09 |
| | CIEN | 2 | 100% | 100% | 100% | — | 87% | 100% | 100% | 0.04 |
| | GLW | 2 | 100% | 100% | 90% | — | 71% | 100% | 100% | 0.02 |
| | COHR | 2 | 100% | 100% | 90% | — | 93% | — | 99% | 0.03 |
| | FORM | 2 | 100% | 100% | 80% | — | 79% | 100% | 100% | 0.01 |

COHR's digests quote no English passage of four words or more, so there is nothing to check.

### Digest marks, run 1 / run 2

| company | Financials | Sub-industry | Orders | Customers | Momentum | identical |
|---|---|---|---|---|---|---|
| AEHR | ✅️ / ✅️ | ⚠️ / ✅️ | ✅️ / ✅️ | ⚠️ / ⚠️ | ✅️ / ✅️ | 4 / 5 |
| CIEN | ✅️ / ✅️ | ⚠️ / ⚠️ | ✅️ / ✅️ | ⚠️ / ⚠️ | ✅️ / ✅️ | 5 / 5 |
| GLW | ✅️ / ✅️ | ⚠️ / ⚠️ | ✅️ / ✅️ | ⚠️ / ✅️ | ✅️ / ✅️ | 4 / 5 |
| COHR | ✅️ / ✅️ | ⚠️ / ⚠️ | ✅️ / ✅️ | ✅️ / ⚠️ | ✅️ / ✅️ | 4 / 5 |
| FORM | ✅️ / ⚠️ | ⚠️ / ⚠️ | ⚠️ / ⚠️ | ✅️ / ✅️ | ⚠️ / ✅️ | 3 / 5 |

## Findings

- **The headline is stable.** Both digests give the same tag on every company (four "beat · beat-raise", one "beat"). On AEHR both runs chose plain "beat" for the same reason: the next-year guidance was the first ever given, so it could not be a raise.
- **Marks are stable where the quarter is clear, less so where it is mixed.** CIEN, with record results, a raised guide and a stated supply limit, gave identical marks. FORM, with a strong quarter but a margin plateau, capacity limits and a flat DRAM guide, flipped on two dimensions. TSEM's 15 of 15 was a clear quarter too. The flips sit on dimensions where the evidence points both ways, and each run lists the same evidence; they differ in which side they weigh more.
- **Customers is the least stable dimension.** It flipped on GLW and COHR. In the [held-out skill-vs-human report](2026-11-25_skill-vs-human.md), Customers is also the only dimension where the skill disagrees with the analyst (AEHR, CIEN). Both results point to the same rule: when unrepeated customer news, concentration or unnamed customers should turn the mark to ⚠️. This is recorded for the analyst's decision.
- **Sub-industry is consistently ⚠️.** Nine of ten runs mark it ⚠️, usually because management gave no view on industry supply and demand or skipped a question about it. This is stable, so if it is wrong it is a rule question, not noise.
- **The validators do their job.** All call logs passed on the first try. Nine of ten digests did too; one carried too many numbers in Financials, got a warning and cut them back.
- **Facts are traceable.** Call-log quotes are 99–100% verbatim and 87–91% of their numbers are found in the transcript (TSEM: 89%); the rest are mostly dates, sums the log computed, and number formats the parser does not match. Digest numbers are 99–100% traceable to the call log. Runs differ in which supporting numbers they cite (overlap 71–95%), not in what they conclude.
- **The product split is stable in 3 of 5 companies.** AEHR, GLW and COHR used the same blocks in both runs; the GLW 93% comes from block names, not boundaries. CIEN grouped two product lines differently (one run kept the next-generation line system inside the current one and split two interconnect products; the other did the opposite), and FORM kept a block for a segment the call never discussed in one run but not the other. The "same sections" metric matches headings, so it does not catch a regrouping like CIEN's; it was read by hand.

## Metric fix

The quote check counted Chinese text in quotation marks that happened to start with a Latin token (for example "FY27 ...") as an English quote, so one such span gave COHR's digests 0% and FORM's 75%. `stability.py` now skips quoted spans that contain Chinese characters. The TSEM figures change only in one place: the call-log quote fidelity is 100%, not the 99% in that report.

## Cost

Average per run, from the agent usage records: call log about 120K tokens and 3.6 minutes; digest about 131K tokens and 2.1 minutes.

## Limits

- Two runs per company, one model, one quarter per company.
- The digest inputs are the analyst's existing call logs (written by earlier skill versions), not logs from the current version.
- Two call-log runs on AEHR stopped at a rate limit after writing their files; both files are complete and pass the validator.

## Next

1. **Decide the Customers rule** (see the held-out report), then re-run AEHR, GLW and COHR digests to see whether the flips disappear.
2. A before/after group with the skills as they were before this repository.

---

<a id="中文"></a>

# 五家公司的稳定性：AEHR、CIEN、GLW、COHR、FORM（2026-11-25）

**问题。** [TSEM 稳定性测试](2026-11-23_stability-tsem.md)中三次运行的速读标签和标记完全相同。换成其他公司，包括三家规则从未调过的公司，是否还成立？

**简短结论。** 结构和事实稳定，判断基本稳定。20 次运行全部通过校验，每一对速读的抬头标签都相同。两次运行之间，**25 个维度标记中 20 个相同**，TSEM 是 15 个中 15 个。所有翻转都在 ✅️ 和 ⚠️ 之间，没有出现 🔻；翻转最多的是客户维。电话会日志的引用几乎逐字可查，5 家中有 3 家两次的业务拆分相同。

## 设置

| | earnings-call-reader | earnings-digest |
|---|---|---|
| 版本 | v1.7.0 | v1.7.0 |
| 输入 | 每家最新一份 transcript：AEHR FY26 Q4、CIEN FY26 Q3、GLW FY26 Q2、COHR FY27 Q1、FORM FY26 Q3 | 该公司现有的电话会日志（最新一季：AEHR FY26 Q4、CIEN FY26 Q3、GLW FY26 Q2、COHR FY26 Q4、FORM FY26 Q2） |
| 运行 | 每家 2 次，每次都在新会话里 | 每家 2 次，每次都在新会话里 |
| 输出 | 新建的电话会日志（中文） | 最新一季的速读（中文） |

- **两次而不是三次。** [成本报告](../../cost-benefit/reports/2026-11-23_cost-vs-quality.md)发现跑 2 次和跑 3 次结论相同，成本只有三分之二。
- AEHR、CIEN、GLW 是留出公司：规则从未在它们上面写过或调过。COHR 和 FORM 是样本内公司。
- 模型：Opus。不上网；每次运行只能看到自己的文件夹。
- 指标：[`evaluation/stability.py`](../stability.py)（定义见 [README](../README.md#稳定性指标stabilitypy)）。"标记相同"是每个维度上给出最常见标记的运行占比，再取平均；两次运行时，五个维度中翻转一个就是 90%。

## 结果

（逐项结果表见英文部分。）

### 速读标记，第 1 次 / 第 2 次

| 公司 | 财务 | 细分产业 | 订单 | 客户 | 业绩节奏 | 相同 |
|---|---|---|---|---|---|---|
| AEHR | ✅️ / ✅️ | ⚠️ / ✅️ | ✅️ / ✅️ | ⚠️ / ⚠️ | ✅️ / ✅️ | 4 / 5 |
| CIEN | ✅️ / ✅️ | ⚠️ / ⚠️ | ✅️ / ✅️ | ⚠️ / ⚠️ | ✅️ / ✅️ | 5 / 5 |
| GLW | ✅️ / ✅️ | ⚠️ / ⚠️ | ✅️ / ✅️ | ⚠️ / ✅️ | ✅️ / ✅️ | 4 / 5 |
| COHR | ✅️ / ✅️ | ⚠️ / ⚠️ | ✅️ / ✅️ | ✅️ / ⚠️ | ✅️ / ✅️ | 4 / 5 |
| FORM | ✅️ / ⚠️ | ⚠️ / ⚠️ | ⚠️ / ⚠️ | ✅️ / ✅️ | ⚠️ / ✅️ | 3 / 5 |

## 结论

- **抬头标签稳定。** 每家公司两份速读的标签都相同（四家"超预期·beat-raise"，一家"超预期"）。AEHR 两次都只给"超预期"，理由也相同：下一年度指引是第一次给出，谈不上上调。
- **季度清晰时标记稳定，季度有好有坏时较不稳定。** CIEN 业绩创纪录、指引上调、供给约束明确，两次标记完全相同。FORM 本季强劲，但毛利率到平台、产能受限、DRAM 指引持平，有两个维度翻转。TSEM 的 15 / 15 也是一个清晰的季度。翻转发生在证据两边都有的维度上；两次运行列出的证据相同，区别在更看重哪一边。
- **客户维最不稳定。** GLW 和 COHR 上都翻转了。在[留出公司的 skill vs 人报告](2026-11-25_skill-vs-human.md)中，客户维也是 skill 与分析师唯一有分歧的维度（AEHR、CIEN）。两个结果指向同一条规则：上季客户进展没再提、集中度、客户未具名，什么时候应该把标记降为 ⚠️。记录下来，交给分析师决定。
- **细分产业稳定地给 ⚠️。** 10 次中 9 次给 ⚠️，通常因为管理层没有谈行业供需，或回避了相关提问。这是稳定的读法，如果不对，是规则问题而不是随机波动。
- **校验脚本起了作用。** 所有电话会日志都一次通过。10 份速读中 9 份也一次通过；1 份财务维数字过多，收到警告后删减。
- **事实可溯源。** 电话会日志的引用 99–100% 逐字可查，87–91% 的数字能在 transcript 中找到（TSEM 为 89%）；其余主要是日期、日志自己算的合计和解析器没匹配上的数字写法。速读的数字 99–100% 能在日志中找到。几次运行的差别在于引用了哪些辅助数字（重叠 71–95%），而不是结论。
- **产品拆分 5 家中 3 家稳定。** AEHR、GLW、COHR 两次用的板块相同；GLW 的 93% 来自板块名称，不是边界。CIEN 两次对两条产品线的分组不同（一次把下一代线路系统放在现有系统里、把两个互连产品分开；另一次正好相反）；FORM 有一次为一个电话会没谈到的业务保留了板块，另一次没有。"板块相同"指标比对的是标题，抓不到 CIEN 这种重新分组，这是人工读出来的。

## 指标修正

引用检查曾把引号里恰好以英文开头的中文（例如 "FY27 ……"）当作英文引用，导致 COHR 速读的引用逐字率为 0%、FORM 为 75%。`stability.py` 现在跳过含中文字符的引号片段。TSEM 的数字只有一处变化：电话会日志的引用逐字率为 100%，不是那份报告里的 99%。

## 成本

按 agent 用量记录，每次运行平均：电话会日志约 12 万 token、3.6 分钟；速读约 13 万 token、2.1 分钟。

## 局限

- 每家公司两次运行、一个模型、一个季度。
- 速读的输入是分析师现有的电话会日志（由旧版 skill 写成），不是当前版本生成的日志。
- AEHR 的两次电话会日志运行在写完文件后因调用额度中断；两份文件都完整并通过校验。

## 下一步

1. **决定客户维规则**（见留出公司报告），然后重跑 AEHR、GLW、COHR 的速读，看翻转是否消失。
2. 加一组本仓库之前的旧版 skill，做前后对比。
