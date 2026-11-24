---
name: quarterly-financials-dashboard
description: "Builds a structured xlsx dashboard of a listed company's key financials over the last N quarters (default 10): non-GAAP P&L + GAAP P&L + GAAP-vs-non-GAAP reconciliation + balance-sheet inventory and order proxies (deferred revenue / customer deposits / contract liabilities) + cash flow, plus Key Observations. Use when the user says 'make a table', 'last N quarters of financials', 'non-GAAP history', 'pull XX's quarterly results', 'financial dashboard / quarterly dashboard / financial summary', 'add inventory / contract liabilities / cash flow', '列张表', '过去 N 个季度的财务数据', or any request to compare many quarters side by side rather than summarise one. Versus earnings-call-reader: that one reads one transcript deeply into markdown; this one takes a ticker and lines up N quarters of numbers in an xlsx. Use both: this one for the financial rhythm, that one for what happened each quarter."
---

# Quarterly Financials Dashboard

Turns a company's last N quarters (default 10) of key financials into one xlsx dashboard plus Key Observations. Goal: within **30 seconds** of opening it, the user sees where the company is in its cycle - by putting non-GAAP P&L, GAAP P&L, inventory / order proxies and cash flow **side by side** on the same quarter axis.

## Conventions (fixed)

- **Layout comes from the script, not from memory**: put the researched numbers into a JSON file and run `python scripts/build_financials_xlsx.py data.json {TICKER}_Financials_{N}Q_Dashboard.xlsx`. The script writes every row, formula, colour, note and the observations table exactly as specified below; the JSON format is in the script header.
- **Check before delivery**: `python scripts/check_financials_xlsx.py FILE.xlsx` - LibreOffice recalculation, formula errors, sheet order, required rows, formulas-not-values, tax-rate note, observations. Fix every FAIL.
- **Language**: row labels and sheet names are fixed English strings (they are read by other skills). Notes follow the request language. Key Observations are always **bilingual in two columns** (English / Chinese).
- **Quarter labels**: the company's fiscal labels, `FY26 Q3` style.

## Core principles

1. **Across quarters, not deep into one.** This is not a research report or a single-quarter recap; it lines up many quarters to see the trend. **The xlsx is the main deliverable**; Key Observations support it.
2. **Non-GAAP and GAAP side by side** - **always** two full P&Ls: non-GAAP is management's view (ex SBC / amortisation / restructuring), GAAP is what investors finally get. **For tech companies these often differ a lot** (especially with recent acquisitions or large SBC); non-GAAP alone badly overstates earnings quality.
3. **Three layers, all required**:
   - **P&L**: Revenue / YoY / QoQ / Gross Margin / Op Income / **Op Margin (%)** / Net Income / Diluted EPS - non-GAAP and GAAP on separate sheets
   - **Balance sheet**: inventories, contract-liability proxies (deferred revenue + customer deposits / contract liabilities), accounts receivable
   - **Cash flow**: cash from operations (CFO), cash & short-term investments at period end
4. **Order proxies are the soul of the table.** Most US semi-equipment / industrial companies **don't formally disclose backlog**, so build the closest proxy from the balance sheet:
   - **Deferred revenue** - billed but not recognised, usually signed-but-undelivered service/installation
   - **Customer deposits** - prepayments to equipment makers: ordered but not shipped
   - **Contract liabilities** - the ASC 606 / IFRS 15 line; common for A-share companies
   - Together (or any one consistently) they **lead revenue by 1–2 quarters** - the best proxy for order inflections.
5. **Cite everything.** Each number has a note on which 8-K / 10-Q / 10-K it came from, at least to the quarter.
6. **Source priority**:
   - **US**: 8-K Exhibit 99.1 (quarterly press release) > 10-Q note "Balance Sheet Components" (inventory / deferred revenue detail) > 10-K (annual) > call transcript (cross-check figures like CFO)
   - **A-share / HK**: periodic reports (quarterly / interim / annual) consolidated balance sheet > cash-flow statement > results-briefing minutes / preliminary results > CNINFO / HKEXnews
   - Cross-check key numbers in at least two sources.

## Workflow

### Step 0: Scope (5 seconds)

- **Company**: ticker / name / exchange
- **Number of quarters**: default 10; follow the user if they say "last 8 quarters" or "last 4 years"

If the conversation has just been about a company (**e.g. its earnings call was just summarised or it was just researched**), use it - **don't ask**.

### Step 1: Pull the data (the bulk of the work)

Quarter by quarter, oldest to newest, use web search + fetch on the 8-K Exhibit 99.1 (US) or periodic report (A-share / HK).

**The SEC EDGAR 8-K Exhibit 99.1 is the gold source** - every quarter's non-GAAP table (gross margin, operating income, net income, diluted EPS) and condensed balance sheet. Note: the 8-K usually has only the summary balance sheet; **inventory / deferred revenue / customer deposit detail is in the 10-Q note (e.g. Note 6 "Balance Sheet Components")**.

**Pull both non-GAAP and GAAP**:
- non-GAAP: gross margin / opex / operating income / operating margin / net income / diluted EPS
- GAAP: the same on a GAAP basis

**Search templates**:
- `"{Company}" Q{n} {YYYY} non-GAAP EPS revenue adjusted` - non-GAAP P&L
- `"{Company}" Q{n} {YYYY} GAAP net income EPS diluted` - GAAP P&L
- `"{Company}" 10-Q {month} {YYYY} inventory deferred revenue customer deposits` - balance-sheet detail
- `"{Company}" Q{n} {YYYY} cash from operations earnings release` - CFO

If a data point is in **neither the 8-K nor the 10-Q** (typical: the 8-K is out but the 10-Q is not yet; or the 10-K hides Q4 detail in a different note), **use null and explain in the notes**. **Never invent a number.**

**Non-GAAP effective tax rate**: no separate row (space), but **must** be in the non-GAAP notes, e.g. "non-GAAP effective tax rate ~X%". It is the key parameter from Op Income to Adj Net Income, and explains why Adj NI ≠ Adj Op Income × (1 − statutory rate) (interest, minorities too). The builder refuses JSON without it.

**Balance-sheet items**: a 10-Q's balance-sheet detail compares "this quarter end" with "last fiscal year end"; take only the current column. For a Q4, use the 10-K (the 8-K may not have detail).

### Step 2: Build the xlsx (script)

Output `{RESEARCH_ROOT}/{TICKER}/{TICKER}_Financials_{N}Q_Dashboard.xlsx` when a local research folder exists; otherwise the session outputs folder. ("Non-GAAP" is not in the file name because it now holds GAAP too.)

**Four sheets** (left to right, fixed names):
1. **`Non-GAAP`** - non-GAAP P&L (incl. Op Margin)
2. **`GAAP`** - GAAP P&L (incl. GAAP Op Margin)
3. **`GAAP vs Non-GAAP`** - the delta (net-income gap, EPS gap, gap as % of Adj NI)
4. **`BS + CF + Observations`** - balance-sheet detail + cash flow + Key Observations (Excel caps sheet names at 31 characters, so the longer "Balance Sheet + CF + Observations" cannot be used)

**Sheet 1 (Non-GAAP) layout (metrics as rows, quarters as columns)**:

```
Row 1   : title (Company — Non-GAAP Quarterly Dashboard (N Quarters))
Row 2   : source line
Row 3   : (blank)
Row 4   : header (Metric | Q(N-9) | ... | Q(now) | TTM)
Row 5   : Period End
Row 6   : Revenue ($M)
Row 7   : Revenue YoY %                 ← formula; helper rows for the first 4 quarters
Row 8   : Revenue QoQ %                 ← formula
Row 9   : Adj Gross Margin %
Row 10  : Adj OpEx ($M)
Row 11  : Adj Operating Income ($M)     ← = Revenue × GM − OpEx (formula)
Row 12  : Adj Op Margin %               ← = Op Income / Revenue (formula) ⭐ required
Row 13  : Adj Net Income ($M)
Row 14  : Adj NI YoY %                  ← formula
Row 15  : Adj NI QoQ %                  ← formula
Row 16  : Adj Net Margin %              ← = NI / Revenue (formula)
Row 17  : Adj EPS ($)
Row 30-33: helper rows (prior-year same quarter revenue / NI; prior quarter for the first QoQ)
Row 38+ : Notes (incl. the non-GAAP tax-rate note)
```

**Sheet 2 (GAAP)**: rows 6–17 parallel to sheet 1 with GAAP numbers. GAAP gross margin: if hard to get, leave null rather than approximating (or approximate and say so in notes); GAAP opex / op income / op margin as complete as possible; GAAP net income / EPS required.

**Sheet 3 (GAAP vs Non-GAAP)**:

```
Row 5   : Adj Net Income ($M)      ← typed copy of sheet 1 (no cross-sheet formulas - less fragile)
Row 6   : GAAP Net Income ($M)     ← typed copy of sheet 2
Row 7   : Delta ($M)               ← = Row 5 − Row 6
Row 8   : Delta / Adj NI %         ← = Row 7 / Row 5
Row 10  : Adj EPS ($)
Row 11  : GAAP EPS ($)
Row 12  : Delta EPS ($)            ← = Row 10 − Row 11
Row 15+ : Notes on the delta's components (SBC / amortisation / restructuring / acquisition one-offs ...)
```

**Sheet 4 (BS + CF + Observations)**:

```
[BALANCE SHEET — Inventory & Demand Signals]
Row 6   : Inventories, net ($M)
Row 7   : Deferred Revenue (current) ($M)
Row 8   : Customer Deposits / Contract Liabilities ($M)
Row 9   : Accounts Receivable, net ($M)
[CASH FLOW]
Row 12  : Cash from Operations ($M)
Row 13  : Cash & ST Investments (EOP) ($M)
[COMPUTED METRICS] (formulas)
Row 16  : Inventory Days (= Inventory / Revenue × 90)
Row 17  : Order-related Liab. (= Deferred Revenue + Customer Deposits)
Row 18  : CFO / Adj NI (cash conversion)
[The Story / 一句话总结]  then the 8-theme observations table
```

**Format standard** (implemented by the builder): Arial 10; typed data blue (0000FF), formulas black; section rows fill D9E1F2 + dark-blue bold text; non-GAAP header 305496 + white bold, GAAP header 8064A2 + white bold (to tell the bases apart at a glance); latest quarter column FFF2CC; `$M` `#,##0.0;(#,##0.0);-`, `%` `0.0%;[Red](0.0%);-`, EPS `$0.00;($0.00);-`, multiples `0.00"x";(0.00"x");-`; column A ~30, quarter columns 12, TTM 14; freeze panes `B5`; thin grey borders (BFBFBF); text cells wrap and **row heights are not hard-coded** (hard-coded heights stop Excel auto-fitting and clip long text).

**Computed items are Excel formulas, never typed**: YoY, QoQ, Op Income, Op Margin, Net Margin, inventory days, order-related liabilities, cash conversion, TTM - so correcting one input updates the whole table.

**Required notes (Non-GAAP sheet)** - the builder adds the standard ones; add the company-specific ones in `notes.nongaap`:
1. fiscal-year convention (e.g. year ends in month X; FY label = ending year)
2. data source (e.g. SEC 8-K press releases)
3. **every estimated / derived number, one by one** (e.g. FY25 Q4 Adj NI = implied full-year Adj NI − Q1–Q3)
4. Op Income and Op Margin are formulas (Revenue × GM − OpEx)
5. **tax-rate note**: "non-GAAP effective tax rate X%"
6. YoY uses helper rows for the first quarters
7. latest quarter highlighted

**Required notes (GAAP vs Non-GAAP)** - in `notes.delta`:
1. delta components: SBC + intangible amortisation + restructuring + acquisition one-offs + tax adjustments
2. unusual quarters (e.g. an acquisition quarter with one-off charges)
3. a normalised run-rate estimate of the delta
4. TTM delta summary

### Step 3: Deliver

1. `python scripts/check_financials_xlsx.py FILE.xlsx` - must PASS (recalculation is required, so other skills reading cached values see numbers).
2. Hand over the xlsx.
3. Short chat note (don't repeat the table):
   - Key observations in **3–5 sentences** (tell the story, don't restate numbers)
   - **One sentence on GAAP vs non-GAAP** (e.g. "TTM GAAP net income is only 66% of non-GAAP, mainly acquisition one-offs + rising SBC")
   - **One natural next step** (e.g. "want a PE / PEG valuation on top of this with company-valuation?")

## Key Observations

**At the top: a "The Story / 一句话总结" highlighted box** (fill FFF2CC, dark-blue text, merged across), **one English paragraph and one Chinese paragraph** (3–5 sentences each). It is read first and **must** include: ① the key quarters at the start / end of the cycle ② revenue / EPS high and low points ③ the leading-indicator inflection most worth catching ④ one sentence on next quarter.

Then the 8-theme table, **three columns**:

| Theme / 主题 | Observation (English) | Observation (中文) |
|---|---|---|
| 1. Revenue cycle / 收入周期 | where in the cycle (peak / trough / recovery) + data | same in Chinese |
| 2. Margin compression / 利润率压力 | change in non-GAAP and GAAP gross and operating margins, and why | |
| 3. Non-GAAP vs GAAP delta / 两套口径的差距 ⭐ required | size, causes, whether it will normalise | |
| 4. Inventory tells the cycle story / 库存讲周期故事 | inventory highs/lows, destocking/restocking rhythm | |
| 5. Order-proxy = leading indicator / 订单代理 = 领先指标 | inflection in deferred revenue + deposits vs revenue inflection lead time | |
| 6. Cash conversion / 现金转化 | CFO / NI ratio, working-capital changes | |
| 7. Guidance trajectory / 指引轨迹 | next-quarter / next-year guidance vs this quarter's actual | |
| 8. Things to monitor / 后续跟踪 | the leading indicators to watch over the next 1–2 quarters | |

**Theme 3 (non-GAAP vs GAAP delta)** is its own dimension for tech companies:
- is the SBC share inflating (compensation structure)?
- is intangible amortisation one-off or structural (new vs existing)?
- any unusual quarters (acquisition one-offs)?
- does the delta mean-revert?

**Bilingual rules**:
- Theme names are English / Chinese separated by " / " (e.g. `1. Revenue cycle / 收入周期`)
- Observations in **two separate columns**, never both languages in one cell - each reader reads one column undisturbed
- The two versions are **paraphrases, not literal translations** - natural in both languages
- Numbers, tickers and product codes (Q3 25, $266.6M, HBM VPA, Dragonfly® 3Di) stay unchanged in both

**How to write observations**:
- Every observation **has numbers** ("op margin rebounded from 21.1% to 25.2%, +410bp", not "margin improved")
- Every observation **says whether it is a leading or lagging indicator** (orders lead, revenue is coincident, gross margin lags)
- Things to monitor names **specific line items** (not "watch results" but "watch whether deferred revenue + customer deposits in the Q1 26 10-Q reflects the $240M HBM VPA")

## Why order proxies matter

Many users and sell-side analysts start writing after a single press release and **badly underweight the balance sheet**. In fact:

- **Deferred revenue + customer deposits** usually lead revenue by 1–2 quarters. E.g. ONTO's deferred revenue jumped to $33.8M in Q4 24 (from $26.8M the quarter before), and Q1 25 revenue then hit a record $266.6M.
- **Inventory** is a lagging and a state indicator. Consecutive declines usually mean destocking / a down-cycle; inventory rising together with revenue is healthy expansion.
- **CFO / non-GAAP NI** is a quality indicator. For semi-equipment companies it should sit around 1.0–1.3x; below 0.5x is a warning (usually AR + inventory both ballooning - revenue quality deteriorating).

Putting the three layers on one N-quarter table is the most effective way to judge **cycle position** - the main difference from a single-quarter call summary.

## Hand-offs

This skill is the **fact base** of company research:

1. **earnings-call-reader** (before or after): read a quarter's call deeply; cross-check with these numbers
2. **company-research** (before): qualitative segment / customer / product frame first, then this skill adds the rhythm
3. **company-valuation** (after): uses this table's non-GAAP + GAAP EPS **as its input**, so it does not re-pull data

That is why **both P&Ls** matter - not for looks, but because **the valuation skill computes PE / PEG on both bases**.

## History

- **First use (ONTO)**: 10 quarters of non-GAAP data with inventory, contract-liability proxies and cash flow, turned into this skill.
- **Upgrade (CIEN 2026Q2)**: GAAP sheet + explicit Op Margin + tax-rate note + GAAP vs non-GAAP delta sheet; 157 formulas.
- **Current**: layout moved into `scripts/build_financials_xlsx.py`; `scripts/check_financials_xlsx.py` before delivery; sheet 4 renamed `BS + CF + Observations` (31-character limit).
