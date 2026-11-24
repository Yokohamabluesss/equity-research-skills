# Mode 3: List Screening

## Goal

The user gives a **company list** (OFC 2026 exhibitors, CES 2026 exhibitors, a broker's research list, an ETF's holdings) + a **business** ("optical communications", "AI compute"); classify every company on that business.

**Per-company classification is the point** - the list is the user's; this mode finds no new companies, it judges "relevance + position" for each one on the list.

## Input

The list may arrive as:

- **plain text** (CSV / one per line)
- **an attachment** (xlsx / pdf / txt - read it)
- **a URL** (an exhibitor page - fetch it)

**Lists can be long** (tens to hundreds) - **process all of them**, never sample. Over 200 companies: tell the user "the list has N companies, about X minutes - continue?"

## Table schema

Fixed 9 columns, **in the original list order** (not re-sorted - the order often means something, e.g. booth numbers):

| # | Field (JSON key) | Content | Required |
|---|---|---|---|
| 1 | No. (`no`) | original position in the list | ✓ |
| 2 | Company (`company`) | name | ✓ |
| 3 | Ticker (`ticker`) | with suffix; "Unlisted" if not listed | ✓ |
| 4 | Market (`market`) | A-share / HK / US / ADR / Unlisted / Private | ✓ |
| 5 | Relevance (`relevance`) | Yes / Partial / No / ⚠️ TBC | ✓ |
| 6 | Relevant products (`products`) | the company's products in this business; "-" if none | ✓ |
| 7 | Position (`position`) | Tier 1 / Tier 2 / New entrant / N/A (when not relevant) | ✓ |
| 8 | Stage (`stage`) | Mass production / Sampling / R&D / Concept / N/A | ✓ |
| 9 | Notes (`notes`) | key customers, why judged unrelated, sources | ✓ |

**No Attention or Lagging columns in mode 3** - not core when screening a list. If the user wants them later, do it separately.

## Relevance

| Label | Meaning |
|---|---|
| **Yes** | a clearly disclosed product / technology directly in the business, and a main part of that business's revenue |
| **Partial** | has related products, but a small part of its business (<20% or only as a supporting component) |
| **No** | main business does not overlap with the business |
| **⚠️ TBC** | not enough public information to judge |

## Process

1. **Read and normalise the list** (name + listed? + ticker); fill missing tickers with a web search.
2. **First pass**: scan each company's website / annual report for the keywords; mark Yes / No / Partial / TBC. **Don't** judge position yet.
3. **Dig into Yes and Partial**: specific products; downstream customer clues (they decide position); stage.
4. **One more search for TBC**: if still unclear, **keep "⚠️ TBC"** - don't force a verdict.
5. **One-line note for No**: "main business is XXX, unrelated to {business}", so the user can review it.

## Pitfalls

1. **Misled by the exhibition** - exhibitions mix businesses (OFC has datacom modules, coherent and PON); attending OFC does not make a company a "datacom module" maker. Look at its products.
2. **Distributors** - exhibitors include agents (e.g. "test-equipment agents"); they are **not manufacturers**. Judge relevance on manufacturing only.
3. **Large companies showing one line** - Samsung / Sony at an optical show may show one niche product; that doesn't make them "optical companies". Note "related products are X% of the company's business".
4. **Not found still gets a row** - never skip a company for lack of information. "⚠️ TBC" is a valid signal to check later.

## Example (OFC 2026 exhibitors × optical communications)

| No. | Company | Ticker | Market | Relevance | Relevant products | Position | Stage | Notes |
|---|---|---|---|---|---|---|---|---|
| 1 | Innolight 中际旭创 | 300308.SZ | A-share | Yes | 800G/1.6T modules | Tier 1 | Mass production | main NVDA supplier |
| 2 | TFC Optical 天孚通信 | 300394.SZ | A-share | Yes | FAU, TEC, isolators | Tier 1 (FAU) | Mass production | main CPO component supplier |
| 3 | Lumentum | LITE | US | Yes | EML, CW laser | Tier 1 | Mass production | core datacom component |
| 4 | Huawei | Unlisted | Private | Yes | modules, coherent, PON | Tier 1 | Mass production | private, not investable |
| 5 | Acme Test Co. | Unlisted | Private | Partial | optical test equipment | N/A | Mass production | equipment, not a component maker |
| 6 | XYZ Industrial | XYZ | US | No | - | N/A | N/A | industrial lasers; unrelated to datacom |
| 7 | Some Korean Co. | 005930.KS | Korea | ⚠️ TBC | no optical business disclosed | - | - | manual review suggested |

**Note**: unlisted and foreign companies on the list stay in the table - every name the user gave gets an answer.
