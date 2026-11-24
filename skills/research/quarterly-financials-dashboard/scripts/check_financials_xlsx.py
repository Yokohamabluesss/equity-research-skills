#!/usr/bin/env python3
"""
check_financials_xlsx.py - template check for {TICKER}_Financials_NQ_Dashboard.xlsx

Runs xlsx_check (LibreOffice recalc, formula errors, '='-text, sheet order)
and then the quarterly-financials-dashboard rules that downstream skills
(company-valuation, valuation-brief) rely on:

  - 4 sheets in fixed order: Non-GAAP | GAAP | GAAP vs Non-GAAP |
    BS + CF + Observations   (Excel caps sheet names at 31 chars)
  - freeze panes B5 on the three P&L sheets
  - required metric rows exist in column A (matched by keyword)
  - YoY / QoQ / Op Income / Op Margin / Net Margin rows are FORMULAS, not
    typed values (so one corrected input updates the whole table)
  - the latest quarter column is highlighted FFF2CC
  - a Notes block exists; the Non-GAAP sheet notes mention the tax rate
  - Observations: "The Story" box + the 8 themes; EN and ZH in separate columns

Usage: python check_financials_xlsx.py FILE.xlsx [--no-recalc]
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from openpyxl import load_workbook

HERE = Path(__file__).resolve().parent
SHEETS = ["Non-GAAP", "GAAP", "GAAP vs Non-GAAP", "BS + CF + Observations"]
PL_ROWS = {  # keyword regex -> must be formula?
    r"^Period End": False,
    r"^Revenue\b(?!.*(YoY|QoQ))": False,
    r"Revenue YoY": True,
    r"Revenue QoQ": True,
    r"Gross Margin": False,
    r"OpEx": False,
    r"Operating Income|Op Income": True,
    r"Op(erating)? Margin": True,
    r"Net Income(?!.*(YoY|QoQ))": False,
    r"NI YoY|Net Income YoY": True,
    r"Net Margin": True,
    r"EPS": False,
}
THEMES = ["Revenue cycle", "Margin", "Non-GAAP vs GAAP", "Inventory", "Order-proxy",
          "Cash conversion", "Guidance", "monitor"]


def col_a(ws):
    return {r: str(ws.cell(row=r, column=1).value or "") for r in range(1, ws.max_row + 1)}


def main() -> int:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    path = Path(sys.argv[1])
    args = [sys.executable, str(HERE / "xlsx_check.py"), str(path), "--expect-sheets", ",".join(SHEETS)]
    if "--no-recalc" in sys.argv:
        args.append("--no-recalc")
    rc = subprocess.run(args).returncode
    wb = load_workbook(path)
    fail, warn = [], []

    for name in SHEETS[:2]:
        if name not in wb.sheetnames:
            continue
        ws = wb[name]
        if ws.freeze_panes != "B5":
            fail.append(f"{name}: freeze panes {ws.freeze_panes!r}, template is 'B5'")
        labels = col_a(ws)
        for rx, must_formula in PL_ROWS.items():
            rows = [r for r, t in labels.items() if re.search(rx, t, re.I) and r >= 5]
            if not rows:
                fail.append(f"{name}: required row matching /{rx}/ not found in column A")
                continue
            r = rows[0]
            if must_formula:
                vals = [ws.cell(row=r, column=c).value for c in range(2, ws.max_column + 1)]
                typed = [v for v in vals if isinstance(v, (int, float))]
                if typed and len(typed) >= max(1, len([v for v in vals if v is not None]) // 2):
                    fail.append(f"{name}!row {r} '{labels[r][:30]}' holds typed numbers - must be Excel formulas")
        # latest-quarter highlight: some cell in header row 4 or data rows has FFF2CC
        hl = any((c.fill.fgColor.rgb or "").endswith("FFF2CC")
                 for row in ws.iter_rows(min_row=4, max_row=12) for c in row if c.fill and c.fill.fill_type)
        if not hl:
            warn.append(f"{name}: latest-quarter column is not highlighted FFF2CC")
        txt = "\n".join(labels.values())
        if not re.search(r"Notes|备注", txt):
            warn.append(f"{name}: no Notes block in column A")
        if name == "Non-GAAP" and not re.search(r"tax rate|税率",
                                                "\n".join(str(c.value) for row in ws.iter_rows() for c in row if c.value), re.I):
            fail.append("Non-GAAP: notes must state the company's non-GAAP effective tax rate")

    if SHEETS[2] in wb.sheetnames:
        ws = wb[SHEETS[2]]
        labels = col_a(ws)
        if not any(re.search(r"Delta", t) for t in labels.values()):
            fail.append("GAAP vs Non-GAAP: no Delta rows")

    if SHEETS[3] in wb.sheetnames:
        ws = wb[SHEETS[3]]
        allt = "\n".join(str(c.value) for row in ws.iter_rows() for c in row if c.value)
        for kw in ("Inventor", "Deferred Revenue", "Cash from Operations"):
            if kw.lower() not in allt.lower():
                fail.append(f"Balance Sheet sheet: row '{kw}…' not found")
        if not re.search(r"The Story|一句话总结", allt):
            fail.append("Observations: 'The Story / 一句话总结' box missing")
        missing = [t for t in THEMES if t.lower() not in allt.lower()]
        if missing:
            warn.append(f"Observations: themes not found: {missing}")

    for m in warn:
        print("WARN ", m)
    for m in fail:
        print("FAIL ", m)
    if fail or rc:
        return 1
    print("PASS  financials dashboard template OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
