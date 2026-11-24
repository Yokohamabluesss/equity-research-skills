#!/usr/bin/env python3
"""
build_xlsx.py - xlsx writer for the stock-discovery skill.

Three modes, fixed column schemas (order matters - do not change):
  business_discovery  9 columns   (mode 1)
  industry_chain      10 columns  (mode 2)
  list_screening      9 columns   (mode 3)

What this script guarantees (so two runs on the same data look the same):
  * column order and headers come from the schema, in English or Chinese
    ("lang": "en" | "zh", default zh for backward compatibility)
  * label columns are VALIDATED: Position / Stage / Attention / Relevance /
    Chain level must START with one of the fixed labels below. A qualifier
    may follow ("量产（光模块）/ 研发（CPO）"), but an unknown label is an error,
    not a silently uncoloured cell.
  * mode 1 rows are sorted deterministically: position > stage > attention
    (high attention first within a tier); mode 3 keeps the user's list order
  * Summary sheet with an optional segment x position overview

Usage:
  python build_xlsx.py input.json --output "{RESEARCH_ROOT}/stocks/CPO_相关公司_20260508.xlsx"
  (without --output: ./stocks/{topic}_{suffix}_{YYYYMMDD}.xlsx, or $STOCK_DISCOVERY_OUTPUT_DIR)

input.json:
  {"mode": "business_discovery", "topic": "CPO", "lang": "en",
   "summary": "optional text for the Summary sheet",
   "rows": [{"company": "Lumentum", "ticker": "LITE", "market": "US",
             "products": "EML, CW laser", "position": "Tier 1", "stage": "Mass production",
             "attention": "High", "lagging": "", "notes": "...", "segment": "Laser chips"}]}
  Chinese keys from older payloads (公司名, Ticker, 市场, 相关产品, 产业地位, 产品阶段,
  市场关注度, 涨幅滞后, 备注, 子环节, 环节层级, 该环节产品, 序号, 业务相关性) are accepted.

Requires: openpyxl
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path

try:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter
except ImportError:
    sys.exit("openpyxl is not installed: pip install openpyxl")

# ---------------------------------------------------------------- schema
# field id -> (zh header, en header, width)
FIELDS = {
    "no": ("序号", "No.", 6), "level": ("环节层级", "Chain level", 10), "segment": ("子环节", "Segment", 22),
    "company": ("公司名", "Company", 22), "ticker": ("Ticker", "Ticker", 14), "market": ("市场", "Market", 8),
    "products": ("相关产品", "Relevant products", 32), "seg_products": ("该环节产品", "Products in this segment", 32),
    "relevance": ("业务相关性", "Relevance", 12), "position": ("产业地位", "Position", 12),
    "stage": ("产品阶段", "Stage", 12), "attention": ("市场关注度", "Attention", 12),
    "lagging": ("涨幅滞后", "Lagging", 10), "notes": ("备注", "Notes", 44),
}
SCHEMAS = {
    "business_discovery": ["company", "ticker", "market", "products", "position", "stage", "attention", "lagging", "notes"],
    "industry_chain": ["level", "segment", "company", "ticker", "market", "seg_products", "position", "stage", "attention", "notes"],
    "list_screening": ["no", "company", "ticker", "market", "relevance", "products", "position", "stage", "notes"],
}
ZH_KEYS = {v[0]: k for k, v in FIELDS.items()}  # Chinese key -> field id
FILENAME_SUFFIX = {"business_discovery": ("相关公司", "Companies"), "industry_chain": ("产业链", "Value_Chain"),
                   "list_screening": ("", "")}

# ---------------------------------------------------------------- labels
# canonical id -> (zh label, en label, fill)
LABELS = {
    "position": [("t1", "头部", "Tier 1", "C6EFCE"), ("t2", "二线", "Tier 2", "FFEB9C"),
                 ("new", "新进入者", "New entrant", "FCE4D6"), ("tbc", "⚠️ 待确认", "⚠️ TBC", "F2F2F2"),
                 ("demand", "下游需求侧", "Demand side", "DDEBF7"), ("na", "N/A", "N/A", "F2F2F2"),
                 ("dash", "-", "-", None)],
    "stage": [("mp", "量产", "Mass production", "A9D08E"), ("smp", "送样", "Sampling", "C6E0B4"),
              ("rd", "研发", "R&D", "FFE699"), ("cpt", "概念", "Concept", "F4B084"), ("na", "N/A", "N/A", "F2F2F2"),
              ("dash", "-", "-", None)],
    "attention": [("hi", "高", "High", "F8CBAD"), ("mid", "中", "Medium", "FFE699"), ("lo", "低", "Low", "DDEBF7"),
                  ("dash", "-", "-", None)],
    "relevance": [("yes", "是", "Yes", "C6EFCE"), ("part", "部分", "Partial", "FFEB9C"),
                  ("no", "否", "No", "F2F2F2"), ("tbc", "⚠️ 待确认", "⚠️ TBC", "FCE4D6")],
    "level": [("up", "上游", "Upstream", "DDEBF7"), ("mid", "中游", "Midstream", "E2EFDA"), ("down", "下游", "Downstream", "FFF2CC")],
}
SORT_ORDER = {"position": ["t1", "t2", "new", "tbc", "demand", "na", "dash"], "stage": ["mp", "smp", "rd", "cpt", "na", "dash"],
              "attention": ["hi", "mid", "lo", "dash"]}
REQUIRED_LABELS = {"business_discovery": ["position", "stage", "attention"],
                   "industry_chain": ["level", "position", "stage", "attention"],
                   "list_screening": ["relevance", "position", "stage"]}

HEADER_FILL, HEADER_FONT = PatternFill("solid", fgColor="305496"), Font(name="Arial", bold=True, color="FFFFFF", size=11)
HEADER_ALIGN = Alignment(horizontal="center", vertical="center", wrap_text=True)
_S = Side(style="thin", color="BFBFBF")
BORDER = Border(left=_S, right=_S, top=_S, bottom=_S)
CELL_ALIGN, BODY = Alignment(vertical="top", wrap_text=True), Font(name="Arial", size=10)


def match_label(field: str, value) -> tuple | None:
    """Return the label tuple whose zh or en text the value starts with."""
    v = str(value or "").strip()
    if not v:
        return None
    for t in sorted(LABELS[field], key=lambda t: -max(len(t[1]), len(t[2]))):
        if v.startswith(t[1]) or v.lower().startswith(t[2].lower()):
            return t
    return False  # present but unknown


def normalize(row: dict) -> dict:
    out = {}
    for k, v in row.items():
        out[ZH_KEYS.get(k, k)] = "" if v is None else v
    return out


def validate(rows, mode) -> list[str]:
    errs = []
    for i, r in enumerate(rows, 1):
        for f in REQUIRED_LABELS[mode]:
            m = match_label(f, r.get(f, ""))
            if m is False:
                legal = " / ".join(f"{t[1]}|{t[2]}" for t in LABELS[f])
                errs.append(f"row {i} ({r.get('company', '?')}): {FIELDS[f][1]} = {r.get(f)!r} - must start with one of: {legal}")
            elif m is None and not (mode == "list_screening" and f != "relevance"):
                errs.append(f"row {i} ({r.get('company', '?')}): {FIELDS[f][1]} is empty")
    return errs


def sort_rows(rows, mode):
    if mode != "business_discovery":
        return rows

    def key(r):
        ks = []
        for f in ("position", "stage", "attention"):
            m = match_label(f, r.get(f))
            ks.append(SORT_ORDER[f].index(m[0]) if m else 99)
        return ks
    return sorted(rows, key=key)  # stable: equal keys keep input order


def write_main(ws, schema, rows, lang):
    li = 0 if lang == "zh" else 1
    for c, f in enumerate(schema, 1):
        cell = ws.cell(row=1, column=c, value=FIELDS[f][li])
        cell.fill, cell.font, cell.alignment, cell.border = HEADER_FILL, HEADER_FONT, HEADER_ALIGN, BORDER
        ws.column_dimensions[get_column_letter(c)].width = FIELDS[f][2]
    for r, row in enumerate(rows, 2):
        for c, f in enumerate(schema, 1):
            v = row.get(f, "")
            cell = ws.cell(row=r, column=c, value=v)
            cell.alignment, cell.border, cell.font = CELL_ALIGN, BORDER, BODY
            if f in LABELS:
                m = match_label(f, v)
                if m and m[3]:
                    cell.fill = PatternFill("solid", fgColor=m[3])
            if f == "lagging" and "🐢" in str(v):
                cell.fill, cell.font = PatternFill("solid", fgColor="FFC7CE"), Font(name="Arial", size=10, bold=True)
    ws.freeze_panes = "A2"
    if rows:
        ws.auto_filter.ref = f"A1:{get_column_letter(len(schema))}{len(rows) + 1}"


def short_name(full):
    full = str(full or "").strip()
    return full.split()[0] if " " in full else full


def write_summary(ws, payload, rows, lang):
    zh = lang == "zh"
    for col, w in zip("ABCDE", [26, 26, 26, 26, 22]):
        ws.column_dimensions[col].width = w
    T = (lambda a, b: a if zh else b)
    r = 1
    ws.cell(row=r, column=1, value=f"{T('主题', 'Topic')}: {payload.get('topic', '')}").font = Font(name="Arial", bold=True, size=14)
    ws.cell(row=r + 1, column=1, value=f"{T('模式', 'Mode')}: {payload.get('mode')}").font = Font(name="Arial", italic=True)
    ws.cell(row=r + 2, column=1, value=f"{T('生成日期', 'Generated')}: {dt.date.today().isoformat()}").font = Font(name="Arial", italic=True)
    r = 5
    ws.cell(row=r, column=1, value=T("总结 / 关键洞察", "Summary / key insights")).font = Font(name="Arial", bold=True, size=12)
    text = payload.get("summary", "") or ""
    c = ws.cell(row=r + 1, column=1, value=text)
    c.alignment = Alignment(wrap_text=True, vertical="top")
    if text:
        ws.merge_cells(start_row=r + 1, start_column=1, end_row=r + 1, end_column=5)
        ws.row_dimensions[r + 1].height = min(500, max(3, len(text) // 80 + text.count("\n") + 1) * 16)
    r += 3
    if any(x.get("segment") for x in rows):
        buckets = [t for t in LABELS["position"] if t[0] in ("t1", "t2", "new", "tbc")]
        segs: dict[str, dict] = {}
        for x in rows:
            seg = x.get("segment") or T("未分类", "Unclassified")
            m = match_label("position", x.get("position"))
            segs.setdefault(seg, {t[0]: [] for t in buckets})
            if m and m[0] in segs[seg]:
                segs[seg][m[0]].append(short_name(x.get("company")))
        if segs:
            ws.cell(row=r, column=1, value=T("子环节分布速览", "Segment overview")).font = Font(name="Arial", bold=True, size=12)
            r += 1
            for i, h in enumerate([FIELDS["segment"][0 if zh else 1]] + [t[1] if zh else t[2] for t in buckets], 1):
                hc = ws.cell(row=r, column=i, value=h)
                hc.fill, hc.font, hc.alignment, hc.border = HEADER_FILL, HEADER_FONT, HEADER_ALIGN, BORDER
            r += 1
            for seg, pm in segs.items():
                ws.cell(row=r, column=1, value=seg).font = Font(name="Arial", bold=True)
                ws.cell(row=r, column=1).border = BORDER
                for i, t in enumerate(buckets, 2):
                    names = pm[t[0]]
                    cc = ws.cell(row=r, column=i, value=("、" if zh else ", ").join(names) if names else "—")
                    cc.alignment, cc.border = Alignment(vertical="center", wrap_text=True), BORDER
                    if names:
                        cc.fill = PatternFill("solid", fgColor=t[3])
                r += 1
            r += 1
    ws.cell(row=r, column=1, value=T("说明", "Notes")).font = Font(name="Arial", bold=True, size=12)
    disc = T("本表由 stock-discovery skill 生成。标签依据公开信息（公告、年报、电话会、券商研报、产业链调研）综合判断；"
             "⚠️ 推测 为基于上下游/招标信息的反推；🐢 涨幅滞后 为相对板块明显未跟涨的标的。本表不构成投资建议，不含估值。",
             "Generated by the stock-discovery skill. Labels are judged from public information (filings, annual reports, calls, "
             "sell-side and supply-chain research); '⚠️ Speculation' marks inferences from supply-chain / tender information; "
             "🐢 marks names that clearly lagged their sector. Not investment advice; no valuation.")
    d = ws.cell(row=r + 1, column=1, value=disc)
    d.font, d.alignment = Font(name="Arial", size=10, italic=True, color="595959"), Alignment(wrap_text=True, vertical="top")
    ws.merge_cells(start_row=r + 1, start_column=1, end_row=r + 1, end_column=5)
    ws.row_dimensions[r + 1].height = 60


def output_path(payload, override):
    if override:
        return Path(override)
    lang = payload.get("lang", "zh")
    base = Path(os.environ.get("STOCK_DISCOVERY_OUTPUT_DIR", "./stocks"))
    topic = str(payload.get("topic") or "stocks").replace("/", "_").replace("\\", "_").replace(" ", "_")
    suf = FILENAME_SUFFIX[payload["mode"]][0 if lang == "zh" else 1]
    today = dt.date.today().strftime("%Y%m%d")
    return base / (f"{topic}_{suf}_{today}.xlsx" if suf else f"{topic}_{today}.xlsx")


def build(payload, out: Path):
    mode = payload.get("mode")
    if mode not in SCHEMAS:
        raise ValueError(f"unknown mode {mode!r}; one of {list(SCHEMAS)}")
    lang = payload.get("lang", "zh")
    rows = [normalize(r) for r in payload.get("rows") or []]
    errs = validate(rows, mode)
    if errs:
        raise ValueError("label check failed - put qualifiers after the label or into Notes:\n  " + "\n  ".join(errs))
    rows = sort_rows(rows, mode)
    wb = Workbook()
    ws = wb.active
    ws.title = "Companies"
    write_main(ws, SCHEMAS[mode], rows, lang)
    write_summary(wb.create_sheet("Summary"), payload, rows, lang)
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    return out, len(rows)


def main():
    ap = argparse.ArgumentParser(description="Build stock-discovery xlsx output.")
    ap.add_argument("input_json")
    ap.add_argument("--output", default=None, help="output path (recommended)")
    a = ap.parse_args()
    payload = json.load(open(a.input_json, encoding="utf-8"))
    try:
        out, n = build(payload, output_path(payload, a.output))
    except ValueError as e:
        sys.exit(f"ERROR {e}")
    print(f"Wrote: {out}  ({n} rows)")


if __name__ == "__main__":
    main()
