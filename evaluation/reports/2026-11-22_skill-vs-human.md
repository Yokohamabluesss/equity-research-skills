# Skill vs human: company-view on TSEM, COHR and FORM (2026-11-22)

[English](#english) | [中文](#中文)

<a id="english"></a>

> The skill evaluated here was called **company-view** at the time; it was renamed **investment-view** in v1.5.0. Its output file was `{TICKER}_财报前瞻判断.md`, now `{TICKER}_投资判断.md`.

**Question.** An analyst reads the skills' summaries and writes a company view by hand. The company-view skill writes the same view from the same material. Where do the two agree, and what does each one see that the other misses?

**Short answer.** On judgment, they agree on 17 of 20 dimension marks. All three disagreements are on one dimension, **Orders**, and they follow one pattern. The skill covers 80–93% of the human's numbers in the quarter text. The human brings structure and outside knowledge the skill does not have. The skill brings anchor numbers and caveats the human skipped.

## Setup

| Run | Skill | Inputs available to the skill | Blind? |
|---|---|---|---|
| TSEM-v1 / TSEM-v2 | company-view v1 / v2 | call log, valuation workbook | no: the rules were tuned on this reference (training set) |
| COHR-v2 | v2 | call log, valuation workbook, ECOC event transcript | no: reference read before the run |
| FORM-v2 | v2 | call log, initial coverage note, valuation workbook (same as the analyst) | no: reference read before the run |
| FORM-v2-transcripts | v2 | two raw transcripts only (input ablation) | no |

References: the analyst's hand-written views. Metrics: `evaluation/compare_view.py` (see the [README](../README.md)). Scoring script and manifest: `evaluation/run_eval.py`, `evaluation/manifest.json`.

## Results

<!-- summary:start -->
| run | skill | marks | quarter numbers (text) | quarter terms | table numbers | core terms | estimates numbers | event numbers | ref lines covered / partial / missed | skill-only lines | core length vs human |
|---|---|---|---|---|---|---|---|---|---|---|---|
| TSEM-v1 | company-view v1 | 4/5 | 85% | 100% | 64% | 64% | 59% | — | 76% / 16% / 8% | 14 | 2.7x |
| TSEM-v2 | company-view v2 | 4/5 | 85% | 100% | 96% | 82% | 91% | — | 89% / 3% / 8% | 6 | 2.3x |
| COHR-v2 | company-view v2 | 5/5 | 80% | 67% | 100% | 46% | 78% | 83% | 55% / 31% / 14% | 15 | 0.4x |
| FORM-v2 | company-view v2 | 8/10 | 93% | 84% | 100% | 58% | 62% | — | 38% / 45% / 16% | 23 | 0.7x |
| FORM-v2-transcripts | company-view v2 | 8/10 | 93% | 84% | 83% | 48% | — | — | 34% / 47% / 19% | 13 | 0.6x |
<!-- summary:end -->

FORM has two quarters, so it has ten marks. "Core length" compares characters.

### Layer 1: did the v1 → v2 rules help? (TSEM, same inputs)

Yes, where the rules aimed. The product table went from 7 of 22 reference rows to 21 of 22. Table number recall rose from 64% to 96%, estimate number recall from 59% to 91%, and reference lines covered from 76% to 89%. Lines that only the skill had fell from 14 to 6. The one mark disagreement did not change, because it is a judgment rule and v2 did not touch it. The Core is still about twice the human's length.

The five changes, each taken from a systematic difference:
1. the Core is a summary (8–15 lines) with the company's peer tier;
2. the product table keeps every row of the thesis products and drops other segments;
3. capacity tables stay tables when supply is the constraint;
4. estimates are carried at full resolution, not condensed;
5. event entries are short: the delta against the current view, plus new checkable facts.

### Layer 2: does it carry over? (COHR, FORM: same rules, not tuned on them)

Partly. The quarter blocks transfer well: 80–93% number recall in text, and table numbers 83–100%. The Core transfers worst, at 46–58% term recall.

FORM was run twice, which works as an input ablation. With only two transcripts, the skill matched 83% of the table numbers and 48% of the Core terms, and it could not write estimates. With the same inputs as the analyst, the scores rose to 100% for table numbers and 58% for Core terms, and estimate number coverage reached 62%. The marks did not change (8/10), and line coverage barely moved (34% → 38%). So the inputs explain the table and estimate gaps. The remaining FORM gap is not an input gap. It comes from how the lines are written: half of the analyst's Core lines are English renderings that the skill phrases differently, and the analyst states conclusions where the skill states evidence (see below).

## Human vs skill: who sees what

This is the main finding: both readers have blind spots, and they are different ones.

**What the human has that the skill does not**
- **Structure from outside the sources.** COHR's Core carries two value-chain ownership tables (who makes the substrate, laser, lens, fibre, engine). FORM's Core ties switch-chip growth to scale-up GPU interconnect, which none of the inputs states. The skill's rule "facts from the inputs only" blocks this by design. That rule keeps the output checkable, at the price of the domain knowledge.
- **Compressed judgment calls**: a single line on when the supply squeeze should ease, or that next year's margin "hurts first" while a new fab ramps. The skill states the evidence. The human states the conclusion.
- **Valuation language the skill is not allowed to use.** The analyst's estimate conclusion calls the multiple "not cheap". The skill's rules forbid cheap / expensive and state what the price requires instead.
- **Data from materials the skill was not given**: an older estimate entry (COHR).

**What the skill has that the human does not**
- **Anchor numbers in Financials.** The human writes trend words ("accelerating"). The skill adds revenue against the guided range, margin steps and EPS against the guide.
- **Caveats and negative signals**: one segment as the only decelerating line, cash down and leverage up because of capex, a halt in external laser sales that tightens supply for the industry, a guided margin that includes a one-off tariff refund, and a CFO figure that differs from the press release. These appear as ⚠️ / 📌 sub-lines. The human views rarely record them.
- **Dates from the source.** The event date in one reference differs from the date in the call log and the valuation workbook by two days. The skill uses the source date.
- **Full-resolution estimates**: the quarterly revenue path, the margin decomposition and consensus attribution by variable.
- **Stale parts inside the inputs.** The FORM workbook's price cell was updated later ($118) than its conclusion page, which still shows the multiples and FCFF of the 2026-09-04 close ($103.90); one consensus line (FY27 revenue gap +3.2%, the numbers give +9.6%) is also stale text. The skill flagged both. The cause is timing, not a wrong number, so the fix went into the rules (v1.3.0): every valuation uses the latest price on the day the skill is called, and the conclusion page reads price, multiples and FCFF from cells instead of typed-in values.

**Where they disagree: Orders (3 of 3 disagreements)**
- The skill gives ⚠️ when hard order data is missing or stale: a contract amount not updated, or no backlog figure with lead times under a quarter. The human gives ✅️ when management's language is strong and demand clearly exceeds capacity.
- More broadly, every reference quarter has five ✅️. The digest rules treat "all ✅️" as a warning sign.
- Both readings are defensible. For a supply-constrained company, orders may simply not be the binding variable. The rule is left for the analyst to decide, not fitted away. One option is to judge Orders by the stronger of "hard data" and "demand exceeds supply", and to state which one applied.

## Limits

- **Not blind.** All three references were read before the rules were written or the runs were made. The numbers measure fit, not generalisation.
- **n is small**: one run per company, so no variance estimate.
- **Lexical proxies undercount paraphrase.** In COHR's event entry the skill condensed long translated sentences into short facts. Number recall there is 83%, yet most lines show as "partial" or "missed". The missed lines were read by hand for this report.
- **The reference is not ground truth.** It is one analyst's view at one time. Where the skill adds a correct caveat, a "skill-only" line is a gain, not an error.

## Next

1. **Held-out test**: FORM FY26 Q3 (the reference has no Q3 block yet). The skill writes it in a fresh session. The analyst writes theirs without seeing it. Then compare.
2. **Stability**: three runs on the same input, comparing marks and number sets between runs.
3. **Decide the Orders rule**, then re-run all four pairs and record the change here.
4. **A judgment-level check**: a reviewer, human or a separate model, labels each missed line as "fact missing", "paraphrased" or "outside the inputs", replacing the lexical proxy for that column.

---

<a id="中文"></a>

> 本报告评估的 skill 当时叫 **company-view**，v1.5.0 起改名为 **investment-view**；产出文件当时叫 `{TICKER}_财报前瞻判断.md`，现在叫 `{TICKER}_投资判断.md`。

# skill vs 人：company-view 在 TSEM、COHR、FORM 上的对比（2026-11-22）

**问题。** 分析师看完各 skill 的总结后手写公司判断；company-view skill 用同样的材料写同一份判断。两者哪里一致，各自看到了对方没看到的什么？

**简短结论。** 判断层面，20 个维度标记里有 17 个一致；3 处分歧全部在**订单**这一维，而且是同一种模式。季度正文中，手写版的数字有 80–93% 被 skill 覆盖。人带来的是 skill 没有的结构和外部知识；skill 带来的是人略过的锚点数字和风险提示。

## 设置

| 运行 | skill | skill 拿到的输入 | 是否盲测 |
|---|---|---|---|
| TSEM-v1 / TSEM-v2 | company-view v1 / v2 | 电话会日志、估值表 | 否：规则就是用它调的（训练集） |
| COHR-v2 | v2 | 电话会日志、估值表、ECOC 会议 transcript | 否：运行前读过手写版 |
| FORM-v2 | v2 | 电话会日志、首次研究笔记、估值表（与分析师相同） | 否：运行前读过手写版 |
| FORM-v2-transcripts | v2 | 只有两份原始 transcript（输入消融） | 否 |

参照：分析师的手写判断。指标：`evaluation/compare_view.py`（见 [README](../README.md)）。打分脚本与清单：`evaluation/run_eval.py`、`evaluation/manifest.json`。

## 结果

| 运行 | 标记一致 | 季度正文数字 | 季度术语 | 表格数字 | 核心术语 | 测算数字 | 会议数字 | 手写行 覆盖 / 部分 / 遗漏 | skill 独有行 | 核心长度 vs 人 |
|---|---|---|---|---|---|---|---|---|---|---|
| TSEM-v1 | 4/5 | 85% | 100% | 64% | 64% | 59% | — | 76% / 16% / 8% | 14 | 2.7x |
| TSEM-v2 | 4/5 | 85% | 100% | 96% | 82% | 91% | — | 89% / 3% / 8% | 6 | 2.3x |
| COHR-v2 | 5/5 | 80% | 67% | 100% | 46% | 78% | 83% | 55% / 31% / 14% | 15 | 0.4x |
| FORM-v2 | 8/10 | 93% | 84% | 100% | 58% | 62% | — | 38% / 45% / 16% | 23 | 0.7x |
| FORM-v2-transcripts | 8/10 | 93% | 84% | 83% | 48% | —（无估值表） | — | 34% / 47% / 19% | 13 | 0.6x |

FORM 有两个季度，所以有 10 个标记。"核心长度"按字符数比较。

### 第一层：v1 → v2 的规则有没有用？（TSEM，同一输入）

有用，而且正好在规则针对的地方。产品表从匹配 22 行中的 7 行到 21 行；表格数字召回率从 64% 到 96%，测算数字召回率从 59% 到 91%，手写行覆盖率从 76% 到 89%；只有 skill 有的行从 14 降到 6。那一处标记分歧没变，因为它是判断规则，v2 没动它。核心仍约为手写版的两倍长。

五条改动，每条都来自一处系统性差异：
1. 核心是摘要（8–15 行），并写出同业梯队；
2. 产品表保留主线产品的每一行，删掉其他分部；
3. 供给是约束时，产能表保持表格；
4. 测算按原分辨率保留，不再压缩；
5. 会议条目要短：相对当前判断的变化，加上新的可核对事实。

### 第二层：换公司还成立吗？（COHR、FORM：同一套规则，没针对它们调）

部分成立。季度块迁移得好：正文数字召回率 80–93%，表格数字 83–100%。迁移最差的是核心，术语召回率 46–58%。

FORM 跑了两次，相当于一次输入消融。只有两份 transcript 时，表格数字覆盖 83%，核心术语 48%，写不出测算；拿到与分析师相同的输入后，表格数字升到 100%，核心术语升到 58%，测算数字覆盖 62%。但标记没变（8/10），行覆盖率几乎没动（34% → 38%）。所以输入解释了表格和测算的差距；FORM 剩下的差距不是输入造成的，而是写法不同：分析师核心里一半是英文对照行，skill 的措辞不同；分析师写结论，skill 写证据（见下）。

## 人 vs skill：谁看到了什么

这是本报告的主要结论：两种读法都有盲区，而且盲区不一样。

**人有、skill 没有的**
- **来自材料之外的结构。** COHR 的核心有两张产业链自供表（衬底、激光器、透镜、光纤、光引擎分别由谁做）；FORM 的核心把交换芯片的增长归到 scale-up 的 GPU 互联，这一点任何输入里都没有。skill 的"事实只来自输入"规则有意挡掉了这些：输出因此可核对，代价是少了领域知识。
- **压缩过的判断**：一句话判断供给紧张何时缓解，或新工厂爬坡那年毛利率"先疼一年"。skill 写的是证据，人写的是结论。
- **skill 规则不允许用的估值措辞。** 分析师的测算结论写了"不算便宜"；skill 的规则禁止判断贵或便宜，改为写明现价需要什么条件。
- **skill 没拿到的材料里的数据**：一条更早的测算记录（COHR）。

**skill 有、人没有的**
- **财务维的锚点数字。** 人写趋势词（"加速中"）；skill 补上营收与指引区间的位置、毛利率台阶、EPS 与指引的对比。
- **风险提示和负面信号**：唯一减速的分部；资本开支导致的现金下降、杠杆上升；对外停售激光器使全行业供给更紧；毛利率指引含一次性关税退款；CFO 口述数字与新闻稿不一致。这些以 ⚠️ / 📌 子行出现，手写版很少记录。
- **来自原始材料的日期。** 一份手写版里的会议日期，与电话会日志和估值表中的日期相差两天；skill 用的是材料里的日期。
- **按原分辨率保留的测算**：逐季营收路径、利润率拆解、按变量归因的一致预期差异。
- **输入里过时的部分。** FORM 估值表的股价格后来更新成了 $118，结论页的倍数和 FCFF 仍是 2026-09-04 收盘价（$103.90）的版本；一致预期页有一行（FY27 营收差异 +3.2%，按数字应为 +9.6%）也是过时文字。skill 标出了这两处。原因是时间不一致，而不是数字算错，所以修正写进了规则（v1.3.0）：每次估值都用调用 skill 当天的最新股价，结论页的股价、倍数和 FCFF 一律引用单元格，不手填数值。

**分歧在哪里：订单（3 处分歧全在这里）**
- 缺少硬订单数据或数据未更新时（合同金额未更新，或没有 backlog 数据且交期不到一个季度），skill 给 ⚠️；管理层措辞强烈、需求明显大于产能时，人给 ✅️。
- 更普遍地看，每个手写季度都是五个 ✅️，而 digest 的规则把"全 ✅️"视为警示信号。
- 两种读法都说得通：对供给受限的公司，订单可能本来就不是约束变量。这条规则留给分析师决定，不靠拟合消掉。一种办法是：订单维按"硬数据"和"需求大于供给"中较强的一项判断，并写明依据的是哪一项。

## 局限

- **不是盲测。** 三份手写版都是在写规则、跑结果之前读过的，这些数字衡量的是拟合，不是泛化。
- **样本小**：每家公司只跑了一次，没有方差估计。
- **字面指标低估同义改写。** 在 COHR 的会议条目里，skill 把很长的译文句子压成了短事实：那里数字召回率 83%，但大多数行显示为"部分"或"遗漏"。本报告的遗漏行都经过人工阅读。
- **参照不是标准答案。** 它是某位分析师在某个时点的看法。skill 补上的正确风险提示属于收获，"skill 独有"行不等于错误。

## 下一步

1. **留出测试**：FORM FY26 Q3（手写版还没有 Q3 块）。skill 在新会话里写，分析师在不看 skill 结果的情况下写自己的，再对比。
2. **稳定性**：同一输入跑三次，比较各次之间的标记和数字集合。
3. **确定订单维规则**，然后重跑四组对比，把变化记在这里。
4. **判断层面的检查**：由人或另一个模型给每条遗漏行打标签："缺事实"、"换了说法"、"超出输入"，在这一列替代字面指标。
