---
name: company-comparison
description: "Compares two (or more) already-researched companies in the same field: business strategy, key technology routes, valuation and financials, other key points. Use when the user says 'compare A and B', 'A vs B', 'compare these few', '对比 A 和 B', '这几家比一下'."
---

# Company Comparison (same field)

Lines up the user's existing single-company research (call logs, digests, valuation workbooks, meeting notes) side by side. **No new research** - only integration of existing material; where material is missing write "not covered in the notes / to verify" and never fill numbers from memory.

## Conventions (fixed)

- **Language**: the request language. The four section headings are fixed: `1. Business and strategy` / `2. Key technology differences` / `3. Valuation and financials` / `4. Other important points` (Chinese: `1. 业务方向和战略` / `2. 关键技术差异` / `3. 估值和财务` / `4. 其他重要的`). The one-line positioning block is always in English.
- **Material location**: `{RESEARCH_ROOT}/{TICKER}/` per company (on a linked computer, read it through the device tools). If the same files also exist in a project, the local copy is usually newer (e.g. a valuation brief may exist only locally) - prefer the newest by modification time.

## 1. Gather material (first, before writing)

1. List each company folder sorted by modification time; prefer the newest:
   - `{TICKER}_Valuation_Brief.md` / `{TICKER}_估值速读.md`: guidance / assumptions / conclusion, PE, PEG, FCFF reverse, gap to consensus
   - `{TICKER}_Digest.md` / `{TICKER}_速读.md`: moat logic + latest-quarter points
   - `{TICKER}_Earnings.md`: first grep `^#` for the structure; read TL;DR, Guidance, Product Summary Table - not the whole file
   - meeting notes (e.g. `0827 meeting notes.txt`), exhibition / launch transcripts (e.g. `ECOC2026.txt`): grep for technology keywords (CPO / NPO / OCS / ELS / VCSEL / 6-inch / 400G …)
   - `{TICKER}_Valuation_Dashboard.xlsx`: read `Conclusion`, `Assumptions` (market cap, shares, cash, debt), `Reverse DCF & Comps`
2. If an xlsx read with `data_only=True` returns blanks (formulas not cached), recalculate it with LibreOffice first (`python scripts/xlsx_check.py FILE`) and read again.
3. If the user says "based on conversations X and Y", search past chats first; if not found, use the files above and say so at the top.
4. Note each valuation workbook's price date; flag different dates.

## 2. Output structure (in chat, Markdown tables)

Opening line: data sources and price dates; mention any upcoming earnings date.

### One-line positioning (English)

One English bullet per company: **bold ticker + colon + positioning**. Capture the business-model essence (e.g. LITE: "The ultimate upstream of optical communications"; COHR: vertically integrated from substrate to full optical solutions). The user may reword it - their version wins.

### 1. Business and strategy

Rows: revenue scale and growth, latest quarter, business mix (segment shares), core strategy, key customers / strategic investors, order visibility, the new direction management values most. After the table, one paragraph on **the biggest strategic difference** and what it means for the other company.

### 2. Key technology differences

One row per technology area (field-specific; optical default: EML / InP capacity and wafer size / CPO / NPO / OCS / optical modules / scale-across · DCI / chip-to-chip interconnect), columns: A's approach and stage, B's approach and stage, who leads / where they differ. After the table, one paragraph: which company is more route-neutral and which is more concentrated.
- Implementation details not in the notes (e.g. OCS on MEMS or liquid crystal) are not written from memory - mark "unverified" or leave out.

### 3. Valuation and financials

One table on the same basis: price / market cap (basic and diluted shares), net cash / net debt, non-GAAP gross margin, operating margin, FCF, quarterly CapEx, FY current / next PE, EPS growth, PEG (two-year CAGR basis + a common S&P three-year growth basis), FCFF Base per share (marked "not a price target") and its premium / discount to the price, what the price implies (reverse DCF), model vs consensus.

After the table, 2–3 judgments; these are always computed:
- **Absolute operating profit**: from next-quarter guidance midpoints (revenue × operating margin), compared with market caps - what is the market paying more / less for (growth slope, margin quality)?
- **Is the premium the same on a common basis**: FCFF Base vs price, years of high growth implied, common-basis PEG. If they are almost the same, the cheaper company is "slower growth", not "mispriced".
- **Each model's risk**: does the disagreement come from the revenue slope or the margin; guidance coverage, share of back-solved targets.

### 4. Other important points

Pick from this list only what actually differs - don't pad: pricing mechanism (LTA locked prices vs spot upside), capital intensity and balance sheet (CapEx, FCF, inventory days, leverage), geopolitics / FCC / US capacity, customer transparency and concentration, one-off GAAP items and dilution, share-price position (52-week move), **what to watch at the next earnings** (2–3 checks per company).

Closing line: offer to save the comparison as `{RESEARCH_ROOT}/{A}_vs_{B}_Comparison.md` (Chinese: `{A}_vs_{B}_对比.md`) and update it after earnings.

## 3. Rules

- All tables in Markdown.
- No buy/sell advice, no price targets; an FCFF per-share value is always marked "not a price target".
- Numbers come from the material; flag inconsistent bases (different fiscal years, different price dates, GAAP vs non-GAAP).
- More than two companies: add columns; one positioning bullet each.
- Positioning such as "ultimate upstream" must be accurate: if something is strictly further upstream (e.g. substrates), add one sentence at the end suggesting the more precise wording.
