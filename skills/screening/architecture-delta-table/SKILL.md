---
name: architecture-delta-table
description: "Builds a segment delta table for a technology-route / architecture migration: for a baseline architecture and 1-N new routes, judges each segment per route as net-new, clear increase, shift, internal offset, decrease, unconfirmed or not applicable; lists US and A-share beneficiaries per segment, each verified against original disclosures; outputs a three-sheet xlsx. Use when the user asks where XX's increment is versus YY, which segments grow or shrink after switching to XX, who wins and who loses, which companies offset internally, to compare routes A and B by segment, or says 'make a delta table', '环节增减量', '谁受益谁受损'. Typical: pluggable → NPO/CPO, air → liquid cooling, liquid → solid-state batteries, HDD → SSD, copper → optical, conventional → advanced packaging. Versus value-chain-bom (what each layer is worth, one architecture) and stock-discovery (who does a business): this judges the direction of change per segment across architectures."
---

# Architecture-Migration Segment Delta Table

## What the table answers

The question most often answered wrong in investment research is "who benefits from the new architecture". The intuitive answer is "whoever makes the new thing", but the real structure is more complicated:

- some segments are **net-new** - the position does not exist in the old architecture; suppliers carry no legacy
- some look incremental but are really a **shift** - the total is unchanged, only the location or form moves (the most common false positive)
- some companies **offset internally** - they lose one piece and win another; the net is close to neutral, not simply a positive
- some segments go **in opposite directions on different new routes** - backing route A means no benefit, backing route B makes it a core increment: the real choice an investor has to make

The table's value is separating these four cases. A good table lets the user point to **the rows that are route-exclusive and the companies that are pure beneficiaries with no internal offset**.

## Conventions (fixed)

- **Build with the script**: `python scripts/build_delta_xlsx.py input.json output.xlsx`. Don't hand-write openpyxl. The script asserts the verdict labels, colours, widths, freeze panes, filters, and prints the rows where the routes disagree and the truly opposite rows.
- **Language**: `"lang": "en"` or `"zh"` in the JSON, following the request. Verdicts may be given in either language; the output uses one.
- **File name**: `{baseline}_to_{routeA}_{routeB}_Segment_Delta_{YYYYMMDD}.xlsx` (Chinese: `{基准架构}到{路线A}_{路线B}_环节增减量_{YYYYMMDD}.xlsx`) in the user's stocks folder (`{RESEARCH_ROOT}/stocks/`). A revision never overwrites the old file - use the date; how the conclusions evolve is itself valuable.

## Step 1: Fix the baseline and the routes

Three things, all required:

1. **Baseline architecture** (the old one being replaced) - every delta is relative to it
2. **New routes** - 2 by default, 1 or 3+ supported. If the user names one, ask whether there are parallel routes; most migrations have more than one (pluggable → LPO / NPO / CPO, liquid → semi-solid / all-solid, cold plate → immersion)
3. **Reference system or scenario** - without a concrete system the quantities can't be judged. "NVIDIA Quantum-X Photonics Q3450-LD, 115.2 Tb/s, 144 × 800G" is far more useful than "a CPO switch"

No reference system given → search for a representative product with public specs and state it in the header (`basis`).

## Step 2: List the segments - mainly, don't miss any

Walk the **signal chain / energy chain / material chain** end to end, not only the "stars". Ask of each of these nine categories: "does this migration touch it?"

| Category | Why it gets missed |
|---|---|
| 1. Core functional devices | won't be missed - the stars |
| 2. Upstream materials and substrates | furthest upstream, least supply-elastic; often the one segment with a physical ceiling |
| 3. **Manufacturing equipment and processes** | **most often missed entirely** - a new architecture often brings a whole new process; equipment makers are net-new beneficiaries with very concentrated share, but they are not in the BOM |
| 4. Packaging and integration | the migration is usually a change in integration, so almost always moves |
| 5. Connectors and structural parts | a new form means new part numbers; often more concentrated globally than the main segment |
| 6. **Test and yield** | non-reworkable architectures push test earlier; demand naturally leads device shipments - a good leading indicator |
| 7. Thermal, power, mechanical | inevitable with higher density |
| 8. Software / control / algorithm chips | some migrations **eliminate** a whole chip class (e.g. removing the DSP) - the most certain decrease |
| 9. Assembly and foundry | the hot spot for internal offsets or decreases; don't forget it |

Start with 20-30 rows; better too many. Deleting empty rows is easier than adding missed ones later.

### Optical: pluggable → NPO / CPO / LPO (checked against real disclosures; a starting list)

**Optical engine and chips**: SiPh engine PIC | modulators (EML direct / SiPh MZM / micro-ring MRM / TFLN) | Driver/TIA | DSP (**removing the DSP is the most certain decrease**) | retimer | switch ASIC
**Light source**: CW laser chips (a different product from EML - don't mix) | ELSFP external laser module | ELSFP connector and cage (**separate from the light-source module itself; very easy to miss**) | micro TEC
**Passive optics**: FAU fiber array | micro-lens arrays / coupling optics | AWG / mux-demux (WDM may be integrated into the PIC - discrete demand questionable) | MPO / MT ferrules | shuffle box | PM fiber harness | isolators (core material: Faraday rotator / TGG)
**Substrate and board**: package substrate | PCB high-speed copper traces (decrease) | high-speed electrical connectors (board-to-board / package socket / optical backplane / blind-mate)
**Equipment, materials, test**: InP substrate | hybrid-bonding equipment (**CPO needs it, NPO doesn't - a typical route-exclusive point**) | fiber coupling / alignment equipment | PIC wafer test KGD | thermal / liquid cooling
**Replaced**: pluggable module housing / assembly

Optical specifics: MPO is usually a shift, not an increase (total port count unchanged); the real increment is PM MPO and shuffle boxes | EML belongs to pluggables, CW to CPO/NPO; they share InP capacity, so they compete for it while demand moves in opposite directions | under CPO much value lands inside the foundry ecosystem (TSMC COUPE covers PIC + EIC + hybrid bonding); under NPO the optical engine stays a detachable module at the system maker | "X is NPO-only" needs verifying - connector makers often sell both routes side by side.

### Starting lists for other fields

- **Air → liquid cooling**: cold plates / CDU / quick disconnects (UQD) / piping / coolant / leak detection / rack retrofit / **power-distribution retrofit** (often missed) | fans and heat pipes (decrease). UQD is the tightest, highest-value segment for cold plates and barely needed for immersion - backing UQD means backing cold plates.
- **Liquid Li-ion → semi / all-solid-state**: electrolyte (oxide / sulfide / polymer - route-exclusive) / lithium-metal anode / **dry-electrode equipment** / isostatic presses / **ultra-low-dew-point dry rooms** / separator (may disappear in all-solid) / electrolyte and LiPF6 (decrease) / **electrolyte-filling stations disappear** (back-end equipment decrease; the market talks only about front-end)
- **Conventional → advanced packaging**: interposer / TSV equipment / hybrid bonding / temporary bond-debond / substrate / underfill / **KGD test moved earlier** / warpage and thermal | wire bonding (decrease)
- **HDD → SSD**: NAND / controller / DRAM cache / interface protocols | heads and platters, spindle motors (decrease) | **server backplanes and cabling change form** (often missed)
- **Copper → optical interconnect**: optical engine / fiber / connectors / light source | DAC and AEC (decrease - note AEC makers' internal offsets) | high-speed copper connectors (decrease)

## Step 3: Judge each segment for each route

**Judge each new route independently** - never merge. Two routes with the same verdict still can't be merged into one write-up: attribution may differ completely (both "clear increase", but on one route the value goes to the foundry, on the other it stays with the system maker).

Seven labels; use exactly one of these strings:

| English | Chinese | Meaning | Test |
|---|---|---|---|
| `⭐⭐ Net-new` | `⭐⭐ 纯新增` | the position does not exist in the old architecture | the most valuable tier; be strict - "more units" is not net-new |
| `⭐ Clear increase` | `⭐ 明显增量` | volume / unit price / technical bar clearly up | say whether volume, price or bar - the investment meaning differs |
| `○ Shift` | `○ 平移` | total roughly unchanged; location or form changes | the most common false positive |
| `⚠️ Internal offset` | `⚠️ 内部抵消` | the company gains and loses; net needs judgment | for **one company's** gains and losses across segments, not a property of a segment |
| `❌ Decrease` | `❌ 减量` | demand falls or disappears | list the companies on the losing side too - the avoid list |
| `❓ Unconfirmed` | `❓ 待证实` | design not public or evidence conflicts | use it honestly - better than guessing a direction |
| `⊘ Not applicable` | `⊘ 不适用` | the architecture clearly does not need it | distinct from Unconfirmed: one is known-not-needed, the other unknown |

**Use the strings exactly - no brackets with qualifiers.** Any condition ("WDM case", "route A only") goes into the note column. Why: the xlsx colours by exact match, and brackets cause **silent missing colour**; the auto-filter also needs clean labels. The script asserts this and stops on a wrong label.

**Four traps:**

1. **If the number of ports / units didn't change, it isn't an increase.** First ask "did the physical quantity of this segment change?"
2. **"X only" must be verified, not inferred.** When you find yourself writing "X-only", look for counter-examples (exhibition demos, side-by-side product pages, MSA documents).
3. **Separate total volume from unit price.** Some segments shrink in volume while unit price jumps several-fold - net up; the reverse also happens.
4. **Watch rows with "the same verdict but opposite attribution".** Colours don't show it; name them in the note and in the conclusions. Often the single most valuable row.

## Step 4: Fill in companies, each checked against original disclosures

**The most error-prone step and the clearest sign of quality.** US / overseas and A-share in **two columns**; every company followed by an evidence mark:

| Mark | Meaning | Acceptable sources |
|---|---|---|
| `★★★` | officially **states** the product is for this route | annual / interim reports, announcements, IR activity records, results briefings, product pages, press releases, call scripts and Q&A |
| `◆` | sell-side wording | **not official**, never on a par with ★★★ |
| `◇` | industry notes / expert calls | usable for volume/price estimates, not for route attribution |
| `○` | has the product but officially places it in **another market** | official source, but the qualifier points elsewhere |
| `△` | generic product description only, **no route wording** | official source without any qualifier |
| `⚠️` | counter-evidence, the company played it down, or inferred | clarification announcements, risk notes |

**Stage** too: ① revenue → ② volume deliveries → ③ pilot production → ④ sampling → ⑤ R&D project → ⑥ capability statement only → ⑦ ⚠️ officially played down / denied

### Three verification moves

**① Find the sentence with the route qualifier.** "Has the product" ≠ "the product is for this route" - two layers apart:

- **Different market** - real case: a company's AWG was put in a CPO table; its annual report says "arrayed waveguide gratings for **backbone and metro** DWDM systems", under **telecom products** → `○`, not `★★★`
- **Different spec tier** - real case: a company's fiber-array wording is only "fiber arrays widely used in optical devices", no CPO / high-channel / PM qualifier, while three peers have explicit wording; listing all four together misreads them as one tier → `△`

No sentence with a qualifier → downgrade; don't list it alongside as if equal.

**② Make sure the company said it.** On investor Q&A platforms, "Dear secretary, does the company make X?" is a **question**, not an answer. Real case: a company tagged "silicon lens in validation" - four consecutive IR records never mention silicon lenses; the term appears only in investors' questions, while the company's actual wording is about a different product in a different row. **The question was taken as wording, and its real row was missed.**

**③ Beware multi-step inference and self-media.** Stock forums, WeChat accounts, Xueqiu posts are never official. Most dangerous is multi-step inference: "A gave B a big order → C supplies B → so C benefits". Real case: a company widely said to have "entered NVIDIA's CPO supply chain, passed top-customer validation, 40% North American share" - its fresh interim report mentions "CPO" once, quoting a government policy document; the company itself says nothing about CPO; exports grew only +2.71% while all growth came from doubled domestic sales - **the story and the financials point opposite ways**.

**Good cross-check habit**: a real entry into a new supply chain usually leaves traces in revenue mix, contract liabilities or capacity investment. When story and financials disagree, trust the financials.

### Record the cold water the company pours on itself

Clarification announcements ("the information is untrue"), "no scaled products or revenue yet", "at the R&D and early-reserve stage", "less than 1% of revenue", **terminated** acquisitions or partnerships (withdraw any earlier judgment based on them) - put them in the note with `⚠️`. This is worth more than good news: scarce, and almost never reposted.

### Other traps

Renamed stock short names (searching the old name misses things - recheck) | product vs material names (one character can put a company in the wrong row) | a capability in one field cannot be extrapolated to another | verification expires (a new interim report or IR record can change the conclusion - date the table and recheck on revision) | if a segment truly has no A-share player, write "⚠️ No A-share company with this product wording" - an empty cell is information; better than forcing one.

**Self-check before output**: can I name the original source for every company in every cell? Did I take a question for an answer? Did I mark sell-side as ★★★? Any multi-step inference? Did I record the cold water? Empty segments - "none", or forced?

## Step 5: Build the xlsx

Organise the data as JSON (format at the top of `scripts/build_delta_xlsx.py`) and run:

```bash
python scripts/build_delta_xlsx.py delta.json "{RESEARCH_ROOT}/stocks/Pluggable_to_NPO_CPO_Segment_Delta_20260817.xlsx"
```

Three sheets: **① Segment Deltas** (main table, one verdict column per route), **② Key Conclusions**, **③ Legend** (both mark systems explained in separate blocks, with per-route counts - generated). The script's printout lists the disagreeing rows and the truly opposite rows; use them in Step 6.

## Step 6: Write the key conclusions

The conclusions are the soul of the table - not a restatement of it. Cover at least:

1. **Route-exclusive points** - rows where the routes go truly opposite ways (printed by the script). First item.
2. **Clusters of unconfirmed items** - if several rows are `❓` on one route, check whether they hinge on **the same open question**. If so, say it: once resolved, they flip together - the highest-value thing to check.
3. **Pure beneficiaries with no internal offset** - companies that both gain on the route and whose main business is not replaced, split US / A-share. The list the user wants most.
4. **Same verdict, opposite attribution** - see Step 3, trap 4.
5. **Corrections and additions in this version** - when revising, say what changed and why. A research table is valuable because it is traceable; never change silently.
6. **Evidence reminders** - which numbers are official, which estimated, which only from self-media. Add a list of "companies that officially named this route" - usually short and very useful.

## Common failure modes

- **Listing only increases, not decreases** - the losing side is the avoid list and often more certain
- **Marking every new-architecture company as a winner** - the internal-offset tier exists to prevent this; system and module makers usually win some and lose some
- **Missing equipment, materials and test** - not in the BOM, but often the most concentrated and offset-free
- **Brackets in labels** - missing colours and broken filters (the script now refuses them)
- **Filling companies from memory** - check every original source
- **Conclusions that restate the table** - give what the table doesn't show: exclusive points, clusters, the pure-beneficiary list
