#!/usr/bin/env python3
"""
check_view.py - structural lint for an investment-view file
({TICKER}_投资判断.md or {TICKER}_Investment_View.md; the older names
{TICKER}_财报前瞻判断.md / {TICKER}_Company_View.md are read the same way).

Checks
  blocks     # 核心 first; quarter blocks; # ---其他会议---; # ---测算---; # 其他说明 -
             in that order (English labels accepted too)
  core       has 增长主驱动 and 新叙事 (Main growth drivers / New narrative)
  quarters   canonical label "FY26 Q2", newest first, no duplicates
  latest     the newest quarter block has: a tag from the fixed set, 下一季超预期点,
             判断：; the five dimensions and Other are checked with
             earnings-digest's check_dims (copied here as check_digest.py);
             WARN on prose-length lines
  dated      entries in Other Events / Estimates dated YYYY-MM-DD, newest first;
             the newest estimate entry is checked with valuation-brief's check
             (copied here as check_brief.py)
  append     with --before OLD: every old line is still present, in order

Old-format issues in older entries (e.g. "26FYQ2", "9/7") are LEGACY warnings.
Usage: python check_view.py FILE [--before OLD]      Exit 1 on FAIL.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:  # shared with earnings-digest and valuation-brief; synced by tools/build.py
    import check_digest
    import check_brief
except ImportError:  # pragma: no cover
    check_digest = check_brief = None

MARK = r"(✅️|✅|⚠️|⚠|🔻)"
L = {
    "zh": dict(core="核心", ev="其他会议", est="测算", notes="其他说明", drivers="增长主驱动", narr="新叙事",
               up=r"^(下一季超预期点|⭐️?下次超预期点)", verdict=r"^判断[：:]",
               dims=["财务", "细分产业", "订单", "客户", "业绩节奏"], tags=["超预期", "符合预期", "不及预期"],
               parts=["指引", "假设", "结论"]),
    "en": dict(core="Core", ev="Other Events", est="Estimates", notes="Other Notes", drivers="Main growth drivers",
               narr="New narrative", up=r"^Next-quarter upside drivers", verdict=r"^Verdict:",
               dims=["Financials", "Sub-industry", "Orders", "Customers", "Momentum"], tags=["Beat", "In line", "Miss"],
               parts=["Guidance", "Assumptions", "Conclusion"]),
}
QH = re.compile(r"^#\s*---\s*(FY(\d{2}) ?Q([1-4])|(\d{2})FYQ([1-4]))\s*---\s*(.*)$")
DATE_CANON = re.compile(r"^(\d{4})-(\d{2})-(\d{2})\b")
DATE_LOOSE = re.compile(r"^(\d{1,2})/(\d{1,2})\b")


def blocks(lines):
    out, cur = [], None
    for i, l in enumerate(lines):
        if l.startswith("# "):
            cur = {"head": l.strip(), "line": i + 1, "body": []}
            out.append(cur)
        elif cur is not None:
            cur["body"].append(l)
    return out


def kind(head, T):
    if QH.match(head):
        return "quarter"
    h = head.lstrip("# ").strip("- ").strip()
    for k in ("core", "ev", "est", "notes"):
        if h.startswith(T[k]):
            return k
    return "other"


def qkey(head):
    m = QH.match(head)
    if m.group(2):
        return (int(m.group(2)), int(m.group(3))), True, m.group(6).strip()
    return (int(m.group(4)), int(m.group(5))), False, m.group(6).strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--before")
    a = ap.parse_args()
    text = Path(a.file).read_text(encoding="utf-8")
    lines = text.splitlines()
    lang = "zh" if re.search(r"^#\s*核心", text, re.M) else "en"
    T = L[lang]
    fail, warn, legacy = [], [], []
    bl = blocks(lines)
    kinds = [kind(b["head"], T) for b in bl]

    if not kinds or kinds[0] != "core":
        fail.append(f"the first block must be '# {T['core']}'")
    rank = {"core": 0, "quarter": 1, "ev": 2, "est": 3, "notes": 4}
    seq = [rank[k] for k in kinds if k in rank]
    if seq != sorted(seq):
        fail.append(f"block order must be: {T['core']} → quarters → {T['ev']} → {T['est']} → {T['notes']}")

    core = next((b for b in bl if kind(b["head"], T) == "core"), None)
    if core:
        body = "\n".join(core["body"])
        for k in ("drivers", "narr"):
            if not re.search(rf"^{re.escape(T[k])}", body, re.M):
                fail.append(f"Core has no '{T[k]}' line")

    qs = [b for b in bl if kind(b["head"], T) == "quarter"]
    keys = []
    for b in qs:
        k, canon, tag = qkey(b["head"])
        keys.append(k)
        if not canon:
            (fail if b is qs[0] else legacy).append(f"line {b['line']}: quarter label - use '# ---FY{k[0]:02d} Q{k[1]}--- …'")
    if keys != sorted(keys, reverse=True):
        fail.append("quarter blocks must be newest first")
    if len(keys) != len(set(keys)):
        fail.append("duplicate quarter blocks")

    if qs:
        b = qs[0]
        k, _, tag = qkey(b["head"])
        if not any(tag.startswith(t) for t in T["tags"]):
            fail.append(f"latest quarter FY{k[0]:02d} Q{k[1]}: header needs a tag from {T['tags']} then a stage phrase")
        body = [l.rstrip() for l in b["body"]]
        flat = [l.strip() for l in body if l.strip()]
        if not any(re.match(T["up"], l) for l in flat):
            fail.append(f"latest quarter: missing '{T['up'].strip('^()').split('|')[0]}'")
        elif any(re.match(r"^⭐️?下次超预期点", l) for l in flat):
            warn.append("latest quarter: use the label '下一季超预期点'")
        if not any(re.match(T["verdict"], l) for l in flat):
            fail.append(f"latest quarter: missing the overall verdict line ('{T['verdict'].strip('^[：:]')}…')")
        if check_digest is None:
            fail.append("check_digest.py missing next to check_view.py - run tools/build.py")
        else:
            f2, w2 = check_digest.check_dims(flat, lang, "latest quarter", bold=False,
                                             other="其他" if lang == "zh" else "Other")
            fail += f2
            warn += w2
        long_lines = [l for l in flat if not l.startswith("|") and len(l) > 110]
        if long_lines:
            warn.append(f"latest quarter: {len(long_lines)} line(s) over 110 characters - split into an outline")

    for sec in ("ev", "est"):
        b = next((x for x in bl if kind(x["head"], T) == sec), None)
        if not b:
            continue
        entries = []
        for i, l in enumerate(b["body"]):
            if l and not l[0].isspace() and l.strip():
                s = l.strip()
                if DATE_CANON.match(s):
                    entries.append((tuple(map(int, DATE_CANON.match(s).groups())), i, True))
                elif DATE_LOOSE.match(s):
                    entries.append((None, i, False))
        if not entries:
            (fail if sec == "est" else warn).append(f"'{T[sec]}': no dated entry (YYYY-MM-DD)")
            continue
        for n, (d, i, canon) in enumerate(entries):
            if not canon:
                (fail if n == 0 else legacy).append(f"'{T[sec]}' entry at line {b['line'] + i + 1}: date must be YYYY-MM-DD")
        dated = [d for d, _, c in entries if c]
        if dated != sorted(dated, reverse=True):
            fail.append(f"'{T[sec]}': entries must be newest first")
        if sec == "est":
            start = entries[0][1]
            end = entries[1][1] if len(entries) > 1 else len(b["body"])
            if check_brief is None:
                fail.append("check_brief.py missing next to check_view.py - run tools/build.py")
            else:
                f2, w2 = check_brief.check("\n".join(b["body"][start:end]), entry=True, zh=(lang == "zh"))
                fail += [f"newest estimate: {x}" for x in f2]
                warn += [f"newest estimate: {x}" for x in w2]

    if a.before:
        old = Path(a.before).read_text(encoding="utf-8").splitlines()
        j = 0
        for i, line in enumerate(old, 1):
            while j < len(lines) and lines[j] != line:
                j += 1
            if j == len(lines):
                fail.append(f"append-only violated: old line {i} missing or edited: {line[:70]!r}")
                break
            j += 1

    for m in legacy:
        print("LEGACY", m)
    for m in warn:
        print("WARN  ", m)
    for m in fail:
        print("FAIL  ", m)
    if fail:
        return 1
    print(f"PASS   investment view OK ({len(qs)} quarter block(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
