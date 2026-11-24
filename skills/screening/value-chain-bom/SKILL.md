---
name: value-chain-bom
description: "Splits a value chain into 'value share by layer + the US / A-share companies in each layer', delivered as a multi-scenario, fully formula-linked xlsx model. Use when the user says 'value breakdown', 'BOM breakdown', 'split XX's value', 'XX value-chain shares', 'which layer is worth the most', 'split by segment with the companies', 'value chain breakdown', 'unit value', 'who captures the most', '价值量拆分', 'BOM 拆分', '哪一层最值钱', or turns a value-chain discussion into 'who makes the money here / what is each layer worth / which companies'. Works for any field (optical, solid-state batteries, AI servers, power semis, advanced packaging ...). Versus stock-discovery: that answers 'which companies do this' (breadth, no money); this answers 'what is each layer worth, what share, who earns it' (depth + quantitative, must be modelled)."
---

# Value Chain BOM

Splits a value chain into **"value share by layer × several scenarios × the companies in each layer"**, delivered as a fully formula-linked xlsx.

The workbook should answer three questions: **Which layer holds the money? Under what conditions does that share change? Whom can I own in each layer?**

## Conventions (fixed)

- **Language**: the request language. Sheet names are fixed per language (section 4): Chinese `1_价值量总表 … 7_来源`, English `1_Value Summary … 7_Sources`.
- **Check before delivery**: `python scripts/check_bom_xlsx.py FILE.xlsx` - LibreOffice recalculation, formula errors, text starting with `=`, unquoted cross-sheet references, sheet set and order, ≥3 scenarios, shares as formulas, the sources sheet's limitation line. Fix every FAIL.
- **File name / place**: `{RESEARCH_ROOT}/{field}_Value_Chain_BOM_{YYYYMMDD}.xlsx` (Chinese: `{赛道}_价值量拆分_标的图谱_{YYYYMMDD}.xlsx`).

---

## 1. The skill's core claims

> **A single-scenario value share is misleading.**

In the same chain, changing one hidden parameter can move the layer shares enormously. So this skill **always models several scenarios**, and requires finding that hidden parameter and making it an explicit, adjustable input.

The second claim:

> **A high value share ≠ worth owning. Supply structure is.**

A layer that is 1% of the BOM, but a duopoly, impossible for customers to build in-house and outside price deflation, may deserve more attention than a 70% layer with full competition. The workbook must make that comparison.

---

## 2. Workflow (six steps, in this order)

### Step 0: Define the scope

Ask (or state at the top) three things:

1. **What is counted and what isn't.** E.g. optical DCI usually counts optical connectivity only, not the switch ASIC or router; solid-state batteries usually count the cell BOM, not pack and BMS. **Without a clear scope the shares mean nothing.**
2. **The unit.** Per link / per device / per GWh / per vehicle / per rack - one unit for the whole workbook.
3. **Markets.** Default A-share + US; others (HK / Japan / Taiwan / unlisted) as reference, labelled.

### Step 1: Research first - don't rush into the model ⚠️

**This step should take more than half the time.** A model without facts is a beautifully formatted piece of scrap.

What to find, in priority order:

1. **ASP anchors** (most important) - a public data combination from which a unit price can be backed out:
   - `annual shipments of a category + annual revenue` → ASP - the hardest method
   - segment revenue in large companies' reports ÷ shipments
   - channel / list prices (channel prices carry a markup; large-customer contract prices can be half or less - say so)
2. **Technical parameters per layer** - the physical quantities that set the count (speed, capacity, loss, energy density, area, layers …)
3. **Topology / architecture factors** - how many really go into one unit (bidirectional? redundant? cascaded? node degree?). **This is the most common source of error**
4. **Market size per layer** - for the top-down cross-check
5. **Players and shares per layer** - supply concentration drives the later judgment

### Step 2: Find the "true variable" ⭐

The most valuable step.

**Method**: first compute the shares the most intuitive way, then ask - **if this differs from the version going around, which assumption differs?**

That assumption is usually the true variable.

> **Example**: the common version of optical DCI value shares is "coherent modules 65–80%, pumps 1–4%"; fully loaded, the model gives "modules 91%, pumps 0.6%". Both are right - the difference is **how many wavelengths are lit per fiber (fill rate)**. The common version implies 6–8 wavelengths; fully loaded is 32. **Fill rate is the true variable, not distance as people assume.**

Make it a **blue adjustable input** in the xlsx, with its own sensitivity sheet.

**Common types of true variable** (examples - don't force them):
- **fill rate / utilisation**: installed but not fully used
- **topology factor**: bidirectional, redundant, cascade levels, node degree
- **generation mix**: old and new specs sold together; shares move with the mix
- **one-off vs recurring**: some layers are a one-time investment, others scale with usage

### Step 3: Build the BOM model (at least 3 scenarios)

Choose scenarios **along the range of the true variable** - three points covering "conservative / typical / extreme".

Every layer's amount is written as:

```
layer amount = quantity formula × unit price
quantity formula = product of scenario parameters (its physical meaning must be obvious)
```

**Annotate the physical meaning of every quantity formula.** E.g. "4 amplifiers per fiber-pair terminal = 2 directions × (booster + preamp)" - miss one topology factor and the result is off by 2x.

### Step 4: Top-down cross-check

Check the bottom-up model against public market sizes:

```
a layer's addressable market ≈ layer unit price × industry annual quantity
```

If it doesn't fit, revisit the assumptions. **If it fits, write that down too** - it is an important endorsement of the model.

Also leave a **self-check cell**: e.g. "a part's share of system BOM" is an input assumption and can also be back-calculated from "part price × quantity ÷ system price". If the two diverge a lot, the ASP assumptions are internally inconsistent - flag it in the workbook rather than hiding it.

### Step 5: Attach companies to each layer

**Every layer is followed by companies** - what makes this different from ordinary industry research.

The summary sheet has "US companies / A-share companies" per layer; a separate sheet holds the detailed map:

| Company | Ticker | Market | Layer(s) | Product in this layer | Position in this layer | Stage | Evidence | Key evidence / notes |

Points:
- **A company can span several layers** - list them all ("③ pumps + ② EDFA + ⑤ DGE + ⑥ WSS"); that is important information in itself
- **Position is judged "in this layer", not company-wide.** A module leader may be tier-2 in coherent
- **If a layer has no A-share player, write "❌ None"** - don't blur it. The gap is a conclusion
- Upstream material / substrate companies: say **which downstream line they follow**, not just "benefits"

### Step 6: Build the xlsx and check it

Fixed structure in section 4, technical points in section 5. **Run `scripts/check_bom_xlsx.py` (it recalculates with LibreOffice) and get zero formula errors.**

---

## 3. Evidence tiers and the "same name, different thing" check (a reminder, not mandatory)

The most common failure in value-chain research is **treating a technically different product as exposure to the target field**. Such errors spread through self-media chain maps, often with very precise numbers (capacity, yield, customer lists) that look highly credible.

**Suggested evidence tier per company:**

| Tier | Meaning |
|---|---|
| ⭐⭐⭐ | announcements / annual-report text / official press releases / earnings calls |
| ⭐⭐ | official product pages / official exhibition releases / traceable sell-side deep dives |
| ⭐ | third-party compilations / self-media, not traceable to official sources |
| ❌ | disproved |

**When a claim has these features, check it against the annual report:**

- "the only domestic mass producer of XX", "one of three worldwide", "breaking the foreign monopoly"
- very precise but unsourced numbers (X0k units per month, X% yield, orders booked to a quarter)
- a customer list of famous names the company itself never disclosed

**"Same name, different thing" traps (cross-industry):**

| Trap | Example |
|---|---|
| same material, different grade | optical-grade lithium niobate wafers vs lithium tantalate for RF SAW - both "lithium" crystals, entirely different uses |
| same wavelength, different use | 980nm **telecom single-mode** pumps (EDFA) vs 976nm **industrial multi-mode** pumps (fiber lasers) |
| same device, different format | **coherent** CDM modulators (long-haul / DCI) vs **PAM-4** modulators (datacom / short reach) |
| same word, different layer | the module's "light source" (1310nm CW, the signal) vs the amplifier's "pump" (980nm, the energy) |
| upstream doesn't care about downstream | substrate / material makers serve both lines; volume follows **the line with more shipments**, not **the line with the hotter story** |

When assigning upstream material companies, compare **orders of magnitude**: if application A ships 200k units a year and B ships 12M, the material maker is essentially a B play even if A's unit price is 10x - **materials sell by wafer / weight, unrelated to downstream unit price**.

---

## 4. Fixed xlsx structure (7 sheets)

Sheet names are numbered so they sort.

| # | Chinese name | English name |
|---|---|---|
| 1 | `1_价值量总表` | `1_Value Summary` |
| 2 | `2_场景与BOM` | `2_Scenarios & BOM` |
| 3 | `3_真变量敏感性` | `3_True Variable` |
| 4 | `4_公司图谱` | `4_Company Map` |
| 5 | `5_关键层专页` | `5_Key Layer` |
| 6 | `6_市场规模交叉验证` | `6_Market Size Check` |
| 7 | `7_来源` | `7_Sources` |

### 1 Value Summary ⭐ main sheet

One table that answers everything. Columns:

| Layer | Core device | Scenario A % | Scenario B % | Scenario C % | Reference range | Check | US companies | A-share companies |

- **All shares are formulas** referencing the BOM sheet; changing an assumption recalculates
- **Split the largest layer further** (indent sub-layers with `　├` `　└`) - the companies are completely different. Deduct the sub-items in the total to avoid double counting
- Below the table: a **check block** - if the user or the market has a reference version, compare line by line with a verdict
- Below that: **scope notes** - which layers are excluded, why, and which companies they correspond to

### 2 Scenarios & BOM

- A: scenario parameters (blue, adjustable), each with unit and basis
- B: unit-price assumptions (blue, yellow fill), each with **low / mid / high + confidence + basis**
- C: BOM detail, three scenarios side by side, each row with "core device" and "calculation basis"
- D: helper metrics (quantities, capacity, unit value)
- E: if the main layer is split, the internal split ratios here (with a 100% total check)

### 3 True Variable sensitivity ⭐

Five points along the true variable, showing how each layer's share drifts.

**Show both "share" and "absolute amount"** - the most valuable observation is often "the share was diluted but the absolute amount did not change".

A "how to read it" paragraph below saying which number to watch.

### 4 Company Map

One row per company, fields as in Step 5. Grouped by layer, within a layer by evidence strength. Disproved companies **stay in the table** with a red fill - so the user sees they were handled.

### 5 Key Layer

For the layer most worth digging into (usually "low share but concentrated supply"):

- A: quantity, amount, share, unit value in the three scenarios
- B: **six-dimension comparison** - this layer vs the largest layer: supply concentration / can customers bypass it in-house / does it take part in price deflation / is it diluted by the true variable / current supply-demand / value share
- C: topic Q&A (the key questions the user asked)
- D: a one-sentence summary with a **ceiling note** (a low share caps the absolute revenue pool)

### 6 Market Size Check

Top-down sizes with derived rows (formulas). A "how to read it" note, flagging **third-party disagreements** (niche market reports often differ several-fold, usually because of whether an application is included).

### 7 Sources

The first row is the **main limitation statement**: which numbers have public sources, which are estimates, and where the workbook's value lies (usually "structure and relative relationships", not "absolute amounts").

Then every source, with its type.

---

## 5. Build notes (pitfalls already hit)

Write with `openpyxl`, recalculate with LibreOffice. Avoid:

### 1. Text cells must not start with `=`

Notes like "= channels × quantity × 2" are parsed as formulas → `#NAME?` or `#N/A` after recalculation. **Use `≡`, or write "equals …".** The checker flags these.

### 2. Cross-sheet references need the sheet prefix, quoted

`="C10/C20"` on another sheet points at **its own** C10. Write:

```python
"='2_Scenarios & BOM'!C10/'2_Scenarios & BOM'!C20"
```

Single quotes are required when a sheet name has spaces or starts with a digit - which all seven do. The checker flags unquoted references.

### 3. Don't mix column meanings

On one assumptions sheet, **scenario columns** (C = A, D = B, E = C) and **range columns** (C = mid, D = low, E = high) side by side are easy to mix up. **Keep scenario parameters and price assumptions in separate blocks, and comment which column a formula takes.**

### 4. Topology factors are easy to miss

Hand-check one scenario after writing the quantity formulas. Typical misses: bidirectional (one set per direction), both ends (transmit + receive), cascades (stages inside one device), node degree (mesh vs point-to-point).

### 5. Recalculation

`scripts/check_bom_xlsx.py` recalculates through LibreOffice (headless, its own profile, 200-second timeout) and replaces the file with the recalculated copy, so the delivered file carries cached values and anyone opening it sees numbers immediately.

### 6. Formatting

- Arial throughout
- **Blue = typed input, black = formula, green = cross-sheet reference**
- key assumptions yellow fill, key layer orange, disproved red, excluded grey
- amounts `$#,##0;($#,##0);-`, shares `0.0%` (**store fractions, not percentages**)
- long notes `wrap_text=True` with a `row_dimensions[r].height`

### 7. Output

See Conventions. Don't restate the table in chat - give three to five of the most counter-intuitive conclusions.

---

## 6. What to say on delivery

Only these; the rest stays in the workbook:

1. **The most counter-intuitive point** (usually "layer X's share is far lower / higher than expected")
2. **The true variable** and how the result moves with it
3. **If the user gave a reference model, the line-by-line check** - if it matches, say so and name its implied assumption
4. **Where the A-share / US gaps are**
5. **One limitation sentence**: which numbers have no public source

---

## Appendix: full reference case (optical scale-across)

Use this skeleton the first time.

**Scope**: optical-connectivity equipment BOM for one link; excludes switch ASIC / router and the fiber cable itself.

**True variables**: ① wavelengths lit per fiber (fill rate) ② number of spans. Distance itself is not a true variable.

**Three scenarios**:
- A campus high-bandwidth: 30km, 100 fiber pairs, 32 wavelengths, single span, C-band
- B metro IPoDWDM: 80km, 100 pairs, typical 8 wavelengths, single span, C-band
- C long-haul: 1,400km, 12 pairs, C+L full 73 wavelengths, 17 ILA sites

**Layers and shares**:

| Layer | A | B | C |
|---|---|---|---|
| ① coherent pluggable modules (incl. DSP / ITLA / modulator / TIA) | 91.0% | 71.6% | 49.3% |
| ② EDFA / Raman systems (excl. pumps) | 2.7% | 8.6% | 23.4% |
| ③ **pump lasers** | **0.57%** | **1.79%** | **15.4%** |
| ④ mux / demux passives | 1.7% | 5.4% | 0.8% |
| ⑤ OCM / DGE / OTDR monitoring | 2.3% | 7.3% | 1.2% |
| ⑥ WSS / OCS optical switching | 0% | 0% | 2.2% |
| ⑦ line-system chassis | 1.7% | 5.4% | 7.7% |

**ASP anchor**: from "2026 800ZR/ZR+ shipments >200k units, revenue >$1B" → module ASP ≈ $5,000. Other layers have no public ASP; ranges are estimates.

**Key observation**: as fill rate goes from 4 to 32 wavelengths, module share rises 55.7% → 91.0% and pump share falls 2.79% → 0.57%, but **the pump amount stays exactly $200,000**. The number of spans is the real lever on pump share (0 spans 2.8% → 35 spans 21%).

**Why the low-share pump layer gets its own sheet**: top five hold ~82% (a duopoly); no hyperscaler designs its own 980nm pump chips; EDFAs are provisioned per fiber, not per wavelength, so they sit outside speed-driven deflation; currently sold out with take-or-pay LTAs. **The only layer in the chain where all four hold at once.**

**A-share gaps**: coherent DSP, ITLA, TIA/Driver, pump chips - all four empty. The only hard foothold is the TFLN modulator layer.
