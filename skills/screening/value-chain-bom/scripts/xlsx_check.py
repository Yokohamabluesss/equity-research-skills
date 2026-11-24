#!/usr/bin/env python3
"""
xlsx_check.py - shared recalculation + lint for every xlsx-producing skill.

Why this exists: formulas written by openpyxl have no cached values, so a
reader that opens the file with data_only=True (or a phone preview) sees
blanks. LibreOffice recalculates them; this script then scans for the
three failure modes that have actually broken past deliverables:

  1. formula errors after recalculation (#REF!, #NAME?, #DIV/0!, #N/A ...)
  2. text cells that start with "=" (Excel parses them as broken formulas)
  3. a sheet layout that does not match the skill's fixed template
     (optional: --expect-sheets "Name1,Name2,..." checks names AND order)

Usage:
  python xlsx_check.py FILE.xlsx                      # recalc in place + lint
  python xlsx_check.py FILE.xlsx --no-recalc          # lint only
  python xlsx_check.py FILE.xlsx --expect-sheets "Conclusion,Assumptions"
  python xlsx_check.py FILE.xlsx --freeze B5          # every sheet frozen at B5

Exit code 0 = clean, 1 = problems found, 2 = could not run.
Requires: openpyxl; LibreOffice (soffice) for recalculation.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from openpyxl import load_workbook
except ImportError:
    sys.exit("openpyxl missing: pip install openpyxl")

ERR_RE = re.compile(r"^#(REF!|NAME\?|DIV/0!|N/A|VALUE!|NUM!|NULL!)")


def recalc(path: Path, timeout: int = 200) -> bool:
    """Recalculate with LibreOffice; replace file with the recalculated copy."""
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        print("WARN  LibreOffice not found - skipped recalculation "
              "(re-verify derived values in Python instead).")
        return False
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "in.xlsx"
        shutil.copy(path, src)
        outdir = Path(tmp) / "out"
        cmd = [soffice, "--headless", "--norestore", "--invisible",
               f"-env:UserInstallation=file://{tmp}/lo_profile",
               "--convert-to", "xlsx:Calc MS Excel 2007 XML",
               "--outdir", str(outdir), str(src)]
        try:
            subprocess.run(cmd, check=True, timeout=timeout,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:  # noqa: BLE001
            print(f"WARN  recalculation failed ({e}); file left unchanged.")
            return False
        out = outdir / "in.xlsx"
        if not out.exists():
            print("WARN  LibreOffice produced no output; file left unchanged.")
            return False
        shutil.copy(out, path)
    return True


def lint(path: Path, expect_sheets: list[str] | None, freeze: str | None) -> list[str]:
    problems: list[str] = []
    wb_f = load_workbook(path)                  # formulas
    wb_v = load_workbook(path, data_only=True)  # cached values

    if expect_sheets:
        actual = wb_f.sheetnames
        if actual != expect_sheets:
            problems.append(f"sheet names/order differ.\n      expected: {expect_sheets}\n      actual:   {actual}")

    n_formulas = 0
    for ws in wb_f.worksheets:
        wv = wb_v[ws.title]
        if freeze and ws.freeze_panes != freeze:
            problems.append(f"{ws.title}: freeze panes = {ws.freeze_panes!r}, expected {freeze!r}")
        for row in ws.iter_rows():
            for c in row:
                v = c.value
                if isinstance(v, str) and v.startswith("="):
                    n_formulas += 1
                    cached = wv[c.coordinate].value
                    if isinstance(cached, str) and ERR_RE.match(cached):
                        problems.append(f"{ws.title}!{c.coordinate}: {cached}  ({v[:60]})")
                    # text that only *looks* like a formula: no function call,
                    # no cell reference, contains CJK or spaces between words
                    body = v[1:]
                    if (not re.search(r"[A-Z]{1,3}\$?\d+|[A-Z]+\(", body)
                            and re.search(r"[一-鿿]|[a-z]{3,}\s+[a-z]{3,}", body)):
                        problems.append(f"{ws.title}!{c.coordinate}: text starts with '=' "
                                        f"(use '≡' or a full-width '＝'): {v[:60]!r}")
                elif isinstance(v, str) and ERR_RE.match(v):
                    problems.append(f"{ws.title}!{c.coordinate}: literal error value {v}")
    print(f"INFO  {len(wb_f.sheetnames)} sheets, {n_formulas} formulas scanned")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--no-recalc", action="store_true")
    ap.add_argument("--expect-sheets", default=None,
                    help="comma-separated sheet names in required order")
    ap.add_argument("--freeze", default=None, help="expected freeze cell on every sheet")
    a = ap.parse_args()
    path = Path(a.file)
    if not path.exists():
        print(f"ERROR file not found: {path}")
        return 2
    if not a.no_recalc:
        if recalc(path):
            print("INFO  recalculated with LibreOffice (cached values now stored)")
    expect = [s.strip() for s in a.expect_sheets.split(",")] if a.expect_sheets else None
    problems = lint(path, expect, a.freeze)
    if problems:
        print(f"FAIL  {len(problems)} problem(s):")
        for p in problems:
            print("  -", p)
        return 1
    print("PASS  no formula errors, no '='-text, layout as expected")
    return 0


if __name__ == "__main__":
    sys.exit(main())
