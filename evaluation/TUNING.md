# Tuning skills from the comparison: a supervised loop with a held-out check

[English](#english) | [中文](#中文)

<a id="english"></a>

## Why

The summary and analysis skills replace judgment an analyst used to write by hand. [`compare_view.py`](compare_view.py) shows where a skill's output differs from the analyst's. This document describes what happens next: how those differences turn into rule changes without the skill drifting away from the analyst, memorising the three references, or learning to game the metrics.

The loop has three kinds of participants, each doing what it is reliable at:

| Part | Does | Why it is this part |
|---|---|---|
| scripts (`run_eval.py`, `diagnose.py`, `gate.py`) | compare, sort the differences, accept or reject a change | these steps must give the same answer every time |
| the `skill-tuner` skill ([`skills/meta/skill-tuner`](../skills/meta/skill-tuner/)) | reads the evidence, writes rule proposals, applies approved edits, re-runs | turning a pattern into a rule needs language and judgment |
| the analyst | approves every edit, decides judgment rules, writes held-out references | the skills replace the analyst's judgment, so the analyst owns the target |

## The loop

```
baseline experiment ──► run_eval ──► diagnose ──► proposals ──► analyst approves
       ▲                                                              │
       │                                                              ▼
  baseline closed ◄── ACCEPT ◄── gate (held-out only) ◄── run_eval ◄── candidate experiment
                      REJECT ──► revert, keep the report
                      PROVISIONAL ──► keep, mark provisional, schedule a held-out run
```

Every pass through the loop is a new experiment with its own report ([README](README.md#how-to-run)).

## Step 1: sort the differences (`diagnose.py`)

Not every difference is something the rules should fix. `diagnose.py` sorts each one into a category, and the category decides who acts:

| Category | Example | Who acts |
|---|---|---|
| input gap | no estimates block because no valuation workbook was given | the user supplies the input; no rule is written to compensate |
| format | a quarter block without its verdict line | a validator or template fix |
| judgment | Orders: skill ⚠️, analyst ✅️ | the analyst; never fitted automatically |
| coverage | Core term recall low in two companies | a rule candidate |
| length | Core 2.3x the reference | a rule candidate |
| skill-only | a correct caveat the analyst skipped | the analyst reads them; a gain, not an error |

Only runs of the current skill version are diagnosed, and only `train` runs count as evidence.

## Step 2: guard against overfitting

The rules are written by looking at a handful of hand-written references. The risk is that the rules memorise those references instead of learning how the analyst works: the scores rise on these companies and nothing improves on the next one. An example:

- **Memorising**: "the Core should mention InP capacity doubling", or pasting the analyst's phrase "just past the inflection of the S-curve" into the rules as a template. COHR's score rises; on a new company the rule is useless or wrong.
- **Generalising**: "when supply is the constraint, keep capacity milestones as a table". Both TSEM and COHR showed it, and it describes a method that carries to any supply-constrained company.

Four guards follow from this:

1. **Two companies or more.** A pattern seen in one company is recorded, not acted on.
2. **Method, not content.** A rule may not contain a company name, product, number, fact or phrase taken from a reference.
3. **Held-out data never trains.** Each run is marked `train` or `heldout` in the manifest. Proposals may cite only train runs. Held-out runs are companies or quarters no rule was tuned on, written in a fresh session without reading the reference first. They are used only by the gate, like exam questions that were not practised.
4. **The smallest edit that explains the pattern**, one per pattern, so a later regression can be traced to one change.

## Step 3: guard against gaming the metric

Any metric that is used as a target stops measuring what it was meant to measure. Line coverage and term recall count shared words. Optimising them would teach the skill to write longer and to copy the analyst's wording, which raises the score and lowers the value. So the metrics have two roles:

| Used to accept a change | Reported only |
|---|---|
| dimension-mark agreement | line coverage (covered / partial / missed) |
| number recall: quarter text, tables, estimates | term recall |
| Core length within 0.5–1.5x the reference (or moving closer to 1x) | skill-only line counts |

Numbers and marks are hard to game: a number is either in the output or not, and a mark is a single judgment. Length is a budget that stops "write more" from passing as "cover more".

## Step 4: the gate (`gate.py`)

The baseline (old rules) and the candidate (new rules) run on the same companies and inputs. Runs are paired by ticker, split and input condition. The verdict uses **held-out pairs only**. "Worse" always means: the new rules' output on a held-out run, compared with the same reference, scores lower than the old rules' output on that run (fewer marks agreeing, lower number recall, or a Core length that leaves the 0.5–1.5x band and moves further from 1x).

- **ACCEPT**: at least one held-out pair, and no acceptance metric got worse beyond a 2-point tolerance.
- **REJECT**: any acceptance metric got worse on a held-out pair. The edits are reverted; the report stays, because a failed change is also a result.
- **PROVISIONAL**: no held-out pair. The edits can stay but are marked provisional in the CHANGELOG until a held-out run is made.

Train pairs are shown too, to check that the change did what it aimed at, but a gain on train data alone is not an improvement.

## Where a fix lands

investment-view writes its five dimensions with earnings-digest's rules and its estimates with valuation-brief's rules; those rules exist only in those two skills. So a gap in the five dimensions is fixed in earnings-digest, a gap in the estimates in valuation-brief (or company-valuation, if the workbook itself lacks it), and everything else (Core, upside drivers, tables, events, length) in investment-view. A fix upstream also changes that skill's standalone output, so its validator must still pass and its framework stays the same.

## Changes the user asks for directly

The loop is the evidence-based path, not the only one. The user can always ask for a rule change directly; it is applied as asked, without the two-company rule. It still keeps the framework (unless the user says otherwise), passes build and self-test, is recorded in the CHANGELOG as user-requested, and is best followed by a re-run of the latest experiment, so its effect is measured like any other change.

## What is never tuned

- judgment rules (the dimension marks): the analyst decides them, with the evidence laid out;
- no buy / sell advice, no price targets, no cheap / expensive;
- the price date (always the latest price on the day the skill is called).

## Commands

```bash
python evaluation/run_eval.py --experiment ID --root ../workspace --out ../workspace/runs/investment-view/eval
python evaluation/diagnose.py --experiment ID --eval-dir ../workspace/runs/investment-view/eval/ID
python evaluation/gate.py --baseline .../BASE_ID/summary.json --candidate .../CAND_ID/summary.json
```

Proposals are written to `workspace/runs/{skill}/proposals/`. The skill version of the scripts is synced from `evaluation/` by `tools/build.py`, and `tools/selftest.py` covers the diagnosis and the three gate verdicts.

## First diagnosis (experiment 2026-11-22, investment-view v2)

(investment-view was called company-view until v1.5.0; the experiment records keep the old label.)

- **Judgment**: Orders differs in two companies (TSEM, FORM). This is a question for the analyst, not a rule candidate.
- **Rule candidates**: Core term coverage (COHR, FORM) and quarter product-table rows (COHR, FORM). The table-row pattern is mostly by design: rows outside the thesis are dropped, and one FORM run had no call log. So the evidence has to be read before anything is proposed.
- **Input gap**: the transcripts-only FORM run had no estimates block.
- No held-out run exists yet, so any change made now would be PROVISIONAL.

## Without a hand-written reference

The loop needs something to compare against. When no hand-written version exists, three other signals can stand in, each with a cost:

| Signal | The reference is | Good for | Caveat |
|---|---|---|---|
| the analyst's edits | the skill's output after the analyst corrected it | coverage, format, wording; the cheapest labels, because the analyst edits anyway | not blind: the analyst saw the skill's version first, so judgment differences are understated |
| outcomes | what happened next (were the "next-quarter upside drivers" right?) | judgment | needs a quarter to pass; this is the fundamental backtest in the roadmap |
| stability | other runs on the same input | consistency | says nothing about whether the output is right |

Without any of these, the gate has no held-out pair, so a change can only be PROVISIONAL.

## Which skills are tuned

| Skill | Tuned? | Why |
|---|---|---|
| investment-view | yes | the main target; its five dimensions are written with earnings-digest's rules and its estimates with valuation-brief's, so its comparison tunes those two as well |
| company-valuation | yes, additions only | compared with the analyst's own model or valuation note |
| stock-discovery | yes, additions only | compared with the analyst's own company list |
| earnings-digest, valuation-brief | through investment-view | not compared on their own |
| earnings-call-reader, quarterly-financials-dashboard | no | factual records: right or wrong, which the validators already check |

**Additions only** means the comparison looks for one thing: key outputs or methods the analyst has and the skill lacks. Examples:

- company-valuation: a driver the analyst used and the skill did not (revenue from capacity × utilisation when supply is the constraint), or a key output the analyst reports and the workbook does not;
- stock-discovery: companies, or a position label, the analyst listed and the skill missed.

If the same gap shows up in two or more companies, the missing item is added to the skill's checklist. The framework does not change: the same sheets, columns, section order, labels and validators. These skills were stabilised first; tuning must not undo that. Each of them needs its own small comparator, because `compare_view.py` reads the investment-view format only.

## Limits

- Only investment-view has a comparator so far; company-valuation and stock-discovery need their own (see above).
- The number of references is small, so "two companies" is a low bar. It should rise as references are added.
- Lexical metrics miss paraphrase. A judgment-level review of missed lines, by a person or a separate model, is the planned next layer.

---

<a id="中文"></a>

# 根据对比结果调整 skill：带留出检验的监督循环

## 为什么

总结类和分析类 skill 替代的是分析师以前手写的判断。[`compare_view.py`](compare_view.py) 指出 skill 的产出和分析师的不同之处；本文说明接下来怎么做：如何把这些差异变成规则修改，同时不让 skill 偏离分析师、不让它死记那几份手写参照、也不让它学会刷指标。

循环里有三方，各做自己可靠的部分：

| 部分 | 做什么 | 为什么由它做 |
|---|---|---|
| 脚本（`run_eval.py`、`diagnose.py`、`gate.py`） | 对比、给差异分类、采纳或拒绝改动 | 这些步骤每次必须给出同样的答案 |
| `skill-tuner` skill（[`skills/meta/skill-tuner`](../skills/meta/skill-tuner/)） | 读证据、写规则提案、应用批准的改动、重跑 | 把模式变成规则需要语言能力和判断 |
| 分析师 | 批准每处改动、决定判断规则、写留出集的手写参照 | skill 替代的是分析师的判断，所以目标由分析师掌握 |

## 循环

```
基线实验 ──► run_eval ──► diagnose ──► 提案 ──► 分析师批准
   ▲                                              │
   │                                              ▼
基线关闭 ◄── 采纳 ◄── gate（只看留出集）◄── run_eval ◄── 候选实验
             拒绝 ──► 撤回改动，保留报告
             暂定 ──► 保留改动并标为暂定，安排留出运行
```

每走一遍循环就是一次新实验，有自己的报告（见 [README](README.md#怎么运行)）。

## 第一步：给差异分类（`diagnose.py`）

不是每处差异都该靠改规则解决。`diagnose.py` 把每处差异归到一个类别，类别决定由谁处理：

| 类别 | 例子 | 谁处理 |
|---|---|---|
| 缺输入 | 没给估值表，所以没有测算块 | 用户补输入；不写规则去弥补 |
| 格式 | 季度块缺总判断行 | 修校验脚本或模板 |
| 判断 | 订单维：skill ⚠️，分析师 ✅️ | 分析师；永远不自动拟合 |
| 覆盖 | 两家公司的核心术语召回率都低 | 规则候选 |
| 长度 | 核心是手写版的 2.3 倍 | 规则候选 |
| skill 独有 | 分析师漏掉的正确风险提示 | 分析师阅读；是收获，不是错误 |

只诊断当前 skill 版本的运行，只有 `train` 运行算证据。

## 第二步：防过拟合

规则是看着少数几份手写参照写出来的。风险是规则记住了这几份参照，而不是学到分析师的方法：这几家公司的分数涨了，下一家公司却没有任何改进。举例：

- **死记**："核心要提 InP 产能翻倍"，或把分析师的原话"S 曲线刚过拐点"当模板写进规则。COHR 的分数会涨，换一家公司这条规则就没用甚至出错。
- **泛化**："供给是约束时，产能里程碑保持表格"。TSEM 和 COHR 都出现了这个问题，而且它描述的是方法，适用于任何供给受限的公司。

由此有四道关：

1. **至少两家公司。** 只在一家出现的模式只记录，不动规则。
2. **写方法，不写内容。** 规则里不能出现来自参照的公司名、产品、数字、事实或措辞。
3. **留出数据永远不参与训练。** 清单里每次运行标为 `train` 或 `heldout`。提案只能引用训练运行。留出运行是没有任何规则针对它调过的公司或季度，在新会话里写，写之前不读手写参照。它们只给 gate 用，就像没练习过的考试题。
4. **用能解释模式的最小改动**，一个模式一处改动，以后出现退步时能追溯到具体哪一处。

## 第三步：防"刷指标"

任何指标一旦被当成目标，就不再衡量它原本要衡量的东西。逐行覆盖率和术语召回率统计的是相同的词；以它们为目标，会教 skill 越写越长、照抄分析师的措辞，分数上去了，价值却下来了。所以指标分两种用途：

| 用来决定是否采纳 | 只报告 |
|---|---|
| 维度标记一致率 | 逐行覆盖率（覆盖 / 部分 / 遗漏） |
| 数字召回率：季度正文、表格、测算 | 术语召回率 |
| 核心长度在手写版的 0.5–1.5 倍之内（或更接近 1 倍） | skill 独有行数 |

数字和标记很难刷：数字要么在输出里，要么不在；标记是一个单独的判断。长度是预算，防止"写得多"冒充"覆盖得多"。

## 第四步：把关（`gate.py`）

基线（旧规则）和候选（新规则）在同样的公司和输入上运行，按股票代码、split 和输入条件配对。结论**只看留出配对**。"变差"始终指：在同一次留出运行上、对照同一份手写版，新规则的输出得分低于旧规则的输出（一致的标记更少、数字召回率更低，或核心长度超出 0.5–1.5 倍且离 1 倍更远）。

- **ACCEPT（采纳）**：至少有一对留出运行，且没有任何采纳指标变差超过 2 个百分点的容差。
- **REJECT（拒绝）**：任何一对留出运行上有采纳指标变差。撤回改动；报告保留，因为失败的改动也是结果。
- **PROVISIONAL（暂定）**：没有留出配对。改动可以保留，但在 CHANGELOG 里标为暂定，直到做了留出运行。

训练配对也会列出，用来确认改动起到了预期作用；但只在训练数据上变好，不算改进。

## 修改落在哪里

investment-view 的五维按 earnings-digest 的规则写，测算按 valuation-brief 的规则写，这两套规则只存在于那两个 skill 里。所以五维的差距改 earnings-digest，测算的差距改 valuation-brief（估值表本身就缺的则改 company-valuation），其余部分（核心、超预期点、表格、会议记录、长度）改 investment-view。改上游也会改变那个 skill 单独使用时的输出，所以它的校验脚本必须仍然通过，框架保持不变。

## 用户直接要求的修改

这个循环是基于证据的路径，但不是唯一的路径。用户随时可以直接要求修改规则，按要求执行，不受"两家公司"规则限制。修改仍然要保持框架不变（除非用户另有要求），通过 build 和自测，在 CHANGELOG 里记为用户要求的修改，之后最好重跑最近一次实验，像其他改动一样衡量效果。

## 永远不调的

- 判断规则（维度标记）：由分析师在证据摆清楚后决定；
- 不给买卖建议、不给目标价、不判断贵或便宜；
- 股价日期（永远是调用 skill 当天的最新价）。

## 命令

```bash
python evaluation/run_eval.py --experiment ID --root ../workspace --out ../workspace/runs/investment-view/eval
python evaluation/diagnose.py --experiment ID --eval-dir ../workspace/runs/investment-view/eval/ID
python evaluation/gate.py --baseline .../基线ID/summary.json --candidate .../候选ID/summary.json
```

提案写到 `workspace/runs/{skill}/proposals/`。skill 里的脚本由 `tools/build.py` 从 `evaluation/` 同步；`tools/selftest.py` 覆盖诊断和 gate 的三种结论。

## 第一次诊断（实验 2026-11-22，investment-view v2）

（investment-view 在 v1.5.0 之前叫 company-view；实验记录保留旧名。）

- **判断**：订单维在两家公司（TSEM、FORM）有分歧。这是要问分析师的问题，不是规则候选。
- **规则候选**：核心术语覆盖（COHR、FORM）和季度产品表的行（COHR、FORM）。表格行这个模式大部分是规则有意造成的：主线以外的行会被删掉，而且有一次 FORM 运行没有电话会日志。所以提案之前必须先读证据。
- **缺输入**：只用 transcript 的那次 FORM 运行没有测算块。
- 目前还没有留出运行，所以现在做的任何改动都只能是暂定。

## 没有手写版时

循环需要一个对照对象。没有手写版时，有三种信号可以替代，各有代价：

| 信号 | 参照是什么 | 适合 | 注意 |
|---|---|---|---|
| 分析师的修改 | 分析师修正过的 skill 输出 | 覆盖、格式、措辞；最便宜的标签，因为分析师本来就会改 | 不是盲测：分析师先看过 skill 的版本，判断上的分歧会被低估 |
| 事后结果 | 后来实际发生的事（"下一季超预期点"兑现了没有） | 判断 | 要等一个季度；就是后续计划里的基本面回测 |
| 稳定性 | 同一输入的其他几次运行 | 一致性 | 说明不了输出对不对 |

三者都没有时，gate 没有留出配对，改动只能是暂定。

## 哪些 skill 会被调整

| Skill | 是否调整 | 原因 |
|---|---|---|
| investment-view | 是 | 主要对象；它的五维按 earnings-digest 的规则写、测算按 valuation-brief 的规则写，所以对比它也就同时调了这两个 skill |
| company-valuation | 是，只做补充 | 与分析师自建的估值表或估值笔记对比 |
| stock-discovery | 是，只做补充 | 与分析师自己的公司名单对比 |
| earnings-digest、valuation-brief | 经由 investment-view | 不单独对比 |
| earnings-call-reader、quarterly-financials-dashboard | 否 | 事实记录，只有对错，校验脚本已经在检查 |

**只做补充**是指对比只找一件事：分析师有、skill 漏掉的关键输出或方法。例如：

- company-valuation：分析师用了、skill 没用的驱动因素（供给受限时按产能 × 稼动率推营收），或分析师报告了、估值表里没有的关键输出；
- stock-discovery：分析师列了、skill 漏掉的公司或地位标注。

同样的遗漏在两家以上公司出现，就把漏掉的项加进 skill 的检查清单。框架不变：同样的工作表、列、章节顺序、标签和校验脚本。这些 skill 是先做稳定的，调整不能破坏这一点。它们各自需要一个小的比较器，因为 `compare_view.py` 只认 investment-view 的格式。

## 局限

- 目前只有 investment-view 有比较器；company-valuation 和 stock-discovery 需要各自的比较器（见上）。
- 手写参照数量少，"两家公司"这个门槛偏低，参照增加后应提高。
- 字面指标识别不了同义改写。计划的下一层是由人或另一个模型对遗漏行做判断层面的复核。
