#!/usr/bin/env python3
"""
build_financials_xlsx.py - writes {TICKER}_Financials_NQ_Dashboard.xlsx from JSON.

The research step (pulling 8-K / 10-Q numbers) is the hard part and stays
with Claude; the layout is fixed and comes only from this script, so every
company's dashboard has the same rows, formulas, colours and notes - which is
what company-valuation and valuation-brief read.

Usage:  python build_financials_xlsx.py data.json OUTPUT.xlsx
Then:   python check_financials_xlsx.py OUTPUT.xlsx

JSON (all series in quarter order, oldest -> newest; null for not disclosed):
{
  "ticker": "FORM", "company": "FormFactor", "unit": "$M",
  "source": "SEC 8-K Exhibit 99.1 + 10-Q/10-K",
  "quarters":   ["FY24 Q2", ...],                 # N quarters (default 10)
  "period_end": ["2024-06-29", ...],
  "nongaap": {"revenue": [...], "gross_margin": [...], "opex": [...],
              "net_income": [...], "eps": [...]},
  "gaap":    {"revenue": [...], "gross_margin": [...], "opex": [...],
              "net_income": [...], "eps": [...]},
  "helper":  {"prior_year_revenue": [4 values for the first 4 quarters],
              "prior_year_nongaap_ni": [4], "prior_year_gaap_ni": [4],
              "prior_quarter_revenue": x, "prior_quarter_nongaap_ni": x,
              "prior_quarter_gaap_ni": x},
  "balance": {"inventory": [...], "deferred_revenue": [...],
              "customer_deposits": [...], "ar": [...],
              "cfo": [...], "cash_st": [...]},
  "notes":   {"nongaap": ["...non-GAAP effective tax rate ~X%..."], "gaap": [...],
              "delta": [...], "balance": [...]},
  "story":   {"en": "...", "zh": "..."},
  "observations": [{"theme": "1. Revenue cycle / 收入周期", "en": "...", "zh": "..."}, ... 8]
}
Gross margin is a fraction (0.565 for 56.5%).
"""
from __future__ import annotations

import json
import sys

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter as L

F = "Arial"
TITLE, SUB = Font(name=F, size=13, bold=True, color="1F4E79"), Font(name=F, size=9, italic=True, color="595959")
BODY, BLUE, BOLD = Font(name=F, size=10), Font(name=F, size=10, color="0000FF"), Font(name=F, size=10, bold=True)
HDR = Font(name=F, size=10, bold=True, color="FFFFFF")
FILL = {k: PatternFill("solid", fgColor=v) for k, v in
        {"ng": "305496", "g": "8064A2", "sec": "D9E1F2", "hl": "FFF2CC", "d": "1F4E79"}.items()}
SEC_FONT = Font(name=F, size=10, bold=True, color="1F4E79")
_s = Side(style="thin", color="BFBFBF")
BORDER = Border(left=_s, right=_s, top=_s, bottom=_s)
WRAP = Alignment(wrap_text=True, vertical="top")
USD, PCT, EPS, MULT = '#,##0.0;(#,##0.0);-', '0.0%;[Red](0.0%);-', '$0.00;($0.00);-', '0.00"x";(0.00"x");-'

TABLE_START_COL = 2


def hdr(ws, row, labels, fill):
    for i, t in enumerate(labels, 1):
        c = ws.cell(row=row, column=i, value=t)
        c.font, c.fill, c.border = HDR, fill, BORDER
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)


def cell(ws, r, c, v, fmt=None, typed=False, hl=False):
    x = ws.cell(row=r, column=c, value=v)
    x.font = BLUE if typed and v is not None else BODY
    x.border = BORDER
    if fmt:
        x.number_format = fmt
    if hl:
        x.fill = FILL["hl"]
    return x


def label(ws, r, text):
    c = ws.cell(row=r, column=1, value=text)
    c.font, c.border, c.alignment = BOLD, BORDER, WRAP


def notes(ws, start, lines):
    ws.cell(row=start, column=1, value="Notes / 备注").font = SEC_FONT
    for i, t in enumerate(lines, 1):
        c = ws.cell(row=start + i, column=1, value=f"{i}. {t}")
        c.alignment, c.font = WRAP, BODY
        ws.merge_cells(start_row=start + i, start_column=1, end_row=start + i, end_column=12)


def pl_sheet(ws, d, key, title, fill, extra_notes):
    q, n = d["quarters"], len(d["quarters"])
    s = d[key]
    last = TABLE_START_COL + n - 1
    ttm = last + 1
    ws["A1"], ws["A2"] = f"{d['company']} ({d['ticker']}) — {title} Quarterly Dashboard ({n} Quarters)", f"Source: {d.get('source','')}"
    ws["A1"].font, ws["A2"].font = TITLE, SUB
    hdr(ws, 4, ["Metric / 项目"] + q + ["TTM"], fill)
    ws.cell(row=4, column=last).fill = FILL["hl"]
    ws.cell(row=4, column=last).font = Font(name=F, size=10, bold=True, color="1F4E79")
    u = d.get("unit", "$M")
    pfx = "Adj " if key == "nongaap" else "GAAP "
    rows = {5: "Period End", 6: f"Revenue ({u})", 7: "Revenue YoY %", 8: "Revenue QoQ %",
            9: f"{pfx}Gross Margin %", 10: f"{pfx}OpEx ({u})", 11: f"{pfx}Operating Income ({u})",
            12: f"{pfx}Op Margin %", 13: f"{pfx}Net Income ({u})", 14: f"{pfx}NI YoY %",
            15: f"{pfx}NI QoQ %", 16: f"{pfx}Net Margin %", 17: f"{pfx}EPS ($)"}
    for r, t in rows.items():
        label(ws, r, t)
    h = d.get("helper", {})
    ni_py = h.get("prior_year_nongaap_ni" if key == "nongaap" else "prior_year_gaap_ni", [None] * 4)
    ni_pq = h.get("prior_quarter_nongaap_ni" if key == "nongaap" else "prior_quarter_gaap_ni")
    label(ws, 30, "Helper: prior-year same-quarter Revenue")
    label(ws, 31, f"Helper: prior-year same-quarter {pfx}Net Income")
    label(ws, 32, "Helper: prior-quarter Revenue / Net Income (for first QoQ)")
    for i in range(n):
        c = TABLE_START_COL + i
        col, hl = L(c), (c == last)
        cell(ws, 5, c, d["period_end"][i], hl=hl)
        cell(ws, 6, c, s["revenue"][i], USD, typed=True, hl=hl)
        cell(ws, 9, c, s["gross_margin"][i], PCT, typed=True, hl=hl)
        cell(ws, 10, c, s["opex"][i], USD, typed=True, hl=hl)
        cell(ws, 13, c, s["net_income"][i], USD, typed=True, hl=hl)
        cell(ws, 17, c, s["eps"][i], EPS, typed=True, hl=hl)
        if i < 4:
            cell(ws, 30, c, (h.get("prior_year_revenue") or [None] * 4)[i], USD, typed=True)
            cell(ws, 31, c, ni_py[i] if i < len(ni_py) else None, USD, typed=True)
            yo_r, yo_n = f"{col}30", f"{col}31"
        else:
            yo_r, yo_n = f"{L(c - 4)}6", f"{L(c - 4)}13"
        if i == 0:
            cell(ws, 32, c, h.get("prior_quarter_revenue"), USD, typed=True)
            cell(ws, 33, c, ni_pq, USD, typed=True)
            qo_r, qo_n = f"{col}32", f"{col}33"
        else:
            qo_r, qo_n = f"{L(c - 1)}6", f"{L(c - 1)}13"
        cell(ws, 7, c, f'=IFERROR({col}6/{yo_r}-1,"")', PCT, hl=hl)
        cell(ws, 8, c, f'=IFERROR({col}6/{qo_r}-1,"")', PCT, hl=hl)
        cell(ws, 11, c, f'=IF(COUNT({col}6,{col}9,{col}10)<3,"",{col}6*{col}9-{col}10)', USD, hl=hl)
        cell(ws, 12, c, f'=IFERROR({col}11/{col}6,"")', PCT, hl=hl)
        cell(ws, 14, c, f'=IFERROR({col}13/{yo_n}-1,"")', PCT, hl=hl)
        cell(ws, 15, c, f'=IFERROR({col}13/{qo_n}-1,"")', PCT, hl=hl)
        cell(ws, 16, c, f'=IFERROR({col}13/{col}6,"")', PCT, hl=hl)
    a, b = L(last - 3), L(last)
    T = L(ttm)
    for r, f, fmt in [(6, f"=SUM({a}6:{b}6)", USD), (9, f'=IFERROR(SUMPRODUCT({a}6:{b}6,{a}9:{b}9)/{T}6,"")', PCT),
                      (10, f"=SUM({a}10:{b}10)", USD), (11, f"=SUM({a}11:{b}11)", USD),
                      (12, f'=IFERROR({T}11/{T}6,"")', PCT), (13, f"=SUM({a}13:{b}13)", USD),
                      (16, f'=IFERROR({T}13/{T}6,"")', PCT), (17, f"=SUM({a}17:{b}17)", EPS)]:
        cell(ws, r, ttm, f, fmt)
    ws.column_dimensions["A"].width = 30
    for c in range(TABLE_START_COL, ttm):
        ws.column_dimensions[L(c)].width = 12
    ws.column_dimensions[T].width = 14
    ws.freeze_panes = "B5"
    std = [f"Fiscal labels follow the company's fiscal year (as reported).",
           f"Source: {d.get('source','')}. Every number traceable to the quarter's filing.",
           "Operating Income and Op Margin are formulas (Revenue × GM − OpEx), not typed values.",
           "YoY for the first 4 quarters uses the helper rows (prior-year same quarter); QoQ for the first quarter uses the prior-quarter helper.",
           "Latest quarter highlighted (FFF2CC). Blue = typed data, black = formula."]
    notes(ws, 38, std + (d.get("notes", {}).get(extra_notes) or []))


def build(d, out):
    n = len(d["quarters"])
    for k in ("period_end",):
        assert len(d[k]) == n, f"{k}: {len(d[k])} values for {n} quarters"
    for part in ("nongaap", "gaap"):
        for k in ("revenue", "gross_margin", "opex", "net_income", "eps"):
            assert len(d[part][k]) == n, f"{part}.{k}: {len(d[part][k])} values for {n} quarters"
    tax_ok = any(("tax" in t.lower() or "税率" in t) for t in d.get("notes", {}).get("nongaap", []))
    assert tax_ok, "notes.nongaap must state the non-GAAP effective tax rate"
    assert len(d.get("observations", [])) == 8, "observations: exactly 8 themes"

    wb = Workbook()
    ws1 = wb.active
    ws1.title = "Non-GAAP"
    pl_sheet(ws1, d, "nongaap", "Non-GAAP", FILL["ng"], "nongaap")
    ws2 = wb.create_sheet("GAAP")
    pl_sheet(ws2, d, "gaap", "GAAP", FILL["g"], "gaap")

    ws3 = wb.create_sheet("GAAP vs Non-GAAP")
    last = TABLE_START_COL + n - 1
    ws3["A1"], ws3["A2"] = f"{d['company']} ({d['ticker']}) — GAAP vs Non-GAAP Reconciliation", "Values copied from sheets 1-2 (no cross-sheet formulas)"
    ws3["A1"].font, ws3["A2"].font = TITLE, SUB
    hdr(ws3, 4, ["Metric / 项目"] + d["quarters"] + ["TTM"], FILL["d"])
    for r, t in {5: "Adj Net Income", 6: "GAAP Net Income", 7: "Delta ($M)", 8: "Delta / Adj NI %",
                 10: "Adj EPS ($)", 11: "GAAP EPS ($)", 12: "Delta EPS ($)"}.items():
        label(ws3, r, t)
    for i in range(n):
        c, col, hl = TABLE_START_COL + i, L(TABLE_START_COL + i), TABLE_START_COL + i == last
        cell(ws3, 5, c, d["nongaap"]["net_income"][i], USD, True, hl)
        cell(ws3, 6, c, d["gaap"]["net_income"][i], USD, True, hl)
        cell(ws3, 7, c, f"={col}5-{col}6", USD, hl=hl)
        cell(ws3, 8, c, f'=IFERROR({col}7/{col}5,"")', PCT, hl=hl)
        cell(ws3, 10, c, d["nongaap"]["eps"][i], EPS, True, hl)
        cell(ws3, 11, c, d["gaap"]["eps"][i], EPS, True, hl)
        cell(ws3, 12, c, f"={col}10-{col}11", EPS, hl=hl)
    T, a, b = L(last + 1), L(last - 3), L(last)
    for r in (5, 6, 7, 10, 11, 12):
        cell(ws3, r, last + 1, f"=SUM({a}{r}:{b}{r})", USD if r < 10 else EPS)
    cell(ws3, 8, last + 1, f'=IFERROR({T}7/{T}5,"")', PCT)
    ws3.column_dimensions["A"].width = 30
    ws3.freeze_panes = "B5"
    notes(ws3, 15, d.get("notes", {}).get("delta") or ["Delta components: SBC + amortisation + restructuring + acquisition one-offs + tax."])

    ws4 = wb.create_sheet("BS + CF + Observations")
    ws4["A1"], ws4["A2"] = f"{d['company']} ({d['ticker']}) — Balance Sheet, Cash Flow & Key Observations", f"Source: {d.get('source','')}"
    ws4["A1"].font, ws4["A2"].font = TITLE, SUB
    hdr(ws4, 4, ["Metric / 项目"] + d["quarters"], FILL["d"])
    bs = d["balance"]
    secs = {5: "BALANCE SHEET — Inventory & Demand Signals", 11: "CASH FLOW", 15: "COMPUTED METRICS"}
    for r, t in secs.items():
        for c in range(1, last + 1):
            ws4.cell(row=r, column=c).fill = FILL["sec"]
        ws4.cell(row=r, column=1, value=t).font = SEC_FONT
    rows = {6: ("Inventories, net ($M)", "inventory"), 7: ("Deferred Revenue (current) ($M)", "deferred_revenue"),
            8: ("Customer Deposits / Contract Liabilities ($M)", "customer_deposits"), 9: ("Accounts Receivable, net ($M)", "ar"),
            12: ("Cash from Operations ($M)", "cfo"), 13: ("Cash & ST Investments (EOP) ($M)", "cash_st")}
    for r, (t, k) in rows.items():
        label(ws4, r, t)
        for i in range(n):
            cell(ws4, r, TABLE_START_COL + i, (bs.get(k) or [None] * n)[i], USD, True, TABLE_START_COL + i == last)
    for r, t in {16: "Inventory Days (= Inventory / Revenue × 90)", 17: "Order-related Liab. (= Deferred Rev + Deposits)",
                 18: "CFO / Adj NI (cash conversion)"}.items():
        label(ws4, r, t)
    for i in range(n):
        c, col, hl = TABLE_START_COL + i, L(TABLE_START_COL + i), TABLE_START_COL + i == last
        cell(ws4, 16, c, f"=IFERROR({col}6/'Non-GAAP'!{col}6*90,\"\")", '0.0', hl=hl)
        cell(ws4, 17, c, f'=IFERROR({col}7+{col}8,"")', USD, hl=hl)
        cell(ws4, 18, c, f"=IFERROR({col}12/'Non-GAAP'!{col}13,\"\")", MULT, hl=hl)
    r = 21
    ws4.cell(row=r, column=1, value="The Story / 一句话总结").font = SEC_FONT
    for k, txt in (("en", d["story"]["en"]), ("zh", d["story"]["zh"])):
        r += 1
        c = ws4.cell(row=r, column=1, value=txt)
        c.fill, c.font, c.alignment = FILL["hl"], Font(name=F, size=10, color="1F4E79"), WRAP
        ws4.merge_cells(start_row=r, start_column=1, end_row=r, end_column=last)
    r += 2
    hdr(ws4, r, ["Theme / 主题", "Observation (English)", "Observation (中文)"], FILL["d"])
    ws4.merge_cells(start_row=r, start_column=2, end_row=r, end_column=6)
    ws4.merge_cells(start_row=r, start_column=7, end_row=r, end_column=last)
    ws4.cell(row=r, column=7, value="Observation (中文)").font = HDR
    ws4.cell(row=r, column=7).fill = FILL["d"]
    for ob in d["observations"]:
        r += 1
        label(ws4, r, ob["theme"])
        for c0, c1, key in ((2, 6, "en"), (7, last, "zh")):
            x = ws4.cell(row=r, column=c0, value=ob[key])
            x.alignment, x.font, x.border = WRAP, BODY, BORDER
            ws4.merge_cells(start_row=r, start_column=c0, end_row=r, end_column=c1)
    notes(ws4, r + 2, d.get("notes", {}).get("balance") or [])
    ws4.column_dimensions["A"].width = 34
    for c in range(TABLE_START_COL, last + 1):
        ws4.column_dimensions[L(c)].width = 12
    ws4.freeze_panes = "B5"
    wb.save(out)
    return out


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    data = json.load(open(sys.argv[1], encoding="utf-8"))
    try:
        print("Wrote", build(data, sys.argv[2]))
    except (AssertionError, KeyError) as e:
        sys.exit(f"ERROR input JSON: {e}")
