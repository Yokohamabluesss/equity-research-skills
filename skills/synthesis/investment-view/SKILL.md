---
name: investment-view
description: "Maintains one living investment view per company ({TICKER}_投资判断.md in Chinese, {TICKER}_Investment_View.md in English): a Core block (positioning, special traits, main growth drivers, new narrative), one judged block per quarter (next-quarter upside drivers, an overall verdict, five ✅️ / ⚠️ / 🔻 dimensions written with earnings-digest's rules, the product table), dated notes from non-earnings events (investor days, launches and trade shows such as OFC / ECOC, broker conferences, meeting notes), and dated estimates written with valuation-brief's rules. Use after an earnings call or a valuation update, or when the user shares an event transcript or meeting notes, e.g. 'update the investment view on XX', 'write XX's quarter judgment', 'add the ECOC event to COHR', 'refresh the core logic', '更新 XX 的投资判断', '财报前瞻判断', '把这个会议加进去', '公司判断'. Adds new quarters and events on top without rewriting earlier ones."
---

# Investment View (投资判断)

One file per company that answers, at any moment: **what is this company, what drives it, what is new, how did the last quarter go, what could beat next quarter, what did other events change, and what does the valuation say.** It is the top of the research workflow: earnings-call-reader reads the calls, earnings-digest judges them, valuation-brief condenses the model, and this skill keeps the judgment current in one compact place.

> This skill was calibrated against hand-written views and is still being tuned; see `CHANGELOG.md` at the repository root.

## Conventions (fixed)

- **File**: `{RESEARCH_ROOT}/{TICKER}/{TICKER}_投资判断.md` (Chinese) or `{TICKER}_Investment_View.md` (English). If either exists, update that one and keep its language. Older names (`{TICKER}_财报前瞻判断.md`, `{TICKER}_Company_View.md`) are recognised: if only an old-name file exists, update it in place and offer to rename it.
- **Language**: a new file follows the language of the request (Chinese → `_投资判断.md`, English → `_Investment_View.md`); an existing file keeps its own language. Fixed strings exist in both languages (table below), and `check_view.py` accepts both.
- **Works on top of two skills**: the five dimensions and Other of each quarter block are written with **earnings-digest's** rules, and the estimates with **valuation-brief's** rules. Load those skills; their rules are the only copy and are not repeated here. They write straight into this file: no separate digest or brief file is created. If a digest or brief for the same quarter / date already exists, carry it over instead of rewriting it. If either skill is not installed, say so and leave that part out; don't improvise it.
- **Style - an outline, not prose**: tab-indented lines, one idea per line, phrases rather than sentences (aim for ≤ 40 Chinese characters or ≤ 25 English words per line). The hierarchy carries the logic: parent = claim, children = evidence. Tables only where a grid is clearer (product table, capacity, value chain).
- **Bilingual core (Chinese file)**: each top-level Core line is written in Chinese, followed by the same line in English on the next line. Sub-points are Chinese with English terms kept as-is. Short English quotes are kept where the exact wording matters.
- **Quarter label** `FY{YY} Q{n}` (fiscal), dates `YYYY-MM-DD`. Full dates matter: every quarter block, event note and estimate is a point-in-time record that can later be checked against what happened.
- **Point-in-time sections are append-only**: quarter blocks, event notes and estimates are never edited after they are written. New ones go on top of their section (newest first). Only the Core block is a living section (see Step 4).
- **Fixed strings** (never paraphrase):

| Element | Chinese file | English file |
|---|---|---|
| Core block | `# 核心` | `# Core` |
| Core labels | `特殊点` (optional) · `增长主驱动` · `新叙事` | `Special traits` · `Main growth drivers` · `New narrative` |
| Quarter block | `# ---FY26 Q2--- {超预期 / 符合预期 / 不及预期}，{一句话阶段}` | `# ---FY26 Q2--- {Beat / In line / Miss}, {one-phrase stage}` |
| Quarter labels | `下一季超预期点` · `判断：{总判断}` | `Next-quarter upside drivers` · `Verdict: {overall}` |
| Dimensions (in order) | `财务` · `细分产业` · `订单` · `客户` · `业绩节奏` | `Financials` · `Sub-industry` · `Orders` · `Customers` · `Momentum` |
| Extras | `其他` | `Other` |
| Events | `# ---其他会议---` | `# ---Other Events---` |
| Estimates | `# ---测算---` → `指引` · `假设` · `结论` | `# ---Estimates---` → `Guidance` · `Assumptions` · `Conclusion` |
| Free notes (user-owned) | `# 其他说明` | `# Other Notes` |

- **Block order**: Core → quarter blocks (newest first) → Other Events → Estimates → Other Notes.
- **Scripts** (`scripts/`, Python 3, no network):
  - `check_view.py FILE [--before OLD]` - structure, labels, marks, dates, order, line length, and the append-only rule. It also runs earnings-digest's dimension checks on the newest quarter block and valuation-brief's checks on the newest estimate entry (`check_digest.py` and `check_brief.py` are copied here by `tools/build.py`, so the checks stay identical).
  - `split_bilingual.py FILE -o OUT` - keeps only the English side of an alternating English / Chinese transcript (about 25% fewer characters on a real launch-event transcript).
- **Calibration** against hand-written views is not part of a normal run; it lives in the repository's `evaluation/` folder.

## Inputs (reuse first)

| Part of the file | Comes from | If missing |
|---|---|---|
| Core | `{TICKER}_Earnings.md` (all quarters), `{TICKER}_Digest.md` / `_速读.md` (logic & narrative), initial coverage note | write it from the call log using the earnings-digest rules below |
| Quarter block | the latest quarter of `{TICKER}_Earnings.md`: five dimensions + Other with earnings-digest's rules (or an existing digest's call block); upside drivers, verdict and tables by this skill | run earnings-call-reader first; never write a quarter block from memory |
| Other Events | the event transcript / minutes / slides the user provides | ask for the file; don't search for "what was said" |
| Estimates | `{TICKER}_Valuation_Dashboard.xlsx` with valuation-brief's rules (or an existing `{TICKER}_Valuation_Brief.md` / `_估值速读.md`) | leave the section as it is; suggest company-valuation |

The judgment rules for the five dimensions live only in earnings-digest, and the estimate rules only in valuation-brief. A rule change made there applies here automatically.

## Step 0: Decide what this run does

One or more of:

- **A. New quarter** - a quarter in `{TICKER}_Earnings.md` that has no block in the view yet → Steps 1–4.
- **B. Event** - the user gives an event file or notes → Step 5.
- **C. New estimate** - a valuation brief / workbook newer than the latest estimate entry → Step 6.
- **D. Core refresh only** - the user asks to revise the core → Step 4.

If the view file exists, copy it to `{its name}.backup.md` first.

## Step 1: Core (new file, or revision in Step 4)

```
# 核心
{一句话定位：它是谁、在产业链哪一层、凭什么不可替代；写成转变时用"从 X 到 Y"}
{same line in English}
	{支撑定位的事实：份额、客户覆盖、营收结构}
	{English}
特殊点                      ← only if a trait changes how to read the company
	{e.g. 供需完全由终端决定；放量节奏跟随下游}
增长主驱动
	{driver 1: product / end market}
		{downstream customers, why it grows, visibility}
	{driver 2}
新叙事
	{narrative 1}
		{before → after: why the position was closed before and why it opens now}
		{hard evidence: product, acquisition, first revenue / guidance, named customer}
		{why it matters: the mechanism, e.g. "CPO 良率要求高，所以测试是刚需"}
```

Rules:
- **The Core is a summary, not a report**: about 8–15 lines plus an optional structure table. Few numbers - the numbers live in the quarter blocks.
- **Positioning is a value-chain position, not a company profile.** Name the layer and what it does and does not do; when the sources support it, place the company in its tier with named peers (e.g. "first tier of SiPho PIC foundries, alongside …").
- **Growth drivers must answer "where does the money come from"**: a product or end market, its downstream customers, and why it is growing.
- **New narrative = not yet in the numbers.** Each item says what changed (before → after), the hardest evidence so far, and the stage (sample / first order / first revenue / guided). If there is none, write `本季无新增` / `No new narrative this quarter`.
- A small table is allowed when it explains the position better than lines (value chain, vertical-integration map) - only if the source material supports every cell.
- Inferences are marked `推测：` / `Speculation:` (e.g. "推测是 AMD").

## Step 2: Quarter block

```
# ---FY26 Q2--- 超预期，{一句话阶段，如"Q1 刚进入放量期"}

下一季超预期点
	{driver 1, with the evidence and timing}
	{driver 2}
判断：{一句总判断}
	✅️财务：{判语，如"S 曲线加速中"}
		{2–4 sub-points}
	✅️细分产业：{判语}
		{按产品线分条：产品 → 产业阶段 / 供需 / 为什么能起量}
	⚠️订单：{判语}
		{backlog / 合约 / LTA / 可见度；口径限定词照抄}
	✅️客户：{判语}
		{按产品线分条：客户 → 节点变化；消失的客户}
	✅️业绩节奏：{判语}
		{按产品线分条：只写相对上季的变化，带 🔼 🔽 🆕 ➡️ ⚠️ 📌}

| 产品 | 当前节点 | 预计放量时间 | 预计贡献体量 |
|---|---|---|---|
{condensed from the call log's latest Product Summary Table}

{optional: a capacity / utilisation / milestone table when supply is the constraint}
其他
	{supply constraint, capacity plan, pricing, one-offs}
```

How to fill it:
- **Tag**: `超预期 / 符合预期 / 不及预期` from actuals vs guidance and consensus; then one phrase on the stage of the cycle ("Q1 刚进入放量期", "爬坡中，2027 放量").
- **下一季超预期点 / Next-quarter upside drivers** (1–3 items): the specific variables that could make the next report beat - capacity ramp speed, a margin step, first revenue of a new product, a guided milestone - each with its evidence and expected timing. This is the forward-looking part of the block; it is what the next quarter's block is checked against.
- **判断 / Verdict**: one sentence that the five marks support.
- **Five dimensions and Other**: write them with earnings-digest's rules (what each dimension covers, the marks and the all-✅️ re-check, 2–4 anchor numbers in Financials, Momentum = changes only, split by product line). Only the layout differs from a digest: here it is the outline above (tab-indented sub-points, no bold), and Other comes after the tables.
- **Product table**: the latest Product Summary Table from the call log. Keep **every row and sub-row of the product lines the thesis is about**, with the cells as written in the log (including 🆕 🔼 ⚠️); drop the rows of segments outside the thesis - they get at most one line under `其他`. Don't invent cells.
- **Capacity tables**: when supply is the constraint, carry the log's capacity tables as tables - utilisation by fab with the vs-prior column, expansion tracks / phases, capacity milestones with their quotes.
- **Numbers and quotes**: every number from the call log; at most one short original quote per point.

## Step 3: Place it

Insert the new quarter block **above** the previous quarter block (directly below the Core block). Never edit older quarter blocks - if something in them turned out wrong, say so in the new block.

## Step 4: Review the Core (living section)

After a new quarter or event, check each Core line against the new evidence:

- still true → leave it, wording untouched (it is the user's wording)
- strengthened or quantified → add the new fact as a child line, marked 🔼 or 🆕
- weakened or contradicted → keep the line, add a child line starting with ⚠️ that states the conflict; don't delete the user's line
- a new driver or narrative appeared → add it with 🆕

List every Core change in the chat reply ("Core: added 🆕 …; flagged ⚠️ …") so the user can accept or undo it.

## Step 5: Other events (non-earnings materials)

Covers investor / analyst days, product launches and trade-show events (OFC, ECOC …), broker-conference fireside chats, management meeting notes, site visits, and press releases.

1. **Identify the event**: company, event name, date, speakers - from the file header or first lines. If the date or company is unclear, ask. Confirm it is the same company (watch similar names).
2. **Bilingual transcripts** (an English paragraph followed by its Chinese translation): `python scripts/split_bilingual.py FILE -o FILE.en.txt` and read the English side; the translation is not a source. Meeting notes in Chinese are read as they are.
3. **Source weight**: management speaking on the record (launch, investor day, conference) is quoted like a call. Broker meeting notes and second-hand minutes are labelled `（纪要口径）` / `(meeting-note basis)` and never treated as guidance.
4. **Write the entry** at the top of `# ---其他会议---`:

```
# ---其他会议---
2026-09-23
	ECOC — PhotonLink 发布会（CEO / CTO / EVP）
		客户合作：CPO >10 个、NPO >10 个、chip-to-chip >5 个
		CPO/NPO
			进度：未改变                ← first line of every topic: the delta vs the current view
				scale-out CPO 2026Q4 量产；scale-up CPO 2H27；NPO 2H27（LTA 核心客户）；chip-to-chip 2029–2030
			CW：与两家头部 AI hyperscaler 签 LTA，覆盖 CPO 与 NPO
			ELS：送样中
		{other topics: products, capacity, TAM / content per system (marked as management view)}
```

   - **The first line of each topic is the delta against the current view**: `进度：未改变 / 提前 / 推迟 / 🆕` (`Progress: unchanged / earlier / later / 🆕`). An event is worth recording mainly for what it changes.
   - Then only new facts about thesis items: counts, timelines, LTAs, sample / production status of the components the thesis depends on.
   - At most one line for management's TAM / content-per-system claims (labelled as management view).
   - Keep an entry short - about 10–20 lines. Skip component catalogues and marketing narrative.
5. If the event changes a Core line or a next-quarter upside driver, handle the Core as in Step 4 and say in the reply which upside driver it affects. Don't edit the quarter block.

## Step 6: Estimates

Add a dated entry at the top of `# ---测算---`, in the valuation-brief format. The entry's date is the day the skill is called, and the price is the latest price on that day (refresh it if the brief or workbook is older, as valuation-brief does):

```
# ---测算---
2026-10-14（股价 $209.16）
	指引
		{next-quarter guidance; long-term targets / milestones}
	假设
		{revenue path and its source}; {margin path}
	结论
		{① revenue-path source and guidance coverage; how conservative}
		{② margin path with a judgment on when the target is reached}
		{③ FY cur PE + EPS growth; FY+1 PE + EPS growth; PEG; FCFF reverse DCF}
		{④ gap to consensus and its source}
```

Write the entry with valuation-brief's rules (load it): read the workbook's Conclusion and PE & PEG sheets, refresh the price as it requires, and write straight into this section - no separate brief file. If a brief for the same date already exists, carry it over. **Carry it at full resolution - this section is not condensed further**:
- guidance with both ends of each range, and which items the company does not guide;
- the long-term model in $ and % (revenue, gross profit, operating profit, net income, opex ratio);
- the quarterly revenue path and the margin path, quarter by quarter where the model has them;
- the margin decomposition (gross-margin change and opex-ratio change, full-year and exit-quarter);
- the consensus gap by year, attributed by variable, plus the one-sentence nature of the disagreement and how consensus moved since the last estimate.

When the conclusion gets long, `数值` (`Figures`) and `一致预期` (`Consensus`) may follow `结论` as extra labels. No "cheap / expensive": write the condition the price requires.

## Step 7: Check and deliver

1. `python scripts/check_view.py FILE --before FILE.backup.md` (first run: without `--before`). Fix every FAIL in the new parts; LEGACY lines are old-format issues in earlier entries - report them once, never rewrite them. Delete the backup after the check passes.
2. Reply with: what was added (quarter / event / estimate), the Core changes (Step 4 list), and the one thing most worth watching before the next report. Don't paste the file.

## Rules

1. **Facts from the inputs only.** Numbers, quotes and customer names come from the call log, the event file or the valuation material - never from memory.
2. **Judgments are explicit and justified**; speculation is labelled.
3. **The user's words are kept.** Core lines are not rewritten; point-in-time entries are not edited.
4. **No buy/sell advice, no price target.** Beat probability and "what the price requires" are fine; "cheap / worth buying" is not.
5. **Fixed strings** are copied from the table above.
