#!/usr/bin/env python3
"""
val_style.py - the fixed visual template of {TICKER}_Valuation_Dashboard.xlsx

Import this instead of re-typing colours and formats in every run; the
template is then identical across companies by construction.

    import sys; sys.path.insert(0, "<skill>/scripts")
    from val_style import *
    wb = new_workbook()                 # 10 sheets, fixed names and order
    ws = wb["Assumptions"]
    page_header(ws, "COHR - Assumptions", "Source: ... | price as of ...")
    header_row(ws, 4, ["Item", "Value", "Basis and derivation"], fill=FILL_D)
    section(ws, 5, "① Market data", ncols=3)
    put(ws, "B6", 312.62, fmt=FMT_PRICE, kind="input")
    put(ws, "B7", "=B6*B8", fmt=FMT_USD_M)          # formula -> black
    finish(ws)                                       # widths, freeze B5, borders
"""
from __future__ import annotations

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

SHEETS = ["Conclusion", "Assumptions", "Revenue & Margin Build", "Non-GAAP EPS Build",
          "GAAP EPS Build", "Consensus Check", "PE & PEG", "FCFF Valuation",
          "Reverse DCF & Comps", "Methodology"]
SHEETS_SOTP = SHEETS[:7] + ["SoTP Valuation", "SoTP Cross-Check & Comps", "Methodology"]

FONT = "Arial"
TITLE = Font(name=FONT, size=13, bold=True, color="1F4E79")
SUB = Font(name=FONT, size=9, italic=True, color="595959")
BODY = Font(name=FONT, size=10, color="000000")
INPUT = Font(name=FONT, size=10, color="0000FF")      # hard-coded data = blue
HDR_FONT = Font(name=FONT, size=10, bold=True, color="FFFFFF")
SEC_FONT = Font(name=FONT, size=10, bold=True, color="1F4E79")
WARN = Font(name=FONT, size=10, bold=True, color="C00000")
VERDICT_FONT = Font(name=FONT, size=11, bold=True, color="C00000")


def _f(hex_):
    return PatternFill("solid", fgColor=hex_)


FILL_D, FILL_NG, FILL_G, FILL_FC = _f("1F4E79"), _f("305496"), _f("8064A2"), _f("1F6F4A")
FILL_SEC, FILL_KEY, FILL_VERDICT, FILL_IN = _f("D9E1F2"), _f("FFF2CC"), _f("FCE4D6"), _f("FFFF00")

FMT_USD_M = '#,##0.0;(#,##0.0);-'
FMT_PCT = '0.0%;[Red](0.0%);-'
FMT_EPS = '$0.00;($0.00);-'
FMT_PE = '0.0"x";(0.0"x");-'
FMT_PEG = '0.00;(0.00);-'
FMT_BPS = '#,##0"bps";(#,##0"bps");-'
FMT_YEARS = '0.0"yr";(0.0"yr");-'
FMT_YEARS_ZH = '0.0"年";(0.0"年");-'   # use in a Chinese-language workbook
FMT_INT = '#,##0;(#,##0);-'
FMT_PRICE = '#,##0.00'

_TH = Side(style="thin", color="BFBFBF")
BORDER = Border(left=_TH, right=_TH, top=_TH, bottom=_TH)
WRAP = Alignment(vertical="top", wrap_text=True)

COL_A, COL_DATA, COL_NOTE = 34, 15, 80   # note/basis columns: 66-105


def new_workbook(sotp: bool = False) -> Workbook:
    wb = Workbook()
    names = SHEETS_SOTP if sotp else SHEETS
    wb.active.title = names[0]
    for n in names[1:]:
        wb.create_sheet(n)
    return wb


def page_header(ws, title: str, subtitle: str):
    ws["A1"], ws["A2"] = title, subtitle
    ws["A1"].font, ws["A2"].font = TITLE, SUB


def header_row(ws, row: int, labels: list[str], fill=FILL_D, col: int = 1):
    for i, lab in enumerate(labels):
        c = ws.cell(row=row, column=col + i, value=lab)
        c.font, c.fill, c.alignment, c.border = HDR_FONT, fill, Alignment(horizontal="center", vertical="center", wrap_text=True), BORDER


def section(ws, row: int, text: str, ncols: int):
    for i in range(1, ncols + 1):
        c = ws.cell(row=row, column=i)
        c.fill, c.border = FILL_SEC, BORDER
    ws.cell(row=row, column=1, value=text).font = SEC_FONT


def verdict(ws, row: int, text: str, ncols: int):
    """Row 5 of Conclusion: the one-sentence method verdict."""
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=ncols)
    c = ws.cell(row=row, column=1, value=text)
    c.font, c.fill, c.alignment = VERDICT_FONT, FILL_VERDICT, WRAP


def put(ws, ref: str, value, fmt: str | None = None, kind: str = "auto", key: bool = False):
    """kind: 'input' (blue, yellow fill), 'data' (blue), 'auto' (formula black / number blue / text black)."""
    if isinstance(value, str) and value.startswith("=") and not _looks_like_formula(value):
        value = "＝" + value[1:]          # text must never start with '='
    c = ws[ref]
    c.value = value
    is_formula = isinstance(value, str) and value.startswith("=")
    if kind == "input":
        c.font, c.fill = INPUT, FILL_IN
    elif kind == "data" or (kind == "auto" and isinstance(value, (int, float)) and not is_formula):
        c.font = INPUT
    else:
        c.font = BODY
    if fmt:
        c.number_format = fmt
    if key:
        c.fill = FILL_KEY
    c.border, c.alignment = BORDER, WRAP if isinstance(value, str) and not is_formula else Alignment(vertical="top")
    return c


def _looks_like_formula(v: str) -> bool:
    import re
    return bool(re.search(r"[A-Z]{1,3}\$?\d+|[A-Z]+\(", v[1:]))


def finish(ws, note_cols: tuple[str, ...] = (), data_cols: int = 12):
    """Fixed page layout: A=34, data=15, note columns wide, freeze B5."""
    from openpyxl.utils import get_column_letter
    ws.column_dimensions["A"].width = COL_A
    for i in range(2, 2 + data_cols):
        L = get_column_letter(i)
        ws.column_dimensions[L].width = COL_NOTE if L in note_cols else COL_DATA
    ws.freeze_panes = "B5"
