---
name: earnings-call-reader
description: "Reads a listed company's earnings-call transcript and writes a structured, investment-oriented call log: guidance, profitability drivers, product-level demand / backlog / customers, ramp timing and capacity. Gets the transcript from a local file in the company folder first, otherwise from Yahoo Finance (verifying company and quarter), otherwise asks the user. Use when the user says 'summarize this call', 'read this transcript', 'earnings call', 'conf call notes', 'update FORM for Q3', '总结这份电话会', '财报电话会', '业绩说明会', or pastes text that is clearly a call transcript (Operator / CEO / CFO / Analyst turns, a Q&A section). If {TICKER}_Earnings.md already exists in the folder, switches to cross-quarter mode: appends the new quarter under each section and marks changes versus the prior quarter with a fixed emoji legend, never editing old quarters."
---

# Earnings Call Reader

Turns one earnings-call transcript into a structured log entry, and keeps one log per company that grows by one quarter per call.

## Goal

Capture the signals that matter most for an investor:

1. Outlook
2. Drivers of current-quarter profitability
3. Product-level demand and industry dynamics
4. Orders and backlog
5. Customers
6. Revenue ramp timing
7. Capacity constraints

## Conventions (fixed - these are what keep runs consistent)

- **Folder layout**: one folder per company, folder name = TICKER, one log per company: `{RESEARCH_ROOT}/{TICKER}/{TICKER}_Earnings.md`. Every quarter is appended to the same file. Transcripts the user saved live in the same folder.
- **Quarter label**: always `FY{YY} Q{n}` in the company's *fiscal* year (e.g. `FY26 Q3`). The TL;DR heading adds the call date: `FY26 Q3 (2026-10-28)`. This is the same fiscal labelling Yahoo/Quartr transcripts use ("Q3 FY2026"). If the user says "2026Q3", treat it as fiscal FY26 Q3; if the transcript header disagrees with what the user asked for, show both and confirm.
- **Output language**: write the log in the language the user wrote the request in. When appending to an existing log, **always use the existing file's language**, whatever the request language. Headings are fixed strings in both languages (table below) - never paraphrase them.
- **Scripts** (in `scripts/`, Python 3, no network):
  - `transcript_tool.py find | verify | clean` - locate, verify and slim the transcript.
  - `check_earnings_log.py` - validate the log skeleton, coverage and the append-only rule after writing.

| Element | English log | Chinese log |
|---|---|---|
| Title | `# {TICKER} Earnings Call Log` | `# {TICKER} Earnings Call Log` |
| H2 | `## TL;DR` | `## 速览（TL;DR）` |
| H2 | `## Guidance` | `## 业绩展望（Guidance）` |
| H2 | `## Drivers of Profitability` | `## 当季盈利驱动因素 (Drivers of Profitability)` |
| H2 | `## Product Breakdown` | `## 分产品 / 分业务线进展 (Product Breakdown)` |
| H3 (first under Product Breakdown) | `### Company-wide Demand / Order Book / Capacity Overview` | `### 整体 Demand / Order Book / Capacity 总览（全公司层面）` |
| H3 | `### {Product name}` | `### {产品名}` |
| H5 (in this order) | `##### Demand / Industry Dynamics` · `##### Order Book / Backlog` · `##### Customers` | same |
| H2 | `## Product Summary Table` | `## Product Summary Table` |
| H2 (optional) | `## Other` → `### FY26 Q3` → `#### Capacity` · `#### Pricing` · `#### Other Notable Points` | `## Other` → `### FY26 Q3` → `#### Capacity` · `#### Pricing` · `#### 自由发挥` |

## Step 0: Get the transcript (local first, then Yahoo, then ask)

Identify **company + TICKER** and the **fiscal quarter** first. If the user gives no quarter, the target is the most recent call.

**0a. Pasted text** - if the user pasted the transcript, use it; save nothing.

**0b. Local file (always try first).** It avoids a web round-trip and gives a reproducible source.

```bash
python scripts/transcript_tool.py find --ticker FORM --quarter "FY26 Q3" --dir "{RESEARCH_ROOT}/FORM"
```

- `FOUND` (matched on the transcript's own header line) → run `verify` on it and use it. Report a file-name typo if the tool flags one; do not rename the user's file.
- `CANDIDATE` (file name matches but no standard header, or a .pdf/.docx this shell cannot read) → open the first lines (pdf/docx with the matching file skill) and use it only if they name the company and the quarter.
- `NOT FOUND` → 0c.

**0c. Yahoo Finance (default web source).**

1. Fetch the index page `https://finance.yahoo.com/quote/{TICKER}/earnings-calls/` (WebFetch works on this page). Ask for the list of titles and URLs. Titles look like `FORM Q3 FY2026 earnings call transcript`.
2. Pick the entry whose title matches **both** the ticker and `Q{n} FY{YYYY}` exactly. If none matches, stop and go to 0d - do not take the nearest quarter.
3. Open the transcript URL **in a browser tool** (built-in browser or Claude in Chrome). **Check before reading the whole page** - run this in the page (javascript tool) and look only at the small result:
   ```js
   (() => { const t = (document.querySelector('main') || document.body).innerText.split(/Copyright ©/)[0];
     return { title: document.title, head: t.slice(0, 300), chars: t.length,
              paywall: /Upgrade to unlock|subscription plan is required/i.test(t), tail: t.slice(-400) }; })()
   ```
   Accept only if the title / head contains `({TICKER}) Q{n} FY{YYYY}` for the requested quarter (e.g. `FormFactor, Inc. (FORM) Q3 FY2026 earnings call transcript`), `paywall` is false, `chars` is in the usual 35k–80k range, and `tail` ends with closing remarks ("This concludes…", "disconnect"). Also check the company name is the one the user meant (share classes, similar tickers).
4. Then read the text with `get_page_text` and a large limit (`max_chars` ≥ 150000). Do **not** use WebFetch for the transcript body: it returns a model-written summary, not verbatim text, so quotes would not be reliable (Yahoo transcript pages often refuse it anyway). Without a javascript tool, read the page and apply the same checks to its first and last lines. (For saved files, `transcript_tool.py verify` runs these checks.)
5. **Paywall**: Yahoo usually shows only the most recent call for free; older calls show a preview and "Upgrade to unlock … A Silver or Gold subscription plan is required". Never summarise a preview - go to 0d.
6. Record the source in the log entry header (URL + retrieval date). Do not re-type the transcript into a file to "cache" it - that costs as many tokens as the transcript. If the user wants a local copy, suggest they save the page as `{TICKER} {YYYY}Q{n}.txt` in the company folder; the next run will then find it in 0b.

**0d. Not available** → tell the user plainly which source failed (no local file / no matching Yahoo entry / paywalled / browser unavailable) and ask them to put the transcript (txt, md, pdf or docx) into `{RESEARCH_ROOT}/{TICKER}/`, or paste it. Stop until they do.

**Optional token saver**: `transcript_tool.py clean FILE -o FILE.clean.txt` removes timestamps, repeated speaker headers and page chrome (≈4% on saved txt files, more on raw page text). It changes no spoken words, so quotes stay exact.

`verify` warnings that need a decision: *no closing line* (possibly truncated - check the last turn; mention it in the log if content is missing), *no Q&A markers* (prepared remarks only - say so in TL;DR).

## Step 1: Identify company and period

Put **company name and TICKER**, **fiscal quarter** (canonical label) and **call date** at the top of the entry.

## Step 2: Detect the mode (important)

```bash
ls "{RESEARCH_ROOT}/{TICKER}/{TICKER}_Earnings.md" 2>/dev/null
```

- **File does not exist** → single-quarter mode (first run). Create `{TICKER}_Earnings.md`.
- **File exists** → cross-quarter mode. Read the whole file, identify the quarters already in it, and append this quarter at the right place in each section. **Never modify any earlier quarter.**
- Before writing in cross-quarter mode, copy the file to `{TICKER}_Earnings.backup.md` (used by the append-only check in step 5 of the write procedure; delete it after the check passes).

Edge cases:

- **The transcript is older than the newest quarter in the file** → do not append. Tell the user: "The file already has {newest}; the transcript you gave is the earlier {quarter}. Confirm whether to insert it into the middle of the timeline." Wait.
- **Same quarter as the newest in the file** → ask: "The file already has {quarter}. Replace it, append a revised version, or stop?"
- **TICKER mismatch** between transcript and file name → stop and ask the user to check the file.

## Output format rules

### Quote rule

Every key claim is followed by the **original quote**:

- **Chinese log**: English original in quotes, then the Chinese translation directly after it on the same line - no "翻译：" label, no separate line:
  > "Demand for our AI accelerators remains significantly ahead of supply, and we expect this to continue through fiscal 2026." 我们 AI 加速器的需求显著超过供给，预计这一情况将持续到 2026 财年
- **English log**: the original quote only.
- If the transcript itself is in Chinese, keep the original only.

### Numbers rule

Every conclusion involving numbers carries the actual number (unless the call gives none). Write "Revenue +47% YoY to $35.1B, above the $33B top of guidance", not "revenue grew strongly".

## Output Structure

The file is organised **by topic**. Two nesting rules coexist:

- **Most sections (TL;DR / Guidance / Drivers / Product Summary Table / Other)**: section → quarter. Quarters are H3 sub-headings; the new quarter goes at the bottom of the section.
- **Product Breakdown (the core)**: section → product → quarter. The new quarter goes **after that product's last quarter**, so all quarters of one product sit together and its progress can be compared at a glance.

Skeleton (English log; the Chinese log uses the headings in the table above):

```
# {TICKER} Earnings Call Log

## TL;DR
### FY26 Q2 (2026-07-29)
...
### FY26 Q3 (2026-10-28)      ← appended this quarter

## Guidance
### FY26 Q2
...
### FY26 Q3                   ← appended, with "vs prior quarter" column

## Drivers of Profitability
### FY26 Q2
### FY26 Q3

## Product Breakdown
### Company-wide Demand / Order Book / Capacity Overview
#### FY26 Q2
#### FY26 Q3                  ← appended under the overview
### Product A
#### FY26 Q2
##### Demand / Industry Dynamics
##### Order Book / Backlog
##### Customers
#### FY26 Q3                  ← appended under Product A
##### Demand / Industry Dynamics (incl. vs prior quarter)
##### Order Book / Backlog (incl. vs prior quarter)
##### Customers (incl. vs prior quarter)
### Product B
...

## Product Summary Table
### FY26 Q2
| table |
### FY26 Q3                   ← new table below the old one; old table untouched

## Other (only if there is content)
### FY26 Q3
#### Capacity
#### Pricing
#### Other Notable Points
```

> **Why "product → quarter" in Product Breakdown but "quarter" elsewhere?** The most useful comparison for an investor is how *one product* progresses across quarters - e.g. EML from "sold out" to "sold out + LTA locked to end-CY27". Keeping a product's quarters together shows that evolution without scrolling. Other sections (like Guidance) are read as "the full picture of one quarter", so grouping by quarter fits them.

The rules below apply to both modes; cross-quarter mode only adds the appending and change markers described in [Cross-quarter mode](#cross-quarter-mode).

---

## TL;DR

3–5 bullets with the most important signals of the call - enough to know the company's story this quarter at a glance.

---

## Guidance

1. List management's guidance for the **next quarter** and the **full year**. Include multi-year outlooks if given (e.g. CY26, FY27).
2. Include any guidance on overall shipments or demand trend.

Suggested format:

| Metric | This quarter actual | Next-quarter guide | Full-year / long-term | Quote |
|---|---|---|---|---|
| Revenue | $35.1B | $37.5B ± 2% | FY26 $160B+ | (quote) |
| Gross margin | 75.0% | 75.5% | — | (quote) |
| CapEx | — | — | CY26 $X00B | (quote) |

If management **raises / lowers / reiterates** guidance, state it explicitly.

---

## Drivers of Profitability

Explain *why* the quarter came out this way. Management usually gives 2–4 reasons; list all of them, each with its quote.

1. **[Driver 1 title]**: one-line summary + numbers
   > "quote..."
2. **[Driver 2 title]**: ...

---

## Product Breakdown - the core

MUST break down by the company's major product categories (e.g. Lumentum: EML / OCS / CPO).

- If the company does NOT clearly break down: write "The company did not break results down by product."
- If a category gets no separate data or comment this call, still list it and write "Not separately discussed on this call."

### Scope Attribution Rule - critical

**This is where this skill most often goes wrong, and where errors most distort an investment view.**

Every statement belongs to one of **two levels**:

| Level | Meaning | Where it goes |
|---|---|---|
| **Company-wide** | Whole company, all product lines, total backlog, total capacity, overall supply, an application story spanning several products | The **Company-wide Overview** block at the top of Product Breakdown. May also be reflected in TL;DR / Other → Capacity |
| **Product-level** | Explicitly about one product line ("EML revenue +80%", "RLS shipments at a record for two straight quarters") | Under that product's `### Product X` |

**Principle: company-wide outranks product.** If a statement is about the business overall, it goes above the products (one level higher); only statements that name a specific product go inside that product.

#### Three-step test for each statement

1. **Subject**: is the speaker talking about "we / the company", or a named product (RLS / EML / Waveserver)?
2. **Evidence**: does the quote name a product? Generic nouns like "demand", "backlog", "orders", "capacity" are almost always company-wide.
3. **Multi-product trap**: "RLS **as well as** 800G ZR pluggable", "Waveserver **and** modems" - also **company-wide**, because it is not one product. Do not file it under RLS because RLS is mentioned. In the RLS block, add a one-line pointer: "see the scale-across application in the Company-wide Overview."

#### Three typical errors (avoid)

**Error 1 - company-wide backlog/supply filed under one product**
- CFO: "we expect demand will continue to outstrip supply at least for the next several quarters" → company-wide supply tightness.
- CFO: "nearly all new orders we are taking now will be for fulfillment in fiscal 2027" → company-wide backlog visibility.
- Correct: the Company-wide Overview block. **Not** repeated under RLS / EML / Waveserver.

**Error 2 - a multi-product application story filed under one product**
- CEO: "three hyperscalers ramping for scale-across, **with our RLS platform as well as 800G ZR pluggable**" → supplied by two product lines.
- Correct: the overview's Demand / Customers paragraph - "three hyperscalers ramping scale-across (jointly supplied by RLS + 800G ZR pluggable)". The RLS and ZR blocks each get a one-line pointer.

**Error 3 - a guidance raise filed under one product**
- CFO: "we are raising FY26 revenue guidance to $5.9-6.3B" → company guidance.
- Correct: the Guidance section. **Not** repeated under a product.

#### Correct block order

```
## Product Breakdown
### Company-wide Demand / Order Book / Capacity Overview
  ← total backlog, overall supply/demand, overall capacity, customer-wide figures,
    multi-product application stories, e.g.:
    - "Backlog +$2B QoQ to $7B", "almost all new orders ship in FY27",
      "demand to exceed supply for several more quarters"
    - "three hyperscalers ramping scale-across (RLS + 800G ZR pluggable)"
### Product A (e.g. RLS)
  ← only what names RLS: RLS shipments +80% YoY, records two quarters running, Hyper-rail roadmap
  ← pointer for shared stories: "scale-across customer progress: see Company-wide Overview"
### Product B (e.g. Waveserver)
### Product C (e.g. 800G ZR Pluggable)
```

#### Fallback rules

- Unsure whether company-wide or product-level → **default to the higher level (company-wide)**: this never overstates one product's visibility.
- Multi-product application stories → company-wide, **naming the products that jointly supply it**.
- The overview is an H3 (`### Company-wide Demand / Order Book / Capacity Overview`) **at the same level as** the product blocks, and always first.

### Nesting rule

Each product is an H3 (`### Product X`), each quarter an H4 (`#### FY26 Q3`), and Demand / Order Book / Customers are H5s in that order. The overview block is also an H3 with H4 quarters. In cross-quarter mode the new quarter goes after the last quarter **of that product / overview**.

### Level-of-detail rule

Products or business lines related to **optical communications / AI / data centers** get full detail (without padding). Other products: core numbers and key changes only.

If the user gives **optical**-type keywords, first decide from the transcript whether each product is optical-related; if so, tell the user "this product is optical-related" (in the product heading, e.g. "【optical-related】") and go into more detail.

---

### Company-wide Demand / Order Book / Capacity Overview

#### {quarter}

All **company-wide** signals for the quarter:

- **Overall demand wording**: management's qualitative description of the demand environment
- **Total backlog / RPO / contract liabilities**: size, QoQ/YoY change, visibility (into which fiscal year)
- **Overall supply / capacity**: company-level tightness, CapEx pace, expansion path
- **Customer-wide figures (if any)**: number of 10%+ customers, cloud share, geography

Same format as the product blocks - every conclusion immediately followed by its quote.

---

### Product A / Category A (e.g. EML)

#### {quarter}

- **Revenue and growth this quarter** (QoQ / YoY)
- **Outlook / contribution of this product**
- **Company progress on this product**

##### Demand / Industry Dynamics

**Every conclusion is followed immediately by its quote - never a list of points with the quotes pasted together at the end.** Investors need to check each judgment against its evidence; separating them makes checking much slower. Same format as Drivers:

1. **[Point title]**: one-line summary + numbers
   > "quote..."

Cover these dimensions (skip any with no content):

- **Demand strength**: is demand for the product hot / is the industry short of supply? Say **which product / sub-segment** and how strong management's wording is.
- **Differentiation and value proposition**: does management explain **why** the product wins - performance, cost, space, power, advantage over competitors? These determine how durable demand and pricing power are, so **expand them; don't compress to one line**.
- **Sub-segment data**: growth differences across sub-categories / channels / customer groups (enterprise vs carrier, hyperscale vs general enterprise), each with its quote.
- **Industry progress / change**: accelerating adoption, technology-route shifts, new applications, structural shifts.
- **Competitive landscape**: share changes or differentiation versus named competitors.

**Note**: only content that **names this product**. "Overall demand is strong" without a product name belongs in the overview.

Summarize:

- Judging by this product's sub-industry, is adoption getting ready to take off / taking off?

##### Order Book / Backlog

Identify these signals (**always keep the original wording when they appear**):

- **demand exceeds supply / demand outpacing supply** (供不应求)
- **sold out / overwhelming demand** (爆单)
- **demand visibility of X years/quarters** (需求能见度)
- **booked / locked for X quarters** (锁定未来订单)
- **capacity constrained / supply-constrained** (产能不足)

Key content (plus anything else you judge important):

- **Backlog size and YoY change**
- **RPO (Remaining Performance Obligations)**, undelivered contract value

**Note**: only order/backlog signals **for this product line**. If the company only discloses total backlog, write "Product-level backlog not disclosed; see Company-wide Overview."

| Metric | Value | YoY / QoQ | Quote |
|---|---|---|---|
| Backlog | $XXB | +XX% YoY | (quote) |
| Orders locked for | next X quarters | — | (quote) |
| Key wording | "demand significantly exceeds supply" | — | (quote) |

Summarize:

- Is demand exceeding supply?
- Order visibility

##### Customers

Focus on **where each customer is in the cycle**:

- **sampling**
- **qualified / certified**
- **pilot production**
- **ramp**
- **volume shipment**
- **sole source**
- **new customers / hyperscalers** - list "X new customers" even when unnamed

**Note**: only customer progress **specific to this product**. A customer buying several products for one application (e.g. three hyperscalers buying RLS + ZR for scale-across) goes in the overview (noting the joint supply), with a one-line pointer here.

- **[Customer]**: currently at [stage]. Quote:
  > "..."

---

#### {next quarter} (cross-quarter: appended here, with vs-prior-quarter marks)

(Same sub-structure: revenue / progress → ##### Demand → ##### Order Book → ##### Customers)

(Repeat for Product B, Product C, ...)

---

### Product Summary Table (TABLE)

**The most valuable table in the log.** All products × their current stage in one view, to judge which revenue lands in the next 2–4 quarters.

| Product | Current stage | Expected ramp timing | Expected contribution (if given) |
|---|---|---|---|
| Product A | volume ramp | contributing since Q3 | - |
| Product B | sampling | H2 FY26 | - |
| Product C | in development | FY27 | - |

Missing information → `—`. **Leave it blank rather than guess.**

**Cross-quarter mode: keep old tables untouched; the new table goes directly below, under its own quarter heading.**

---

### Other (omit if empty)

Always `### {quarter}` first, then the H4s below.

#### Capacity

If mentioned:

- **Current capacity & utilization**
- **Expansion plans**: new fabs, equipment purchases, CapEx size, start-up dates
- **Foundry partners**: TSMC / Samsung / SMIC etc., advanced-node allocation
- **Relief timeline** (most important): when management expects supply and demand to balance

> Capacity here is **company-wide** capacity / CapEx / expansion. It **complements** the overview block: the overview has the current state and this quarter's signals; Other → Capacity has the expansion plan and timeline. If they overlap, the overview can carry a pointer: "see Other → Capacity".

#### Pricing

If mentioned: **price increases**, **price expectations**.

#### Other Notable Points (Chinese log: 自由发挥)

Important points outside the sections above, 1–2 sentences each.

---

## Cross-quarter mode

Only when `{TICKER}_Earnings.md` already exists.

### Core principles

1. **Old content is read-only.** Every existing quarter's text, tables and quotes stay exactly as they are. If old content is wrong, note it in this quarter's entry - do not fix it in place.
2. **Where to append depends on the section type**:
   - TL;DR / Guidance / Drivers / Product Summary Table / Other: add `### {this quarter}` after the section's last quarter.
   - Product Breakdown (overview and each product): add `#### {this quarter}` (H4, not H3) after that block's last quarter.
3. **Change marks are required only in**: Guidance; the overview's Backlog / Demand; each product's Demand / Industry Dynamics, Customers, and Order Book / Backlog. Other sections (TL;DR, Drivers, Capacity, Pricing, Other Notable Points) are appended without comparison marks.

### Change legend (fixed - use no other symbols)

Marks are **emoji + bold**:

| Symbol | Meaning | Example |
|---|---|---|
| 🔼 | progress / raise / positive change | customer moved from qualification → ramp |
| 🔽 | setback / cut / negative change | guidance cut, customer delayed |
| ➡️ | unchanged | guidance reiterated |
| 🆕 | new item | new customer, new product line |
| ⚠️ | warning / inflection | from "demand exceeds supply" → "demand softening" |
| 📌 | worth comparing, not clearly good or bad | metric definition changed |

### Append rules by section

#### A. Guidance

Compare each metric with last quarter's guidance/actuals and **add a "vs prior quarter" column** (Chinese log: "vs 上季"):

| Metric | This quarter actual | Next-quarter guide | Full-year / long-term | vs prior quarter | Quote |
|---|---|---|---|---|---|
| Revenue | $35.1B | $37.5B | FY26 $160B+ | **🔼 full-year raised (prior $150B)** | ... |
| Gross margin | 75.0% | 75.5% | — | **➡️ unchanged** | ... |
| CapEx | — | — | CY26 $X00B | **🆕 first CY26 figure** | ... |

If management says raise / lower / reiterate, quote it.

#### B. Overview → Backlog / Demand / Capacity

- Total backlog: $XXB this quarter (prior $YYB) → **🔼 +X% QoQ**
- Visibility: locked into FY27 (prior: FY26 H2) → **🔼 +X quarters**
- Supply wording: "significantly short of supply" (prior: "short of supply") → **🔼 tighter**

#### C. Product → Demand / Industry Dynamics

Append under the product's last quarter (H4). In this quarter's Summarize, add a **vs prior quarter** line:

> **vs prior quarter**: 🔼 industry tone upgraded from "steady" to "accelerating adoption"; management used "structural shift" for the first time

If a product was discussed last quarter but not at all this quarter, still add its quarter heading with one line:

> **vs prior quarter**: ⚠️ management did not discuss this product's industry dynamics this quarter

#### D. Product → Customers

**Customer by customer.** For each customer **already seen last quarter**, add the change after its stage:

- **AWS**: now in **volume ramp 🔼**
  > "AWS is now ramping into volume production..."
  > **vs prior quarter**: was in qualification

If a customer named last quarter is **not mentioned at all** this quarter, add at the end of the product's Customers:

> ⚠️ **Customers not mentioned**: [Customer X] from last quarter does not appear in this transcript

#### E. Product → Order Book / Backlog

At the end of Summarize:

- Demand vs supply: "significantly short" (prior "short") → **🔼 tighter**
- Visibility: 4 quarters (prior 3) → **🔼 +1 quarter**
- Backlog: $XXB (prior $YYB) → **🔼 +X% QoQ**

### Product Summary Table

**The new table goes directly below the old one**, under its quarter heading. **No vs-prior column** - the tables side by side are the comparison. New rows may carry 🆕 after the product name. The user deletes old tables manually.

### Write procedure

1. Read the whole log; list existing quarters (H4 in Product Breakdown, H3 elsewhere).
2. Take the **most recent quarter** as the comparison baseline.
3. Draft this quarter, including all change marks; **classify every statement company-wide vs product first**.
4. **Never overwrite the whole file.** Insert blocks with targeted edits (insert-after-anchor or append):
   - most sections: insert `### {this quarter}` after the section's last quarter;
   - Product Breakdown (overview and products): insert `#### {this quarter}` (H4) after that block's last quarter.
5. Run the validator; fix every FAIL in the new quarter, then delete the backup:
   ```bash
   python scripts/check_earnings_log.py {TICKER}_Earnings.md --before {TICKER}_Earnings.backup.md
   ```
   (First run: `python scripts/check_earnings_log.py {TICKER}_Earnings.md`.) LEGACY lines are issues in old quarters - report them to the user once if useful, never fix them in place.
6. Re-read the new quarter once: nothing company-wide or multi-product filed under a single product.

---

## Rules

**MOST IMPORTANT: Do NOT hallucinate.** Content comes only from the transcript. Fetching the transcript itself (Step 0) is the only web access; do not look anything else up unless the user asks in a follow-up.

1. **Restraint**: no judgments without a basis; no "this is good for the stock".
2. **Fidelity**: translations are exact, not embellished; every number exactly right. "We're cautiously optimistic" is 审慎乐观, not 非常看好.
3. **Language**: see Conventions - request language for a new log, the existing file's language when appending.
4. **Scope attribution**: strictly company-wide > product. **Company-wide content (including multi-product application stories) goes in the overview at the top of Product Breakdown, never under a single product** - that would make readers misjudge one line's visibility.
5. **Fixed strings**: headings, quarter labels and the change legend are copied from this file, never paraphrased.

Final reminder: this log is **for investment decisions**, not company PR. Quotes make it checkable, translation makes it readable, structure makes it comparable - all three are required.
