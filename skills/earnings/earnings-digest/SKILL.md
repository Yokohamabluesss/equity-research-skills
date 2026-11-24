---
name: earnings-digest
description: "Condenses a company's {TICKER}_Earnings.md (the detailed cross-quarter log written by earnings-call-reader) into a one-page investment digest with two fixed blocks: Logic & Narrative (mandatory [Core in one line] [Main growth driver] [New narrative] labels plus 3-5 durable moat points) and Earnings Call ---FY26 Q4---{Beat / In line / Miss}--- (Financials / Sub-industry / Orders / Customers / Momentum / Other, where the ✅️ ⚠️ 🔻 before each dimension is a JUDGMENT of that dimension, not a bullet). Financials focuses on trend, S-curve position, second derivative and degree words rather than piles of numbers; Sub-industry on management's view of each product's industry stage and supply-demand; Orders / Customers / Momentum on visibility, structural change and deltas. Use when the user says 'summarize this md', 'make a digest', 'logic and narrative', 'same format as the CIEN/LITE digest for XX', '做个速读', '逻辑和叙事', '财报会议速读', '浓缩版', or points at a {TICKER}_Earnings.md and wants a short investor summary."
---

# Earnings Digest (Logic & Narrative + Earnings Call)

Condenses a company's **existing `{TICKER}_Earnings.md`** (the detailed cross-quarter log from earnings-call-reader) into an **investor's one-page digest** with two fixed blocks: `===Logic & Narrative===` and `===Earnings Call===`. Goal: in 30 seconds the reader knows *why this company is worth anything* (logic) and *the few things that mattered on this call, and whether each dimension was good or not* (call).

## Position and hand-offs

- **Input**: one `{TICKER}_Earnings.md` (TL;DR / Guidance / Product Breakdown / Order Book / Customers for several quarters). If the user pasted a transcript and there is **no** log, suggest running earnings-call-reader first, or do a one-off digest in chat in this format.
- **This skill condenses and judges; it does not re-analyse.** Every fact must be traceable to the input log - no outside lookups or speculation (unless the user asks in a follow-up). But **judgment is one of this skill's outputs** - see "Judgment marks".
- **Next step**: investment-view uses this digest's logic & narrative as its Core and its call block as the starting point of a quarter block.
- **Versus earnings-call-reader**: that one "reads thick" (one quarter → long structured log); this one "reads thin and sets the tone" (long log → one page, with a good / concern / weakening verdict per dimension).

## Conventions (fixed)

- **Language**: the user's request language. When updating an existing digest file, keep that file's language. Labels, block markers and tags are fixed strings in both languages (template below) - never paraphrase them.
- **Quarter label**: `FY{YY} Q{n}`, the same label the call log uses (e.g. `FY26 Q4`).
- **Self-check script**: after drafting, save the draft and run `python scripts/check_digest.py draft.md` (or pipe it on stdin). Fix every FAIL; treat WARN as a prompt to re-check.

## Step 0: Scope (5 seconds)

- **Company**: from the file name `{TICKER}_Earnings.md` or context. If a company was just being discussed, use it - don't ask.
- **Quarters**: by default digest only the **latest quarter** in the Earnings Call block (Logic & Narrative is always a cross-quarter distillation).
  - "Compare the last N quarters" / "evolution" → multi-quarter mode: several `---{quarter}---` blocks, each with the delta versus the prior quarter emphasised in Momentum.
- **Output**: by default **in chat** (the user usually pastes it into their own notes). If they say "save it", write `{TICKER}_Digest.md` (English) or `{TICKER}_速读.md` (Chinese) in the same folder; if either file already exists, update that one.

---

## ⭐ Judgment marks (the emoji is a verdict, not a bullet)

**This is the most-misused part of the skill.** The emoji before each dimension is **not a checkbox and not decoration**: it is your **explicit verdict** on that dimension this quarter. One of three:

| Mark | Meaning | Use when |
|---|---|---|
| ✅️ | **good / positive this quarter** | almost all key signals in this dimension point up; no material counter-evidence |
| ⚠️ | **material concern or mixed signals** | good and bad coexist, or one negative signal could change the view (a key number stopped being updated, an important customer disappeared, a metric became vague) |
| 🔻 | **clearly weakening** | the main signals point down, or an inflection-level deterioration |

**Hard rules:**
1. **All five dimensions ✅️ is suspicious** - it means labels were stuck on, not judgments made. Most quarters have at least one or two ⚠️.
2. **The mark must be justified by its own text**: a ⚠️ must say what the concern is; a ✅️ must not be full of negatives.
3. **The verdict is on the quality of this quarter's signals in that dimension, not on the stock** - no buy/sell, no cheap/expensive.
4. "Other" carries no mark - plain numbered list.

---

## Output format (copy this skeleton exactly)

English:

```
===Logic & Narrative===

[Core in one line] <what the company is, which layer of the value chain, why it is hard to replace - one sentence, max two lines>
[Main growth driver] <the engine of this growth cycle: which demand curve, product, end market. Must answer "where does the money come from">
[New narrative] 🆕 <a second curve or identity shift that surfaced this/recent quarters and is not yet fully priced. If none: "No new narrative this quarter; still XXX" - that is information too>

1. <differentiation / moat>: <the biggest difference from peers + why it is structural and monetisable>
2. <first-to-market / generation lead>: <which generation / product it leads>
3. <structural demand-side or business-model logic>
(3-5 numbered items, only what is stable across quarters - moat, positioning, long-term story; not this quarter's news)

===Earnings Call=== ---FY{YY}Q{n}---{Beat / In line / Miss}---

{✅️|⚠️|🔻}**Financials**: <trend + S-curve position + second derivative + degree words; few numbers, more judgment>
{✅️|⚠️|🔻}**Sub-industry**: <management's view of each product/direction's industry stage and supply-demand - not the company's own growth numbers>
{✅️|⚠️|🔻}**Orders**: <total backlog / RPO + split + LTA coverage> <order signal per growth curve> <"real order" signals>
{✅️|⚠️|🔻}**Customers**: <hyperscaler changes + tier-2 cloud momentum + concentration + new wins + customers that disappeared>
{✅️|⚠️|🔻}**Momentum**: <versus the previous call: what accelerated / slipped / is new - ★ the key section, deltas only>
Other:
1. <where exactly supply is constrained, by product>
2. <multi-year TAM and its split (if given)>
3. <capacity / CapEx / pricing / one-offs / open legal or commercial matters>
```

Chinese (same structure, fixed strings):

```
===逻辑和叙事===

【公司一句话核心】…
【增长主驱动】…
【新叙事】🆕 …（若无：本季无新增，仍是 XXX）

1. …
2. …
3. …

===财报会议=== ---FY{YY} Q{n}---{超预期 / 符合预期 / 不及预期}---

{✅️|⚠️|🔻}**财务**：…
{✅️|⚠️|🔻}**细分产业**：…
{✅️|⚠️|🔻}**订单**：…
{✅️|⚠️|🔻}**客户**：…
{✅️|⚠️|🔻}**业绩节奏**：…
其他：
1. …
```

(The quarter in the header is written `FY26 Q4`, e.g. `---FY26 Q4---Beat·beat-raise---`.)

---

## How to fill each part (this sets the signal-to-noise ratio)

### Logic & Narrative - set the tone first, then expand

The three bracket labels are **mandatory** and come before the numbered items:

- **[Core in one line]**: "who is it, at which layer". A good one names the division of labour with adjacent layers (e.g. "doesn't make modules or systems; makes the PICs upstream of both"). **Not a company profile - a value-chain position.**
- **[Main growth driver]**: "where does this cycle's money come from". Tie it to a traceable demand curve (penetration of an end market, a product-generation upgrade, a customer group's CapEx). If a second synchronous curve exists (main product + companion part growing 1:1), name it.
- **[New narrative]**: "what the market may not have priced yet" - a second curve that surfaced recently, an identity shift (from "selling parts" to "selling integration"), a new business model. **If there truly is none, say so** - two quarters in a row with no new narrative is itself a signal.

The numbered items below still hold only **cross-quarter, durable** moat and long-term logic - not this quarter's news (that goes in Momentum).

### Financials - ⭐ capture the *derivative* and the *degree*, not the *numbers*

**This line's output is judgment, not data transfer.** Keep a few anchor numbers; express the rest as **direction + S-curve position + second derivative + degree words**.

**Four questions it must answer:**

1. **Is revenue accelerating or decelerating?** Full "beat + raise", or beat without raise / raise without beat?
2. **Where is the margin-% S-curve?** Steepest part / past the steepest point, rising more slowly / plateau.
3. **Where is the absolute-profit-$ S-curve?** ⭐ **Discuss it separately from margin - their inflections usually differ.**
4. **Has the ceiling (asymptote) moved?** Management raising or cutting its long-term margin target matters more than this quarter's margin.

**Internal method (compute it yourself; you don't have to write it all out):**
- Position **margin %** by the **series of QoQ margin increments**: widening or narrowing? E.g. +650 → +700 → +440 → +340 bps peaks at the 2nd point and then narrows → "past the steepest point, rising more slowly".
- Position **absolute profit $** by the **series of QoQ increments in operating / net profit**. While revenue is still climbing hard, absolute profit can keep accelerating even as margin slows.
- **The two curves**: margin usually tops out first (it hits the target GM / OM ceiling); profit inflects later (when revenue plateaus too).
- ⚠️ **Counter-lesson**: writing only "margin decelerating" gets read as "profit is peaking" - **wrong**. Always give the direction of absolute profit as well.

**Style (different from the other lines - follow it):**
- ✅ Right: "Gross and operating margin both **jumped sharply** this quarter; the flat quarter in between was seasonal, not a break in trend. QoQ increments in absolute profit are **getting bigger each quarter - second derivative positive, no inflection yet**. And management raised its own 2028 GM target: **the asymptote is moving up, not hitting a plateau**."
- ❌ Wrong: "GM 23.5→26.7→26.8→29.9% (QoQ +200→+320→+10→+320bp), OM 12.8→16.1→15.6→19.6% …" - **that is copying the dashboard, not a digest**.
- **Degree words are mandatory**: sharply / significantly / mildly / slightly / first-ever / record / second derivative positive / rising more slowly / plateaued.
- **Keep at most 2–4 anchor numbers** (usually: revenue and EPS against the guided range or the beat/miss size, this quarter's margin level and its step, the long-term target margin).
- **GAAP and non-GAAP separately**: the **composition and trend** of the gap matter more than its size (pure SBC, or acquisition one-offs too? narrowing or widening - and because the numerator shrank or the denominator grew?). A big GAAP one-off gets "does not affect non-GAAP / operations".
- **Name the one real deterioration** this quarter (tax-rate normalisation, FX, a one-off charge) and say whether it is permanent or one-time.

### Sub-industry - ⭐ capture *management's view of the industry*, not the company's own growth

**This line most easily turns into a product-revenue bulletin.** The right subject is **management's qualitative view of each product/direction's industry stage, adoption progress and supply-demand**. The company's growth numbers are only supporting evidence.

**For each product/direction:**

1. **How far along is the industry?** Technology validation / first commercial order / early adoption / accelerating substitution / substitution done, front moving on. ⭐ **The most valuable thing is a change in stage wording across quarters** - e.g. from "form factor X will dominate for a long time" to "the move to X is basically complete; the next frontier is…". Such upgrades matter more than any number - highlight them.
2. **What is supply-demand like?** Short of supply / size of the gap / sold out / visibility into which year / supply rising. And **has the bottleneck moved** (last quarter A, this quarter B)?
3. **Why can this line ramp (or not)?** The industry-side conditions (ecosystem compatibility, reliability concerns resolved, cost curve, adoption hurdles). **This "why" is worth more than "how much it grew"** - it decides how durable demand is.

**Also:**
- **Narrative → first order** ("first commercial order", "initial order", "first-to-market") - highlight it; it is the hardest evidence of industry progress.
- ⚠️ **Substitution vs addition**: if the new form *replaces* the old one (no added unit value), say so, or readers will assume it is incremental.
- **★ Don't compress a self-standing investment line into one phrase**: segments like scale-across, OCS, CPO/NPO, pump lasers get their own point **even if not the biggest news this quarter**. Test: if it is a moat / growth curve in Logic & Narrative, it needs its own coverage here and in Orders.
- **Call out the industry supply-demand gap**: if peers are expanding heavily and management declines to assess industry balance, that is this line's most important ⚠️.
- Optical / AI / data-center products get a little more detail; others briefly.

### Orders - capture *visibility* and *authenticity*; every growth curve gets its order signal

- Total backlog / RPO, hardware vs services/software split, how much ships in the next N months, LTA / long contracts coverage to which year.
- **★ One order signal per main line**: sold out / capacity multiple / share / LTA structure (take-or-pay, term, pricing lever) / first triple-digit quarter, etc. Don't stop at the total.
- "Real order" signals: customers pushing for earlier delivery, pulling long contracts forward - these show demand hardness better than backlog numbers.
- ⚠️ **A key amount that stops being updated is a major signal**: a contract / backlog figure repeatedly cited and then not updated for two quarters must be flagged - especially when management, asked directly, confirms "no update".
- ⚠️ **Separate capacity wording from order wording**: management often gives both a capacity multiple and a contract value; never mix them. "Spoken for" ≠ "booked" - keep such qualifiers verbatim.

### Customers - capture *structural change*

- Hyperscalers: added / share shifts / who dropped out of 10%+.
- Neoclouds / tier-2 clouds: momentum upgrades ("some have momentum" → "won the vast majority" - call out such jumps).
- New wins, sole source, sampling → qualification → volume progression; build-vs-buy customers crossing over from in-house to outsourcing.
- ⚠️ **Disappeared customers and disappeared metrics matter as much**: partners named last quarter all absent this quarter, or "X active customers" no longer repeated - list them; a common source of ⚠️.

### Momentum - ★ the most important line; deltas only

- Versus the previous call: what **accelerated** (timeline pulled in, volume raised), what **slipped / was cut**, what **appeared for the first time** (new product line / customer / narrative), whether the tightest supply point **moved**, which metric **changed its basis**.
- Mark each with 🔼 / 🔽 / 🆕 / ➡️ / ⚠️ / 📌.
- One sentence on where "the story changed" versus last quarter. If it basically didn't, write "no change except X" - that is information too.

### Other - key items outside the five dimensions (no judgment marks)

- Supply constraints by product.
- Multi-year TAM and split (if given).
- Capacity / CapEx pace, pricing mechanism, share count / one-offs, upgraded strategic wording, whether the long-term financial model has been beaten / raised.
- Open legal and commercial matters (litigation, disputes, regulation) and whether they are provisioned.

---

## Tag convention (`---{quarter}---{tag}---`)

- English: `Beat` / `In line` / `Miss`; Chinese: `超预期` / `符合预期` / `不及预期` - judged on actuals versus guidance and consensus.
- A rhythm suffix may be added: beat with consecutive raises → `Beat·beat-raise` (`超预期·beat-raise`).
- Unsure → neutral `In line`, and state the direction and size of the beat/miss objectively in Financials.
- ⚠️ **The header tag and the dimension marks are two different things**: a quarter can be a Beat with ⚠️ on Orders/Customers - good results and clean signals are not the same.

---

## Style rules

1. **Language** per Conventions; keep key English terms / product codes untranslated in a Chinese digest (Hyper-rail, EML, CW, pump laser, scale-across, multi-rail, 1.6T, OCS, CPO, NPO, ELS, LPO/LRO …).
2. **Numbers by line**:
   - **Financials**: 2–4 anchors + trend + degree words. **No increment series, no dashboard copy.**
   - **Sub-industry**: qualitative stage and supply-demand first; numbers as support.
   - **Orders / Customers / Momentum**: **numbers wherever possible** - "pump capacity 4x, ~70–80% share, 3-year take-or-pay", not "orders strong".
3. **Bold the key judgment and inflection words** (not just numbers).
4. **Restraint**: no buy/sell, no cheap/expensive, no outside speculation; faithful to the log; translations not inflated ("cautiously optimistic" ≠ "very bullish").
5. **Momentum always focuses on deltas** - never restate this quarter's static description.
6. **Marks must be real judgments** (see "Judgment marks") - all five ✅️ means check again.

---

## Mini example (fragment, to show tone and density)

```
===Logic & Narrative===

[Core in one line] A vertically integrated laser-chip supplier - no modules, no systems; it makes the InP chips upstream of both module and system makers: the "arms dealer" of optical networking.
[Main growth driver] AI is compute-constrained → optical interconnect demand is rigid; scale-out / scale-across / scale-up are all moving from copper to optics, and the company rides "every link needs my laser chip".
[New narrative] 🆕 From selling chips to selling modules: first NPO and ELS module orders landed - the company's first entry into in-rack scale-up on the system side.

1. Moat = InP capacity that can swing between EML and CW + subsea-grade reliability - capacity flexibility is itself the barrier.
2. Scale-across: the same story as the system vendor at a different layer - they sell multi-rail line systems, this company sells the pump laser + narrow-linewidth laser + WSS inside.
3. First-mover for exclusivity: years of joint development turned into 3-year take-or-pay LTAs - demand secured before capacity is built.

===Earnings Call=== ---FY26 Q4---Beat·beat-raise---

✅️**Financials**: Revenue above the top of guidance and EPS well above consensus - a full beat + raise. **The two S-curves have split and must be read separately**: **margin % is past its steepest point, rising more slowly** (quarterly increments have narrowed clearly from the peak; GM is basically at the long-term target), while **absolute profit is still accelerating** - QoQ increments in operating profit grow every quarter, second derivative positive, no inflection yet. ⭐ More important, **the asymptote is moving up**: management raised the operating-margin target at the $2B level by a notch, so margin is not hitting a plateau; the ceiling was lifted. GAAP shows a large one-off loss from converting the converts to equity - **no effect on non-GAAP or operations**, and it actually reduced debt.

⚠️**Sub-industry**: Demand overall is still "supply far short of demand", but **the bottleneck has moved** - last quarter the tightest was EML; this quarter management says high-power lasers are "even further behind than EML". ⚠️ The expansion timing has to be re-sequenced. **Scale-across is the most advanced**: from "narrative" to "several quarters of volume", with supply sold out - **substitution done, adoption accelerating**. 🆕 **NPO reached the edge of industrialisation** - first ELS module order this quarter, from story to first order; what lets it ramp is reuse of the existing ecosystem, which removed customers' serviceability concerns. 1.6T is shipping; the upgrade cycle is confirmed through CY27. ⚠️ But management did not assess industry supply-demand once peers' expansions land.

✅️**Orders**: Scale-across - pump capacity 4x over the next few quarters, ~70–80% share, several 3-year take-or-pay LTAs; OCS doubled Q3→Q4, Q1 includes the first triple-digit quarter, H2 CY26 tracking $400M; UHP ~$50M by end-CY26, first triple-digit quarter in fiscal Q3 FY27; first ELS order H2 CY27. Customers are chasing deliveries and asking to pull LTAs forward.

✅️**Customers**: The big OCS customer (previously in-house) → crosses over in early 2027 to make the company its first supplier, taking the vast majority; transceivers pulled by the lead tier-1 hyperscaler's custom AI cluster, 800G→1.6T; 🆕 several high-velocity NPO engagements.

✅️**Momentum**: Versus Q3 - 🆕 first NPO + ELS orders (in-rack scale-up reaches first order); ⚠️ tightest supply moved from EML to high-power lasers; 🔼 scale-across quantified (10 straight quarters of growth + pump 4x + 3-year take-or-pay); 🔼 CW moved from internal use to external supply, GM approaching EML's; 🔼 $1.25B milestone more than a quarter early, $2B-level OM model raised.

Other:
1. Tightest supply = high-power laser ("way behind") + pump (sold out); 🆕 additional long-term InP substrate agreement with AXT.
2. The long-term financial model has been beaten; new targets at the next OFC.
3. Convert-to-equity drove a large GAAP loss but cut debt by $1.1B; non-GAAP diluted shares 101.1M.
```

---

## Self-check (before output)

1. Run `scripts/check_digest.py` on the draft; fix all FAILs.
2. Are all three labels there? If there is no new narrative, does it say so honestly?
3. Is Financials still piling up increment series? Could half the numbers become degree words without losing information?
4. Does Financials discuss margin % and absolute profit $ separately, and say whether the asymptote moved?
5. Does Sub-industry describe **industry stage and supply-demand**, or a product-revenue bulletin? Does each point answer "why can it ramp"?
6. Are the marks real judgments? All ✅️? Is every ⚠️ justified in its text?
7. Is Momentum deltas only?
8. Any buy/sell or cheap/expensive language slipped in?

## After delivery

- In chat: end with one line offering to save it as `{TICKER}_Digest.md` (or `{TICKER}_速读.md`) or to expand a dimension.
- If writing a file: only create / overwrite the digest file. **Never modify the source `{TICKER}_Earnings.md`.**
