# Mode 2: Value-Chain Mapping

## Goal

The user names a **value chain** (DCI / 800G modules / solid-state batteries / AI servers / HBM / SiC substrates ...); map the main players of every upstream / midstream / downstream segment.

**Chain completeness is the point** - especially upstream (equipment, materials, key components are easily missed). **1-2** main players per segment are enough; **don't pile them on**.

## Table schema

Fixed 10 columns, **order fixed**:

| # | Field (JSON key) | Content | Required |
|---|---|---|---|
| 1 | Chain level (`level`) | Upstream / Midstream / Downstream | ✓ |
| 2 | Segment (`segment`) | the specific segment ("Upstream - laser chips", "Midstream - module packaging") | ✓ |
| 3 | Company (`company`) | name | ✓ |
| 4 | Ticker (`ticker`) | with suffix | ✓ |
| 5 | Market (`market`) | A-share / HK / US / ADR | ✓ |
| 6 | Products in this segment (`seg_products`) | the company's products in this segment | ✓ |
| 7 | Position (`position`) | Tier 1 / Tier 2 / ⚠️ TBC (downstream customers: Demand side) | ✓ |
| 8 | Stage (`stage`) | Mass production / Sampling / R&D / Concept | ✓ |
| 9 | Attention (`attention`) | High / Medium / Low | ✓ |
| 10 | Notes (`notes`) | key customers, share, dual listings | ✓ |

## Upstream / midstream / downstream

| Level | Typical content |
|---|---|
| **Upstream** | raw materials / equipment / key chips / key components - what decides supply |
| **Midstream** | modules / packaging / integration - turning upstream into usable products |
| **Downstream** | application customers / system makers / integrators - what pulls demand |

**Rule: follow the money** - whoever upstream sells to is midstream; whoever midstream sells to is downstream. If one company spans several segments (Samsung in HBM upstream and NAND downstream), **list it in each relevant segment** with "same company" in Notes.

## Template (reference only; follow the actual industry)

### 800G optical-module chain

```
Upstream:
  ├─ Laser chips: EML / CW (Lumentum LITE / Yuanjie 688498.SH)
  ├─ Modulators: SiPh modulators (Coherent COHR / Everbright 688048.SH)
  ├─ Detectors: APD / PIN PD (Coherent / Sanan 600703.SH)
  ├─ Fiber arrays: FAU (TFC 300394.SZ / HGTECH 000988.SZ)
  ├─ Lenses / isolators: (Lante Optics 688127.SH)
  ├─ PCB: high-speed PCB (WUS 002463.SZ)
  ├─ MCU / DSP: DSP chips (Marvell MRVL / MaxLinear MXL)
Midstream:
  ├─ Module packaging: (Innolight 300308.SZ / Eoptolink 300502.SZ / Coherent COHR / Accelink 002281.SZ)
  ├─ COB / CoWoS processes: (HGTECH 000988.SZ)
Downstream:
  ├─ Switches / routers: (Arista ANET / Cisco CSCO / Ruijie 301165.SZ)
  ├─ AI servers / GPUs: (NVIDIA NVDA / AMD / Inspur 000977.SZ)
  └─ Cloud providers: (Amazon / Google / Meta / ByteDance / Alibaba)
```

Use it as a **checklist** - for every level ask "is a segment missing?"

## Search playbook

1. **Start from an existing chain map as the skeleton**: `{industry} value chain map / supply chain diagram`; `{产业链} 产业链 全景图`, `{产业链} 产业图谱` - **sell-side chain maps** (CITIC, CICC, Huatai, Shenwan) are the most reliable.
2. **Search each segment's leaders**: upstream is easiest to miss - search each upstream sub-segment explicitly ("laser chip leaders", "high-speed PCB CCL makers"); upstream equipment / material players are often in Taiwan, Japan or Europe - **don't look only at A-shares + US**.
3. **Cross-check from the customer side**: "where does this module maker buy its EML?" often reveals missing upstream players.

## Pitfalls

1. **Missing upstream segments**: DCI and AI-server chains have dozens of upstream sub-segments (materials, equipment, chips, components, connectors, power, cooling ...); the "unsexy" ones are missed (CCL, connectors, PMICs, heat sinks). **Self-check after mapping**: is every BOM category mapped to at least one company?
2. **Listing distributors**: some "concept stocks" are only agents or distributors - **list manufacturers, not agents**.
3. **Piling on leaders**: 1-2 per segment. If three really share a segment (Innolight, Eoptolink, HGTECH in modules), list three with the position difference.

## Example (DCI chain fragment)

| Chain level | Segment | Company | Ticker | Market | Products in this segment | Position | Stage | Attention | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Upstream | Laser chips (EML/CW) | Lumentum | LITE | US | 100G/200G EML | Tier 1 | Mass production | High | main supplier to NVDA / Innolight |
| Upstream | Laser chips (EML/CW) | Yuanjie 源杰科技 | 688498.SH | A-share | 25G/50G DFB, CW | Tier 2 | Mass production | Medium | domestic substitution leader |
| Upstream | High-speed PCB | WUS 沪电股份 | 002463.SZ | A-share | M6/M7-grade PCB | Tier 1 | Mass production | High | main NVDA, Broadcom supplier |
| Midstream | Coherent modules | Cisco / Acacia | CSCO | US | 400G ZR / ZR+ | Tier 1 | Mass production | High | mainstream for DCI coherent |
| Downstream | Cloud providers | Microsoft | MSFT | US | Azure WAN | Demand side | - | High | main buyer |
