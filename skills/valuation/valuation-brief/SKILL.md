---
name: valuation-brief
description: "Condenses the {TICKER}_Valuation_Dashboard.xlsx produced by company-valuation into a three-part 'Guidance / Assumptions / Conclusion' valuation note ({TICKER}_Valuation_Brief.md, or {TICKER}_估值速读.md in Chinese). Use when the user says 'valuation brief', 'valuation summary', 'condense the valuation', 'write it as guidance / assumptions / conclusion', 'turn the valuation into a note', '估值速读', '估值总结', or wants a short conclusion right after a valuation. The conclusion always has four items: revenue-path source and how conservative it is; margin path (with a judgment on when the long-term target is reached); FY cur and FY+1 PE with EPS growth listed separately -> PEG -> FCFF reverse DCF (when applicable); difference versus consensus."
---

# Valuation Brief

Condenses a finished valuation (usually the company-valuation workbook `{TICKER}_Valuation_Dashboard.xlsx`) into the user's own note format: **Guidance / Assumptions / Conclusion** - short, accurate, with every basis clear.

## Conventions (fixed)

- **Language**: the request language; when overwriting an existing brief, keep its language. Section names and the title line are fixed strings: English `Guidance` / `Assumptions` / `Conclusion`, Chinese `指引` / `假设` / `结论`.
- **File name**: `{TICKER}_Valuation_Brief.md` (English) or `{TICKER}_估值速读.md` (Chinese); if either exists, update that one.
- **Self-check**: `python scripts/check_brief.py BRIEF.md` (title, section order, the four conclusion items and their order, advice wording). Fix every FAIL.

## Input

In priority order (`{RESEARCH_ROOT}/{TICKER}/`):

1. `{TICKER}_Valuation_Dashboard.xlsx`: Conclusion, Assumptions, Revenue & Margin Build, PE & PEG, FCFF Valuation, Reverse DCF & Comps, Consensus Check
2. `{TICKER}_Earnings.md`: check the guidance wording
3. `{TICKER}_Financials_*Dashboard.xlsx`: historical GM and opex series (for the judgments)
4. No valuation workbook → ask the user to run company-valuation first; never invent numbers

Read the xlsx with openpyxl `data_only=True`. If formula cells have no cached values, recalculate first (`python scripts/xlsx_check.py FILE` does it with LibreOffice), or recompute in Python with the same formulas.

## Output

- File: `{RESEARCH_ROOT}/{TICKER}/{TICKER}_Valuation_Brief.md` (or `_估值速读.md`); overwrite if it exists
- Also paste the full text in chat (in a code block) so the user can copy it
- Tab-indented outline, field for field like the template below

## Fixed template

```
{TICKER} Valuation Brief (price ${price}, {price date})

Guidance
	{next-quarter guidance: revenue range, GM range, opex range, EPS range}
	{management long-term targets / milestones: e.g. "first >$3B quarter by end-FY27", long-term GM / opex model}
Assumptions
	{FY cur remaining quarters' revenue path and source, e.g. +9.25% per quarter (back-solved from the >$3B target)}; {FY+1 revenue path and source}
	{GM path: step per quarter, when it reaches the long-term target}; {opex % path}
Conclusion
	① revenue-path source and how conservative it is
	② margin path (with a judgment)
	③ valuation: PE and growth by year → PEG → FCFF reverse DCF
	④ difference versus consensus
```

Chinese title line: `{TICKER} 估值速读（股价 ${价格}，{取价日期}）`, sections `指引` / `假设` / `结论`.

## The four conclusion items (hard rules)

### ① Revenue-path source and how conservative it is

- Say what FY cur revenue rests on: 🟢 guidance-locked / 🟡 back-solved from a management target / 🔴 own assumption, and give the **guidance coverage ratio** (Conclusion sheet, block ②).
- When judging "conservative / neutral / optimistic", **the reason must match the company's constraint type**:
  - **Supply-constrained** (capacity sets revenue, e.g. InP capacity doubling): argue with capacity-expansion progress, whether orders are fully booked and how far visibility reaches - **not only "industry demand is strong"**.
  - **Demand-driven**: then argue with industry demand, order growth, inventory cycle.
- If FY+1 is an own assumption, say separately that "visibility is lower".

### ② Margin path (a real judgment, not a label)

- Separate **full-year** from **exit-quarter** figures: e.g. "FY27 operating margin 20.4% → 24.0% (Q4 alone 25%)" - never present a single-quarter number as the full year.
- Split it into "GM improvement" and "opex leverage", each with its basis.
- Opex decline: separate "direction backed by a management quote" from "the slope I assumed".
- **Judge when the long-term target is reached**: if the company gave only a target (e.g. GM >42%) and no date, first write "no date given; the model assumes quarter X", then judge using all three:
  1. **Required slope vs historical slope**: the per-quarter step needed from the **latest actual** (not the guidance) to the target, versus the mean step of the last 4 actual quarters
  2. **Whether the drivers are on the way**: capacity / process upgrades (e.g. 6-inch wafer share), high-margin product ramps, pricing
  3. **Industry demand and supply-demand state**: a supply shortage supports pricing, which helps GM
  - Land on one of "reasonable / optimistic / conservative" and keep the key numbers
  - "Current" means the latest actual; guidance is labelled separately (e.g. "from FY26 Q4's 40.2% (Q1 guidance midpoint 40.5%)")

### ③ Valuation (fixed order)

1. **Two years separately**, one line each, P/E with EPS growth:
   - `FY{cur} PE {x}x, EPS growth {g}%` (if growth includes one-off parts - margin recovering from a cycle low, a low base - add ⚠️ in brackets)
   - `FY{cur+1} PE {x}x, EPS growth {g}%`
2. **Then PEG**: main version = Lynch multi-year CAGR (FY cur P/E ÷ 2–3-year EPS CAGR) with its value; if the one-year FY cur PEG is distorted by one-offs, one sentence on why it is not used; if peer data exist, one same-basis comparison (e.g. "in line with LITE's PEG").
3. **Then FCFF reverse DCF**:
   - Only when the workbook rates FCFF fit "medium" or "high"; if "low", write "FCFF not applicable: {one-line reason}"
   - Form: "the price requires growth of {g_high} for about {N} years after FY{x} (mature margin {m}%)", compared with the workbook's Base and management's long-term model - is the market-implied condition more or less aggressive?
- **Never write "cheap / expensive / worth buying".** If the user's draft has such a judgment, rewrite it as a condition: "near-term PE is not demanding; to accept the price you need to believe {condition}".

### ④ Difference versus consensus

- FY cur and FY+1 EPS difference in %
- One sentence on the source (revenue / margin / conversion and share count); ⚠️ if beyond ±10%

## When the user gives their own draft first

Keep the user's structure, wording and judgments; fix only these, and list in chat what changed and why:

1. Reasoning that doesn't match the constraint type (supply-constrained but argued only from demand)
2. A single quarter written as the full year or vice versa; guidance written as the "current" actual
3. A model assumption written as company guidance (especially the date a long-term target is reached) - but keep the user's judgment and add the supporting numbers
4. One-year growth that includes one-offs used directly for valuation
5. "Cheap / expensive" conclusions without the reverse-DCF condition
6. Empty sections (e.g. Assumptions) - fill from the workbook

## Example (COHR, 2026-10)

```
COHR Valuation Brief (price $312.62, 2026-10-09 close)

Guidance
	FY27 Q1: revenue $2.2–2.4B, GM 39.5–41.5%, opex $400–420M, EPS $1.85–2.05
	First >$3B quarter by end-FY27; long-term GM >42%, opex 18%
Assumptions
	FY27 Q2–Q4 revenue +9.25% per quarter (back-solved from the >$3B target); FY28 +8% per quarter (own assumption)
	GM +50bps per quarter, 42% in FY27 Q4; opex 17.8% → 17.0%
Conclusion
	FY27 revenue rests mainly on back-solved management targets (guidance coverage only 9%); the company is supply-constrained, capacity doubling finished a quarter early, FY27 is fully booked and orders reach into CY2028, so the target looks conservative. FY28 is an own assumption with lower visibility
	FY27 operating margin rises from 20.4% to 24.0% (Q4 alone 25%), driven by GM improvement and opex leverage. Management has stated the opex direction; 42% GM is a long-term target with no date, and the model assumes FY27 Q4: from FY26 Q4's 40.2% (Q1 guidance midpoint 40.5%) that needs about +45bps per quarter, below the FY26 four-quarter mean of +53bps; with the rising 6-inch InP share and 1.6T / OCS / CPO about to ramp, reaching it in FY27 is reasonable
	FY27 PE 32.8x, EPS growth 70% (⚠️ includes a one-off recovery of GM from the cycle low)
	FY28 PE 21.5x, EPS growth 53%
	PEG (FY26→FY28 two-year CAGR 61%) about 0.54, in line with LITE (same basis 0.68 vs 0.66); the FY27 one-year PEG of 0.47 is flattered by the one-off and not used
	FCFF reverse DCF: the price needs about 5 years of +25% growth after FY28 (mature GAAP EBIT margin 24%); at management's long-term model of ~21% it needs about 6 years; the workbook Base assumes only 3, so the market-implied condition is more optimistic than management's model
	Broadly in line with consensus (FY27 EPS +1.0%, FY28 +3.7%); the difference is in the size of margin expansion, not growth
```

## Principles

- Use only numbers from the valuation workbook, the call log and the financial dashboard; no new forecasts
- **Price = the latest price on the day the skill is called.** If the workbook's price is older, or its price cell and its notes disagree, fetch the latest price, recompute the multiples from the workbook's EPS, and put that date in the title line
- Every number's basis is clear (full year / single quarter, actual / guidance, non-GAAP / GAAP, fiscal year-end)
- No buy/sell advice, no target price; the FCFF per-share value is not a target price

## Next step

investment-view copies this brief, at full resolution and with its date, to the top of the `# ---测算---` (Estimates) section of the company view.
