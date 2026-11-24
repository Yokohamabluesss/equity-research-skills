#!/usr/bin/env python3
"""
status.py - what exists for one company, and what is behind.

Reads the files the other skills write in {RESEARCH_ROOT}/{TICKER}/ and reports:
  transcripts   quarters found in transcript files (header "Q3 FY2026" or name "TSEM 2026Q3")
  call log      latest quarter in {TICKER}_Earnings.md
  digest        latest quarter in {TICKER}_速读.md / _Digest.md
  financials    latest quarter in *_Financials_*Dashboard.xlsx
  valuation     "data as of" date and latest reported quarter in *_Valuation_Dashboard.xlsx
  view          latest quarter block and latest estimate date in the investment view
then one "suggested" workflow (A first coverage / B new quarter / C-E otherwise).

Usage: python status.py FOLDER [--ticker TSEM] [--json]      Python 3, standard library, no network.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path

Q = re.compile(r"FY(\d{2}) ?Q([1-4])")
VIEW_NAMES = ("_投资判断.md", "_Investment_View.md", "_财报前瞻判断.md", "_Company_View.md")


def qkey(m) -> tuple:
    return (int(m.group(1)), int(m.group(2)))


def label(k) -> str | None:
    return f"FY{k[0]:02d} Q{k[1]}" if k else None


def max_q(text: str, rx=Q):
    ks = [qkey(m) for m in rx.finditer(text)]
    return max(ks) if ks else None


def xlsx_strings(p: Path) -> list[str]:
    """Every text cell of a workbook as whole strings (rich-text runs joined, tags removed)."""
    try:
        with zipfile.ZipFile(p) as z:
            xml = [z.read(n).decode("utf-8", "ignore") for n in z.namelist()
                   if n == "xl/sharedStrings.xml" or n.startswith("xl/worksheets/sheet")]
    except (zipfile.BadZipFile, OSError):
        return []
    out = []
    for x in xml:
        for item in re.findall(r"<(?:si|is)>(.*?)</(?:si|is)>", x, re.S):
            out.append(re.sub(r"<[^>]+>", "", item))
    return out


def quarter_header(strings: list[str]):
    """Latest quarter among cells that are exactly a quarter label (column headers), not prose."""
    ks = [(int(m.group(1)), int(m.group(2))) for s in strings for m in [re.fullmatch(r"\s*FY(\d{2}) ?Q([1-4])\s*", s)] if m]
    return max(ks) if ks else None


def transcript_quarter(p: Path):
    head = p.read_text(encoding="utf-8", errors="ignore")[:400] if p.suffix in (".txt", ".md") else ""
    m = re.search(r"Q([1-4]) FY(\d{4})", head)
    if m:
        return (int(m.group(2)) % 100, int(m.group(1)))
    m = re.search(r"(\d{4}) ?Q([1-4])", p.stem)
    return (int(m.group(1)) % 100, int(m.group(2))) if m else None


def status(folder: Path, ticker: str | None = None) -> dict:
    t = ticker or folder.name
    out = {"ticker": t, "folder": str(folder), "exists": folder.is_dir()}
    if not folder.is_dir():
        out["suggested"] = "A. First coverage (no folder yet)"
        return out
    files = list(folder.iterdir())
    tq = [transcript_quarter(p) for p in files if p.suffix == ".txt"]
    tq = sorted({k for k in tq if k})
    out["transcripts"] = [label(k) for k in tq]
    log = folder / f"{t}_Earnings.md"
    out["call_log"] = label(max_q(log.read_text(encoding="utf-8"), re.compile(r"^#{3,4} FY(\d{2}) ?Q([1-4])", re.M))) if log.exists() else None
    dg = next((folder / f"{t}{s}" for s in ("_速读.md", "_Digest.md") if (folder / f"{t}{s}").exists()), None)
    out["digest"] = label(max_q(dg.read_text(encoding="utf-8"))) if dg else None
    fin = sorted(p for p in files if re.search(r"_Financials_.*Dashboard.*\.xlsx$", p.name))
    out["financials"] = label(quarter_header(xlsx_strings(fin[-1]))) if fin else None
    val = sorted(p for p in files if re.search(r"_Valuation_Dashboard.*\.xlsx$", p.name))
    out["valuation_date"] = out["valuation_quarter"] = None
    if val:
        vt = "\n".join(xlsx_strings(val[0]))
        m = re.search(r"(?:数据截止|data as of) (\d{4}-\d{2}-\d{2})", vt)
        out["valuation_date"] = m.group(1) if m else None
        m = re.search(r"(?:最新已披露财季|latest reported quarter) (\d{4})Q([1-4])", vt)
        out["valuation_quarter"] = f"FY{int(m.group(1)) % 100:02d} Q{m.group(2)}" if m else None
    view = next((folder / f"{t}{s}" for s in VIEW_NAMES if (folder / f"{t}{s}").exists()), None)
    out["view_quarter"] = out["view_estimate"] = None
    if view:
        vt = view.read_text(encoding="utf-8")
        out["view_quarter"] = label(max_q(vt, re.compile(r"^# ---FY(\d{2}) ?Q([1-4])---", re.M)))
        est = re.split(r"^# ---(?:测算|Estimates)---", vt, flags=re.M)
        m = re.search(r"^(\d{4}-\d{2}-\d{2})", est[1], re.M) if len(est) > 1 else None
        out["view_estimate"] = m.group(1) if m else None
    out["behind"] = behind = []
    k = lambda s: tuple(int(x) for x in re.findall(r"\d+", s)) if s else (0, 0)
    newest_tx = out["transcripts"][-1] if out["transcripts"] else None
    if newest_tx and k(newest_tx) > k(out["call_log"]):
        behind.append(f"call log ({out['call_log'] or 'none'}) is behind the transcripts ({newest_tx})")
    ref = out["call_log"]
    for key, name in (("financials", "financials dashboard"), ("valuation_quarter", "valuation"), ("view_quarter", "investment view")):
        if ref and out.get(key) and k(out[key]) < k(ref):
            behind.append(f"{name} ({out[key]}) is behind the call log ({ref})")
    if ref and view and not out["view_quarter"]:
        behind.append("investment view has no quarter block")
    if out["valuation_date"] and out["view_estimate"] and out["view_estimate"] < out["valuation_date"]:
        behind.append(f"latest estimate ({out['view_estimate']}) predates the valuation ({out['valuation_date']})")
    if not any(out.get(x) for x in ("call_log", "financials", "valuation_date", "view_quarter")):
        out["suggested"] = "A. First coverage"
    elif behind:
        out["suggested"] = "B. New quarter (bring the files above up to date)"
    else:
        out["suggested"] = "Up to date: C (add an event), D (find companies) or E (review) as needed"
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", type=Path)
    ap.add_argument("--ticker")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    s = status(a.folder, a.ticker)
    if a.json:
        print(json.dumps(s, ensure_ascii=False, indent=1))
        return 0
    print(f"{s['ticker']}  ({s['folder']})")
    if not s["exists"]:
        print("  folder not found")
    else:
        for k, lab in (("transcripts", "transcripts"), ("call_log", "call log"), ("digest", "digest"), ("financials", "financials"),
                       ("valuation_date", "valuation as of"), ("valuation_quarter", "valuation quarter"),
                       ("view_quarter", "investment view"), ("view_estimate", "latest estimate")):
            v = s.get(k)
            print(f"  {lab:<18} {', '.join(v) if isinstance(v, list) else (v or '-')}")
        for b in s["behind"]:
            print(f"  behind: {b}")
    print(f"  suggested: {s['suggested']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
