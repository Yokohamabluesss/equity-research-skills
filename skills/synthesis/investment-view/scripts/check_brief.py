#!/usr/bin/env python3
"""
check_brief.py - format lint for a valuation-brief note (EN or ZH).

Checks the fixed template:
  - title line "{TICKER} Valuation Brief (price $X, date)" / "{TICKER} 估值速读（股价 $X，日期）"
  - the three sections in order: Guidance / Assumptions / Conclusion (指引 / 假设 / 结论)
  - Conclusion covers the four required items, in order:
      1 revenue-path source + guidance coverage
      2 margin path
      3 valuation: FY cur PE + growth, FY+1 PE + growth, then PEG, then FCFF
        (or an explicit "FCFF not applicable")
      4 difference versus consensus
  - no cheap / expensive / buy / target-price wording outside a conditional sentence

Usage: python check_brief.py BRIEF.md     (or - for stdin). Exit 1 on FAIL.
"""
import re
import sys


def check(text: str, entry: bool = False, zh: bool | None = None) -> tuple:
    """Return (fail, warn). entry=True checks one dated estimate entry inside an
    investment view (no title line; investment-view copies this file)."""
    if zh is None:
        zh = "估值速读" in text or "结论" in text
    S = (["指引", "假设", "结论"] if zh else ["Guidance", "Assumptions", "Conclusion"])
    fail, warn = [], []
    first = text.strip().splitlines()[0] if text.strip() else ""
    if not entry:
        if zh and not re.match(r"^[A-Z0-9.]{1,10} 估值速读（股价 \$?[\d,.]+，.+）", first):
            fail.append("title must be '{TICKER} 估值速读（股价 $X，取价日期）'")
        if not zh and not re.match(r"^[A-Z0-9.]{1,10} Valuation Brief \(price \$?[\d,.]+, .+\)", first):
            fail.append("title must be '{TICKER} Valuation Brief (price $X, date)'")
    elif not re.search(r"\$\s?[\d,.]+", first):
        fail.append("entry line must carry the price used (e.g. '2026-10-09（股价 $312.62）')")
    lines = text.splitlines()
    idx = []
    for s_ in S:
        i = next((k for k, l in enumerate(lines) if l.strip() == s_), None)
        if i is None:
            fail.append(f"missing section line '{s_}'")
        idx.append(i)
    if None not in idx and idx != sorted(idx):
        fail.append("sections must be in order: " + " / ".join(S))
    concl = "\n".join(lines[idx[2] + 1:]) if idx[2] is not None else ""
    checks = [
        ("revenue-path source / coverage", r"覆盖率|指引锁定|目标反解|自建" if zh else r"coverage|guidance-locked|back-solved|own assumption"),
        ("margin path", r"利润率|毛利率" if zh else r"margin"),
        ("FY cur + FY+1 PE with EPS growth", r"FY\d{2}\s*PE.*\n?.*FY\d{2}\s*PE"),
        ("PEG", r"PEG"),
        ("FCFF reverse (or 'not applicable')", r"FCFF"),
        ("difference vs consensus", r"一致预期" if zh else r"consensus"),
    ]
    pos = []
    for name, rx in checks:
        m = re.search(rx, concl, re.I | re.S)
        if not m:
            fail.append(f"Conclusion is missing: {name}")
        else:
            pos.append(m.start())
    if len(pos) == len(checks):
        pe, peg, fcff = pos[2], pos[3], pos[4]
        if not pe < peg < fcff:
            fail.append("valuation order must be: two PE lines (with growth) -> PEG -> FCFF")
    bad = re.findall(r"(便宜|很贵|太贵|值得买|买入|目标价|\bcheap\b|\bexpensive\b|\bbuy\b|price target)", text, re.I)
    for b in sorted(set(bad)):
        warn.append(f"wording '{b}': rewrite as a condition ('to accept the price you need to believe ...')")
    return fail, warn


def main() -> int:
    text = sys.stdin.read() if len(sys.argv) < 2 or sys.argv[1] == "-" else open(sys.argv[1], encoding="utf-8").read()
    zh = "估值速读" in text
    fail, warn = check(text, zh=zh)
    for w in warn:
        print("WARN ", w)
    for f in fail:
        print("FAIL ", f)
    if fail:
        return 1
    print(f"PASS  brief format OK ({'zh' if zh else 'en'})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
