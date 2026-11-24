#!/usr/bin/env python3
"""
check_valuation_xlsx.py - template check for {TICKER}_Valuation_Dashboard.xlsx

Runs xlsx_check (LibreOffice recalc + formula errors + '='-text) and then
the company-valuation template rules that make two companies' workbooks
comparable side by side:

  - the 10 fixed sheets in fixed order (or the SoTP variant)
  - every sheet: title in A1 (Arial 13 bold), subtitle in A2, freeze at B5,
    column A width 34
  - Conclusion: a method-verdict row (fill FCE4D6) within the first rows,
    and a "Method conclusion / 方法结论" sentence
  - Assumptions: a basis/derivation column ("Basis" / "依据")
  - FCFF page: a terminal-value share of EV is reported
  - Notes block present at the bottom of each table page

Usage: python check_valuation_xlsx.py COHR_Valuation_Dashboard.xlsx [--no-recalc]
Exit 1 on any FAIL.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from openpyxl import load_workbook

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from val_style import SHEETS, SHEETS_SOTP  # noqa: E402


def text_of(ws, max_rows=400):
    out = []
    for row in ws.iter_rows(max_row=max_rows):
        for c in row:
            if isinstance(c.value, str):
                out.append(c.value)
    return "\n".join(out)


def main() -> int:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    path = Path(sys.argv[1])
    recalc = "--no-recalc" not in sys.argv
    wb = load_workbook(path)
    expected = SHEETS_SOTP if "SoTP Valuation" in wb.sheetnames else SHEETS
    args = [sys.executable, str(HERE / "xlsx_check.py"), str(path), "--expect-sheets", ",".join(expected)]
    if not recalc:
        args.append("--no-recalc")
    rc = subprocess.run(args).returncode
    wb = load_workbook(path)
    fail, warn = [], []

    for ws in wb.worksheets:
        a1 = ws["A1"]
        if not a1.value:
            fail.append(f"{ws.title}: A1 title missing")
        elif not (a1.font and a1.font.bold and (a1.font.sz or 0) >= 12):
            warn.append(f"{ws.title}: A1 title is not the fixed TITLE style (Arial 13 bold)")
        if not ws["A2"].value:
            warn.append(f"{ws.title}: A2 subtitle missing")
        if ws.freeze_panes != "B5":
            fail.append(f"{ws.title}: freeze panes {ws.freeze_panes!r}, template is 'B5'")
        w = ws.column_dimensions["A"].width
        if w and abs(w - 34) > 2:
            warn.append(f"{ws.title}: column A width {w:.0f}, template is 34")
        if ws.title not in ("Methodology",) and not any(k in text_of(ws) for k in ("Notes", "备注")):
            warn.append(f"{ws.title}: no 'Notes / 备注' block found")

    if "Conclusion" in wb.sheetnames:
        ws = wb["Conclusion"]
        hit = False
        for row in ws.iter_rows(min_row=3, max_row=8):
            for c in row:
                fg = (c.fill.fgColor.rgb or "") if c.fill and c.fill.fill_type else ""
                if fg.endswith("FCE4D6") and c.value:
                    hit = True
        if not hit:
            fail.append("Conclusion: no method-verdict row (fill FCE4D6) in rows 3-8")
        t = text_of(ws)
        if not any(k in t for k in ("Method conclusion", "方法结论")):
            fail.append("Conclusion: missing the one-sentence 'Method conclusion / 方法结论'")
        if not any(k in t for k in ("coverage", "覆盖率")):
            warn.append("Conclusion: guidance-coverage ratio (指引覆盖率) not found")
    if "Assumptions" in wb.sheetnames:
        t = text_of(wb["Assumptions"], 12)
        if not any(k in t for k in ("Basis", "依据")):
            fail.append("Assumptions: the 'Basis and derivation / 依据与推导过程' column header is missing")
    fc = "FCFF Valuation" if "FCFF Valuation" in wb.sheetnames else None
    if fc:
        t = text_of(wb[fc])
        if not any(k in t for k in ("Terminal", "终值")):
            fail.append("FCFF Valuation: terminal-value share of EV is not reported")

    for m in warn:
        print("WARN ", m)
    for m in fail:
        print("FAIL ", m)
    if fail or rc:
        return 1
    print("PASS  valuation template OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
