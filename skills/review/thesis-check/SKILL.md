---
name: thesis-check
description: "Checks the user's own investment thesis / one-line outline for a company against existing research (earnings-call logs, filings, initial coverage, valuation workbook) and public web sources, flags the problems, and returns a corrected version plus an English version. Use when the user shares their thesis outline (text or screenshot) and asks to check it, fact-check it, tighten it, or translate it - e.g. 'check my thesis on XX', 'is this outline right', '校对一下我的投资逻辑', '帮我检查大纲并出英文版'."
---

# Thesis Check (outline fact-check + English version)

The user gives their own investment outline for a company (usually: one-line summary + layered points such as logic / scarcity / expansion / risks; text or a screenshot). This skill does two things:

1. **Check**: test each point against evidence; find factual errors, overstated scope, unclear attribution and stale data; propose the smallest fix.
2. **English version**: an idiomatic investment-memo English version that keeps the user's structure.

## Principles

- **The outline is the user's, not yours.** Keep their structure, wording style and choices. Don't add back anything they said they don't need (e.g. "no need to add demand drivers"). Change only what is wrong; don't rewrite.
- **Only real problems.** Every problem has evidence; a correct point is marked "✅ accurate" - don't nitpick to look thorough.
- **No buy/sell advice**, no cheap/expensive.

## Output format (fixed - four blocks, this order)

Headings are fixed strings in the reply language:

| English | Chinese |
|---|---|
| `① Issues` | `① 问题清单` |
| `② Corrected outline` | `② 修正后的中文大纲` |
| `③ English version` | `③ English version` |
| `④ Sources` | `④ Sources` |

Block ② is in the outline's own language (if the user wrote in English, ② is the corrected English outline and ③ is omitted unless they ask for a Chinese version).

## Step 1: Gather evidence (local research AND web verification - both)

### 1a. Local material first

Read what this conversation already analysed and the company's files in the research folder (`{RESEARCH_ROOT}/{TICKER}/`):

- `{TICKER}_Earnings.md` (quarterly call log - the main source of management quotes)
- `{TICKER}_Digest.md` / `{TICKER}_速读.md`, `*_Initial_Coverage.md` / `*_首次研究.md` (qualitative background, competition)
- `{TICKER}_Financials_*Dashboard.xlsx` (revenue mix, margins, orders / backlog)
- `{TICKER}_Valuation_Dashboard.xlsx` (assumptions, consensus)
- `{TICKER}_投资判断.md` / `{TICKER}_Investment_View.md` (investment-view: the current Core and the latest quarter verdict; an outline that contradicts them is worth flagging)
- the raw transcripts (`.txt`) - management's words come from the transcript; notes are only an index

### 1b. Then verify and extend with the web (a standard step, not a fallback)

Local notes are second-hand and may misattribute sources, be stale, or carry only management's side. These kinds of claims **must** be checked with WebSearch / WebFetch:

1. **Rank and share claims** ("No. 1", "highest", "leading", "X% share", "de facto standard"): find third-party research firms' public releases or media reports - Dell'Oro, Cignal AI, LightCounting, Omdia, Yole, TrendForce, IDC. State **firm + period + basis** (global / regional, sub-segment, revenue / units).
2. **Competitor claims** ("the only", "only X", "first to market", "ahead of rivals"): check the competitors' own calls, releases and launches for their latest progress.
3. **Latest developments**: anything since the latest local call - investor days, 8-Ks, releases, new orders, acquisitions, guidance changes.
4. **Second-hand data in local notes**: check the original source is right and whether a newer period exists.

Web rules:

- **Prefer original sources** (company releases, SEC filings, research firms' own releases, call transcripts), then credible media; aggregators and forums are leads, not evidence.
- **Company disclosures beat third-party aggregates**: if they conflict, use the company's and note the conflict in the basis column.
- **Not found → say so**: write "could not be verified in public sources" and suggest a verifiable wording or a source label - don't silently keep it or fill a number from memory.
- Use only WebSearch / WebFetch for pages; if a site can't be fetched, use another public source - don't work around it with curl etc.
- Search with purpose: only the claims in the outline that need checking, not general industry research.

## Step 2: Break the outline into checkable claims

Split each point into single claims and tag each one:

| Type | Meaning | Requirement |
|---|---|---|
| Fact | disclosed numbers, orders, product parameters | must be found in disclosures; every number exact |
| Third-party data | research-firm share, rank, market size | firm and period stated |
| Management view | CEO/CFO judgment or expectation | written "management believes …", never as objective fact |
| User judgment | the user's own investment conclusion | check support; don't force changes |
| Inference | a conclusion drawn from facts | check the reasoning holds |

## Step 3: Check each claim (key checks)

1. **Overstated scope**: "covers all AI test" when the company does one test step; "scarce" when true only in a niche. Narrow it to what the evidence supports.
2. **Attribution**: a management statement ("the fastest-growing segment") written as fact → "management believes".
3. **Competitor claims limited to a sub-segment**: "only X competes" must say where X competes and where there is no comparable rival; customers' in-house / captive suppliers count as competition. Check against the rival's latest disclosures.
4. **Progress written ahead of reality**: a business still sampling / in development / negotiating written as expanded → add the stage, e.g. "memory (in development, no orders yet)".
5. **Numbers and sources**: parameters, amounts, shares match disclosures; source given and correct; different bases of the same number explained.
6. **Ranks and shares**: every "No. 1" / "highest" has a verifiable source (company or third party) with firm, period, sub-segment and region; flag those with no public source.
7. **Timeliness**: the latest period? Point out newer data (incl. recent news and third-party reports).
8. **Ambiguity**: sentences a reader could misread (e.g. the competitor line reading as "only one company does this").

## Step 4: Output

### ① Issues (only the points with problems)

| Original | Problem | Basis | Suggested fix |
|---|---|---|---|

Basis is specific: the call quote (English original; Chinese translation too in a Chinese reply), the disclosed number, the file name; web sources with firm / outlet and date. After the table, one sentence: "All other points are accurate."

### ② Corrected outline

Keep the user's hierarchy (one line → first-level points → second-level points); replace only the sentences with problems. Third-party data get firm and period in brackets.

### ③ English version

- mirrors the corrected outline's hierarchy one-to-one - nothing added or dropped
- investment-memo style: concise, active voice, few adjectives
- management views as "Management views / believes …"
- product names, models, tickers, numbers and quotes unchanged; keep source brackets (e.g. "(Dell'Oro, 2025)", "(Semiconductor Today)")
- colloquial Chinese turned into professional English (「卡位」→ "entrenched position", 「越往后测越贵」→ "the later a defect is caught, the more it costs")

### ④ Sources

Local file names used + web sources as markdown links.

## Example 1 (AEHR, 2026-10)

User outline:
- Entrenched in wafer-level burn-in test, a scarce company, expanding horizontally across AI
  - Logic: currently the fastest-growing segment in all of semiconductor test, especially wafer-level burn-in…
  - Scarcity: strong technology (WaferPak manages each die's temperature; FOX-XP 3,500W per test position, 9 wafers in parallel); basically only NEXUSTEST (Linkstar) competes
  - Expansion: AI processors, silicon photonics, memory

Findings:
- "Fastest-growing segment" is the CEO's words - "I believe that burn-in is by far the fastest-growing segment in all of semiconductor test" → make it a management view
- "Only NEXUSTEST" → limit it: NEXUSTEST (Linkstar's overseas subsidiary) competes only in SiC / power WLBI; no volume-production rival seen in AI processors and silicon photonics; the 10-K also cites customers' in-house / affiliated suppliers
- "Memory" → no orders yet; management says FY27 orders possible, FY28 volume - mark "in development"
- the rest (WaferPak, 3,500W, 9 in parallel) accurate

English one-liner: "A scarce, entrenched player in wafer-level burn-in, expanding horizontally across AI."

## Example 2 (CIEN, 2026-10) - web verification changes the conclusion

- "Highest share in North America": the local note says "~50% in North America (industry research)" with no firm named, and no public source has that number; Dell'Oro's 2025 annual report shows Ciena No. 2 globally in optical transport (Huawei No. 1) and **No. 1 globally in DCI**, with DCI revenue highly concentrated in North America → suggest "No. 1 globally in DCI (Dell'Oro, 2025)" - verifiable and closer to the outline's theme
- "Top three in 800G ZR": the local note credits Cignal AI; web check shows the original source is Dell'Oro (2025Q3, ZR/ZR+ overall) → correct the source and state the period
- "First to market again": checked the rival's progress with Nokia's 2026Q2 call - "secured our first multi-rail ILA design win with a major customer" → keep the "first order" fact and note that the rival has followed
