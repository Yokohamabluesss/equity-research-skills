#!/usr/bin/env python3
"""
check_earnings_log.py - structural validator for {TICKER}_Earnings.md

The earnings-call-reader skill appends one quarter at a time to a single
long log. The two things that silently degrade such a log are (a) drift in
the heading skeleton - a quarter appended at the wrong level, a section
skipped, a label written three different ways - and (b) edits to old
quarters. This script checks both. It does NOT judge content quality.

Checks
  skeleton   title line, the six top-level sections in fixed order
  levels     quarters are H3 in normal sections, H4 under each product;
             product sub-sections are the three fixed H5s in fixed order
  overview   the company-wide overview block is the FIRST H3 under
             Product Breakdown
  labels     quarter headings use the canonical label "FY26 Q3"
  order      quarters are chronological and unique under every parent
  coverage   the latest quarter appears in every required section and under
             every product that was covered in the previous quarter
  deltas     in cross-quarter mode the latest Guidance block has a "vs prior
             quarter" column and change markers use the fixed legend
  append     with --before OLD.md: every line of the old file is still
             present, unchanged and in order (old quarters untouched)

Problems in older quarters are reported as LEGACY warnings (old content must
not be edited, so they are informational); problems in the latest quarter
are FAIL. Exit code 1 if any FAIL.

Usage
  python check_earnings_log.py FORM_Earnings.md
  python check_earnings_log.py FORM_Earnings.md --before FORM_Earnings.backup.md
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SECTIONS = [  # (id, regex for the H2 heading, required)
    ("tldr", r"^(TL;DR|速览)", True),
    ("guidance", r"^(Guidance|业绩展望)", True),
    ("drivers", r"^(Drivers of Profitability|当季盈利驱动因素)", True),
    ("products", r"^(Product Breakdown|分产品)", True),
    ("summary", r"^Product Summary Table", True),
    ("other", r"^Other", False),
]
OVERVIEW_RE = re.compile(r"^(Company-wide|整体)")
H5_ORDER = ["Demand / Industry Dynamics", "Order Book / Backlog", "Customers"]
OTHER_H4 = re.compile(r"^(Capacity|Pricing|Other Notable Points|自由发挥)")
CANON_Q = re.compile(r"^FY(\d{2}) Q([1-4])\b")
LOOSE_Q = [
    (re.compile(r"^Q([1-4]) ?FY ?(\d{2,4})\b"), 2, 1),
    (re.compile(r"^(\d{4}) ?Q([1-4])\b"), 1, 2),
    (re.compile(r"^FY ?(\d{4}) ?Q([1-4])\b"), 1, 2),
    (re.compile(r"^(\d{2})FYQ([1-4])\b"), 1, 2),
]
LEGEND = set("🔼🔽🆕📌") | {"➡️", "⚠️", "➡", "⚠"}
NEAR_MISS = {"⬆️": "🔼", "⬇️": "🔽", "🔺": "🔼", "🔻": "🔽", "↑": "🔼", "↓": "🔽", "✨": "🆕", "❗": "⚠️"}
VS_RE = re.compile(r"vs\.? ?(上季|prior|previous|last)", re.I)


class Node:
    def __init__(self, level, title, line):
        self.level, self.title, self.line = level, title, line
        self.children: list[Node] = []
        self.body: list[str] = []

    def text(self) -> str:
        return "\n".join(self.body + [c.text() for c in self.children])


def parse(md: str) -> Node:
    root = Node(0, "ROOT", 0)
    stack = [root]
    in_code = False
    for i, raw in enumerate(md.splitlines(), 1):
        if raw.strip().startswith("```"):
            in_code = not in_code
        m = None if in_code else re.match(r"^(#{1,6})\s+(.*?)\s*$", raw)
        if m:
            lvl = len(m.group(1))
            node = Node(lvl, m.group(2), i)
            while stack[-1].level >= lvl:
                stack.pop()
            stack[-1].children.append(node)
            stack.append(node)
        else:
            stack[-1].body.append(raw)
    return root


def qkey(title: str):
    """Return ((fy, q), canonical?) or (None, False)."""
    m = CANON_Q.match(title)
    if m:
        return (2000 + int(m.group(1)), int(m.group(2))), True
    for rx, gy, gq in LOOSE_Q:
        m = rx.match(title)
        if m:
            y = int(m.group(gy))
            return ((y + 2000 if y < 100 else y), int(m.group(gq))), False
    return None, False


def label(k) -> str:
    return f"FY{k[0] % 100:02d} Q{k[1]}"


class Report:
    def __init__(self, latest):
        self.latest = latest
        self.fail, self.warn, self.legacy = [], [], []

    def add(self, msg, quarter=None, hard=True):
        if quarter is not None and self.latest is not None and quarter < self.latest:
            self.legacy.append(msg)
        elif hard:
            self.fail.append(msg)
        else:
            self.warn.append(msg)


def check_quarter_children(parent: Node, lvl: int, rep: Report, where: str):
    keys = []
    last_q_idx = max([i for i, c in enumerate(parent.children) if qkey(c.title)[0]], default=-1)
    for idx, c in enumerate(parent.children):
        k, ok = qkey(c.title)
        if c.level != lvl or k is None:
            # a stray heading before the newest quarter heading belongs to old content
            owner = k if k else ((0, 0) if idx < last_q_idx else None)
            rep.add(f"line {c.line}: under '{where}' expected an H{lvl} quarter heading "
                    f"(e.g. 'FY26 Q3 (2026-05-06)'), found H{c.level} '{c.title[:50]}'",
                    quarter=owner)
            continue
        if not ok:
            rep.add(f"line {c.line}: non-canonical quarter label '{c.title[:40]}' -> use '{label(k)}'",
                    quarter=k, hard=False)
        keys.append((k, c))
    seq = [k for k, _ in keys]
    if seq != sorted(seq):
        rep.add(f"'{where}': quarters not in chronological order: {[label(k) for k in seq]}",
                quarter=max(seq) if seq else None)
    if len(seq) != len(set(seq)):
        rep.add(f"'{where}': duplicate quarter headings: {[label(k) for k in seq]}", quarter=max(seq))
    return keys


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--before", help="copy of the log taken BEFORE this run (append-only check)")
    a = ap.parse_args()
    md = Path(a.file).read_text(encoding="utf-8")
    root = parse(md)

    # latest quarter across the document
    all_keys = []

    def walk(n):
        k, _ = qkey(n.title)
        if k and n.level in (3, 4):
            all_keys.append(k)
        for c in n.children:
            walk(c)
    walk(root)
    latest = max(all_keys) if all_keys else None
    quarters = sorted(set(all_keys))
    rep = Report(latest)
    cross = len(quarters) >= 2
    prev = quarters[-2] if cross else None

    h1 = [c for c in root.children if c.level == 1]
    if not h1 or not re.search(r"Earnings Call Log", h1[0].title):
        rep.fail.append("first line must be '# {TICKER} Earnings Call Log'")
    doc = h1[0] if h1 else root

    # top-level sections
    h2 = [c for c in doc.children if c.level == 2]
    found = {}
    for sid, rx, _ in SECTIONS:
        for c in h2:
            if re.search(rx, c.title):
                found[sid] = c
                break
    for sid, rx, req in SECTIONS:
        if req and sid not in found:
            rep.fail.append(f"missing section matching '{rx.strip('^')}'")
    order = [h2.index(found[s]) for s, _, _ in SECTIONS if s in found]
    if order != sorted(order):
        rep.fail.append("top-level sections out of order; required: TL;DR, Guidance, Drivers, "
                        "Product Breakdown, Product Summary Table, Other")

    # normal sections: H3 = quarter
    for sid in ("tldr", "guidance", "drivers", "summary", "other"):
        if sid not in found:
            continue
        sec = found[sid]
        keys = check_quarter_children(sec, 3, rep, sec.title)
        ks = [k for k, _ in keys]
        if latest and sid != "other" and latest not in ks:
            rep.fail.append(f"'{sec.title}' has no {label(latest)} block")
        if sid == "other":
            for k, q in keys:
                for c in q.children:
                    if not OTHER_H4.match(c.title):
                        rep.add(f"line {c.line}: under Other/{label(k)} use H4 Capacity / Pricing / "
                                f"Other Notable Points, found '{c.title[:40]}'", quarter=k, hard=False)
        if sid == "guidance" and cross and latest in ks:
            blk = dict(keys)[latest].text()
            if not VS_RE.search(blk):
                rep.fail.append(f"Guidance/{label(latest)}: cross-quarter mode needs a 'vs prior quarter' column")

    # product breakdown
    if "products" in found:
        sec = found["products"]
        h3 = [c for c in sec.children if c.level == 3]
        if not h3 or not OVERVIEW_RE.match(h3[0].title):
            rep.fail.append("first H3 under Product Breakdown must be the company-wide overview "
                            "('### Company-wide Demand / Order Book / Capacity Overview')")
        for blk in h3:
            keys = check_quarter_children(blk, 4, rep, blk.title[:40])
            ks = [k for k, _ in keys]
            is_over = bool(OVERVIEW_RE.match(blk.title))
            if latest and (is_over and latest not in ks):
                rep.fail.append(f"overview block has no {label(latest)} sub-block")
            if latest and not is_over and prev in ks and latest not in ks:
                rep.fail.append(f"'{blk.title[:40]}' was covered in {label(prev)} but has no "
                                f"{label(latest)} block (write '⚠️ not mentioned this quarter' instead of skipping)")
            if is_over:
                continue
            for k, q in keys:
                subs = [c.title for c in q.children if c.level == 5]
                core = [s for s in subs if s in H5_ORDER]
                if core != [h for h in H5_ORDER if h in core] or len(core) < 3:
                    rep.add(f"line {q.line}: '{blk.title[:30]}/{label(k)}' needs H5 sections "
                            f"{H5_ORDER} in this order; found {subs}", quarter=k, hard=False)

    # latest-quarter content checks: change markers
    if cross and latest:
        latest_txt = []

        def collect(n):
            k, _ = qkey(n.title)
            if k == latest:
                latest_txt.append(n.text())
            else:
                for c in n.children:
                    collect(c)
        collect(doc)
        txt = "\n".join(latest_txt)
        for bad, good in NEAR_MISS.items():
            if bad in txt:
                rep.warn.append(f"{label(latest)}: change marker '{bad}' is not in the legend; use '{good}'")

    # append-only
    if a.before:
        old = Path(a.before).read_text(encoding="utf-8").splitlines()
        new = md.splitlines()
        j = 0
        for i, line in enumerate(old, 1):
            while j < len(new) and new[j] != line:
                j += 1
            if j == len(new):
                rep.fail.append(f"append-only violated: old line {i} is missing or was edited: {line[:80]!r}")
                break
            j += 1

    print(f"INFO  quarters found: {[label(k) for k in quarters]}  latest: {label(latest) if latest else '-'}  "
          f"mode: {'cross-quarter' if cross else 'single-quarter'}")
    for m in rep.legacy:
        print("LEGACY", m)
    for m in rep.warn:
        print("WARN  ", m)
    for m in rep.fail:
        print("FAIL  ", m)
    if rep.fail:
        return 1
    print("PASS   skeleton, levels, coverage" + (" and append-only" if a.before else "") + " OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
