---
name: stock-discovery
description: "Finds and screens listed companies (A-share / HK / US) for a business, a value chain, or a given company list. Modes: (1) business discovery - as many companies doing one business (CPO, FAU, SiC MOSFET, AI PCB, EML ...) as possible, with their position; (2) value-chain mapping - 1-2 main players per upstream / midstream / downstream segment, chain completeness first; (3) list screening - classify every company on a list (e.g. OFC exhibitors) for a business. Use when the user says 'find companies doing XX', 'which listed companies do XX', 'map the XX value chain', 'XX related stocks', 'who on this list does XX', '挖一下做 XX 的公司', 'XX 产业链梳理', 'XX 相关标的', or just 'who does XX'. Outputs a standardised xlsx where every company has products / position / stage / market attention / a lagging-stock flag. Versus company-research (deep dive on a known company): this is the upstream step that finds the companies."
---

# Stock Discovery

Answers a frequent research question: "**in this business / value chain / list, which listed companies actually do it, and how far along is each?**" It pulls companies scattered across annual reports, supply-chain research, exhibitor lists, tenders and trade media into **one structured xlsx with position labels**.

## Conventions (fixed)

- **Output**: always through `scripts/build_xlsx.py` with `--output "{RESEARCH_ROOT}/stocks/{file name}"` (file names below). The script fixes column order, validates the label columns, sorts mode 1 deterministically and writes the Summary sheet.
- **Language**: `"lang": "en"` or `"zh"` in the JSON payload, following the request language. Headers, labels and the Summary sheet switch with it; JSON keys may be English (preferred) or the legacy Chinese ones.
- **Fixed labels** - a label cell must **start with** one of these (a short qualifier may follow, e.g. `Tier 2 (Tier 1 in FAU)`; longer explanations go in Notes). Anything else is rejected by the script rather than silently left uncoloured:

| Column | English | Chinese |
|---|---|---|
| Position | Tier 1 / Tier 2 / New entrant / ⚠️ TBC / Demand side / N/A | 头部 / 二线 / 新进入者 / ⚠️ 待确认 / 下游需求侧 / N/A |
| Stage | Mass production / Sampling / R&D / Concept / N/A | 量产 / 送样 / 研发 / 概念 / N/A |
| Attention | High / Medium / Low | 高 / 中 / 低 |
| Relevance (mode 3) | Yes / Partial / No / ⚠️ TBC | 是 / 部分 / 否 / ⚠️ 待确认 |
| Chain level (mode 2) | Upstream / Midstream / Downstream | 上游 / 中游 / 下游 |

## Three modes

**First decide which mode the request is** - search paths, granularity and columns differ. If unclear, ask.

| Mode | Trigger | Focus | Row key |
|---|---|---|---|
| **① Business discovery** | one **specific business** (big like CPO, small like FAU, tiny like 850nm VCSEL) - "find companies doing XX" | **coverage breadth** | company |
| **② Value-chain mapping** | a **chain** (DCI / 800G modules / solid-state batteries / AI servers) - "map XX upstream and downstream" | **chain completeness** - every segment covered, 1-2 main players each | chain segment |
| **③ List screening** | **a company list + a business** - "which OFC 2026 exhibitors do optical" | **per-company classification** | company, in the user's list order |

Each mode's search playbook and table format is in `references/mode-1-business-discovery.md`, `references/mode-2-industry-chain.md`, `references/mode-3-list-screening.md` - **read the matching reference after triggering.**

---

## Shared workflow

### Step 0: Mode + scope

**Mode** - match the triggers above. If ambiguous ("AI PCB upstream and downstream" could be either), ask briefly: "Do you want ① who does this business (breadth first), or ② every segment of the chain and who is in each (completeness first)?"

**Markets** - default **A-share + US**. Follow the user if they say "A-shares only" or "add HK". Otherwise use the default; **don't ask**.

**Keywords** - turn the segment word into **product-level search keywords**, e.g.:

- "optical communications" → `optical modules / components / EML / CW laser / DFB / VCSEL / SiPh / FAU / TEC / isolators`
- "AI servers" → `GPU modules / HBM / NVLink / CCL / AI PCB / cold plates / BBU / power modules`
- "solid-state batteries" → `sulfide electrolyte / oxide electrolyte / polymer electrolyte / lithium-metal anode / dry-electrode equipment`

**This matters most - the finer the split, the more complete the result.** If unsure, search how the industry splits it first (`{segment} value chain key components` / `{赛道} 产业链 主要环节`).

### Step 1: Broad search

Search from several angles, **in both Chinese and English**:

1. **Segment + listed companies**: `{segment} public companies`, `{segment} suppliers stock`, `{segment} key players`; `{业务} A 股上市公司`, `{业务} 标的`, `{业务} 龙头`, `{业务} 概念股`
2. **Annual-report / prospectus disclosures** - **the hardest source**, the company's own words: `{segment} customer` / `{segment} supplier 10-K`; `{业务关键词} 主要客户` / `主要供应商`
3. **Industry research (sell-side, consultancies)**: `{segment} industry report`, `{segment} market research TrendForce / Yole / Omdia`; `{业务} 产业链 研报`
4. **Exhibitions / anchor customers' supplier lists**: `{anchor customer} supplier {business}` (e.g. "NVIDIA optical module suppliers", "CATL solid electrolyte partner"); OFC / CES / SEMICON / LASER World of Photonics China / CHTF exhibitor lists
5. **Reverse search, from downstream up**: take known downstream companies (NVIDIA / Innolight / CATL) and search their suppliers - this often finds hidden champions

**Take notes while searching** - company, ticker, market, product clue. **Don't filter yet** - keep a few extra and cut later.

### Step 2: Per-company verification

For each company **verify three things before it goes into the table**:

1. **Does the business really exist?** Announcements, annual reports, product pages or IR material state it explicitly. If only a report or forum post says so and official material doesn't, **downgrade to "⚠️ Speculation"**.
2. **Stage** - one of four:
   - **Mass production**: shipping, with revenue
   - **Sampling**: samples under customer validation, not at scale
   - **R&D**: in development, not sampled
   - **Concept**: only mentioned in announcements / roadshows, no product or R&D investment seen
3. **Position in this business** - one of three:
   - **Tier 1**: among the top few, clearly ahead in share, recognised by key downstream customers
   - **Tier 2**: has product and customers but clearly behind in scale and position
   - **New entrant**: just entered, in customer qualification, revenue ~zero

**Basis for position**: first downstream customers' supply-share disclosures (Apple, TSMC supply chains), then the company's own share claims (with scepticism), last sell-side "leader / tier-2" descriptions. **If evidence is thin, use "⚠️ TBC".**

### Step 3: Market attention

Label **High / Medium / Low** from three dimensions:

| Dimension | High | Medium | Low |
|---|---|---|---|
| **Broker coverage** | ≥10 brokers | 3-9 | <3 or only small local brokers |
| **Retail discussion** | very active on Xueqiu / Guba / Twitter / Reddit, often trending | some, not concentrated | almost none |
| **News exposure** | frequently in mainstream financial media in the last 3 months | occasionally | almost never |

Combine into **one** label - **don't** score the three separately.

### Step 4: Lagging flag ⭐

This skill's signature signal: companies that **do the business but whose stock has not followed the sector** (maybe overlooked, maybe fundamentally weak - flag it either way).

**Method**:
1. Pick a sector benchmark (A-share: concept index or sector ETF; US: a leader such as LITE / CRDO).
2. Compare the company's **3-month / 6-month / YTD** return with the benchmark.
3. If the company clearly does the business **and** at least two windows are clearly below the benchmark (e.g. benchmark +30% YTD, company +5% or down), mark **🐢** and put the benchmark and the gap in Notes.

**No need to check every company** - prioritise "has the business, decent position, low or medium attention"; those are most likely overlooked.

**No valuation** - no PE / PB / target price / buy-sell. The lagging flag is **information**, not a recommendation.

### Step 5: Output xlsx

Write the rows to a JSON file and run:

```bash
python scripts/build_xlsx.py rows.json --output "{RESEARCH_ROOT}/stocks/CPO_Companies_20260508.xlsx"
```

If the script reports a label error, fix the label (or move the qualifier into Notes) and rerun - don't edit the script.

**File names**:

| Mode | English | Chinese |
|---|---|---|
| ① | `{business}_Companies_{YYYYMMDD}.xlsx` | `{业务}_相关公司_{YYYYMMDD}.xlsx` |
| ② | `{chain}_Value_Chain_{YYYYMMDD}.xlsx` | `{产业链}_产业链_{YYYYMMDD}.xlsx` |
| ③ | `{list}_{business}_{YYYYMMDD}.xlsx` | `{清单名}_{业务}_{YYYYMMDD}.xlsx` |

Column schemas are in each mode's reference; the payload format is at the top of `scripts/build_xlsx.py`.

#### Segment overview ⭐

Each row may carry an **optional** `segment` field (not a main-table column in mode 1; **only used for the Summary sheet**). If any row has it, the script adds a "segment × position" overview to the Summary sheet - the whole field's player map at a glance.

**Strongly recommended in mode 1** - business discovery naturally spans several material / product sub-segments (e.g. a Low-CTE CCL system = CCL laminate / spherical silica / Low-CTE glass cloth / Low-CTE resin / HVLP copper foil); the overview is more readable than a long list.

**Mode 2** has a `segment` column already; the overview reuses it.

**Mode 3** shows no overview unless the user wants a breakdown - then add `segment` to rows.

```json
{"company": "Novoray 联瑞新材", "ticker": "688300.SH", "market": "A-share",
 "products": "spherical silica", "position": "Tier 1", "stage": "Mass production",
 "attention": "High", "lagging": "", "notes": "...", "segment": "Spherical silica (Low-CTE filler)"}
```

Segment names must be **consistent** ("spherical silica" vs "silica" are two buckets) - the script groups by exact string.

---

## Shared rules

1. **Cite everything** - every company's key labels (business, stage, position) have at least one explicit source in Notes (announcement / 10-K / broker report / media link). If unverifiable, **downgrade or leave out** - never force it.
2. **Mark speculation** - anything inferred from supply-chain, tender or customer-matching information is written `⚠️ Speculation: …`.
3. **Don't miss ADR / H-share dual listings** - e.g. TSMC (TSM), Alibaba (BABA / 9988.HK), CATL (300750.SZ / 3750.HK). List the most liquid market; mention the others in Notes.
4. **Ticker format**: A-shares with suffix (`300750.SZ`, `688981.SH`, `002463.SZ`); US bare (`NVDA`, `LITE`); HK (`9988.HK`, `3750.HK`).
5. **No market cap, PE, target price** - this is discovery and screening, not valuation. The **only** price-related field is the lagging flag.
6. **Breadth trade-offs**:
   - mode 1: **8-15 companies** by default, ordered Tier 1 → Tier 2 → new entrant, at most 5-7 per tier (the script sorts)
   - mode 2: **1-2** main players per segment - **don't pile them on**; chain completeness matters more
   - mode 3: as many as the list has; companies with **no** related business stay in the table as "No" relevance, so the user sees nothing was skipped

---

## Immediately after triggering

1. Read the matching reference (`references/mode-{1,2,3}-*.md`)
2. Step 0: mode + markets + keyword split
3. Steps 1-4
4. `scripts/build_xlsx.py` → `{RESEARCH_ROOT}/stocks/`
5. A short summary (≤300 words) + the file path / link

Don't restate the whole table in chat - it's in the xlsx; give the summary and insights.
