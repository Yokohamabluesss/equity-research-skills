#!/usr/bin/env python3
"""
check_digest.py - format lint for an earnings-digest output (EN or ZH).

The digest is short and judgment-heavy, so the failure modes are format
drift and "fake judgment". This checks what can be checked mechanically:

  - both block markers, in order (===Logic & Narrative=== / ===逻辑和叙事===,
    ===Earnings Call=== / ===财报会议===)
  - the three bracket labels, in order, before the numbered list; the
    "new narrative" line starts with 🆕 or says there is none
  - 3-5 numbered moat/logic items
  - every quarter header: ---FY26 Q4---{tag}--- with a tag from the fixed set
  - the five judged dimensions in fixed order, each starting with exactly one
    judgment mark (✅️ ⚠️ 🔻), then an unmarked "Other" numbered list
  - WARN if all five marks are ✅️ (no judgment was made)
  - WARN if the Financials line carries more than 6 numbers (dashboard copy)
  - WARN on buy/sell/price-target/cheap/expensive language

Usage:  python check_digest.py DIGEST.md      (or:  ... - < digest.txt)
Exit 1 on any FAIL.
"""
from __future__ import annotations

import re
import sys

MARKS = ("✅️", "✅", "⚠️", "⚠", "🔻")
LANG = {
    "en": {
        "logic": "===Logic & Narrative===", "call": "===Earnings Call===",
        "labels": ["[Core in one line]", "[Main growth driver]", "[New narrative]"],
        "dims": ["Financials", "Sub-industry", "Orders", "Customers", "Momentum"],
        "other": "Other:", "none": re.compile(r"no new", re.I),
        "tags": re.compile(r"^(Beat|In line|Miss)(·beat-raise)?$"),
    },
    "zh": {
        "logic": "===逻辑和叙事===", "call": "===财报会议===",
        "labels": ["【公司一句话核心】", "【增长主驱动】", "【新叙事】"],
        "dims": ["财务", "细分产业", "订单", "客户", "业绩节奏"],
        "other": "其他：", "none": re.compile(r"本季无新增"),
        "tags": re.compile(r"^(超预期|符合预期|不及预期)(·beat-raise)?$"),
    },
}
QHDR = re.compile(r"---\s*(FY\d{2} Q[1-4]|\d{2}FYQ[1-4])\s*---\s*(.+?)\s*---")
ADVICE = re.compile(r"买入|卖出|目标价|值得买|低估|高估|\b(buy|sell|hold) (rating|recommendation|the stock)\b|"
                    r"\bstrong buy\b|price target|undervalued|overvalued|\bcheap\b|\bexpensive\b", re.I)


def check_dims(lines: list, lang: str, q: str, bold: bool = True, other: str | None = None) -> tuple:
    """The five judged dimensions of one quarter block, then an unmarked Other list.

    Shared with investment-view (which copies this file): there the block is a
    tab-indented outline without bold, so bold=False and Other is a bare label."""
    L = LANG[lang]
    other = other or L["other"]
    fail, warn = [], []
    found, marks = [], []
    alt = "|".join(map(re.escape, MARKS))
    for dim in L["dims"]:
        if bold:
            rx = rf"^({alt})?\s*\*\*{re.escape(dim)}\*\*"
        else:
            rx = rf"^({alt})?\s*\**{re.escape(dim)}\**\s*(（[^）]*）|\([^)]*\))?\s*([：:]|$)"
        ln = next((l for l in lines if re.match(rx, l)), None)
        if ln is None:
            fail.append(f"{q}: missing dimension {'**' + dim + '**' if bold else dim}")
            continue
        found.append(lines.index(ln))
        m = next((mk for mk in MARKS if ln.startswith(mk)), None)
        if m is None:
            fail.append(f"{q}: {dim} has no judgment mark (✅️ / ⚠️ / 🔻)")
        else:
            marks.append(m.rstrip("️"))
        if dim == L["dims"][0]:
            nums = re.findall(r"[$¥]?\d+(?:\.\d+)?\s*(?:%|bps?|x|B|M|亿|pp)?", ln)
            if len(nums) > 6:
                warn.append(f"{q}: Financials line has {len(nums)} numbers - keep 2-4 anchors, "
                            f"express the rest as direction + degree")
    if found != sorted(found):
        fail.append(f"{q}: dimensions out of order: {' / '.join(L['dims'])}")
    if marks and all(m == "✅" for m in marks) and len(marks) == 5:
        warn.append(f"{q}: all five dimensions are ✅️ - re-check: a key amount no longer updated, a customer or "
                    f"metric that disappeared, a bottleneck that moved, an avoided supply question")
    oi = next((k for k, l in enumerate(lines) if l.startswith(other)), None)
    if oi is None:
        fail.append(f"{q}: missing '{other}' list")
    elif oi + 1 < len(lines) and lines[oi + 1].startswith(MARKS):
        fail.append(f"{q}: the Other list carries no judgment marks")
    return fail, warn


def advice_warnings(text: str) -> list:
    return [f"advice/valuation wording found: '{m}' - no buy/sell or cheap/expensive view"
            for m in sorted({x.group(0) for x in ADVICE.finditer(text)})]


def main() -> int:
    text = sys.stdin.read() if len(sys.argv) < 2 or sys.argv[1] == "-" else open(sys.argv[1], encoding="utf-8").read()
    lang = "zh" if "===逻辑和叙事===" in text or "===财报会议===" in text else "en"
    L = LANG[lang]
    fail, warn = [], []

    i_logic, i_call = text.find(L["logic"]), text.find(L["call"])
    if i_logic < 0:
        fail.append(f"missing block marker {L['logic']}")
    if i_call < 0:
        fail.append(f"missing block marker {L['call']}")
    if i_logic >= 0 and i_call >= 0 and i_logic > i_call:
        fail.append("logic block must come before the earnings-call block")
    logic = text[i_logic:i_call] if 0 <= i_logic < i_call else ""

    # labels
    pos = [logic.find(lb) for lb in L["labels"]]
    for lb, p in zip(L["labels"], pos):
        if p < 0:
            fail.append(f"missing label {lb}")
    if all(p >= 0 for p in pos) and pos != sorted(pos):
        fail.append("labels out of order: " + " → ".join(L["labels"]))
    nl = logic.find(L["labels"][2])
    if nl >= 0:
        line = logic[nl:].splitlines()[0]
        if "🆕" not in line and not L["none"].search(line):
            fail.append("new-narrative line must start with 🆕, or say explicitly that there is none")
    items = re.findall(r"^\s*(\d+)\.\s", logic, re.M)
    if not 3 <= len(items) <= 5:
        fail.append(f"logic block needs 3-5 numbered items, found {len(items)}")
    if all(p >= 0 for p in pos):
        first_item = re.search(r"^\s*1\.\s", logic, re.M)
        if first_item and first_item.start() < max(pos):
            fail.append("the three labels must come before the numbered items")

    # quarter blocks
    call = text[i_call:] if i_call >= 0 else ""
    heads = list(QHDR.finditer(call))
    if not heads:
        fail.append("no quarter header like ---FY26 Q4---{tag}--- after the earnings-call marker")
    for n, h in enumerate(heads):
        q, tag = h.group(1), h.group(2).strip()
        if not re.match(r"FY\d{2} Q[1-4]", q):
            warn.append(f"quarter label '{q}' - canonical form is 'FY26 Q4'")
        if not L["tags"].match(tag):
            fail.append(f"{q}: tag '{tag}' not in the fixed set")
        end = heads[n + 1].start() if n + 1 < len(heads) else len(call)
        block = call[h.end():end]
        lines = [l.strip() for l in block.splitlines() if l.strip()]
        f2, w2 = check_dims(lines, lang, q)
        fail += f2
        warn += w2

    warn += advice_warnings(text)

    for w in warn:
        print("WARN ", w)
    for f in fail:
        print("FAIL ", f)
    if fail:
        return 1
    print(f"PASS  digest format OK ({lang}, {len(heads)} quarter block(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
