---
name: company-research
description: "Structured first-time research (initial coverage) on a listed company, centred on one segment the user names (optical, AI servers, solid-state batteries, CRO, power semis ...). Use when the user says 'research XX', 'dig into XX's YY business', 'initial coverage of XX', '研究一下 XX', '首次覆盖', or gives a company plus a segment (e.g. 'LITE EML', 'Coherent silicon photonics'), even without the word 'research'. Four steps: financial snapshot and revenue mix; a 10-quarter dashboard xlsx; forward-looking signals (margins, inventory, contract liabilities); a deep dive drilled down to product level (optical splits into EML / CW / DFB / VCSEL / SiPh / modules, each analysed separately). Built-in QA mode: after the note exists, 'QA', 'QA mode' or '追问模式' switches to answering follow-ups in chat without editing the note until 'exit' / '退出' - those triggers also use this skill."
---

# Company Research (initial coverage)

Turns "I want a first look at company X in segment Y" into a structured, focused, trustworthy research note.

## Conventions (fixed)

- **Language**: the note is written in the request language. Fixed file names: English `{TICKER}_{Segment}_Initial_Coverage.md`, Chinese `{公司简称}_{重点业务}_首次研究.md`. The dashboard is always `{TICKER}_Financials_10Q_Dashboard.xlsx` (see Step 1.5).
- **Folder**: `{RESEARCH_ROOT}/{TICKER}/` when a local research folder exists; otherwise the session outputs folder.
- **Step headings are fixed strings** (so later skills and later reads find them): `## Step 1: Financial Snapshot`, `## Step 1.5: 10-Quarter Dashboard`, `## Step 2: Forward-Looking Financial Signals`, `## Step 3: Deep Dive — {segment}`, `## Open Questions / Information Gaps` (Chinese: `## Step 1：基本财务画像`, `## Step 1.5：近 10 季报表`, `## Step 2：深度财务信号`, `## Step 3：{重点业务}深度剖析`, `## 信息缺口与未解决问题`).

## Core principles

1. **Focus on the target segment.** The user names one direction each time. Other businesses get one line; **don't** spread effort evenly.
2. **Drill down to product level - critical.** User keywords are usually **segment-level** ("optical", "AI servers", "power semis"), while companies disclose at **product level** in annual reports, calls and IR material (optical: **EML / CW laser / DFB / VCSEL / SiPh / optical modules / components**; AI servers: **GPU modules / HBM / NVLink switches / cold plates**; power semis: **SiC MOSFET / GaN HEMT / IGBT modules**). **Always drill from segment to product** and run Step 3's three questions for each product. If unsure how to split, do one web search on how the company itself splits it in its latest annual report or call, and **follow the company's own breakdown**.
3. **Cite everything.** Every specific number and every customer name carries an inline citation to its source - the search tool's citation where one is provided, otherwise `[Source: document, period / URL]` right after the claim. If something can't be found, say so; never make it up.
4. **Mark speculation explicitly.** Customer information inferred from public information (supply-chain relationships, tenders, capacity matching) must be written "⚠️ Speculation: …" (Chinese: "⚠️ 推测：…").
5. **Source priority**:
   - **A-share / HK**: company announcements (CNINFO, HKEXnews) > annual / quarterly reports > call transcripts / results briefings > Xueqiu / Eastmoney > sell-side summaries
   - **US**: SEC 10-K / 10-Q / 8-K > call transcripts (Seeking Alpha, Motley Fool, Yahoo Finance) > company IR > financial media (Bloomberg / Reuters / CNBC)
   - Avoid single sources; cross-check key numbers in at least two places.

## Workflow

### Step 0: Scope the target

Confirm two things; if the request **already says them**, go straight to Step 1 - **don't** ask:

- **Company**: ticker / full name / exchange
- **Target segment**: the business direction to study

If only a company is given, ask briefly: "Which part of XX's business should I focus on?"

If the direction is obvious (e.g. "Innolight 800G" → optical modules), **don't** ask - take it.

**Then do one web search on how this company actually splits the segment into products** - e.g. `{company} annual report revenue breakdown {segment}` or `{TICKER} product breakdown {segment}`. This sets the granularity of Step 1 and the product list of Step 3; **don't** skip it. If the company splits the segment into EML / CW / DFB-level products, Step 3 must cover each.

---

### Step 1: Financial Snapshot & Revenue Breakdown

**Goal**: in 30 seconds the user knows "what it does, how it makes money, how big it is".

**Must include**:

1. **One-line positioning**: main business and position in the value chain.
2. **Latest revenue and earnings**: revenue, net income attributable to shareholders, YoY. Prefer the **latest quarter**, then the **latest annual report**. State the period ("2025Q3 single quarter" or "FY2024").
3. **Revenue breakdown - key**: by business / product / region, absolute values and % of total.
   - **If the company splits finely, follow it** - don't merge. E.g. if it discloses "800G / 400G / 200G and below / other", list all four.
   - **If the target segment can be split further into products (EML / CW / DFB in optical), split it** - the basis for Step 3.
   - If only a coarse split exists ("communications / data center"), use it and say "not further disclosed".
   - **Call out the target segment's share of revenue.**
4. **Margin mix**: which business has the highest / lowest margin (if disclosed), any clear drag.

**Step 1 format**:

```markdown
## Step 1: Financial Snapshot

**Positioning**: [one line]

**Latest results** (2025Qx / FY2024):
- Revenue: xxx, YoY +/-x%
- Net income: xxx, YoY +/-x%
- Gross margin: xx%

**Revenue mix** (by [business / product / region]):
| Segment | Revenue | Share | YoY |
|---|---|---|---|
| **[Target segment]** ⭐ | xxx | xx% | +x% |
| └ Product A (e.g. EML) | xxx | xx% | +x% |
| └ Product B (e.g. CW) | xxx | xx% | +x% |
| Business B | xxx | xx% | +x% |

**Margin highlights**: [1-2 sentences]
```

> No market cap, PE, PB, price target or price action - this skill does no valuation and no timing.

---

### Step 1.5 (required): 10-Quarter Dashboard - **a mandatory deliverable**

**Goal**: next to the text, a **hard-number table of the rhythm**. Step 1 is one period; Step 1.5 is ten - they complement each other.

**Required**: every initial coverage **must** come with an xlsx `{TICKER}_Financials_10Q_Dashboard.xlsx` in the same folder as the note. It can't be skipped or replaced by a markdown table.

**How**:

- **Preferred: run the `quarterly-financials-dashboard` skill** (if available) - it does exactly this, with its builder script and checker, and adds GAAP, balance-sheet order proxies and cash flow.
- **Fallback** (that skill unavailable): build an xlsx with the xlsx skill holding at least these 11 columns per quarter:

| # | Field | Note |
|---|---|---|
| 1 | Quarter | fiscal label (e.g. FY26 Q1) |
| 2 | Period End | YYYY-MM-DD |
| 3 | Revenue ($M / RMB 100M) | same unit as the company's reports |
| 4 | Revenue YoY | % |
| 5 | Revenue QoQ | % |
| 6 | Adj Gross Margin | non-GAAP |
| 7 | Adj Net Income | non-GAAP |
| 8 | Adj NI YoY | |
| 9 | Adj NI QoQ | |
| 10 | Adj Net Margin | = Adj NI / Revenue (Excel formula) |
| 11 | Adj EPS ($) | required for US; A-share: EPS RMB/share |

> If the company only reports GAAP (common for A-shares), use GAAP and label the headers "GAAP" - **always state the basis**; never mix GAAP and non-GAAP.

**Discipline (both paths)**:

1. **YoY / QoQ are Excel formulas**, not values computed in Python - so changing one number updates the table.
2. **If YoY needs prior-year quarters outside the 10 shown, add helper rows** - don't leave YoY blank.
3. **Highlight the latest quarter** (light yellow `FFF2CC`).
4. **Cite every number** (notes or cell comments): the company's 8-K / quarterly / annual report, not news media.
5. **Explain every derived number** - e.g. a Q4 Adj NI derived as "full-year EPS − first three quarters".
6. **Frozen header + sensible widths**, readable on opening.
7. Run the checker (`check_financials_xlsx.py` from quarterly-financials-dashboard, or at least a LibreOffice recalculation) before delivery.

**In the md**, between Step 1 and Step 2, a short pointer only - **don't copy the table into the md**:

```markdown
## Step 1.5: 10-Quarter Dashboard

See `{TICKER}_Financials_10Q_Dashboard.xlsx` (same folder): last 10 fiscal quarters of revenue / non-GAAP gross margin / non-GAAP net income / net margin / Adj EPS, with YoY / QoQ.

**Key observations (at most 3)**:
1. [e.g. revenue YoY accelerated from −0.5% in FY24 Q4 to +33.1% in FY26 Q1, five straight quarters of acceleration]
2. [e.g. Adj GM bottomed at 41.0% in FY25 Q2, back to 44.7% in FY26 Q1]
3. [e.g. Adj net margin jumped from 5.4% in FY25 Q2 to 13.8% in FY26 Q1, +8.4pp in three quarters]
```

Then Step 2.

---

### Step 2: Forward-Looking Financial Signals

**Goal**: find financial signals that **lead** future results. **Not** a dump of every financial number - pick the ones that reflect **segment momentum**.

> Step 2 vs Step 1.5: Step 1.5 is the **rhythm table** (YoY/QoQ trend); Step 2 is the **leading-indicator analysis** (inventory, contract liabilities, backlog) - "why is it changing and what does it mean".

**Must include**:

1. **Gross / net margin by quarter (last 4–6 quarters)**:
   - The xlsx has the numbers; here **explain the drivers** - product-mix upgrade? raw-material costs? operating leverage? ASP declines / price cuts?
   - Quote management's explanation from the call if there is one.
2. **Inventory**:
   - Latest amount, QoQ and YoY.
   - **Context check**: inventory growth vs revenue growth - inventory growing much faster than revenue usually means a build-up (ample orders, or slow sales); a sharp fall usually means supply constraints or order drawdown.
   - If raw materials / WIP / finished goods are split, focus on **raw materials and WIP** - they show forward build intent.
3. **Contract liabilities / advances from customers**:
   - Latest amount, QoQ and YoY.
   - **Important**: a sharp rise usually means a strong order book - a very hard leading indicator.
   - Especially for long-cycle B2B businesses.
4. **Other signals as relevant** (not all needed):
   - **Accounts receivable**: reasonable, or growing much faster than revenue (credit risk)?
   - **CapEx / construction in progress**: capacity-expansion pace, future supply
   - **R&D as % of revenue**: important for tech companies
   - **Operating cash flow vs net income**: earnings quality
   - **Inventory / receivables turnover**: operating efficiency

**Format**: sub-headings + short paragraphs, not data dumps. Every indicator gets at least one "Read-through: …" sentence.

---

### Step 3 (key): Deep Dive on the Target Segment

**The core of the note. The first steps are groundwork; this one is the thickest and deepest.**

**Cardinal rule - drill down to product level**:

User keywords are usually **segment-level**; the company's **product portfolio is finer**. Common splits:

| User keyword | Product-level split (examples) |
|---|---|
| Optical communications | optical transceivers (800G / 1.6T / 400G) / EML / CW laser / DFB / VCSEL / SiPh / optical chips / optical components |
| AI servers | GPU modules / HBM / NVLink switch / cold plates / PCB / BBU |
| Power semis | SiC MOSFET / GaN HEMT / IGBT modules / Si MOSFET |
| Energy storage (ESS) | cells / PCS / BMS / system integration |
| CRO | preclinical / clinical (I/II/III) / CDMO / safety assessment |

**Expansion rules**:
- **If the company has ≥2 clear products in the segment, expand 3.1 / 3.2 / 3.3 for each** - "product definition / market position / customers" for every product.
- **Don't mix them.** Not "the optical business's customers include NVIDIA, Google…", but EML's customers, modules' customers, SiPh's customers separately.
- **Skip products the company doesn't have.**
- **If the company truly doesn't split the segment** (e.g. only "optical revenue xxx"), say "The company does not split this segment further by product" and run the three questions once for the whole.

#### 3.1 Product definition & value-chain position

For each product:

- **What it is**: 1-2 plain sentences, no jargon pile.
- **Use case in the user's segment**: e.g. "800G modules interconnect switches in AI data centers; they carry the east-west traffic of GPU clusters".
- **Value-chain position**: upstream (key materials / components suppliers), downstream (applications / direct customer types).
- **Criticality / moat**: a bottleneck position or commoditised competition? Where are the technical barriers?

#### 3.2 Market position & competitive edge

- **Market share**: a number if available (source and year), otherwise qualitative ("domestic leader" / "top 3" / "tier-2 challenger").
- **Core competence**: tech leadership? capacity? customer lock-in? cost? With **concrete evidence** - "first to mass-produce 1.6T modules", "sole source for an NVIDIA generation".
- **Tier 1 supplier?** Tier 1 or 2? In leading customers' key BOM? Sole source?
- **Key competitors**: 2–4, with a short comparison where possible (scale, process node, customer mix).

#### 3.3 Key customers

- **Disclosed top customers**: if the annual report names the top 5, cite them; if not (many A-shares disclose only shares - "customer A / largest customer"), say so.
- **Customer signals from calls / investor-relations records**: "we supply a major North American hyperscaler", "qualified at customer H" - capture them all.
- **If no clear customer is found, inference is allowed but must be labelled**:
  - explain the basis (supply-chain matching, tenders / RFQs, industry practice, geography)
  - start with "⚠️ Speculation:"
  - e.g. "⚠️ Speculation: the company does not name customers, but its main capacity is in Suzhou Industrial Park and its 2024 new-line specs closely match customer X's public tender, so X is likely one of the top two customers."
- **List all target-segment customers**; for other businesses only the overall top 5, or one line.
- **If the segment has several products, list customers per product** (EML customers are **module makers** like Lumentum / Coherent / Innolight itself; module customers are **hyperscalers** like NVIDIA / Google / Meta).

---

## QA mode

**Triggers**: "QA", "QA mode", "追问模式", "QA 模式".

**Purpose**: after the note (.md) exists, the user wants to dig into a detail, number, customer or product. This mode **only answers in chat** and **does not modify the note**.

### Rules in QA mode

1. **Answer in chat; don't touch the files.** Unless the user explicitly says "update the md", "write it into the file", "add it to section X", **never** reopen, regenerate or re-deliver the md / xlsx.
2. **Depth matches the question**:
   - Simple facts ("what's its gross margin", "who are the top 5 customers") → 1–3 sentences.
   - Analytical questions ("why is 800G GM higher than 400G", "how much do its customers overlap with Coherent's") → structured, full answer.
   - **Don't** turn a simple question into an essay.
3. **Same rigour**: facts (numbers, customers, shares) still carry citations; inferences still start with "⚠️ Speculation:" and give the basis; if not found, say so.
4. **Live lookups allowed**: if the question goes beyond the note (note covers to 2025Q3; "is 2025Q4 out?"), search and answer - still only in chat.
5. **Don't rerun Steps 1/2/3.** QA answers one point precisely.

### Leaving QA mode

"exit" or "退出" leaves QA mode. A new research request afterwards starts again at Step 0.

### QA example

> User: QA
>
> Assistant: QA mode on - ask follow-ups on the research above.
>
> User: Roughly what share of 800G module revenue is NVIDIA?
>
> Assistant: Neither the annual report nor the calls give revenue by customer (A-share companies usually disclose only the combined top-5 share). Known: top-5 customers ≈ xx% [Source: FY2024 annual report]. ⚠️ Speculation: matching NVIDIA H100/H200 system shipments with the company's 800G volumes suggests NVIDIA alone is roughly xx–xx% of module revenue, but this is indirect and the company has not confirmed it.
>
> User: When does 1.6T ramp?
>
> Assistant: On the 2025Q3 results call management said it plans to start volume shipments in H1 2026 [Source: 2025Q3 results briefing]; it is currently sampling.
>
> User: exit
>
> Assistant: QA mode off.

---

## Output

**Two files by default**, delivered to the user:

1. **Note**: `{TICKER}_{Segment}_Initial_Coverage.md` (Chinese: `{公司简称}_{重点业务}_首次研究.md`), e.g. `LITE_EML_Initial_Coverage.md`, `中际旭创_光通信_首次研究.md`.
2. **Dashboard**: `{TICKER}_Financials_10Q_Dashboard.xlsx` in the same folder. **Never omitted.**

The md follows Step 1 → Step 1.5 → Step 2 → Step 3, opening with a metadata block:

```markdown
# {Company full name} ({TICKER}) Initial Coverage — {target segment}

> Date: YYYY-MM-DD
> Target segment: xxx
> Data as of: xxxx Qx
> Exchange: xxx
> Attached: {TICKER}_Financials_10Q_Dashboard.xlsx
```

It ends with **Open Questions / Information Gaps** - key information not found (e.g. "no separate GM for 800G modules", "main customers not named") for the user's follow-up research.

Then a 3–5 sentence chat summary with the 2–3 most important signals - **don't** repeat the report.

## Citation rules

- Every number, customer name and market share carries a citation (tool citation or `[Source: …]`).
- Speculation gets **no** citation - citations are for sourced facts; speculation gets the "⚠️ Speculation:" prefix.
- For transcript content, say "On the 2025Q3 call, management said …" and cite it.

## Don'ts

- ❌ Don't invent data. Better "not found in public information".
- ❌ No buy/sell advice, price targets or valuation conclusions. **Nothing** on market cap, PE, PB, PS, PEG, share-price performance, technicals.
- ❌ Step 1 is not an encyclopedia entry - no founder stories or company history.
- ❌ Don't spread Step 3 evenly over all products; the user cares about one segment.
- ❌ Don't forget "if the company splits finely, follow it" - the user stressed it.
- ❌ **Never omit the Step 1.5 xlsx.**
- ❌ **Don't paste the 10 rows of the xlsx into the md** - at most 3 observations + the file name; copying makes the md long and breaks single-source-of-truth.
- ❌ **In QA mode, never modify, regenerate or re-deliver the .md / .xlsx** unless the user explicitly asks.

## A complete small example (optical)

> User: Research Innolight, focus on optical communications

The keyword is **segment-level** "optical", so Step 0 searches first and finds several products (by speed: 800G / 1.6T / 400G / 200G and below; plus in-house optical components / chips). Step 3 runs the three questions **for each product**.

Expected skeleton:

```
## Step 1: Financial Snapshot
Positioning: global optical-module leader, core supplier for AI data-center interconnect.
2025Qx revenue xxx, YoY +x%, net income xxx ...
Revenue mix:
| Segment | Revenue | Share |
| **Optical communications** ⭐ | xxx | xx% |
| └ 800G modules | xxx | xx% |   ← product level, following the company's split
| └ 1.6T modules | xxx | xx% |
| └ 400G modules | xxx | xx% |
| └ 200G and below | xxx | xx% |
| └ In-house optical components / chips | xxx | xx% |
| Other | xxx | xx% |

## Step 1.5: 10-Quarter Dashboard
See `300308_Financials_10Q_Dashboard.xlsx`.
Observations: ① revenue YoY accelerated from +xx% in 2023Q4 to +xx% in 2025Q3; ② mix-driven GM up xx pp; ③ net margin up xx pp.

## Step 2: Forward-Looking Financial Signals
- GM rose from xx% in 2024Q4 to xx% in 2025Q3, mainly from a higher 800G share (mix shift)… (interpretation, not a repeat of Step 1.5)
- Inventory +xx% QoQ, raw materials +xx% QoQ, consistent with a 1.6T build for H2…
- Contract liabilities +xx QoQ; order visibility into H1 2026…

## Step 3: Deep Dive — Optical Communications

### Product 1: 800G modules
#### 3.1 Product & value chain
Interconnect between GPUs and spine-leaf switches in AI training clusters (east-west traffic)…
Upstream: EML laser chips (Lumentum, Coherent); downstream: NVIDIA, AWS, Google, Meta…
#### 3.2 Position
~xx% global share (2024 shipments), first tier with Coherent and Eoptolink…
#### 3.3 Customers
- Top-5 customers xx% of revenue, not named (Customer A/B/C).
- 2025Qx call: "demand from major North American customers remains strong".
- ⚠️ Speculation: from supply-chain checks and public tenders, the top two are likely NVIDIA and Google (or AWS).

### Product 2: 1.6T modules
#### 3.1 …  next-generation module for the NVIDIA Rubin / B300 era…
#### 3.2 …  expected to ramp in 2026; among the first to sample…
#### 3.3 …  still sampling; customers not disclosed…

### Product 3: In-house optical components / chips
#### 3.1 …  vertical integration upstream, mainly for captive use, some external sales…
#### 3.2 …  small but strategically important; eases EML supply tightness…
#### 3.3 …  mostly captive; external customers not disclosed…
```

Key points of the example: **"optical" became three products with three separate passes** - their customer groups differ (hyperscalers for 800G, module makers for in-house components), so **never mix them**; and **Step 1.5 always attaches the xlsx**.

That is a proper initial coverage: focused, product-level, sourced, speculation labelled, not spread evenly, with the 10-quarter rhythm table attached.
