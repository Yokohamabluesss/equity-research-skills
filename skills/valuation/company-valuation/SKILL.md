---
name: company-valuation
description: "Valuation judgment for a listed company, built bottom-up quarter by quarter from guidance, financial trends, orders, industry demand and product ramps down to non-GAAP and GAAP EPS; sell-side consensus is only a cross-check (its implied quarterly growth is backed out, never copied). Outputs a 10-sheet xlsx with the same format for every company: Conclusion (guided vs assumed growth, key assumptions, gaps to consensus, a one-line PE vs FCFF vs SoTP verdict), PE / PEG on two bases and three periods, three-scenario multi-stage FCFF, reverse DCF of the current price and a peer PE check. Use when the user says 'value it', 'what's the PE', 'is it expensive', 'PEG', 'DCF', 'FCFF', 'what does the price imply', 'SoTP', '估值一下', '贵不贵', or turns a company discussion to valuation. The last step after company-research, earnings-call-reader and quarterly-financials-dashboard. No buy/sell advice, no price target."
---

# Company Valuation

Valuation judgment for a company that has already been researched / tracked through earnings. Output: an xlsx valuation dashboard **with the same format for every company** plus a short read-out. The point is that within 30 seconds on the **Conclusion** sheet the user sees four things:

1. Which parts of the modelled growth path are **locked by company guidance** and which are **my assumptions**;
2. What the key guidance and the key assumptions are;
3. Where and on which variable the model differs from consensus;
4. **Whether this company should be valued on PE, FCFF or SoTP.**

The PE / PEG, FCFF, reverse-DCF and peer details come after.

## Conventions (fixed)

- **Language**: sheet names are always the English names below. Cell text (labels, basis, notes) follows the request language; when updating an existing dashboard, keep its language.
- **Template by construction**: build the workbook with `scripts/val_style.py` (sheet list, colours, fonts, number formats, page layout). Do not re-type hex codes or formats by hand.
- **Check before delivery**: `python scripts/check_valuation_xlsx.py {TICKER}_Valuation_Dashboard.xlsx` recalculates with LibreOffice, scans for formula errors and text starting with `=`, and checks the template (sheets, order, freeze panes, verdict row, basis column, terminal-value share). Fix every FAIL.
- **Inputs from other skills**: `{TICKER}_Earnings.md`, `{TICKER}_Financials_*Dashboard.xlsx`, `{TICKER}_Digest.md` or `{TICKER}_速读.md`, `{TICKER}_*_Initial_Coverage.md` or `{TICKER}_*_首次研究.md`.

---

## Core principles

### 1. ⭐ EPS forecasts are built bottom-up by quarter; consensus is only a cross-check

**The most important rule, and the easiest one to skip.**

❌ **Forbidden**: entering consensus full-year EPS as the Base case.
✅ **Required**: derive **each quarter's** revenue growth, gross margin and opex ratio from **five kinds of evidence - call guidance, financial trends, orders and visibility, industry demand, product ramp timing** - and build up to EPS.

Why: consensus is "the average of other people's models"; it does not explain its assumptions and lags the latest call. Copying it throws away the point of the workbook. The user wants "**why do you forecast this**", not "**what do others forecast**".

Consensus has two required uses:
- **Back out its implied quarterly path** (principle 3) and set it next to the model, quarter by quarter.
- **Sanity check**: if model full-year EPS differs from consensus by more than ±10%, explain in Notes and on Conclusion which variable causes it (revenue pace? gross margin? opex? share count?).

### 2. ⭐ Every assumption states "why"

The Assumptions sheet **always has three columns**: `Item | Value | Basis and derivation`.

The third column does not accept "assumed", "expected", "based on history". It must point to concrete evidence, at least one of:
- **A call quote** (management's words; in a Chinese workbook, English original + Chinese)
- **A guidance number** (range and midpoint, and which end was used)
- **A verifiable historical series** (e.g. "last 4 quarters' GM step +60/+30/+57/+66bps, mean +53bps, so +50bps")
- **An order / capacity / product-timing fact**
- **Back-solving management's long-term target**

**If an assumption truly has no basis, write "No direct basis; X used (conservative/neutral)" - label it honestly, don't dress it up.**

### 3. ⭐ Back out consensus's implied quarterly growth

Consensus usually gives only full-year revenue and EPS. Split it by quarter:
- Guided quarters are locked to company guidance (the sell side copies these too).
- Remaining quarters by **constant QoQ growth**: assume the remaining N quarters grow at a constant g; solve g so the year sums to consensus.
- Put the implied g next to the model's g.

Value: you see immediately "what the sell side is actually assuming".

### 4. ⭐ Three methods: choose first, then compute

Supported: **PE / PEG**, **multi-stage FCFF (with reverse DCF)** and **SoTP**. **Decide which fits before starting**, and put the verdict on the first line of Conclusion (see "Method selection framework").

Default:
- **Do PE and FCFF together** (PE as the near-term anchor, FCFF for the long end and the reverse DCF), and give a one-line view on Conclusion of which is more credible.
- **Only when SoTP fits better** convert the FCFF sheet into a SoTP sheet (see "SoTP variant").

### 5. ⭐ FCFF is about scenarios + reverse DCF, not a precise point

The least useful FCFF is a per-share value to the cent used as a target price. Here FCFF has exactly three jobs:

1. **Three scenarios**: vary only **high-growth years N1** and **mature EBIT margin** (plus terminal growth) and see how wide the per-share range is - the width is information.
2. **Reverse DCF**: fix WACC and terminal growth and solve for the **(N1, mature margin) combinations implied by the current price**, then judge whether those conditions are reasonable.
3. **Cross-check**: compare 1–2-year forward PE with peers - do growth and earnings quality explain the premium / discount?

⚠️ **An FCFF per-share value is not a target price.** Always phrase it as "under scenario X the model gives $Y per share", followed by "this is not a price target".

### 6. Non-GAAP and GAAP, both

The two bases give very different views of earnings quality; using one alone misleads.

**GAAP is not modelled separately**: `GAAP EPS = non-GAAP EPS − delta per share`. The delta needs a basis:
- its components (acquired-intangible amortisation / SBC / restructuring / impairment / gains / tax adjustments)
- the **rigid** part (amortisation) versus the **flexible** part (SBC)
- whether it narrows or widens, and why

⚠️ **FCFF always starts from GAAP EBIT**, never non-GAAP EBIT - SBC is a real cost to shareholders; adding it back systematically overstates free cash flow. If SBC is large relative to revenue, say so in Notes.

### 7. P/E timing must be exact

The numerator (price) is "now"; the denominator (EPS) needs an explicit period. **Three periods, always**:
- **FY(current)** - the current fiscal year
- **NTM (next twelve months)** - rolling 12 months from today, weights by actual months, stated
- **FY(current+1)** - the next full fiscal year

### 8. PEG must be time-aligned

PEG = P/E ÷ G. **If the P/E denominator is FY(t) EPS, G must be FY(t)-related growth**:

| PEG version | P/E | G | Use |
|---|---|---|---|
| **PEG (FY cur)** | FY(cur) P/E | FY(cur) YoY EPS growth | 📌 **sell-side standard**, main basis |
| **PEG (Peter Lynch)** | FY(cur) P/E | 2–3-year forward EPS CAGR | 📌 Lynch's original; smooths one-year noise |
| **PEG (NTM)** | NTM P/E | same multi-year CAGR | rolling basis |
| **PEG (conservative)** | FY(cur) P/E | sell-side multi-year growth | conservative bound |

**Never output FY(cur) P/E with FY(cur+1) YoY G** - misaligned, the classic valuation error.

⚠️ Equally common: **EPS-based P/E divided by revenue growth**. P/E's denominator is EPS, so G must be EPS growth. With revenue growth, the matching multiple is EV/Sales, not P/E.

If FY(cur) has a reset effect (low base, acquisition one-off, negative prior year, margin recovering from a cycle low), that PEG is distorted: **flag it with ⚠️ in the sheet** and recommend the Lynch multi-year version on Conclusion.

### 9. No buy/sell advice, no target price, no "cheap/expensive"

Present multiples, per-share ranges, implied conditions, and comparisons with history and peers. Write "NTM PE is X vs peers at Y", "the price requires N years of high growth and an M% mature margin" - not "expensive", "cheap", "worth buying".

---

## ⭐ Method selection framework

### Three veto questions first

| # | Question | If "no" |
|---|---|---|
| 1 | **Consistently profitable** over the forecast, with a small and predictable GAAP / non-GAAP gap? | **PE unusable or badly distorted** |
| 2 | Free-cash-flow **direction predictable** (CapEx pace clear, not in an extreme expansion or contraction)? | **FCFF has low credibility** |
| 3 | **A single main business**, segments valued on similar logic, no large non-operating assets? | **Use SoTP instead** |

### Then the positive fit

**PE / PEG first** when:
- single main business, positive earnings, clean basis
- growth visibility comes from **orders / long contracts / contract values** (externally verifiable)
- CapEx does not dominate cash flow, or moves with revenue
- a clear peer group exists (same segment, business model, growth band)

**FCFF first** when:
- cash flow stable and predictable; the capital cycle has peaked
- **no usable peers** (unique business, cross-segment, no meaningful peer multiples)
- margin is mid-way through a structural rise, so PE's denominator is too assumption-sensitive (a 10% change in the denominator moves P/E ~11% the other way)
- terminal value is a manageable share of EV (<75%)

**Both (the default)**: PE as the near-term anchor (1–2 years, verifiable), FCFF for the long end and the reverse DCF ("what does the price imply"). If they conflict, the conflict is the most important output.

**SoTP fits better** if any of:
- **segments with very different valuation logic**, e.g. "equipment (low margin, cyclical, share fights) + software subscriptions (high margin, recurring) + patent licensing (almost pure profit, decoupled from shipments)" - any single group multiple is pulled up by the high-margin part and down by the low-margin part
- **segments growing in opposite directions** (one shrinking, one growing fast) - group growth hides the structure
- **large non-operating assets**: high net cash relative to market cap, patent portfolios, long-term equity stakes, real estate
- **large minority interests or JV structures** - parent vs consolidated differ a lot
- **a segment being spun off / sold**

> Typical case: a telecom-equipment maker with four parts - mobile networks + network infrastructure + cloud and network services + patent licensing. Licensing is under 10% of revenue but may be over a third of operating profit and has nothing to do with the equipment cycle. A group PE overvalues equipment and undervalues licensing; a group FCFF mashes two different cash-flow curves into one. Choose **per segment** (equipment EV/Sales or EV/EBITDA, software EV/Sales, licensing DCF or perpetuity), sum, then adjust for net cash and minorities.

### Output requirement

**Row 1 of the Conclusion content (row 5 of the sheet) is a one-sentence method verdict in a fixed form:**

> **Method conclusion**: this company is currently best valued with **{PE / FCFF / PE+FCFF / SoTP}**, because {reason}; {excluded method} does not fit because {reason}.

---

## Workflow

### Step 0: Scope (10 seconds)

- **Company**: ticker / exchange
- **Fiscal position**: latest reported quarter, current quarter in progress
- **Share price**: **must** be fetched by web search as the latest price on the day the skill is called (also when an existing workbook is reused); record the date and time (close / intraday / after-hours) next to the price cell. The Conclusion sheet reads price, multiples and FCFF results from cells (formulas), never as typed-in numbers, so a price update flows through every sheet
- **⭐ Method pre-check**: run the three veto questions and settle PE / FCFF / SoTP up front

**If the conversation has been about a company** (an earnings-call log or dashboard just updated), use it - **don't ask**.

### Step 1: Load existing data (reuse first; don't pull everything from the web)

```bash
ls {RESEARCH_ROOT}/{TICKER}/{TICKER}_Financials_*Dashboard.xlsx 2>/dev/null           # quarterly history
ls {RESEARCH_ROOT}/{TICKER}/{TICKER}_Earnings.md 2>/dev/null                          # guidance and events
ls {RESEARCH_ROOT}/{TICKER}/{TICKER}_Digest.md {RESEARCH_ROOT}/{TICKER}/{TICKER}_速读.md 2>/dev/null   # condensed logic
ls {RESEARCH_ROOT}/{TICKER}/{TICKER}_*_Initial_Coverage.md {RESEARCH_ROOT}/{TICKER}/{TICKER}_*_首次研究.md 2>/dev/null
```

Extract the **five kinds of evidence**:

| Evidence | From | Used to set |
|---|---|---|
| **① Guidance** | Earnings.md → Guidance | next-quarter revenue / GM / opex / tax / EPS anchors |
| **② Financial trends** | Financials Dashboard | historical QoQ/YoY, GM step series, opex trends, conversion |
| **③ Orders and visibility** | Earnings.md → Order Book | whether growth can hold, visibility into which FY |
| **④ Industry demand / capacity** | Earnings.md → Demand / Capacity | demand- vs supply-constrained; capacity ramp timing |
| **⑤ Product ramp timing** | Earnings.md → Product Summary Table | first revenue of new products and their ramp |

FCFF additionally needs **D&A, CapEx history and plans, working-capital items (inventory / AR / AP / contract liabilities), debt and cash** - from the Financials Dashboard.

### Step 2: ⭐ Bottom-up quarterly model

Build in this **fixed order**, leaving a basis at every layer:

#### 2.1 Revenue path (QoQ by quarter)
- **Guided quarters**: guidance midpoint (Base), top (Upside), bottom (Downside)
- **Unguided quarters**: QoQ must come from at least one of:
  a. **Back-solving a management long-term target** ⭐ highest priority (run-rate targets, quarterly revenue milestones, capacity multiples)
  b. **Capacity / supply timing**: when capacity doubles, when the bottleneck clears, "full financial effect in quarter X"
  c. **Order visibility**: how far backlog reaches, contract values, whether fully booked
  d. **Product ramp**: which quarter a new product's first revenue arrives
  e. **Historical seasonality**: only for demand-driven companies; **give it much less weight for supply-constrained ones**
- ⚠️ **Whether capacity arrives as a step or a line is the most-missed point.** If management says "full financial effect in quarter X", that quarter's QoQ should be clearly above its neighbours - don't flatten it into constant growth.

#### 2.2 Gross-margin path
- Start: the next-quarter guidance range
- ⭐ **Prefer assuming an *incremental* gross margin to assuming GM levels**: `GP(t) = GP(t−1) + incremental GM × ΔRev`. Basis: management's disclosed drop-through, or back-solved from "current point" and "long-term model point".
- **Always compare with the company's own long-term GM target** and say when the path reaches it.

#### 2.3 Operating-expense path
- Start: next-quarter opex guidance midpoint ÷ revenue midpoint
- Then: any **opex target model**, and management's statements on operating leverage
- Line items can move in opposite directions (SG&A down, R&D deliberately up)

#### 2.4 Operating income → net income conversion
- **List the last 4 quarters' actual conversion ratios**; look at the trend
- **Back-calibrate with next-quarter EPS guidance** - if no EPS guidance, cross-check gross or operating profit against consensus
- All three scenarios use the same conversion path

#### 2.5 Diluted shares
- Separate **one-off dilution** from **recurring dilution** (equity comp usually 1–2% a year)
- If management states expansion will not dilute, quote it

#### 2.6 EPS
`EPS = (revenue × GM − opex) × conversion ÷ diluted shares`, all as Excel formulas.

### Step 3: ⭐ Back out consensus and compare

1. Get consensus **full-year revenue** and **full-year EPS** (source, number of analysts, update date, GAAP or non-GAAP)
2. Back out the implied QoQ for the remaining quarters with constant growth
3. **Side by side by quarter: model vs consensus**, and **attribute the gap by variable** (points from revenue, from GM, from opex / tax / shares)
4. One sentence on **the nature of the disagreement** (level of growth, or the shape of the ramp?)

### Step 4: PE (3 scenarios × 2 bases × 3 periods, all formulas)

### Step 5: PEG (strictly time-aligned, principle 8)

### Step 6: ⭐ Multi-stage FCFF, three scenarios

#### 6.1 WACC (every input with its basis)
```
Ke = Rf + β × ERP
Kd(after tax) = Kd(pre-tax) × (1 − tax rate)
WACC = Ke × E/(D+E) + Kd(after tax) × D/(D+E)
```
- Rf: local 10-year government yield, with the date
- ERP: state the source (Damodaran / broker)
- β: source and regression window; if the business model just changed, say whether historical β still applies
- weights use **market value** of equity and **book value** of debt

#### 6.2 Three stages
| Stage | Years | Revenue growth | EBIT margin |
|---|---|---|---|
| High growth | **N1 (scenario variable)** | g1 (extended from the model) | linear from today to **m_mature (scenario variable)** |
| Transition | N2 (fixed, usually 3–5 years) | linear from g1 to g_term | m_mature |
| Terminal | ∞ | **g_term ≤ nominal GDP (usually 2.0–3.0%)** | m_mature |

⭐ **The three scenarios vary only N1, m_mature and g_term.** Do not just flex revenue ±10% - that is not scenario analysis.

#### 6.3 Annual FCFF
```
FCFF = EBIT × (1 − tax) + D&A − CapEx − ΔNWC
```
- **EBIT on a GAAP basis** (principle 6)
- D&A and CapEx as ratio paths to revenue, with when they converge (after heavy expansion, CapEx/revenue should fall back near D&A/revenue)
- ΔNWC: extrapolate the historical NWC / revenue ratio; **large customer prepayments are negative NWC that flows back out on delivery - say so**

#### 6.4 Valuation summary (required items)
```
EV = Σ PV(explicit FCFF) + PV(terminal value)
Terminal value = FCFF(final year) × (1+g_term) / (WACC − g_term)
Equity = EV + net cash − minority interests
Per share = equity ÷ diluted shares
```
- ⭐ **Always report terminal value as a share of EV**:
  - <60%: normal
  - 60–75%: acceptable, flag it
  - **>75%: ⚠️ valuation driven mainly by the terminal assumption; FCFF credibility drops**
  - **>85%: 🔻 FCFF should not be the main method; fall back to PE or SoTP and say so on Conclusion**

#### 6.5 Sensitivity matrix (required)
**N1 (high-growth years) × m_mature (mature EBIT margin)** two-way table of per-share value. Fix WACC and g_term and state them in the header.

### Step 7: ⭐ Reverse DCF + peer cross-check

#### 7.1 What the current price implies
Fix WACC and g_term; set model per-share value = current price; solve for the required **(N1, m_mature)** combinations:

| If mature EBIT margin is | Then high growth must last |
|---|---|
| m_mature − 5pp | N years |
| m_mature (management target) | N years |
| m_mature + 5pp | N years |

Then answer two questions (the most persuasive part of the workbook - it needs no forecast, only a judgment of whether the conditions are reasonable):
1. **Market-implied conditions vs management's own long-term model - which is more aggressive?**
2. **Are the conditions achievable industrially?** (capacity plans, contract terms, competition, product life cycles)

#### 7.2 1–2-year forward PE against peers
Choose **3–6 peers** (same segment / business model / growth band):

| Company | NTM P/E | FY+1 P/E | FY+1 EPS growth | Gross or net margin (quality) | Implied PEG |
|---|---|---|---|---|---|

The point is **not "lowest PE is cheapest"** but **fit**: can **growth** and **earnings quality** explain this company's premium / discount? If not, where does the gap come from (higher visibility? different cycle position? governance / geopolitical discount?)

### Step 8: ⭐ Write Conclusion (written last, placed first)

See "Conclusion fixed structure".

### Step 9: Output the xlsx (⭐ fixed template) + read-out in chat

---

## ⭐ Fixed output template (identical across companies)

**Hard rule. Companies may differ only in the number of rows and the text; sheet names, order, block structure, colours, number formats and column widths are identical.** All of these are defined in `scripts/val_style.py`.

### 10 sheets, fixed order and names

| # | Sheet (English, fixed) | Content |
|---|---|---|
| 1 | `Conclusion` | ⭐ method verdict + growth-path sources + key guidance and assumptions + gaps to consensus + three methods side by side + tracking list |
| 2 | `Assumptions` | market data + three-column assumptions (item / value / **basis and derivation**) |
| 3 | `Revenue & Margin Build` | quarterly revenue / GM / opex / operating income / conversion / net income / EPS chain |
| 4 | `Non-GAAP EPS Build` | quarterly actuals + annual totals (FY-1 / FY cur / NTM / FY+1) |
| 5 | `GAAP EPS Build` | the same, GAAP |
| 6 | `Consensus Check` | consensus implied quarterly path + side by side with the model + attribution |
| 7 | `PE & PEG` | EPS / PE / G / PEG / other multiples |
| 8 | `FCFF Valuation` | WACC + three stages × three scenarios + annual FCFF + summary + terminal share + sensitivity |
| 9 | `Reverse DCF & Comps` | implied (N1, margin) combinations + peer PE cross-check |
| 10 | `Methodology` | sources, modelling method, WACC and terminal assumptions, limits and risks |

> **SoTP variant**: if Step 0 decides on SoTP, sheet 8 becomes `SoTP Valuation` (per segment: revenue / profit / chosen multiple / basis / segment EV) and sheet 9 `SoTP Cross-Check & Comps` (sum, net cash and minorities, the segment multiples implied by the price, per-segment peers). The other 8 are unchanged. `val_style.new_workbook(sotp=True)` creates this set.

### Fixed colours (do not change)

| Use | Colour | Note |
|---|---|---|
| TITLE | text `1F4E79`, Arial 13 bold | row 1 of every sheet |
| SUB | text `595959`, Arial 9 italic | row 2 of every sheet |
| FILL_D header | fill `1F4E79` + white bold | Conclusion / Assumptions / Consensus / PE&PEG / Revenue Build |
| FILL_NG header | fill `305496` + white bold | non-GAAP headers |
| FILL_G header | fill `8064A2` + white bold | GAAP headers |
| **FILL_FC header** | fill `1F6F4A` + white bold | sheets 8 / 9 (green, to separate them from the earnings-basis sheets) |
| FILL_SEC section | fill `D9E1F2` + text `1F4E79` bold | title row of each ①②③ block |
| FILL_KEY highlight | fill `FFF2CC` | NTM P/E, FY+1 P/E, main PEG, per-share value, Base column |
| **FILL_VERDICT** | fill `FCE4D6` + text `C00000` bold | the method-verdict row on Conclusion |
| FILL_IN input | fill `FFFF00` + blue text | price, WACC and other inputs the user should override |
| hard-coded data | text `0000FF` (blue) | finance convention: blue = typed |
| formulas | text `000000` (black) | black = computed |
| WARN | text `C00000` bold | ⚠️ risk and distortion notes |
| borders | thin `BFBFBF` | everywhere |

Fonts: **Arial 10** (title 13, subtitle 9).

### Fixed number formats

```
$M        : '#,##0.0;(#,##0.0);-'
percent   : '0.0%;[Red](0.0%);-'
EPS       : '$0.00;($0.00);-'
P/E       : '0.0"x";(0.0"x");-'
PEG       : '0.00;(0.00);-'
bps       : '#,##0"bps";(#,##0"bps");-'
years     : '0.0"yr";(0.0"yr");-'     (Chinese workbook: '0.0"年";(0.0"年");-')
shares    : '#,##0;(#,##0);-'
price     : '#,##0.00'
```

### Fixed page structure

Every sheet: row 1 title; row 2 subtitle; row 3 blank; row 4 header; data from row 5; **freeze panes `B5`**; column A width **34**; data columns **15**; basis/notes columns **66–105**; blocks numbered `① ② ③` with a FILL_SEC title row; a `Notes` block (Chinese: `备注`) at the bottom.

⚠️ **Text cells must not start with `=`** (Excel parses them as formulas → `#N/A`). Use a full-width `＝` if text must start with an equals sign; `val_style.put()` does this automatically.

---

## ⭐ Conclusion fixed structure

`Conclusion` is the front page; a user who reads only this page gets every key point. **Six blocks, fixed order:**

### ① Method verdict (FILL_VERDICT, first content row, one sentence)

> **Method conclusion**: this company is currently best valued with **{method}**, because {reason}; {excluded method} does not fit because {reason}.

Followed by a three-row table that leaves the reasoning on record:

| Method | Fit | One-line reason |
|---|---|---|
| PE / PEG | high / medium / low | |
| FCFF | high / medium / low | include terminal share of EV |
| SoTP | high / medium / low | |

### ② What the growth path rests on: guidance vs assumption (⭐ the key block)

Label the source of each forecast period (quarter or year) and **give the guidance coverage ratio**:

| Period | Revenue | Source | Basis |
|---|---|---|---|
| 2026Q3 | $520M | 🟢 **guidance-locked** | formal guidance midpoint |
| 2026Q4 | $570M | 🟡 **back-solved from a management target** | from the "$1B run rate for product X" target |
| 2027Q1–Q4 | … | 🟡 **back-solved** / 🔴 **own assumption** | … |

**Guidance coverage ratio** = forecast revenue directly locked by formal guidance ÷ total forecast revenue.
Comment on it in one sentence, e.g. "Only 10.8% of forecast revenue is locked by guidance; 89.2% comes from back-solved management targets and own assumptions - **the model's reliability depends mainly on management delivering its long-term targets, not on near-term guidance accuracy**."

Three tiers:
- 🟢 **guidance-locked**: a formal quarterly / annual guidance number
- 🟡 **back-solved from a management target**: from public run-rate targets, quarterly milestones, capacity multiples, contract values (**evidence-based but not guided**)
- 🔴 **own assumption**: no direct management basis; from historical series, industry judgment or conservative choices

### ③ Key guidance

Every piece of company guidance used in the model: metric / value / period / quote - so readers see the anchors without opening Assumptions.

### ④ Key assumptions

Only the **5–8 most result-sensitive** (not all), each with: item / value / one-line basis / **sensitivity** (±X in the assumption moves EPS or per-share value ±Y%). The sensitivity column is required - it tells readers which assumptions to watch.

### ⑤ Gaps to consensus

- By year: revenue / gross profit / EPS - model vs consensus vs difference %
- **Attribution by variable**: points from revenue, from GM, from the rest
- **One sentence on the nature of the disagreement**: level of growth, shape of the ramp, or a different basis?
- Any deviation beyond ±10% gets an explicit ⚠️ and a reason

### ⑥ Three methods side by side + tracking list

| Method | Downside | Base | Upside | Basis note |
|---|---|---|---|---|
| P/E (FY+1, non-GAAP) | | | | |
| P/E (NTM, non-GAAP) | | | | |
| FCFF per-share value | | | | ⚠️ not a price target |
| Reverse DCF: implied by price | — | N years of high growth + M% mature margin | — | vs management target |

Last block: **the 3 variables most worth tracking** (one sentence each on why it could change the conclusion).

---

## Required Notes

**Conclusion**: disclaimer (no buy/sell advice; FCFF per-share value is not a price target); definition of the guidance coverage ratio.

**Assumptions**: data sources and price time; one-sentence modelling summary.

**Revenue & Margin Build**: ① basis of each layer; ② how conversion or gross profit was back-calibrated; ③ which variables drive the scenario differences.

**Consensus Check**: ① consensus source, number of analysts, update date, basis; ② back-out method; ③ attribution by variable.

**PE & PEG**: ① disclaimer; ② which cells are user inputs; ③ PEG alignment rule + statement that misaligned pairs are not output (incl. "EPS-based P/E is never divided by revenue growth"); ④ "forward PE" means different things by source (Bloomberg = next FY / Yahoo·Google = NTM / Xueqiu·Eastmoney = current FY / S&P CapIQ = FY+1); ⑤ if FCF is negative, P/FCF and EV/FCF are not usable; ⑥ **denominator sustainability** - which drivers make up this growth burst and which are one-off (margin recovery from a cycle low is one-off).

**FCFF Valuation**: ① source and date of every WACC input; ② the three-stage structure and the scenario variables; ③ **terminal share of EV** + the matching credibility note; ④ basis of the D&A / CapEx / ΔNWC paths; ⑤ ⚠️ EBIT on GAAP basis; ⑥ ⚠️ per-share value is not a price target.

**Reverse DCF & Comps**: ① how the reverse was solved; ② market-implied vs management model conclusion; ③ peer selection criteria and what is not comparable; ④ ⚠️ if the premium/discount is not explained by growth and quality, where it may come from.

**Methodology**: sources / full quarterly assumptions / GAAP delta assumptions / WACC and terminal assumptions / method choice / limits and risks.

---

## Output path

`{RESEARCH_ROOT}/{TICKER}/{TICKER}_Valuation_Dashboard.xlsx` when a local research folder is available; otherwise the session's outputs folder (e.g. `/mnt/user-data/outputs/`), or `./` in a terminal session.

---

## Delivery

1. Run `python scripts/check_valuation_xlsx.py {file}` - recalculates with LibreOffice and checks errors + template. If LibreOffice is unavailable, **independently recompute every derived value in Python** and say in chat that it was cross-verified.
2. Hand over the xlsx (present the file / give its path).
3. A 4–7 sentence read-out in chat that **must** include:
   - ⭐ **the method verdict** (PE / FCFF / both / SoTP, and why)
   - **what the growth path rests on**: the guidance coverage ratio, and what carries the rest
   - **core assumptions**: quarterly revenue QoQ and its basis; GM path and endpoint
   - **multiples at the current price**: FY cur / NTM / FY+1
   - **FCFF result shape**: per-share range across scenarios + terminal share + **what the price implies** (years of high growth, mature margin), and whether that is reasonable
   - **model vs consensus**: size of the gap, which variable, nature of the disagreement
   - **which PEG version to use**, its value and why
   - **disclaimer**: "No buy/sell advice and no price target; the FCFF per-share value is a model output under scenario assumptions, not a target price. Whether it is expensive is your call."

---

## More on PE periods

"Forward PE" means different things by source - **check which before using a web PE**:

| Source | Default "forward PE" |
|---|---|
| Bloomberg | best next fiscal year |
| Yahoo Finance | NTM (rolling 12 months) |
| Google Finance | NTM |
| Xueqiu / Eastmoney | current-FY consensus |
| S&P Capital IQ | FY current+1 by default |

**So**: for a rigorous PEG, first check which fiscal year the P/E denominator is, then match same-year EPS growth.

---

## Reading guide (rules of thumb, not hard rules)

**NTM PE (tech hardware)**: <15x low / 15–25x reasonable / 25–40x premium / >40x high (needs very strong multi-year visibility).

**PEG (Lynch)**: <0.7 clearly low (rare) / 0.7–1.2 reasonable / 1.2–1.5 rich but explainable / >2 clearly high.

**FCFF terminal share**: <60% normal / 60–75% flag / >75% ⚠️ / >85% 🔻 switch method.

**Reading the reverse DCF**: if the price implies **more aggressive** conditions than management's own long-term targets, the market has priced in over-delivery; if **less**, the market discounts the targets. Neither is a buy/sell call, but it defines "what you need to believe to accept the price".

**Where multiple percentiles do not apply - say so explicitly:**
- cyclicals at the bottom: depressed EPS inflates PE → use EV/Sales or EV/EBITDA
- loss-makers: negative EPS, PE not applicable
- acquisition periods: one-off GAAP charges depress EPS
- **high-growth names: PEG looks very low; check what makes up the growth and how long it lasts** - the most common misreading
- **margin-recovery growth**: part of EPS growth is margin recovering from a cycle low - one-off, not repeatable; a one-year YoY PEG denominator systematically understates PEG

---

## Hand-offs with other skills

1. `company-research` → qualitative picture + initial coverage note
2. `quarterly-financials-dashboard` → N quarters of non-GAAP + GAAP + cash-flow history
3. `earnings-call-reader` → guidance and events per call (**the main evidence for this model**)
4. `earnings-digest` → condensed logic and narrative
5. **`company-valuation` (this skill)** → ties it all together into a model, multiples, cash flows and implied conditions
6. `valuation-brief` → condenses this workbook into a short note
7. `investment-view` → carries the brief into the company's dated estimates (`# ---测算---`)

Reuse what is already in the company folder before pulling from the web.

---

## Version history

- **V1**: PE + PEG, two bases, two periods, 5 sheets.
- **V2**: bottom-up quarterly EPS made mandatory; consensus demoted to a cross-check with its implied quarterly path backed out; three-column Assumptions; fixed cross-company template (7 sheets, colours, formats); added `Revenue & Margin Build` and `Consensus Check`.
- **V3**: `Conclusion` sheet first (method verdict, guidance-vs-assumption source tiers and coverage ratio, key guidance and assumptions with sensitivity, attribution of gaps to consensus, three methods side by side, tracking list); multi-stage FCFF (`FCFF Valuation`, `Reverse DCF & Comps`); method selection framework with SoTP variant; FCFF on GAAP EBIT; EPS-based P/E never divided by revenue growth.
- **V3.1 (current)**: template moved into `scripts/val_style.py`; `scripts/check_valuation_xlsx.py` checks recalculation, formula errors and the template before delivery; output language follows the request.
