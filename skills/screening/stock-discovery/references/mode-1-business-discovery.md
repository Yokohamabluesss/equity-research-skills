# Mode 1: Business Discovery

## Goal

The user names a **specific business** (big like "CPO" or "AI PCB", small like "FAU", "850nm VCSEL", "sulfide solid electrolyte"); find as many listed companies doing it as possible.

**Coverage breadth is the point** - better to find 3 extra and drop them than to miss one with a real business.

## Table schema

Fixed 9 columns, **order fixed** (the script enforces it):

| # | Field (JSON key) | Content | Required |
|---|---|---|---|
| 1 | Company (`company`) | Chinese / English name (both if available) | ✓ |
| 2 | Ticker (`ticker`) | with exchange suffix: `300308.SZ` / `LITE` / `9988.HK` | ✓ |
| 3 | Market (`market`) | A-share / HK / US / ADR | ✓ |
| 4 | Relevant products (`products`) | the company's specific products in this business (fine-grained: "FAU array", not "optical components") | ✓ |
| 5 | Position (`position`) | Tier 1 / Tier 2 / New entrant / ⚠️ TBC | ✓ |
| 6 | Stage (`stage`) | Mass production / Sampling / R&D / Concept | ✓ |
| 7 | Attention (`attention`) | High / Medium / Low | ✓ |
| 8 | Lagging (`lagging`) | 🐢 or empty (not lagging / not checked) | optional |
| 9 | Notes (`notes`) | key customers, source links, speculation notes, dual listings | ✓ |

### Hidden field: segment - strongly recommended

Business discovery nearly always spans several sub-segments (optical = EML / CW / DFB / FAU / SiPh / modules; Low-CTE CCL = laminate / silica / glass cloth / resin / copper foil). Add an optional `segment` to each row; the script renders a "segment × position" overview on the Summary sheet.

It is **not** one of the 9 main columns; **Summary only**.

- Keep segment names consistent ("spherical silica" vs "silica" are two buckets)
- Put each company in its **most important** segment (one row per company; don't copy it into several segments)
- 4-7 segments is best; more makes the overview fragmented

## Sorting (done by the script)

1. **Position**: Tier 1 > Tier 2 > New entrant > TBC
2. **Stage**: Mass production > Sampling > R&D > Concept
3. **Attention**: High > Medium > Low (low attention last within a tier, so "good business, nobody watching" names are easy to compare - a source of alpha)

## Search playbook

| Granularity | Query templates |
|---|---|
| **Big segment** (CPO, AI PCB, solid-state batteries) | `{business} value chain map`, `{业务} 产业链全景`, `{业务} 受益标的 券商`, `{业务} 国产替代` |
| **Specific product** (FAU, EML, sulfide electrolyte) | `{product} domestic suppliers`, `{产品} 国内厂商`, `{产品} 谁做`, `{产品} 招标 中标`, `{downstream KA} {product} supplier` |
| **New concept** (quantum computing, CXL) | `{concept} pure play stocks`, `{概念} 概念股 名单` - beware **hype riders**; verify real R&D investment |

## Pitfalls

1. **"Concept stock list" trap**: Baidu / Xueqiu "XX concept stock" lists include hype riders - verify each against announcements / annual reports. If a company only said on an investor platform "we are watching / studying XX" with no R&D or product plan disclosed, it is **Concept**, not R&D.
2. **Mixing product levels**: for "optical", don't list everything tagged optical. Split into specific products (modules? components? laser chips?), decide which one each company does, and say so in Relevant products.
3. **Missing Taiwan**: many key optical and semiconductor players are listed in Taiwan (LandMark, WIN Semiconductors, Luxnet, Episil ...). Unless excluded, **list key Taiwan players**, marked "Taiwan", with "drop if not needed".
4. **Similar names**: e.g. 亨通光电 600487.SH vs 亨通股份; several "长光" companies - always confirm by ticker.

## Example (CPO business discovery)

| Company | Ticker | Market | Relevant products | Position | Stage | Attention | Lagging | Notes |
|---|---|---|---|---|---|---|---|---|
| Innolight 中际旭创 | 300308.SZ | A-share | 800G/1.6T modules, CPO optical engine | Tier 1 | Mass production (modules) / R&D (CPO) | High | | main NVIDIA supplier |
| Lumentum | LITE | US | EML, CW laser (core CPO light source) | Tier 1 | Mass production | High | | NVDA, Coherent customers |
| TFC Optical 天孚通信 | 300394.SZ | A-share | FAU, TEC, isolators (CPO components) | Tier 2 (Tier 1 in FAU) | Mass production | Medium | 🐢 | YTD +5% vs CPO index +35%; FAU leader but seen as "non-core" |
