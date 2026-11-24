#!/usr/bin/env python3
"""
check_bom_xlsx.py - template + pitfall check for the value-chain-bom workbook.

Runs xlsx_check (LibreOffice recalc, formula errors, '='-text) and then the
value-chain-bom rules, most of which come from bugs hit in earlier builds:

  - the 7 sheets in fixed order (Chinese or English names, see below)
  - cross-sheet references to sheet names that start with a digit or contain
    spaces are quoted:  ='2_Scenarios & BOM'!C10   (unquoted refs break)
  - the summary sheet's share cells are formulas (shares must re-calculate
    when an assumption changes), and at least 3 scenario columns exist
  - percentages are stored as fractions (a share > 1.5 is flagged)
  - the sources sheet starts with the "main limitation" statement

Usage: python check_bom_xlsx.py FILE.xlsx [--no-recalc]
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from openpyxl import load_workbook

HERE = Path(__file__).resolve().parent
ZH = ["1_价值量总表", "2_场景与BOM", "3_真变量敏感性", "4_公司图谱", "5_关键层专页", "6_市场规模交叉验证", "7_来源"]
EN = ["1_Value Summary", "2_Scenarios & BOM", "3_True Variable", "4_Company Map", "5_Key Layer", "6_Market Size Check", "7_Sources"]
UNQUOTED = re.compile(r"(?<!['A-Za-z0-9_])(\d[^'!=(),+\-*/ ]*|[^'!=(),+\-*/]* [^'!=(),+\-*/]*)!\$?[A-Z]{1,3}\$?\d+")


def main() -> int:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    path = Path(sys.argv[1])
    wb = load_workbook(path)
    names = ZH if wb.sheetnames and wb.sheetnames[0].startswith("1_价值") else EN
    args = [sys.executable, str(HERE / "xlsx_check.py"), str(path), "--expect-sheets", ",".join(names)]
    if "--no-recalc" in sys.argv:
        args.append("--no-recalc")
    rc = subprocess.run(args).returncode
    wb = load_workbook(path)
    wbv = load_workbook(path, data_only=True)
    fail, warn = [], []

    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, str) and c.value.startswith("=") and "!" in c.value:
                    if UNQUOTED.search(c.value):
                        fail.append(f"{ws.title}!{c.coordinate}: unquoted sheet reference in {c.value[:70]!r} "
                                    f"- write ='2_Sheet name'!C10")

    if names[0] in wb.sheetnames:
        ws, wv = wb[names[0]], wbv[names[0]]
        hdr_rows = [[str(c.value or "") for c in r] for r in ws.iter_rows(min_row=1, max_row=8)]
        scen = max((sum(1 for v in r if re.search(r"场景|Scenario", v)) for r in hdr_rows), default=0)
        if scen < 3:
            fail.append(f"{names[0]}: found {scen} scenario columns - the skill requires at least 3")
        typed = 0
        for row in ws.iter_rows(min_row=5):
            for c in row:
                if c.number_format and "%" in c.number_format:
                    if isinstance(c.value, (int, float)):
                        typed += 1
                    v = wv[c.coordinate].value
                    if isinstance(v, (int, float)) and v > 1.5:
                        warn.append(f"{names[0]}!{c.coordinate}: share {v} > 150% - store shares as fractions (0.91, not 91)")
        if typed > 3:
            fail.append(f"{names[0]}: {typed} percentage cells hold typed numbers - shares must be formulas linked to the BOM sheet")

    if names[6] in wb.sheetnames:
        first = " ".join(str(c.value or "") for r in wb[names[6]].iter_rows(min_row=1, max_row=4) for c in r)
        if not re.search(r"限制|limitation", first, re.I):
            fail.append(f"{names[6]}: the first rows must state the main limitation (what is sourced vs estimated)")

    for m in warn[:20]:
        print("WARN ", m)
    for m in fail:
        print("FAIL ", m)
    if fail or rc:
        return 1
    print("PASS  value-chain workbook OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
