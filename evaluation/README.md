# Evaluation: skill output vs the analyst's own judgment

[English](#english) | [中文](#中文)

<a id="english"></a>

## Why this folder exists

The summary skills in this repository (earnings-call-reader, earnings-digest, valuation-brief, investment-view) produce what an analyst used to write by hand. Two readers can look at the same earnings call: **a human reading the skill's summaries and writing a judgment**, and **an AI running the skill on the raw material**. Comparing the two outputs is a direct check of the skill's results. Format validators (`check_*.py`) only say whether an output is well-formed. This comparison asks whether it says what the analyst would have said, and where it says something the analyst missed.

The setup works like supervised learning:

| Supervised learning | Here |
|---|---|
| label | the analyst's hand-written investment view (`{TICKER}_投资判断.md`) |
| model | the investment-view skill (its `SKILL.md` rules) |
| training | editing the rules after reading the differences |
| loss | the proxies below (mark disagreement, missed numbers and lines) |
| held-out set | a company or quarter the rules were never tuned on |

## Two kinds of reports

| | Skill vs human | Stability |
|---|---|---|
| question | does the skill say what the analyst would say? | does the skill say the same thing every time? |
| compared with | the analyst's hand-written view | other runs of the same skill on the same input |
| needs a hand-written reference | yes | no |
| scripts | `compare_view.py`, `run_eval.py` | `stability.py` |
| a good result means | close to the analyst (accuracy) | low run-to-run variance (consistency) |

A skill can be stable and still wrong, or right on average and unstable; the two are reported separately.

## What is measured: three layers

1. **Effect: did a rule change help?** Run two skill versions on the same inputs and compare both with the same reference (TSEM v1 → v2 in the first report).
2. **Generalisation: does it hold on companies the rules were not tuned on?** The first study included COHR and FORM, whose references had already been read. In the [held-out company study](reports/2026-11-25_skill-vs-human.md), the rules were fixed before testing AEHR, CIEN and GLW. Across one fresh session per company, 12 of 14 comparable marks matched the analyst’s.
3. **Stability: same input, same output?** The current skill run several times on one input, in separate sessions. The same script can later compare against the skills as they were before this repository. Metrics and protocol: [below](#stability-metrics-stabilitypy).

A fourth question, whether the judgments turn out to be right, needs time: every quarter block and estimate is dated, so the "next-quarter upside drivers" can later be scored against the next report. That is the fundamental backtest in the roadmap.

## Metrics (`compare_view.py`)

All metrics are proxies, not a quality score.

| Metric | What it compares | Read it as |
|---|---|---|
| marks | the five ✅️ / ⚠️ / 🔻 dimension marks, for every quarter both files have | judgment agreement: the most important number |
| labels | whether each quarter has upside drivers, verdict, five dimensions, product table, Other | structure |
| numbers | value-based: `$1.3B` = `13亿` = `$1,300M`, `430bps` = `4.3pp`, `CY27` = `2027`, ranges split into both ends; recall and precision | factual coverage |
| terms | products, companies, technologies; case-insensitive, with aliases | topic coverage |
| lines | each reference line's CJK bigrams, words and numbers, looked up anywhere in the generated file: covered (≥ 50%), partial (25–50%), missed (< 25%); plus "skill-only" lines the reference has nothing like | what each side has that the other lacks |
| tables | product-table rows matched by their first cell | table completeness |
| length | lines and characters per block | verbosity and style drift |

Text and tables are scored separately, because tables are mostly copied from the call log while the judgment lives in the text. Lexical overlap undercounts paraphrase: a fact written in different words can show as "partial" or "missed". So number recall and the mark table count more than line coverage, and a human read of the missed lines is part of every review.

## Stability metrics (`stability.py`)

A group is N outputs of one skill version from the same input, each from a separate session (the runs must not see each other).

| Metric | Measures | Read it as |
|---|---|---|
| valid | share of runs that pass the current validator | conformance to the fixed template |
| same tag | share of runs with the most common beat / in-line / miss tag | headline stability |
| same marks | per dimension, share of runs with the most common mark, averaged | judgment stability |
| number overlap | mean pairwise overlap of the numbers cited (value-based) | factual stability |
| length cv | standard deviation / mean of output length | verbosity drift (lower is steadier) |
| same sections | (call logs) mean pairwise overlap of section and product headings | whether the product split is stable |
| quotes verbatim | with `--source`: share of quoted English passages found word for word in the source | quote fidelity |
| numbers traceable | with `--source`: share of the output's numbers that appear in the source | no invented numbers |

Protocol: the current skill runs two or three times on the same input (two give the same verdict as three, see the cost report), each run in a fresh session: earnings-call-reader on one transcript (`--format log --source TRANSCRIPT`) and earnings-digest on one call log (`--format digest --source LOG`), e.g. `python evaluation/stability.py --format digest OLD_DIR NEW_DIR --source LOG`. The judgment is expected to vary a little even when the format does not. A before/after comparison adds a second group, the old skill from the private workspace, run the same way.

## How to run

```bash
# one pair
python evaluation/compare_view.py GENERATED.md REFERENCE.md            # markdown
python evaluation/compare_view.py GENERATED.md REFERENCE.md --json     # full report
# every run of one experiment
python evaluation/run_eval.py --experiment 2026-11-22_skill-vs-human --root PATH/TO/WORKSPACE --out PATH/TO/OUT
```

**One experiment, one report.** `manifest.json` is a list of experiments. An experiment is one question asked at one time, for example "v2 rules vs the analyst on three companies"; it can cover several companies, and they share one report, `reports/{experiment id}.md`. Every new experiment (a new rule version, a held-out test, a stability test) gets a new id and therefore a new report; earlier reports are not rewritten. `run_eval.py` creates the report from a skeleton the first time and afterwards refreshes only the generated results table between the `summary` markers, so the written findings are never overwritten. An experiment marked `"status": "closed"` is refused.

Each run records its skill version and **input condition** (call log, initial coverage, valuation workbook, event files available or not). A gap caused by a missing input is not counted as a skill error; running the same company with fewer inputs is a cheap ablation.

A generated file and its reference should be in the same language. Marks, numbers and terms still compare across languages, but line coverage (CJK bigrams) does not.

## Data policy

The references are the analyst's private notes and the raw transcripts are copyrighted, so neither is in this repository. The manifest paths point into a private workspace. Published reports contain aggregate metrics and short paraphrased findings only. The per-run files written by `run_eval.py`, which quote reference lines, stay in the workspace.

## From differences to rule changes

[TUNING.md](TUNING.md) describes the loop that turns these comparisons into rule changes: `diagnose.py` sorts the differences, the `skill-tuner` skill proposes edits for patterns seen in two or more companies, the analyst approves, and `gate.py` accepts a change only if held-out runs do not get worse. Each run in the manifest is marked `split: train` (may be evidence) or `heldout` (only judges).

## Reports

- [2026-11-22: skill vs human, TSEM / COHR / FORM](reports/2026-11-22_skill-vs-human.md)
- [2026-11-23: stability, TSEM FY26 Q2](reports/2026-11-23_stability-tsem.md)
- [2026-11-25: skill vs human on held-out companies, AEHR / CIEN / GLW](reports/2026-11-25_skill-vs-human.md)
- [2026-11-25: stability, five companies](reports/2026-11-25_stability-5co.md)

---

<a id="中文"></a>

# 评估：skill 产出 vs 分析师本人的判断

## 为什么单独建这个文件夹

仓库里的总结类 skill（earnings-call-reader、earnings-digest、valuation-brief、investment-view）产出的，正是分析师以前手写的内容。同一场电话会可以有两种读法：**人看 skill 的总结再写判断**，和 **AI 直接用 skill 读原始材料**。把两份结果放在一起比，就是对 skill 结果的直接检验。格式校验脚本（`check_*.py`）只回答"格式对不对"；这里回答的是"说的是不是分析师会说的，以及哪些是分析师漏掉的"。

这个设置和监督学习是同构的：

| 监督学习 | 这里 |
|---|---|
| 标签 | 分析师手写的投资判断（`{TICKER}_投资判断.md`） |
| 模型 | investment-view skill（`SKILL.md` 里的规则） |
| 训练 | 看完差异后修改规则 |
| 损失 | 下面的近似指标（标记不一致、漏掉的数字和行） |
| 留出集 | 规则从没针对它调过的公司或季度 |

## 两类报告

| | skill vs 人 | 稳定性 |
|---|---|---|
| 回答的问题 | skill 说的是不是分析师会说的？ | skill 每次说的是不是一样？ |
| 和什么比 | 分析师的手写判断 | 同一 skill 在同一输入上的其他几次运行 |
| 需要手写参照 | 需要 | 不需要 |
| 脚本 | `compare_view.py`、`run_eval.py` | `stability.py` |
| 结果好意味着 | 接近分析师（准确） | 几次运行差别小（一致） |

一个 skill 可能很稳定但不对，也可能平均来看对但不稳定，所以两类结果分开报告。

## 测什么：三层

1. **有效性：规则改动有没有用？** 同一份输入跑两个版本的 skill，和同一份手写版对比（第一份报告里的 TSEM v1 → v2）。
2. **泛化：换一家规则没调过的公司还成立吗？** 首轮实验已读过 COHR 和 FORM 的手写参照。[留出公司实验](reports/2026-11-25_skill-vs-human.md#中文)先固定规则，再对 AEHR、CIEN、GLW 各开一个新会话测试。14 个可比较的标记中，12 个与分析师一致。
3. **稳定性：同样输入，同样输出？** 当前版本的 skill 在同一输入上、在不同会话里运行多次。以后可以用同一个脚本，与本仓库之前的旧版 skill 做前后对比。指标和做法见[下文](#稳定性指标stabilitypy)。

第四个问题是"判断事后是否正确"，需要时间：每个季度块和测算都带日期，"下一季超预期点"可以在下一次财报后打分，这就是后续计划里的基本面回测。

## 指标（`compare_view.py`）

都是近似指标，不是质量分。

| 指标 | 比较什么 | 怎么读 |
|---|---|---|
| 标记 | 两份文件共有的每个季度的五维 ✅️ / ⚠️ / 🔻 | 判断是否一致，最重要的一项 |
| 标签 | 每个季度是否有超预期点、总判断、五维、产品表、其他 | 结构 |
| 数字 | 按数值匹配：`$1.3B` = `13亿` = `$1,300M`，`430bps` = `4.3pp`，`CY27` = `2027`，区间拆成两端；召回率和精确率 | 事实覆盖 |
| 术语 | 产品、公司、技术；不分大小写，带别名表 | 话题覆盖 |
| 行 | 手写版每一行的中文二元组、英文词和数字，在生成文件任意位置查找：覆盖（≥ 50%）、部分（25–50%）、遗漏（< 25%）；以及手写版完全没有的"skill 独有"行 | 双方各自多了什么 |
| 表格 | 产品表按首列匹配行 | 表格完整度 |
| 长度 | 每块的行数和字符数 | 啰嗦程度和风格漂移 |

正文和表格分开计分：表格大多从电话会日志照抄，判断写在正文里。字面重叠会低估同义改写：换了说法的同一个事实可能显示为"部分"或"遗漏"。所以数字召回率和标记表比行覆盖率更可靠，每次复核都要人看一遍遗漏行。

## 稳定性指标（`stability.py`）

一组 = 同一版本的 skill 在同一输入上的 N 次输出，每次在单独的会话里运行（各次之间互不可见）。

| 指标 | 衡量什么 | 怎么读 |
|---|---|---|
| valid | 通过当前校验脚本的运行占比 | 是否符合固定模板 |
| same tag | 给出最常见的超预期 / 符合 / 不及预期标签的运行占比 | 结论标签是否稳定 |
| same marks | 每个维度上给出最常见标记的运行占比，取平均 | 判断是否稳定 |
| number overlap | 各次引用的数字两两重叠程度的平均（按数值匹配） | 事实是否稳定 |
| length cv | 输出长度的标准差 / 均值 | 篇幅漂移（越低越稳） |
| same sections | （电话会日志）各次板块和产品标题两两重叠程度的平均 | 产品拆分是否稳定 |
| quotes verbatim | 加 `--source` 时：引用的英文原文能在原始材料中逐字找到的比例 | 引用忠实率 |
| numbers traceable | 加 `--source` 时：输出中的数字能在原始材料中找到的比例 | 有没有编造数字 |

做法：当前版本在同一份输入上跑两到三次（跑 2 次和 3 次结论相同，见成本报告），每次都在新会话里：earnings-call-reader 读一份 transcript（`--format log --source transcript`），earnings-digest 读一份电话会日志（`--format digest --source 日志`），例如 `python evaluation/stability.py --format digest 旧版目录 新版目录 --source 日志`。格式稳定时判断仍可能有少量波动。做前后对比时，再加一组：私人工作区里的旧版 skill，按同样方式运行。

## 怎么运行

```bash
# 单对比较
python evaluation/compare_view.py 生成文件.md 手写文件.md             # markdown
python evaluation/compare_view.py 生成文件.md 手写文件.md --json      # 完整报告
# 某一次实验的全部运行
python evaluation/run_eval.py --experiment 2026-11-22_skill-vs-human --root 工作区路径 --out 输出路径
```

**一次实验，一份报告。** `manifest.json` 是一个实验列表。一次实验是在某个时点提出的一个问题，例如"v2 规则 vs 分析师，三家公司"；可以包含多家公司，共用一份报告 `reports/{实验 id}.md`。每做一次新实验（新规则版本、留出测试、稳定性测试）就用新 id，也就是新报告；以前的报告不改写。`run_eval.py` 第一次运行时按模板生成报告，之后只刷新 `summary` 标记之间自动生成的结果表，手写的结论不会被覆盖。标为 `"status": "closed"` 的实验会被拒绝重跑。

每次运行都记录 skill 版本和**输入条件**（是否有电话会日志、首次研究、估值表、会议文件）。缺输入造成的差距不算 skill 的错；同一家公司少给输入再跑一次，就是一次低成本的消融实验。

生成文件和手写版应是同一种语言。标记、数字、术语可以跨语言比较，但逐行覆盖（中文二元组）不行。

## 数据政策

手写版是分析师的私人笔记，原始 transcript 有版权，两者都不放进仓库；manifest 里的路径指向私人工作区。公开的报告只有汇总指标和简短的转述结论；`run_eval.py` 写出的逐次文件会引用手写原文，留在工作区。

## 从差异到规则修改

[TUNING.md](TUNING.md) 说明如何把这些对比变成规则修改：`diagnose.py` 给差异分类，`skill-tuner` skill 对两家以上公司出现的模式提出修改，分析师批准，`gate.py` 只在留出运行不变差时采纳。清单里每次运行标为 `split: train`（可作证据）或 `heldout`（只当裁判）。

## 报告

- [2026-11-22：skill vs 人，TSEM / COHR / FORM](reports/2026-11-22_skill-vs-human.md)
- [2026-11-23：稳定性，TSEM FY26 Q2](reports/2026-11-23_stability-tsem.md)
- [2026-11-25：留出公司上的 skill vs 人，AEHR / CIEN / GLW](reports/2026-11-25_skill-vs-human.md)
- [2026-11-25：稳定性，五家公司](reports/2026-11-25_stability-5co.md)
