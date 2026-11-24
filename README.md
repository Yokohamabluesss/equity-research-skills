# Equity Research Skills for Claude

[English](#english) | [中文](#中文)

<a id="english"></a>

A set of 12 Claude skills that cover one equity-research workflow end to end: finding the companies in a value chain, first-time coverage, reading earnings calls quarter after quarter, valuation, keeping one living judgment per company, and checking an investment thesis. Two meta skills sit on top: an entry point that suggests and chains the right skills, and one that improves the others from their comparison with the analyst's own work (14 skills in total). They were developed on optical communications, AI infrastructure and semiconductor supply-chain companies, and work for US, A-share and Hong Kong listings.

Some of the skills **summarise** (turning a 60-page call transcript into a structured log). Others **analyse** (a bottom-up valuation model, a value-chain BOM, an architecture-migration delta table). In both cases the hard part is not getting one good answer. It is getting the **same structure, the same labels and the same standards of evidence every time**, so that outputs can be compared across quarters and across companies. Most of the engineering in this repo exists to make that happen.

[See the TSEM examples](examples/README.md) · [Read the evaluation report](evaluation/reports/2026-11-22_skill-vs-human.md) · [Start here](#start-here)

## Evaluate → tune: skills that improve against the analyst

The summary and analysis skills replace work an analyst used to do by hand. So besides checking that outputs are well-formed, [`evaluation/`](evaluation/) compares **the AI running a skill on the raw material** with **the analyst's own hand-written judgment of the same company**, and uses the differences to improve the skill. The hand-written views act as labels, the skill as the model, rule edits as training:

```
skill output vs hand-written ──► sort the differences ──► propose rule edits ──► analyst approves
             ▲                                                                       │
             └──── kept only if held-out companies do not get worse ◄── re-run ◄─────┘
```

First results ([report](evaluation/reports/2026-11-22_skill-vs-human.md), TSEM / COHR / FORM):

- **Judgment**: 17 of 20 dimension marks agree. All three disagreements are on Orders: the skill flags missing or stale order data, while the analyst trusts strong demand language.
- **Facts**: the skill covers 80–93% of the analyst's numbers in the quarter text. One manual pass through the loop (v1 → v2) raised table and estimate coverage from about 60% to above 90%.
- **Different blind spots**: the analyst adds value-chain structure and domain knowledge from outside the sources; the skill adds anchor numbers and caveats the analyst skipped.
- **Limits**: not yet blind, one run per company. A held-out quarter is next.

This compares the skill with the analyst (accuracy). A separate [stability report](evaluation/reports/2026-11-23_stability-tsem.md) runs the same skill several times on the same input and compares the runs with each other (consistency): on TSEM, three digests gave identical tags and marks.

**Tuning.** Scripts sort the differences (input gap, format, judgment, coverage, length); the `skill-tuner` skill proposes rule edits only for patterns seen in two or more companies; the analyst approves; a gate keeps a change only if held-out companies do not get worse. Judgment rules are never changed automatically, word overlap is never a target, and the output framework of each skill stays fixed. Details: **[evaluation/TUNING.md](evaluation/TUNING.md)**.

## Cost-benefit: what quality costs

`evaluation/` measures how good the output is; **[cost-benefit/](cost-benefit/)** measures what it costs to get it, and decides whether a cheaper way of running a skill is good enough. A cheaper way can be a smaller model, fewer inputs, fewer repeated runs, or preprocessing. Each run records tokens, tool calls and time; quality reuses the same metrics, and a cheaper setup is accepted only under the same "not worse" rule as `gate.py`. First round ([report](cost-benefit/reports/2026-11-23_cost-vs-quality.md)):
- **Model tier.** Sonnet and Haiku cost ~0.45x and ~0.025x of Opus per run and stay accurate (quotes verbatim, numbers traceable), but their outputs are about half as long and keep fewer facts. The call-log reader stays on Opus; Haiku is a candidate for the digest.
- **Inputs.** Cleaning and the bilingual split are free (3%–4% and ~54% fewer tokens). The full FORM input set costs 2.2x the transcripts alone and is worth it.
- **Repeated runs.** Two stability runs give the same verdict as three.

## Examples

`examples/TSEM/` (Tower Semiconductor) runs the full chain on three earnings calls (FY26 Q1–Q3), in English and Chinese: the call log in cross-quarter mode, a 10-quarter financials dashboard, the 10-sheet valuation workbook at the current price, and the investment view with each quarter added on top of the last (the append-only checks pass). Raw transcripts are not included; [`examples/README.md`](examples/README.md) lists the sources and the limits of each example.

## Start here

Not sure which skill to use, or want several of them in one go? Start with **research-workflow**. Say what you want in plain words:

> "Do the full update on TSEM" · "Start coverage of COHR" · "What should I run next for FORM?" · "这些 skill 怎么用"

It checks the company folder first (which quarter each file has reached, what is out of date), then offers one choice:

| Workflow | Runs |
|---|---|
| A. First coverage | company-research → earnings-call-reader (two calls) → company-valuation → investment-view |
| B. New quarter | earnings-call-reader → quarterly-financials-dashboard → company-valuation → investment-view |
| C. Add an event | investment-view (investor day, trade show, broker conference, meeting notes) |
| D. Find companies | stock-discovery → value-chain-bom or architecture-delta-table → company-comparison |
| E. Review | thesis-check or company-comparison |

Optional add-ons: compare with your own hand-written note, a stability check, a cost-quality record, rule proposals. It then runs each skill in order and checks every output before the next step uses it. A request that already names one task ("summarise this call", "value it") goes straight to that skill.

## Using the skills

- **Not sure where to start?** See [Start here](#start-here).
- **Claude app**: import the packaged files in `dist/*.skill`.
- **Other agents**: `SKILL.md` follows the open Agent Skills format, which other tools such as Codex CLI and Gemini CLI also read; copy the skill folder into that tool's skills directory. Scripts need a host that can run Python.
- **Claude Code / file-based setups**: copy a skill folder from `skills/<group>/<skill>/` into your skills directory.
- `SKILL.md` is the English version that Claude loads. `SKILL.zh-CN.md` is the same skill in Chinese, kept for Chinese readers.
- Outputs follow the language of your request. When a skill appends to an existing file, it keeps that file's language.
- Scripts need Python 3 and `openpyxl`. LibreOffice is used for recalculation when it is installed.
- `{RESEARCH_ROOT}` means your research folder, with one subfolder per ticker.

```bash
python tools/build.py       # lint every skill, sync shared scripts, package dist/*.skill
python tools/selftest.py    # run every script on synthetic fixtures
```

## Workflow

```
 screening/            research/              earnings/              valuation/           synthesis/           review/
 stock-discovery   ─┐  company-research   ─┐  earnings-call-reader ─┐ company-valuation ─┐ investment-view ─┐  thesis-check
 value-chain-bom    ├▶ quarterly-         ├▶ earnings-digest       ├▶ valuation-brief   ├▶                 ├▶ company-comparison
 architecture-     ─┘  financials-       ─┘                        ─┘                   ─┘ (+ events)     ─┘
 delta-table           dashboard
 "who is in it?"       "what is this          "what changed this     "what does the       "what is our         "is the thesis right?
                        company?"              quarter?"              price imply?"        view now?"           how do they differ?"
```

Each skill reads the files the previous ones wrote, from one folder per company (`{RESEARCH_ROOT}/{TICKER}/`), so nothing has to be pulled from the web twice.

## Skills

| Folder | Skill | Type | Output |
|---|---|---|---|
| `screening` | **stock-discovery** | Screen | xlsx: companies × products / position / stage / attention / lagging flag |
| `screening` | **value-chain-bom** | Analyse + model | xlsx: value share per layer in ≥3 scenarios + the companies in each layer |
| `screening` | **architecture-delta-table** | Analyse | xlsx: per-segment verdict for each new route (net-new / increase / shift / offset / decrease …) |
| `research` | **company-research** | Analyse | Initial-coverage note (md) + 10-quarter dashboard |
| `research` | **quarterly-financials-dashboard** | Summarise (numbers) | xlsx: non-GAAP + GAAP + reconciliation + order proxies + cash flow + observations |
| `earnings` | **earnings-call-reader** | Summarise | One growing `{TICKER}_Earnings.md` per company, one quarter appended per call |
| `earnings` | **earnings-digest** | Summarise + judge | One-page digest with a ✅️ / ⚠️ / 🔻 verdict per dimension |
| `valuation` | **company-valuation** | Model | 10-sheet valuation workbook: bottom-up EPS, PE/PEG, FCFF scenarios, reverse DCF |
| `valuation` | **valuation-brief** | Summarise | Three-part note: guidance / assumptions / conclusion |
| `synthesis` | **investment-view** | Synthesise + judge | One living investment view per company: core thesis, a judged block per quarter (five dimensions written with earnings-digest's rules), notes from non-earnings events, dated estimates (valuation-brief's rules) |
| `review` | **thesis-check** | Review | Fact-checked outline + English version + sources |
| `review` | **company-comparison** | Review | Side-by-side comparison from existing research |
| `meta` | **research-workflow** | Start here | Checks the company folder, offers fixed workflows (first coverage / new quarter / event / find companies / review) and optional add-ons (comparison, stability, cost record), then runs the skills in order |
| `meta` | **skill-tuner** | Improve the skills | Rule proposals from the comparison with hand-written outputs; accepted only if held-out results do not get worse |

What each skill does, why it was designed that way, and where its consistency controls are: **[docs/SKILLS_GUIDE.md](docs/SKILLS_GUIDE.md)**.

## Design principles

1. **Evidence before conclusions.** Every number carries a source. Management views are labelled as management views. Inferences are marked `⚠️ Speculation`. Missing data stays blank, never guessed.
2. **Facts and judgments are kept apart.** Summaries quote the transcript; judgments are explicit and fixed-format (the digest's ✅️ / ⚠️ / 🔻, the valuation's 🟢 guided / 🟡 back-solved / 🔴 assumed tiers), so a reader can always tell which is which.
3. **Fixed templates.** Headings, sheet names, label sets, quarter labels (`FY26 Q3`) and file names are fixed strings in both English and Chinese. That keeps outputs comparable and lets one skill reliably read another's output.
4. **Scripts where determinism matters.** A language model is good at reading and judging, but it is not reliable at reproducing a 10-sheet layout identically every time. Layout, validation and recalculation are handled by small Python scripts that the skills call.
5. **No investment advice.** No buy/sell calls, no price targets; an FCFF value is always labelled a scenario output.

## How consistency is enforced

| Control | Where | What it prevents |
|---|---|---|
| Append-only check (`--before`) | earnings-call-reader | edits to old quarters while a new one is appended |
| Skeleton + coverage validator | earnings-call-reader | quarters at the wrong heading level, skipped sections, a product silently dropped |
| Local-first transcript lookup with header verification | earnings-call-reader | summarising the wrong company or quarter; mislabelled file names |
| Paywall / truncation detection | earnings-call-reader | summarising a preview or a cut-off transcript |
| Format lint | earnings-digest, valuation-brief | missing labels, wrong section order, "all ✅️" non-judgments, advice wording |
| Template builders | quarterly-financials-dashboard, company-valuation (style module), stock-discovery, architecture-delta-table | layouts drifting between companies; typed numbers where formulas belong |
| Label validation | stock-discovery, architecture-delta-table | unknown labels that would silently lose their colour and break filters |
| Recalculation + error scan | all xlsx skills (`xlsx_check.py`) | `#REF!` / `#NAME?`, text cells starting with `=`, files that open blank |
| Append-only point-in-time records | investment-view | rewriting earlier quarter verdicts, event notes or estimates after the fact |
| Comparison with hand-written references | investment-view ([evaluation/](evaluation/): `compare_view.py`, `run_eval.py`, `diagnose.py`, `gate.py`) | the output's judgment and coverage drifting away from the analyst's own views |
| Self-test | `tools/selftest.py` | regressions in any of the above (50 cases, including expected failures) |

## Limitations

- The checkers verify structure, not truth. They catch a skipped section or an edited old quarter; they cannot tell whether a judgment is right.
- Quality depends on the sources. Yahoo Finance usually offers only the most recent transcript for free; older ones need a subscription or a file you provide.
- The skills were tuned on optical, semiconductor and AI-infrastructure companies. Other sectors work, but the built-in checklists (e.g. the optical segment list) are less complete there.
- The skills were developed iteratively with Claude. The scripts were written with AI assistance, then reviewed and tested with `tools/selftest.py`.
- Nothing here is investment advice.

## Extending to other industries

The workflow, file formats, validators and the evaluate → tune loop do not depend on the industry. What does:

- **product breakdowns**: company-research and earnings-call-reader split "optical" into EML / CW / VCSEL / SiPh / modules; another industry needs its own split;
- **segment lists and starter checklists** in stock-discovery, value-chain-bom and architecture-delta-table (liquid cooling, solid-state batteries, advanced packaging and storage already have starter lists);
- **reference cases**: two or three companies run end to end, plus one hand-written view, so the loop has something to tune against.

## Repository layout

```
skills/<group>/<skill>/SKILL.md          English skill (loaded by Claude)
skills/<group>/<skill>/SKILL.zh-CN.md    Chinese version
skills/<group>/<skill>/scripts/          builders and checkers used by the skill
shared/xlsx_check.py                     shared recalc + lint, copied into skills by tools/build.py
tools/                                   build and self-test
docs/SKILLS_GUIDE.md                     what each skill does and why
evaluation/                              skill output vs hand-written judgment: scripts, manifest, reports, TUNING.md
cost-benefit/                            cost per run vs quality: cost.py, runs.json, reports
CHANGELOG.md                             version record
examples/                                sample outputs (see below)
dist/                                    packaged .skill files
```

## Roadmap

1. **Measured stability.** Run the current skills several times on the same input, in separate sessions, and measure what scripts can compute: validator pass rate, quote fidelity (the share of quotes found verbatim in the transcript), number traceability, and run-to-run consistency of product splits and digest verdicts ([`evaluation/stability.py`](evaluation/README.md#stability-metrics-stabilitypy)). [First results on TSEM](evaluation/reports/2026-11-23_stability-tsem.md): six runs, all valid; the three digests gave identical tags and marks. COHR and FORM are next. A before/after comparison with the skills as they were before this repository can be added with the same script.
2. **investment-view calibration.** investment-view will continue to be adjusted and upgraded as more hand-written references are compared ([evaluation/](evaluation/)). Next: a held-out (blind) quarter, a decision on the Orders rule, and a judgment-level review of missed lines. Each change is recorded in [CHANGELOG.md](CHANGELOG.md).
3. **New skills** to fill gaps found in daily use.
4. **More industries.** Extend the built-in checklists and examples beyond optical communications and semiconductors, starting from the lists that already exist for liquid cooling, solid-state batteries, advanced packaging and storage.
5. **Fundamental backtesting.** Turn research signals into rules fixed in advance (for example guidance raises, order-proxy inflections, or the dimension verdicts recorded in each investment view), then test on point-in-time historical data against a benchmark, with an out-of-sample period, to see whether they lead subsequent fundamentals or returns.
6. **A runner, in a separate repository.** A program that uses this repository as its library of skills, evaluation and cost-benefit scripts, and adds what a chat session cannot: batch and scheduled runs, several models side by side, the fundamental backtests above, and price-chart analysis. This repository stays the content; the runner only orchestrates.

---

<a id="中文"></a>

# 面向 Claude 的股票研究 Skills

一套 12 个 Claude skill（另有 2 个元 skill：一个是入口，负责推荐并串联合适的 skill；一个根据与分析师手写结果的对比改进其他 skill；共 14 个），覆盖一条完整的股票研究流程：找出产业链里的公司、首次覆盖、逐季读电话会、估值、为每家公司维护一份持续更新的判断、校对投资逻辑。这些 skill 主要在光通信、AI 基础设施和半导体供应链公司上打磨，适用于美股、A 股和港股。

其中有**总结型**（把 60 页的电话会 transcript 变成结构化日志），也有**分析型**（自下而上的估值模型、产业链价值量拆分、架构迁移增减量对照表）。两类的难点都不在于某一次答得好，而在于**每一次都保持同样的结构、同样的标签、同样的证据标准**，这样不同季度、不同公司的输出才能放在一起比较。这个仓库里的大部分工程工作都是为了做到这一点。

[查看 TSEM 成品](examples/README.md#示例) · [阅读评估报告](evaluation/reports/2026-11-22_skill-vs-human.md#中文) · [从这里开始](#从这里开始)

## 评估 → 调整：对照分析师不断改进的 skill

总结类和分析类 skill 替代的是分析师以前手写的工作。所以除了检查输出格式是否合规，[`evaluation/`](evaluation/) 还把 **AI 用 skill 直接读原始材料的结果**，和**分析师对同一家公司的手写判断**放在一起比较，并用差异来改进 skill：手写判断相当于标签，skill 相当于模型，修改规则相当于训练。

```
skill 产出 vs 手写版 ──► 给差异分类 ──► 提出规则修改 ──► 分析师批准
        ▲                                                   │
        └──── 留出公司不变差才保留 ◄── 重跑 ◄─────────────────┘
```

第一批结果（[报告](evaluation/reports/2026-11-22_skill-vs-human.md)，TSEM / COHR / FORM）：

- **判断**：20 个维度标记中 17 个一致。3 处分歧都在订单维：skill 对缺失或未更新的订单数据给出警示，分析师更相信强烈的需求表述。
- **事实**：季度正文中分析师写的数字，skill 覆盖 80–93%；手动走过一轮循环（v1 → v2）后，表格和测算的覆盖率从约 60% 升到 90% 以上。
- **盲区不同**：分析师补上材料之外的产业链结构和领域知识；skill 补上分析师略过的锚点数字和风险提示。
- **局限**：还不是盲测，每家公司只跑了一次；下一步是留出季度测试。

以上是 skill 和分析师比（准确度）。另一份[稳定性报告](evaluation/reports/2026-11-23_stability-tsem.md)让同一个 skill 在同一份输入上跑多次，几次运行之间互相比（一致性）：在 TSEM 上，三份速读的标签和标记完全相同。

**调整。** 脚本先给差异分类（缺输入、格式、判断、覆盖、长度）；`skill-tuner` skill 只对两家以上公司都出现的模式提出规则修改；分析师批准；把关脚本确认留出公司没有变差才保留改动。判断规则永远不自动修改，字面重叠永远不作为目标，各 skill 的输出框架保持不变。详见 **[evaluation/TUNING.md](evaluation/TUNING.md)**。

## 成本效益：质量要花多少

`evaluation/` 衡量输出好不好；**[cost-benefit/](cost-benefit/)** 衡量为此花了多少，并判断更便宜的跑法够不够好。更便宜的跑法包括：更小的模型、更少的输入、更少的重复次数、预处理。每次运行记录 token、工具调用和用时；质量沿用同一套指标，更便宜的跑法只有满足与 `gate.py` 相同的"没变差"规则才采纳。第一轮（[报告](cost-benefit/reports/2026-11-23_cost-vs-quality.md)）：
- **模型档位。** Sonnet 和 Haiku 每次运行的成本约为 Opus 的 0.45 倍和 0.025 倍，输出依然准确（引用逐字、数字可溯源），但篇幅约一半，保留的事实更少。电话会日志继续用 Opus；速读可以考虑 Haiku。
- **输入。** 清理和双语拆分没有质量代价（分别少 3%–4% 和约 54% 的 token）。FORM 的完整输入是只给 transcript 的 2.2 倍成本，值得。
- **重复次数。** 稳定性测试跑 2 次和 3 次结论相同。

## 示例

`examples/TSEM/`（Tower Semiconductor）用三次电话会（FY26 Q1–Q3）跑完整条流程，中英文各一套：跨季度模式的电话会日志、10 季财务表、按当前股价的 10 页估值表，以及逐季叠加的投资判断（“只追加”检查都通过）。原始 transcript 不放进仓库；来源和每个示例的局限见 [`examples/README.md`](examples/README.md)。

## 从这里开始

不知道该用哪个 skill，或者想一次把几个串起来用？从 **research-workflow** 开始，直接说你想做什么：

> 「把 TSEM 这季全部更新」·「开始覆盖 COHR」·「FORM 下一步该跑什么」·「这些 skill 怎么用」

它会先检查公司文件夹（每个文件到了哪一季、哪些已经过期），然后给出一个选择：

| 流程 | 运行 |
|---|---|
| A. 首次覆盖 | company-research → earnings-call-reader（两次电话会）→ company-valuation → investment-view |
| B. 新季度 | earnings-call-reader → quarterly-financials-dashboard → company-valuation → investment-view |
| C. 加一个会议 | investment-view（投资者日、展会、券商会议、会议纪要） |
| D. 找标的 | stock-discovery → value-chain-bom 或 architecture-delta-table → company-comparison |
| E. 复核 | thesis-check 或 company-comparison |

可选附加项：与你自己的手写判断对比、稳定性检查、成本质量记录、规则修改建议。之后它按顺序运行各 skill，每一步的输出检查通过后才交给下一步。已经明确是某一件事的请求（「总结这份电话会」「估值一下」）会直接交给对应的 skill。

## 使用方法

- **不知道从哪开始？** 见[从这里开始](#从这里开始)。
- **Claude 应用**：导入 `dist/*.skill` 里打包好的文件。
- **其他 agent**：`SKILL.md` 采用开放的 Agent Skills 格式，Codex CLI、Gemini CLI 等其他工具也能读取；把 skill 文件夹复制到对应工具的 skills 目录即可。脚本需要宿主能运行 Python。
- **Claude Code / 文件式环境**：把 `skills/<分组>/<skill>/` 整个文件夹复制到你的 skills 目录。
- `SKILL.md` 是 Claude 实际加载的英文版；`SKILL.zh-CN.md` 是同一个 skill 的中文版，供中文读者阅读。
- 输出语言跟随提问语言；追加到已有文件时沿用该文件的语言。
- 脚本需要 Python 3 和 `openpyxl`；装了 LibreOffice 时会用它重算公式。
- `{RESEARCH_ROOT}` 指你的研究根目录，每个 ticker 一个子文件夹。

```bash
python tools/build.py       # 检查所有 skill、同步共享脚本、打包 dist/*.skill
python tools/selftest.py    # 用合成数据跑一遍所有脚本
```

## 工作流

```
 screening/ 产业筛选   research/ 公司研究     earnings/ 财报跟踪      valuation/ 估值      synthesis/ 判断       review/ 复核
 stock-discovery   ─┐  company-research   ─┐  earnings-call-reader ─┐ company-valuation ─┐ investment-view ─┐  thesis-check
 value-chain-bom    ├▶ quarterly-         ├▶ earnings-digest       ├▶ valuation-brief   ├▶                 ├▶ company-comparison
 architecture-     ─┘  financials-       ─┘                        ─┘                   ─┘ （含其他会议）   ─┘
 delta-table           dashboard
 「这里面有谁？」        「这家公司是什么？」     「这一季变了什么？」      「现价隐含了什么？」    「现在怎么看？」        「投资逻辑对吗？两家差在哪？」
```

每个 skill 读取前面 skill 写在同一个公司文件夹（`{RESEARCH_ROOT}/{TICKER}/`）里的文件，同样的数据不必从网上拉两次。

## Skill 一览

| 文件夹 | Skill | 类型 | 输出 |
|---|---|---|---|
| `screening` | **stock-discovery** | 筛选 | xlsx：公司 × 相关产品 / 产业地位 / 产品阶段 / 关注度 / 涨幅滞后 |
| `screening` | **value-chain-bom** | 分析 + 建模 | xlsx：≥3 个场景下各层价值量占比 + 每层对应公司 |
| `screening` | **architecture-delta-table** | 分析 | xlsx：每条新路线逐环节的判断（纯新增 / 增量 / 平移 / 内部抵消 / 减量 …） |
| `research` | **company-research** | 分析 | 首次研究笔记（md）+ 近 10 季报表 |
| `research` | **quarterly-financials-dashboard** | 总结（数字） | xlsx：Non-GAAP + GAAP + 口径差异 + 订单代理项 + 现金流 + 关键观察 |
| `earnings` | **earnings-call-reader** | 总结 | 每家公司一份持续增长的 `{TICKER}_Earnings.md`，每次电话会追加一季 |
| `earnings` | **earnings-digest** | 总结 + 判断 | 一页速读，每个维度给出 ✅️ / ⚠️ / 🔻 判断 |
| `valuation` | **company-valuation** | 建模 | 10 页估值表：自下而上 EPS、PE/PEG、FCFF 三情景、反推现价 |
| `valuation` | **valuation-brief** | 总结 | 三段式笔记：指引 / 假设 / 结论 |
| `synthesis` | **investment-view** | 综合 + 判断 | 每家公司一份持续更新的投资判断：核心逻辑、每季判断（五维按 earnings-digest 的规则写）、电话会以外的会议记录、带日期的测算（按 valuation-brief 的规则写） |
| `review` | **thesis-check** | 复核 | 校对后的大纲 + 英文版 + 来源 |
| `review` | **company-comparison** | 复核 | 基于已有研究的横向对比 |
| `meta` | **research-workflow** | 入口 | 检查公司文件夹，给出固定流程（首次覆盖 / 新季度 / 会议 / 找标的 / 复核）和可选附加项（对比、稳定性、成本记录），再按顺序运行各 skill |
| `meta` | **skill-tuner** | 改进 skill | 根据与手写结果的对比提出规则修改；只有留出结果不变差才采纳 |

每个 skill 做什么、为什么这样设计、一致性靠哪里控制，见 **[docs/SKILLS_GUIDE.md](docs/SKILLS_GUIDE.md)**。

## 设计原则

1. **先有证据，再下结论。** 每个数字都有来源；管理层观点标明是管理层观点；推测标 `⚠️ 推测`；查不到的留空，不猜。
2. **事实和判断分开。** 总结部分引用原文；判断部分写得明确、格式固定（速读的 ✅️ / ⚠️ / 🔻，估值的 🟢 指引锁定 / 🟡 目标反解 / 🔴 自建假设），读者始终分得清哪句是事实、哪句是判断。
3. **固定模板。** 标题、sheet 名、标签集合、季度标签（`FY26 Q3`）和文件名在中英文下都是固定字符串，输出可比，一个 skill 也能可靠地读取另一个 skill 的输出。
4. **需要确定性的地方交给脚本。** 语言模型擅长阅读和判断，但不擅长每次都一模一样地复刻一个 10 页的表格版式。版式、校验和重算由 skill 调用的小型 Python 脚本完成。
5. **不给投资建议。** 不给买卖建议、不给目标价；FCFF 结果永远标明是情景下的模型输出。

## 一致性是怎么保证的

| 控制手段 | 所在 skill | 防止什么 |
|---|---|---|
| 只追加检查（`--before`） | earnings-call-reader | 追加新季度时改动了旧季度 |
| 骨架 + 覆盖度校验 | earnings-call-reader | 季度挂错标题层级、漏板块、某个产品被悄悄漏掉 |
| 先本地后网络的 transcript 查找 + 标题核对 | earnings-call-reader | 总结了错误的公司或季度；文件名写错 |
| 付费墙 / 截断检测 | earnings-call-reader | 拿预览片段或被截断的 transcript 做总结 |
| 格式检查 | earnings-digest、valuation-brief | 缺标注、顺序错、"全是 ✅️" 的假判断、买卖类措辞 |
| 模板生成脚本 | quarterly-financials-dashboard、company-valuation（样式模块）、stock-discovery、architecture-delta-table | 不同公司之间版式走样；该写公式的地方填了数字 |
| 标签校验 | stock-discovery、architecture-delta-table | 未登记的标签导致静默漏色、筛选失效 |
| 重算 + 错误扫描 | 所有 xlsx skill（`xlsx_check.py`） | `#REF!` / `#NAME?`、以 `=` 开头的文字、打开后一片空白的文件 |
| 时点记录只追加 | investment-view | 事后改写以前的季度判断、会议记录或测算 |
| 与手写参照对比 | investment-view（[evaluation/](evaluation/)：`compare_view.py`、`run_eval.py`、`diagnose.py`、`gate.py`） | 输出的判断和覆盖面逐渐偏离分析师本人的看法 |
| 自测 | `tools/selftest.py` | 以上任何一项的回归（50 个用例，含预期失败的用例） |

## 局限

- 检查脚本验证的是结构，不是对错：能发现漏掉的板块或被改动的旧季度，但判断不了一个结论是否正确。
- 输出质量取决于信息源。Yahoo Finance 通常只免费提供最近一次电话会的 transcript，更早的需要订阅或由用户提供文件。
- 这些 skill 主要在光通信、半导体和 AI 基础设施公司上调试过。其他行业也能用，但内置的检查清单（例如光通信环节清单）没那么完整。
- skill 文本是与 Claude 反复迭代写成的；脚本在 AI 辅助下编写，经过人工检查，并用 `tools/selftest.py` 测试。
- 本仓库内容不构成投资建议。

## 扩展到其他行业

工作流、文件格式、校验脚本和"评估 → 调整"循环都与行业无关。与行业有关的是：

- **产品拆分**：company-research 和 earnings-call-reader 会把"光通信"拆成 EML / CW / VCSEL / SiPh / 光模块；换一个行业需要它自己的拆分；
- **环节清单和起步清单**：stock-discovery、value-chain-bom、architecture-delta-table 里的清单（液冷、固态电池、先进封装、存储已有起步清单）；
- **参照案例**：两三家公司完整跑一遍，再加一份手写判断，循环才有可以对照调整的对象。

## 仓库结构

```
skills/<分组>/<skill>/SKILL.md          英文 skill（Claude 加载）
skills/<分组>/<skill>/SKILL.zh-CN.md    中文版
skills/<分组>/<skill>/scripts/          该 skill 调用的生成与检查脚本
shared/xlsx_check.py                    共享的重算 + 检查脚本，由 tools/build.py 复制进各 skill
tools/                                  打包与自测
docs/SKILLS_GUIDE.md                    每个 skill 做什么、为什么这样设计
evaluation/                             skill 产出 vs 手写判断：脚本、清单、报告、TUNING.md
cost-benefit/                           每次运行的成本 vs 质量：cost.py、runs.json、报告
CHANGELOG.md                            版本记录
examples/                               输出示例（见下）
dist/                                   打包好的 .skill 文件
```

## 后续计划

1. **量化稳定性**：当前版本的 skill 在同一份输入上、在不同会话里运行多次，测量脚本能自动计算的指标：校验通过率、引用忠实率（引用能在 transcript 中逐字找到的比例）、数字可溯源率、多次运行之间产品拆分和速读判断的一致性（[`evaluation/stability.py`](evaluation/README.md#稳定性指标stabilitypy)）。[TSEM 的第一批结果](evaluation/reports/2026-11-23_stability-tsem.md)：六次运行全部通过校验，三份速读的标签和标记完全相同；接下来是 COHR 和 FORM。以后可以用同一个脚本加上与本仓库之前旧版 skill 的前后对比。
2. **investment-view 校准**：未来这部分会继续做调整和升级，随着对比更多手写参照不断改进（[evaluation/](evaluation/)）。下一步：留出季度的盲测、确定订单维规则、对遗漏行做判断层面的复核。每次改动记录在 [CHANGELOG.md](CHANGELOG.md)。
3. **新增 skills**：补上日常使用中发现的空缺。
4. **扩展到更多行业**：把内置的检查清单和示例从光通信、半导体扩展出去，先从已有起步清单的液冷、固态电池、先进封装、存储做起。
5. **基本面回测**：把研究信号预先写成固定规则（例如指引上调、订单代理项拐点、每份投资判断里记录的各维度判断），在时点数据上对照基准回测，并留出样本外区间，检验它们是否领先后续的基本面或股价表现。
6. **运行器（单独的仓库）**：一个把本仓库当作 skill、评估和成本效益脚本库来调用的程序，补上聊天会话做不到的部分：批量和定时运行、多个模型并排对比、上面的基本面回测，以及 K 线图分析。本仓库保持为内容库，运行器只负责调度。
