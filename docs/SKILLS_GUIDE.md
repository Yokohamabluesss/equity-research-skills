# Skills Guide

[English](#english) | [中文](#中文)

<a id="english"></a>

For each skill: **what it does**, **why it was designed this way**, **its basic logic**, and **the parts worth noticing**, meaning the most distinctive design choices and the controls that keep its output stable from run to run.

Shared conventions (all skills): one folder per company (`{RESEARCH_ROOT}/{TICKER}/`); quarter labels `FY26 Q3` in the company's fiscal year; output in the request language, or in the existing file's language when appending; fixed headings and labels in both languages; no buy/sell advice.

---

## Screening

### stock-discovery

**What it does.** For a business (e.g. CPO, FAU, SiC MOSFET), a value chain (e.g. DCI, HBM) or a list of companies (e.g. OFC exhibitors), it finds the relevant listed companies and labels each one's products, position, product stage and market attention. It also flags stocks that clearly lagged their sector.

**Why it was designed this way.** The question "who actually does X?" comes up constantly, and the usual answers ("concept stock" lists, forum threads) mix real suppliers with companies riding the hype. The three modes exist because the three questions need different things: breadth (who does it), completeness (does every link of the chain have a name) and per-company classification (go through this list one by one).

**Basic logic.** Identify the mode → split the segment into product-level keywords → search broadly in Chinese and English (filings, research, exhibitor lists, reverse search from known customers) → verify each company (does the business exist, what stage, what position) → rate market attention → check whether the stock lagged → build the xlsx.

**Worth noticing.**
- *Product-level keyword splitting* ("optical" → EML / CW / DFB / FAU / SiPh …). This is the single biggest factor in how complete the result is.
- *The lagging flag (🐢)*: names that clearly have the business but did not follow the sector. It is an information label, not a recommendation.
- *Stability*: `build_xlsx.py` fixes the column order, **validates every label** (an unknown label is an error instead of a silently uncoloured cell), **sorts mode-1 rows deterministically** (position → stage → attention), and writes the segment overview. The first version had a machine-specific output path hard-coded; it now takes `--output`.

### value-chain-bom

**What it does.** It splits a value chain into value shares by layer across at least three scenarios, attaches the US and A-share companies in each layer, and delivers a fully formula-linked 7-sheet workbook.

**Why it was designed this way.** A single value-share table misleads. In DCI, the widely quoted "modules 65–80%, pumps 1–4%" and a fully loaded "modules 91%, pumps 0.6%" are both correct; they differ only in how many wavelengths are lit per fiber. The skill makes that hidden parameter, the **true variable**, an explicit input. Its second claim: a high value share does not make a layer worth owning; supply structure does.

**Basic logic.** Fix the scope and unit → research ASP anchors and topology factors (more than half the effort) → find the true variable by reconciling with the version that is going around → build three scenarios along it → cross-check top-down against market sizes → attach companies per layer, with evidence tiers → build and check the workbook.

**Worth noticing.**
- *The true-variable sensitivity sheet* shows both share and absolute amount. The most useful finding is often "the share was diluted but the dollars did not move".
- *"Same name, different thing" checks* (e.g. telecom 980nm pumps vs industrial 976nm pumps) stop a company being counted as exposure to the wrong product.
- *Stability*: `check_bom_xlsx.py` encodes the pitfalls hit in earlier builds: unquoted cross-sheet references to sheet names that start with a digit, text cells starting with `=`, typed percentages where formulas belong, fewer than three scenarios, and a missing limitation statement. It also runs a LibreOffice recalculation so the delivered file carries values.

### architecture-delta-table

**What it does.** For an architecture migration (pluggable → NPO/CPO, air → liquid cooling, liquid → solid-state batteries …), it judges every segment for every new route on a fixed 7-label scale and lists the beneficiaries and losers with evidence marks.

**Why it was designed this way.** "The new architecture benefits whoever makes the new thing" is usually wrong. The table separates four cases that intuition merges: net-new segments, shifts that only look like growth, companies whose gains and losses offset, and segments that move in opposite directions on different routes, which is where an investor actually has to choose.

**Basic logic.** Fix the baseline, the routes and a reference system → list 20–30 segments across nine categories (equipment, materials and test are the ones usually missed) → judge each route independently → fill in companies and verify each against its original disclosure → build the xlsx → write conclusions (route-exclusive points first).

**Worth noticing.**
- *Two independent mark systems*: segment verdicts (⭐⭐ net-new … ⊘ not applicable) and evidence marks on companies (★★★ official … ⚠️ counter-evidence).
- *Verification rules taken from real mistakes*: an investor's question on a Q&A platform is not the company's answer; "has the product" is not "supplies this route"; when story and financials point in opposite directions, trust the financials.
- *Stability*: the generator used to be embedded in SKILL.md and re-typed on every run, which cost tokens and invited drift. It is now `scripts/build_delta_xlsx.py`, which **asserts the verdict labels** (a bracketed qualifier stops the build) and prints the rows where the routes disagree, so the conclusions cannot skip them.

---

## Research

### company-research

**What it does.** It writes first-time coverage of a company, centred on the segment the user cares about: a financial snapshot, a 10-quarter dashboard, forward-looking signals, and a product-level deep dive. A QA mode answers follow-up questions without touching the note.

**Why it was designed this way.** Users ask about a segment ("optical"), but companies disclose products (EML, CW, modules), and each product has different customers and a different competitive position. Mixing them produces statements that are true for the segment but false for every product in it.

**Basic logic.** Scope (one search on how the company itself splits the segment) → Step 1 snapshot and revenue mix → Step 1.5 10-quarter dashboard (required) → Step 2 leading indicators (margins, inventory, contract liabilities) with a read-through for each → Step 3: for each product, what it is, its position, its customers → open questions.

**Worth noticing.**
- *Following the company's own product split* sets the structure of the whole note.
- *Speculation is labelled* (`⚠️ Speculation`, with its basis) and never carries a citation; citations are reserved for sourced facts.
- *Stability*: fixed step headings and file names; the dashboard is delegated to quarterly-financials-dashboard's builder. The original citation markers were empty (the tags had been lost in editing), so they were replaced with an explicit rule: use the tool's citation, or `[Source: …]`.

### quarterly-financials-dashboard

**What it does.** It lines up N quarters (default 10) of non-GAAP and GAAP P&L, their reconciliation, balance-sheet order proxies (deferred revenue, customer deposits, contract liabilities), inventory and cash flow in one workbook, plus a bilingual "Story" and eight observation themes.

**Why it was designed this way.** Most semi-equipment and industrial companies do not disclose backlog, yet deferred revenue plus customer deposits usually lead revenue by one to two quarters. Single-quarter summaries underweight the balance sheet. Showing GAAP next to non-GAAP prevents non-GAAP alone from overstating earnings quality. The workbook is also the input to company-valuation.

**Basic logic.** Pull 8-K / 10-Q / 10-K (or periodic reports) quarter by quarter → write the numbers to JSON → the builder produces the 4-sheet workbook → the checker validates it → a 3–5 sentence story in chat.

**Worth noticing.**
- *Order proxies* are treated as leading indicators; observations must say whether each indicator leads or lags.
- *Stability*: `build_financials_xlsx.py` writes every row, formula, colour and note from the spec, so two companies' dashboards are identical in layout. It refuses input without the non-GAAP tax-rate note or without eight observations. `check_financials_xlsx.py` checks that YoY / QoQ / margins are **formulas, not typed numbers**. The original fourth sheet name, "Balance Sheet + CF + Observations", was 33 characters, over Excel's 31-character limit, and was silently truncated; it is now `BS + CF + Observations`.

---

## Earnings

### earnings-call-reader

**What it does.** It turns an earnings-call transcript into a structured log: TL;DR, guidance, profitability drivers, a product-by-product breakdown (demand, order book, customers), a product summary table and other notes. It keeps **one file per company** that grows by one quarter per call, with changes against the prior quarter marked.

**Why it was designed this way.** The useful comparison is how one product evolves over time (e.g. "sold out" → "sold out + LTA locked to CY27"). So the product section is organised product → quarter, while sections that are read as one quarter's full picture (guidance) are organised by quarter. The most damaging error is misattribution: filing a company-wide backlog comment, or a story about several products, under one product overstates that product's visibility. Hence the scope-attribution rule, "company-wide outranks product".

**Basic logic.** Get the transcript (local file → Yahoo Finance → ask the user) and verify it → detect the mode (new file / append / older quarter / same quarter) → classify every statement company-wide or product-level → write with quotes and numbers → in cross-quarter mode add change markers from a fixed legend → validate.

**Worth noticing.**
- *Scope attribution*: a three-step test (subject → evidence → the multi-product trap), with a default to the higher level when unsure.
- *Transcript sourcing*: `transcript_tool.py find` searches the company folder first and matches on the transcript's own header line (`(FORM) Q3 FY2026`), not the file name. A file saved as `TESM` instead of `TSEM` is still found, and the typo is reported. If nothing is found locally, the Yahoo index page is fetched and the entry must match ticker and quarter exactly; the transcript page is read in a browser because WebFetch returns a summary rather than verbatim text. `verify` rejects a paywalled preview and warns on truncation. A saved transcript missing its closing lines is flagged.
- *Stability*: `check_earnings_log.py` checks the heading skeleton, heading levels, canonical quarter labels, chronological order, that the latest quarter appears in every section and under every product covered last quarter, and, given a backup with `--before`, that **every old line is still present and unchanged**. Run on two existing logs, it found real drift: one used `FY26 Q3` and the other `2026Q1`, and the "Other" section had no quarter heading in the first quarter. Old content is reported as LEGACY and never rewritten.

### earnings-digest

**What it does.** It condenses the call log into one page: Logic & Narrative (core position, main growth driver, new narrative, 3–5 durable moat points) plus, per quarter, five judged dimensions (financials, sub-industry, orders, customers, momentum) and a list of other items.

**Why it was designed this way.** A digest is useful only if it judges. The emoji before each dimension is a **verdict** (✅️ good / ⚠️ concern / 🔻 weakening), not a bullet, and a digest with all five ✅️ almost always means no judgment was made. The financials line is about trend and the second derivative, not a copy of the dashboard; margin % and absolute profit are discussed separately because their inflections differ.

**Basic logic.** Read the log → set the three narrative labels → judge each dimension and justify the mark in its own text → momentum lists only changes versus the previous call → lint → deliver in chat (or save).

**Worth noticing.**
- *The S-curve method* for financials: locate margin % and profit $ separately from their QoQ increment series, and check whether the asymptote (the long-term target) moved.
- *Stability*: `check_digest.py` checks block markers, label order, 3–5 logic points, the fixed tag set (Beat / In line / Miss), the five dimensions in order with exactly one mark each, an unmarked Other list, and warns on "all ✅️", more than six numbers in the financials line, and buy/sell or cheap/expensive wording.

---

## Valuation

### company-valuation

**What it does.** It values a company with a bottom-up quarterly model (revenue → margin → opex → conversion → shares → EPS), PE / PEG on two bases and three periods, a three-scenario multi-stage FCFF, a reverse DCF of the current price, and a peer cross-check. The output is a 10-sheet workbook whose first sheet is a conclusion page.

**Why it was designed this way.** Copying consensus EPS throws away the point of a model. Consensus is only a cross-check, and its implied quarterly growth is backed out so that the disagreement becomes visible. FCFF is not used to produce a precise target; it shows how wide the scenario range is and, more usefully, what the current price already assumes (years of high growth × mature margin), which needs no forecast, only a judgment of plausibility. The method itself is chosen first (three veto questions decide between PE, FCFF and SoTP).

**Basic logic.** Scope and method pre-check → load existing files (call log, dashboard, digest) → build quarterly revenue, margin, opex, conversion and shares, each with a stated basis → back out consensus → PE / PEG (strictly time-aligned) → FCFF (GAAP EBIT, terminal share of EV reported) → reverse DCF and peers → conclusion page → check.

**Worth noticing.**
- *Guidance coverage ratio*: the share of forecast revenue locked by formal guidance (🟢), against what is back-solved from management targets (🟡) or assumed (🔴). It tells the reader how much of the model rests on management delivering.
- *Alignment rules*: never FY(cur) P/E with FY(cur+1) growth; never EPS-based P/E divided by revenue growth; FCFF always starts from GAAP EBIT, because SBC is a real cost.
- *Stability*: `val_style.py` holds the sheet list, colours, fonts, number formats and page layout, so the template is identical across companies by construction. `check_valuation_xlsx.py` recalculates the workbook and checks sheets and order, freeze panes, the verdict row, the basis column and the terminal-value share. On two existing workbooks it passed one and caught one sheet without frozen panes in the other.

### valuation-brief

**What it does.** It condenses the valuation workbook into a short note in three parts, guidance / assumptions / conclusion, where the conclusion always has four items in a fixed order.

**Why it was designed this way.** The note is the user's own format, so its rules are mostly about honesty of basis: separate full-year from exit-quarter figures, separate actuals from guidance, and argue a supply-constrained company with capacity and order evidence rather than "demand is strong". Statements such as "cheap" or "expensive" are rewritten as conditions ("to accept the price you need to believe …").

**Basic logic.** Read the workbook (recalculate first if needed) → fill the template → judge when the long-term margin target is reached, using the required slope against the historical slope, the drivers and the supply-demand state → list the valuation in a fixed order (two PE lines with growth → PEG → FCFF reverse) → compare with consensus → lint.

**Worth noticing.** It can also edit a draft the user wrote first, keeping the user's judgments and fixing only six listed problem types. *Stability*: `check_brief.py` checks the title line, section order, the presence and order of the four conclusion items, and advice wording.

---

## Synthesis

### investment-view

**What it does.** It keeps one living investment view per company (`{TICKER}_Investment_View.md` / `{TICKER}_投资判断.md`): a Core block (positioning, special traits, main growth drivers, new narrative), one judged block per quarter (next-quarter upside drivers, an overall verdict, five ✅️ / ⚠️ / 🔻 dimensions, the product table), dated notes from non-earnings events (investor days, launches and trade shows, broker conferences, meeting notes), and dated estimates.

**Why it was designed this way.** The other skills each answer one question; the analyst's working document combines them in a compact outline, and that combination was being written by hand. The Core comes from earnings-digest's logic & narrative and the estimates from valuation-brief; the skill adds the parts no other skill covers: the forward-looking "what could beat next quarter", and events outside earnings calls, recorded mainly as **deltas against the current view** ("progress: unchanged / earlier / later").

**Basic logic.** Decide what the run adds (new quarter / event / estimate / core refresh) → write it in the fixed outline → place it on top of its section → review the Core line by line (keep, strengthen 🔼, flag ⚠️, add 🆕, and list the changes) → check.

**Worth noticing.**
- *One copy of each rule*: the five dimensions are written with earnings-digest's rules and the estimates with valuation-brief's rules, directly into this file (no separate digest or brief file). The rules exist only in those two skills, and `check_view.py` runs their own validators (synced by `tools/build.py`), so a rule change there applies here automatically.
- *Point-in-time records*: quarter blocks, event notes and estimates are dated and never edited afterwards, so a later check (or a future backtest) can compare what was believed then with what happened.
- *Compared with the analyst's own views*: [`evaluation/`](../evaluation/) runs the skill on the same material the analyst had and compares the result with the hand-written view (marks for every quarter, value-based number matching, line-level coverage both ways). In the [first report](../evaluation/reports/2026-11-22_skill-vs-human.md), 17 of 20 marks agree (the three differences are all on Orders); one rule revision raised table and estimate number coverage from about 60% to above 90%.
- *Stability*: `check_view.py` checks the block order, fixed labels, one mark per dimension in order, YYYY-MM-DD dates newest first, line length (outline, not prose) and the append-only rule. `split_bilingual.py` keeps only the English side of interleaved transcripts.

---

## Review

### thesis-check

**What it does.** It checks the user's own investment outline against local research and the web, lists only the real problems with evidence, and returns a minimally corrected outline plus an English version in investment-memo style.

**Why it was designed this way.** Outlines fail in predictable ways: overstated scope, management opinion written as fact, unqualified "the only competitor", progress written ahead of reality, and ranks with no source. Local notes are second-hand, so rank, share, competitor and recent-news claims are **always** verified on the web against original sources.

**Basic logic.** Gather local evidence → web verification of the four claim types → split the outline into claims and tag each (fact / third-party data / management view / user judgment / inference) → run eight checks → output in four fixed blocks.

**Worth noticing.** The outline remains the user's: their structure and wording are kept, and correct points are marked accurate instead of being nitpicked. Example 2 in the skill shows web verification changing a conclusion: an unsourced "~50% North America share" became "No. 1 globally in DCI (Dell'Oro, 2025)".

### company-comparison

**What it does.** It compares two or more already-researched companies on business and strategy, technology routes, valuation and financials, and other differences, using only existing material.

**Why it was designed this way.** A comparison is only as good as its common basis: same price dates, same PEG definition, same GAAP / non-GAAP treatment. The skill forbids filling gaps from memory and always computes a few things that reveal whether a valuation gap is "slower growth" or "mispricing": absolute operating profit against market cap, premiums on a common basis, and the source of each model's risk.

**Basic logic.** Collect each company's newest files → one-line positioning in English → four fixed sections as Markdown tables, each followed by a short judgment → an offer to save the comparison.

**Worth noticing.** Technical details that are not in the notes are marked "unverified" rather than recalled. *Stability*: fixed section headings and a fixed list of rows per section.

## Meta

### research-workflow

**What it does.** The front door. It checks what already exists for a company, offers a short menu of fixed workflows (first coverage, new quarter, add an event, find companies, review) and optional add-ons (compare with the analyst's own note, a stability check, a cost-quality record, rule proposals), then runs the chosen skills in order.

**Why it was designed this way.** Each skill already triggers on its own description, so a single task needs no menu. What was missing was the chain: which skills, in which order, with which file passed on, and when a check must pass before going on. Keeping this as a skill rather than a program means the user can stop or change course at any step, and every analysis rule still lives in exactly one skill.

**Basic logic.** `status.py` reads the company folder (latest quarter in each file, valuation date, latest estimate) and says what is behind → one question with the workflows and add-ons → a short plan with inputs found and missing → each step runs the real skill and its validator → a table of files and checks.

**Worth noticing.** It never re-states another skill's rules and never continues with missing inputs without asking. Options use the host's question tool when there is one, and a numbered list otherwise. *Stability*: the folder check is a script covered by the self-test.

### skill-tuner

**What it does.** It turns the comparison between a skill's outputs and the analyst's hand-written outputs into rule changes: run the evaluation, sort the differences, propose edits, apply the approved ones, re-run as a new experiment, and keep a change only if held-out results do not get worse.

**Why it was designed this way.** The summary and analysis skills replace subjective work, so "better" means "closer to how the analyst judges", and the analyst has to stay in charge of that target. Unchecked, a loop like this overfits a handful of references or learns to game word-overlap metrics. The skill therefore routes each kind of difference to whoever should act on it, and never tunes judgment rules itself.

**Basic logic.** `run_eval.py` → `diagnose.py` sorts differences into input gap / format / judgment / coverage / length / skill-only and finds patterns across companies → proposals only for patterns in two or more companies, written as method, never as content → the analyst approves → rules edited, build + self-test → new experiment with held-out runs → `gate.py` accepts, rejects or marks provisional → CHANGELOG.

**Worth noticing.** Held-out runs are never evidence, only judges. Acceptance uses marks, number recall and a length budget; line coverage and term recall are reported but never targets. Full method: [evaluation/TUNING.md](../evaluation/TUNING.md). *Stability*: the sorting and the accept/reject decision are scripts with fixed thresholds, covered by the self-test.

---

<a id="中文"></a>

# Skills 说明

每个 skill 分四部分说明：**做什么**、**为什么这样设计**、**基本逻辑**、**值得注意的地方**（最有特点的设计，以及保证每次输出稳定的控制点）。

所有 skill 共用的约定：每家公司一个文件夹（`{RESEARCH_ROOT}/{TICKER}/`）；季度标签统一为公司财年口径的 `FY26 Q3`；输出语言跟随提问语言，追加到已有文件时沿用该文件的语言；标题和标签在中英文下都是固定字符串；不给买卖建议。

---

## 产业筛选（screening）

### stock-discovery

**做什么。** 针对一个业务（如 CPO、FAU、SiC MOSFET）、一条产业链（如 DCI、HBM）或一份公司名单（如 OFC 参展商），找出相关上市公司，标注每家的相关产品、产业地位、产品阶段和市场关注度，并标出相对板块明显没跟涨的股票。

**为什么这样设计。** "到底谁在做 X"是最常被问的问题，而常见答案（"概念股"名单、论坛帖子）把真正的供应商和蹭热度的公司混在一起。分三种模式，是因为三个问题要的东西不同：广度（谁在做）、完整性（产业链每一环都有人）、逐家判断（把这份名单一家家过一遍）。

**基本逻辑。** 判断模式 → 把赛道拆成产品级关键词 → 中英文多角度搜索（公告年报、研报、展商名单、从已知客户反向搜）→ 逐家核实（业务是否存在、阶段、地位）→ 评估关注度 → 检查是否涨幅滞后 → 生成 xlsx。

**值得注意的地方。**
- *产品级拆词*（"光通信" → EML / CW / DFB / FAU / SiPh …）：这一步决定结果全不全。
- *涨幅滞后标记（🐢）*：业务明确存在、但股价没跟上板块的标的。这只是信息标签，不是推荐。
- *稳定性*：`build_xlsx.py` 固定列顺序，**校验每一个标签**（未登记的标签直接报错，不会静默漏色），对模式 1 **做确定性排序**（地位 → 阶段 → 关注度），并生成子环节速览。旧版脚本里写死了某台电脑上的会话路径，现在改为用 `--output` 指定。

### value-chain-bom

**做什么。** 把一条产业链按层拆成价值量占比（至少 3 个场景），每层挂上美股和 A 股公司，交付一份 7 页、全公式联动的表。

**为什么这样设计。** 单一场景的价值量占比会误导人。以 DCI 为例，市面流传的"模块 65–80%、泵浦 1–4%"和满配计算的"模块 91%、泵浦 0.6%"都对，区别只在每根光纤点亮几个波。这个 skill 把这类隐藏参数（**真变量**）变成显式输入。它的第二个主张是：占比高不等于值得买，供给结构才是关键。

**基本逻辑。** 确定口径和单位 → 研究 ASP 锚点和拓扑因子（占一半以上的时间）→ 和市面版本对账，找出真变量 → 沿真变量取 3 个场景 → 用市场规模做自上而下交叉验证 → 每层挂公司并标证据等级 → 建表并检查。

**值得注意的地方。**
- *真变量敏感性页*：同时显示占比和绝对金额，最有价值的发现往往是"占比被稀释了，金额却没变"。
- *"同名不同物"检查*（如通信级 980nm 泵浦与工业级 976nm 泵浦），避免把公司算成错误产品的受益标的。
- *稳定性*：`check_bom_xlsx.py` 把以前建表踩过的坑写成了检查项：以数字开头的 sheet 名在跨表引用中没加引号、文字格以 `=` 开头、该用公式的占比填了数字、场景少于 3 个、来源页缺少限制说明。它还会用 LibreOffice 重算，交付的文件打开就有数值。

### architecture-delta-table

**做什么。** 针对一次架构迁移（可插拔 → NPO/CPO、风冷 → 液冷、液态 → 固态电池等），对每条新路线逐环节用固定的 7 档标签做判断，并列出受益方、受损方及证据标记。

**为什么这样设计。** "新架构利好做新东西的公司"通常是错的。这张表把直觉会混在一起的四种情况分开：纯新增的环节、看起来像增量其实是平移的环节、得失相抵的公司、在不同路线下方向相反的环节（这才是投资上真正要做选择的地方）。

**基本逻辑。** 确定基准、路线和基准机型 → 按九类列出 20–30 个环节（设备、材料、测试最容易漏）→ 每条路线独立判断 → 填公司并逐家回原始披露核实 → 生成 xlsx → 写结论（路线互斥点放第一条）。

**值得注意的地方。**
- *两套独立的标记*：环节判断（⭐⭐ 纯新增 … ⊘ 不适用）和公司证据标记（★★★ 官方 … ⚠️ 反证）。
- *来自真实错误的核实规则*：投资者在互动平台上的提问不是公司的回答；"有这个产品"不等于"供这条路线"；叙事和财务方向相反时以财务为准。
- *稳定性*：生成脚本以前嵌在 SKILL.md 里，每次都要重写一遍，既费 token 又容易写走样。现在独立成 `scripts/build_delta_xlsx.py`，**对判断标签做断言**（带括号的限定会让构建直接失败），并打印各路线判断不一致的行，结论里漏不掉。

---

## 公司研究（research）

### company-research

**做什么。** 对一家公司做首次研究，围绕用户关心的业务展开：基本财务画像、近 10 季报表、前瞻财务信号、产品级深度剖析。内置追问模式，回答后续问题时不改动笔记。

**为什么这样设计。** 用户问的是赛道（"光通信"），公司披露的是产品（EML、CW、光模块），而每个产品的客户和竞争地位都不同。混在一起写，得出的结论对赛道成立，对其中每个产品却都不成立。

**基本逻辑。** 确定范围（先搜一次公司自己怎么拆这个赛道）→ Step 1 财务画像与收入结构 → Step 1.5 近 10 季报表（必交）→ Step 2 领先指标（毛利率、库存、合同负债），每项都给出解读 → Step 3 每个产品分别回答"是什么、地位如何、客户是谁" → 信息缺口。

**值得注意的地方。**
- *跟着公司自己的产品口径拆*，这决定了整篇笔记的结构。
- *推测必须标注*（`⚠️ 推测`，并写明依据），推测不加引用；引用只用于有出处的事实。
- *稳定性*：步骤标题和文件名固定；报表交给 quarterly-financials-dashboard 的生成脚本。原文里的引用标记是空的（编辑过程中标签丢失了），现在改为明确规则：用工具的引用格式，或写 `[来源：…]`。

### quarterly-financials-dashboard

**做什么。** 把 N 个季度（默认 10 个）的 Non-GAAP 和 GAAP 利润表、两者的差异、资产负债表上的订单代理项（递延收入、客户押金、合同负债）、库存和现金流放进一份表，并附中英双语的"一句话总结"和 8 个观察主题。

**为什么这样设计。** 大多数半导体设备和工业品公司不披露 backlog，但递延收入加客户押金通常领先营收 1–2 个季度。只看单季新闻稿的总结会严重忽略资产负债表。GAAP 和 Non-GAAP 并列，是为了避免只看 Non-GAAP 而高估盈利质量。这份表也是 company-valuation 的输入。

**基本逻辑。** 逐季拉取 8-K / 10-Q / 10-K（或定期报告）→ 把数字写进 JSON → 生成脚本输出 4 页表 → 检查脚本校验 → 在对话里用 3–5 句话讲清楚故事。

**值得注意的地方。**
- *订单代理项*被当作领先指标；每条观察都要说明这个指标是领先的还是滞后的。
- *稳定性*：`build_financials_xlsx.py` 按规格写出每一行、每个公式、配色和备注，不同公司的报表版式完全一致。缺少 Non-GAAP 税率注释或观察不足 8 条时，脚本拒绝生成。`check_financials_xlsx.py` 检查 YoY / QoQ / 利润率**是公式而不是手填的数字**。原来第四页的名字 "Balance Sheet + CF + Observations" 有 33 个字符，超过了 Excel 31 个字符的上限，会被 LibreOffice 悄悄截断，现已改为 `BS + CF + Observations`。

---

## 财报跟踪（earnings）

### earnings-call-reader

**做什么。** 把电话会 transcript 写成结构化日志：速览、业绩展望、盈利驱动因素、分产品进展（需求、订单、客户）、产品汇总表和其他要点。**每家公司只有一份文件**，每次电话会追加一季，并标出相对上季的变化。

**为什么这样设计。** 最有用的对比是同一个产品随时间怎么演变（如"售罄" → "售罄 + LTA 锁到 CY27 末"），所以分产品板块按"产品 → 季度"组织；而业绩展望这类要整体看一个季度的板块按季度组织。最伤人的错误是归属错误：把全公司的 backlog 或多产品联供的故事放进某个单一产品，会让读者高估这个产品的可见度。所以有"整体 > 产品"的归属规则。

**基本逻辑。** 获取 transcript（本地文件 → Yahoo Finance → 请用户提供）并核对 → 判断模式（新建 / 追加 / 更早的季度 / 同一季度）→ 把每句话归到全公司或单一产品 → 带原文引用和数字写作 → 跨季度模式下用固定的符号标注变化 → 校验。

**值得注意的地方。**
- *归属层级*：三步法（主语 → 证据 → 多产品陷阱），拿不准时归到上一级。
- *transcript 获取*：`transcript_tool.py find` 先查公司文件夹，按 transcript 自带的标题行（`(FORM) Q3 FY2026`）匹配，而不是只看文件名。文件名把 `TSEM` 写成 `TESM` 时照样能找到，并提示笔误。本地没有时去 Yahoo 列表页，ticker 和季度必须完全一致；正文用浏览器读取，因为 WebFetch 返回的是摘要而不是原文。`verify` 会拒绝付费墙预览，并提示可能被截断。缺了结尾几句的 transcript 会被标出来。
- *稳定性*：`check_earnings_log.py` 检查标题骨架、标题层级、规范的季度标签、时间顺序、最新一季是否出现在每个板块和上季覆盖过的每个产品下；如果用 `--before` 传入备份，还会检查**每一行旧内容都还在且没被改动**。用它检查现有的两份笔记，发现了真实的不一致：一份用 `FY26 Q3`，另一份用 `2026Q1`；"Other" 板块的第一季没有季度标题。旧内容只报告为 LEGACY，不会被改写。

### earnings-digest

**做什么。** 把电话会日志压缩成一页：逻辑和叙事（一句话核心、增长主驱动、新叙事、3–5 条跨季度稳定的护城河），加上每季五个带判断的维度（财务、细分产业、订单、客户、业绩节奏）和"其他"。

**为什么这样设计。** 速读只有在下判断时才有用。每个维度前的 emoji 是**判断**（✅️ 好 / ⚠️ 隐忧 / 🔻 转弱），不是项目符号；五个维度全是 ✅️ 几乎就等于没做判断。财务栏讲趋势和二阶导，而不是把仪表盘抄一遍；利润率和利润绝对额分开讲，因为两者的拐点通常不同步。

**基本逻辑。** 读日志 → 写三个叙事标注 → 逐维度判断，并在正文里给出依据 → 业绩节奏只写相对上一季的变化 → 格式检查 → 在对话里输出（或存文件）。

**值得注意的地方。**
- *财务栏的 S 曲线方法*：分别用利润率和利润额的 QoQ 增量序列定位各自所处的阶段，并看天花板（长期目标）有没有被上调。
- *稳定性*：`check_digest.py` 检查分块标记、标注顺序、3–5 条逻辑、固定的 tag 集合（超预期 / 符合预期 / 不及预期）、五个维度的顺序及每个维度恰好一个判断标记、"其他"不带标记；遇到"全是 ✅️"、财务栏超过 6 个数字、买卖或贵贱类措辞时给出警告。

---

## 估值（valuation）

### company-valuation

**做什么。** 用自下而上的逐季模型（营收 → 毛利率 → 费用 → 转换率 → 股本 → EPS）给公司估值，计算双口径、三个时间口径的 PE / PEG，做三情景多阶段 FCFF、反推现价隐含条件和可比公司交叉检查。输出一份 10 页的表，第一页是结论页。

**为什么这样设计。** 照抄一致预期的 EPS 就失去了建模的意义。一致预期只作交叉验证，并反解出它隐含的逐季增速，让分歧一目了然。FCFF 不用来算精确的目标价，而是看情景区间有多宽，更重要的是看现价已经隐含了什么（高增长持续几年 × 成熟期利润率多少）：这一步不需要预测，只需要判断条件合不合理。估值方法本身先选（三道否决题决定用 PE、FCFF 还是 SoTP）。

**基本逻辑。** 确定范围并预判方法 → 读取已有文件（电话会日志、财务报表、速读）→ 逐季推导营收、毛利率、费用、转换率和股本，每一项写明依据 → 反解一致预期 → PE / PEG（严格时间对齐）→ FCFF（用 GAAP EBIT，报告终值占比）→ 反推与可比公司 → 结论页 → 检查。

**值得注意的地方。**
- *指引覆盖率*：预测营收中被公司正式指引锁定的比例（🟢），与由管理层目标反解（🟡）或自建假设（🔴）的部分对照，告诉读者这个模型有多大程度依赖管理层兑现目标。
- *对齐规则*：不用 FY(cur) P/E 配 FY(cur+1) 的增速；不用 EPS 口径的 P/E 除以营收增速；FCFF 一律从 GAAP EBIT 起算，因为 SBC 是真实成本。
- *稳定性*：`val_style.py` 存放 sheet 清单、配色、字体、数字格式和页面布局，模板在构造上就跨公司一致。`check_valuation_xlsx.py` 重算并检查 sheet 名与顺序、冻结窗格、方法结论行、依据列和终值占比。在现有的两份估值表上，一份通过，另一份查出有一页没有冻结窗格。

### valuation-brief

**做什么。** 把估值表压缩成"指引 / 假设 / 结论"三段式短笔记，结论固定为四条，顺序固定。

**为什么这样设计。** 这是用户自己的笔记格式，所以规则主要关于口径是否诚实：全年和单季分开、实际值和指引分开；对供给受限的公司，用产能和订单论证，而不是一句"需求很好"。"便宜 / 贵"这类说法改写成条件句（"要接受现价，需要相信……"）。

**基本逻辑。** 读估值表（需要时先重算）→ 填模板 → 判断长期利润率目标何时达成（所需斜率 vs 历史斜率、驱动因素、供需状态）→ 按固定顺序写估值（两年 PE 及增速 → PEG → FCFF 反推）→ 对比一致预期 → 格式检查。

**值得注意的地方。** 也可以修改用户先写的草稿：保留用户的判断，只修六类列明的问题。*稳定性*：`check_brief.py` 检查标题行、三段顺序、结论四条是否齐全且顺序正确，以及买卖类措辞。

---

## 综合判断（synthesis）

### investment-view

**做什么。** 每家公司维护一份持续更新的投资判断文件（`{TICKER}_投资判断.md` / `{TICKER}_Investment_View.md`）：核心（定位、特殊点、增长主驱动、新叙事）、每季一个判断块（下一季超预期点、总判断、五维 ✅️ / ⚠️ / 🔻、产品表）、电话会以外材料的带日期记录（投资者日、发布会与展会、券商会议、会议纪要），以及带日期的测算。

**为什么这样设计。** 其他 skill 各自回答一个问题，而分析师实际用的工作文档是把它们组合成一份精简大纲，这一步一直是手写的。核心来自 earnings-digest 的逻辑和叙事，测算来自 valuation-brief；本 skill 补上其他 skill 没有覆盖的部分：前瞻的"下一季可能在哪里超预期"，以及电话会以外的会议，并且主要记录**相对当前判断的变化**（"进度：未改变 / 提前 / 推迟"）。

**基本逻辑。** 确定本次新增什么（新季度 / 会议 / 测算 / 刷新核心）→ 按固定大纲写 → 放到所在板块的最上面 → 逐条复核核心（保持、加强 🔼、标注 ⚠️、新增 🆕，并列出改动）→ 检查。

**值得注意的地方。**
- *每条规则只有一份*：五维按 earnings-digest 的规则写，测算按 valuation-brief 的规则写，直接写进本文件（不另外生成速读或估值速读文件）。这些规则只存在于那两个 skill 里，`check_view.py` 也直接运行它们的校验脚本（由 `tools/build.py` 同步），所以在那里改规则，这里自动生效。
- *时点记录*：季度块、会议记录和测算都带日期、写下后不再修改，以后核对（或将来回测）时可以比较当时怎么判断、后来实际发生了什么。
- *与分析师本人的判断对比*：[`evaluation/`](../evaluation/) 用分析师当时拥有的同样材料跑 skill，再与手写判断对比（每个季度的标记、按数值匹配的数字、双向的逐行覆盖）。[第一份报告](../evaluation/reports/2026-11-22_skill-vs-human.md)中 20 个标记有 17 个一致（3 处分歧都在订单维）；一轮规则修订把表格和测算的数字覆盖率从约 60% 提高到 90% 以上。
- *稳定性*：`check_view.py` 检查块顺序、固定标签、每个维度恰好一个标记且顺序正确、YYYY-MM-DD 日期且最新在前、行长度（大纲而非段落），以及只追加规则。`split_bilingual.py` 对中英交替的 transcript 只保留英文。

---

## 复核（review）

### thesis-check

**做什么。** 用本地研究和网络信息校对用户自己写的投资逻辑大纲，只列出有证据的真问题，给出最小改动的修正版和投资备忘录风格的英文版。

**为什么这样设计。** 大纲出错的方式很固定：范围夸大、把管理层观点写成事实、"只有一家竞争对手"没限定细分、进度写超前、排名没有出处。本地笔记是二手整理，所以排名、份额、竞争对手和最新动态这几类论断**必须**到网上对照原始来源核实。

**基本逻辑。** 收集本地证据 → 网络核实四类论断 → 把大纲拆成单条论断并标类型（事实 / 第三方数据 / 管理层观点 / 用户判断 / 推断）→ 做八项检查 → 按固定的四块输出。

**值得注意的地方。** 大纲始终是用户的：保留用户的结构和措辞，没问题的条目直接标准确，不为显得认真而挑刺。skill 里的示例 2 展示了网络核实如何改变结论：一条没有出处的"北美约 50% 份额"被改成了"DCI 全球第一（Dell'Oro，2025）"。

### company-comparison

**做什么。** 只用已有材料，从业务与战略、技术路线、估值与财务、其他差异四个方面对比两家或多家已经研究过的公司。

**为什么这样设计。** 对比的质量取决于口径是否一致：取价日期一致、PEG 定义一致、GAAP / Non-GAAP 处理一致。这个 skill 禁止凭记忆补数字，并且固定计算几项能看出估值差距是"增速低"还是"错杀"的指标：营业利润绝对额与市值之比、统一口径下的溢价、各自模型的风险来源。

**基本逻辑。** 收集每家公司最新的文件 → 英文一句话定位 → 四个固定板块用 Markdown 表格呈现，每张表后附简短判断 → 提议保存对比。

**值得注意的地方。** 笔记里没有的技术细节标"未核实"，不凭记忆写。*稳定性*：板块标题固定，每个板块的行固定。

---

## 元 skill（meta）

### research-workflow

**做什么。** 入口。先检查这家公司已有哪些文件，给出几条固定流程（首次覆盖、新季度、加一个会议、找标的、复核）和可选附加项（与分析师手写版对比、稳定性检查、成本质量记录、规则修改建议），再按顺序运行选中的 skill。

**为什么这样设计。** 每个 skill 本来就能按描述自动触发，单一任务不需要菜单。缺的是"串联"：用哪些 skill、什么顺序、把哪个文件交给下一步、哪一步的检查必须先通过。做成 skill 而不是程序，用户在任何一步都能停下或改方向，而每条分析规则仍然只存在于一个 skill 里。

**基本逻辑。** `status.py` 读取公司文件夹（各文件的最新季度、估值日期、最新测算），指出哪些已过期 → 一个问题列出流程和附加项 → 一条简短计划，写明找到和缺少的输入 → 每一步运行真正的 skill 和它的校验 → 输出文件与检查结果表。

**值得注意。** 它从不复述其他 skill 的规则；缺输入时不问就不继续。宿主有提问工具时用可点选的选项，没有时用编号列表。*稳定性*：文件夹检查是脚本，有自测覆盖。

### skill-tuner

**做什么。** 把 skill 产出与分析师手写结果的对比变成规则修改：运行评估、给差异分类、提出修改、应用被批准的修改、作为新实验重跑，只有留出结果不变差时才保留改动。

**为什么这样设计。** 总结类和分析类 skill 替代的是主观工作，所以"更好"意味着"更接近分析师的判断方式"，而这个目标必须由分析师掌握。不加约束的话，这种循环会对少数几份参照过拟合，或学会刷字面重叠的指标。所以本 skill 把每类差异交给该处理它的一方，并且从不自行调整判断规则。

**基本逻辑。** `run_eval.py` → `diagnose.py` 把差异分为缺输入 / 格式 / 判断 / 覆盖 / 长度 / skill 独有，并找跨公司模式 → 只对两家以上公司出现的模式提案，写方法不写内容 → 分析师批准 → 修改规则，build + 自测 → 带留出运行的新实验 → `gate.py` 采纳、拒绝或标为暂定 → 写入 CHANGELOG。

**值得注意的地方。** 留出运行只当裁判，永远不当证据。采纳看标记、数字召回率和长度预算；逐行覆盖率和术语召回率只报告，从不作为目标。完整方法见 [evaluation/TUNING.md](../evaluation/TUNING.md)。*稳定性*：分类和采纳决定都由固定阈值的脚本完成，并有自测覆盖。
