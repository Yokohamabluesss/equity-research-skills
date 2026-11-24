#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Architecture-migration segment delta table - xlsx builder.

Usage: python build_delta_xlsx.py input.json output.xlsx

Input JSON:
{
  "lang": "en" | "zh",                       # default zh
  "title": "Pluggable -> NPO / CPO segment deltas",
  "baseline": "Pluggable",
  "routes": ["NPO", "CPO"],
  "basis": "Reference system: NVIDIA Quantum-X ...",
  "segments": [
    {"name": "Optical engine SiPh/PIC",
     "baseline_form": "inside the module, one per module",
     "forms":    {"NPO": "moved next to the ASIC on the PCB", "CPO": "co-packaged with the ASIC"},
     "verdicts": {"NPO": "⭐ Clear increase",                 "CPO": "⭐ Clear increase"},
     "us": "TSM (COUPE) ...", "cn": "HGTECH 000988 ...",
     "note": "⚠️ under CPO the value is absorbed by TSMC's ecosystem ...",
     "highlight": true}
  ],
  "conclusions": [{"title": "⭐⭐ Only 2 route-exclusive points", "body": "..."}]
}
A verdict must be exactly one of the seven labels (English or Chinese - both
are accepted and written in the output language). No brackets: put any
qualifier ("WDM case only") into "note". The script asserts this, because a
cell value that does not match exactly would be silently left uncoloured and
would break the auto-filter.
"""
import json
import sys
from collections import Counter

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

FT = "Arial"
# key: (zh label, en label, colour, zh meaning, en meaning)
VERDICTS = {
    "new":    ("⭐⭐ 纯新增", "⭐⭐ Net-new", "A9D08E",
               "旧架构里不存在这个位置，做这个的公司没有历史包袱",
               "The position does not exist in the old architecture; suppliers carry no legacy"),
    "inc":    ("⭐ 明显增量", "⭐ Clear increase", "D9EAD3",
               "环节本来就有，但用量、单价或技术门槛明显提升",
               "The segment existed, but volume, unit price or technical bar rises clearly"),
    "shift":  ("○ 平移", "○ Shift", "FFF2CC",
               "总量基本不变，只是位置或形态改变（最容易被误判成利好）",
               "Total roughly unchanged, only location or form changes (most often mistaken for a positive)"),
    "offset": ("⚠️ 内部抵消", "⚠️ Internal offset", "FCE4D6",
               "公司有得有失，净影响需自行判断，不能简单算作利好",
               "The company gains and loses; net effect needs judgment, not simply a positive"),
    "dec":    ("❌ 减量", "❌ Decrease", "F4CCCC",
               "该环节需求下降或消失——这是规避清单", "Demand for the segment falls or disappears - the avoid list"),
    "tbc":    ("❓ 待证实", "❓ Unconfirmed", "EDEDED",
               "方案尚未公开或存在矛盾证据，暂不下判断", "Design not public or evidence conflicts; no verdict yet"),
    "na":     ("⊘ 不适用", "⊘ Not applicable", "D0CECE",
               "该架构明确不需要这个环节（与『待证实』不同：这是知道不需要）",
               "The architecture clearly does not need it (unlike Unconfirmed: this is known)"),
}
EVIDENCE = {
    "★★★": ("C6E0B4", "公司官方文件（年报/半年报/公告/IR 记录/官网产品页）明示该产品供这条路线",
            "Official company documents (annual / interim report, announcement, IR record, product page) explicitly tie the product to this route"),
    "◆":   ("FCE4D6", "券商研报口径——不是官方，不可与 ★★★ 并列", "Sell-side research - not official; never on a par with ★★★"),
    "◇":   ("F2DCDB", "产业纪要 / 专家访谈口径", "Industry notes / expert calls"),
    "○":   ("FFF2CC", "有该产品，但公司官方把它归在其他应用市场（如电信而非数通）",
            "Has the product, but the company officially places it in another market (e.g. telecom, not datacom)"),
    "△":   ("F2F2F2", "仅有通用产品描述，无任何路线口径", "Generic product description only, no route wording"),
    "⚠️":  ("FCE4D6", "存在反证、公司自身降温、或该项为推断", "Counter-evidence, the company itself played it down, or inferred"),
}
TXT = {
    "zh": {"sheet1": "① 环节增减量对照", "sheet2": "② 关键结论", "sheet3": "③ 图例与读法",
           "seg": "环节", "form": "{} 形态", "verdict": "{} 增量判断", "us": "美股 / 海外受益", "cn": "A 股受益",
           "note": "⚠️ 抵消 / 受损 / 判断依据", "num": "#", "concl": "结论", "body": "说明",
           "mark": "标记", "meaning": "含义", "count": "{} 列出现次数",
           "banner": "读法：先看各路线的【增量判断】列是否一致——不一致的行才是需要做路线选择的地方。"
                     "颜色仅是判断列枚举值的映射，含义见③页。首列黄底 = 本次新增或大幅修改的环节。",
           "sep": "——— 以下是【公司名后面的口径标记】，与上面的增量档位是两套独立标记，不要混读 ———"},
    "en": {"sheet1": "① Segment Deltas", "sheet2": "② Key Conclusions", "sheet3": "③ Legend",
           "seg": "Segment", "form": "{} form", "verdict": "{} verdict", "us": "US / overseas beneficiaries",
           "cn": "A-share beneficiaries", "note": "⚠️ Offsets / losers / basis", "num": "#", "concl": "Conclusion",
           "body": "Explanation", "mark": "Mark", "meaning": "Meaning", "count": "count in {}",
           "banner": "How to read: first check whether the routes' verdict columns agree - rows where they differ are where a "
                     "route choice matters. Colours only map the verdict labels (see sheet ③). Yellow first cell = segment "
                     "added or substantially revised in this version.",
           "sep": "——— Below: the EVIDENCE marks after company names - a separate system from the verdicts above ———"},
}
HDR_FILL = PatternFill("solid", fgColor="1F3864")
HDR_FONT = Font(name=FT, bold=True, color="FFFFFF", size=10)
CELL_FONT, BOLD_FONT = Font(name=FT, size=10), Font(name=FT, size=10, bold=True)
_TH = Side(style="thin", color="BFBFBF")
BORDER = Border(left=_TH, right=_TH, top=_TH, bottom=_TH)
WRAP = Alignment(vertical="top", wrap_text=True)
HDR_ALIGN = Alignment(vertical="top", horizontal="center", wrap_text=True)
MID = Alignment(vertical="center", horizontal="center", wrap_text=True)
HL_FILL = PatternFill("solid", fgColor="FFF2CC")

LOOKUP = {}
for k, v in VERDICTS.items():
    LOOKUP[v[0]] = k
    LOOKUP[v[1]] = k


def verdict_key(val, where):
    val = str(val)
    assert val in LOOKUP, (f"unregistered verdict {val!r} ({where}). Legal: "
                           f"{[v[1] for v in VERDICTS.values()]} or {[v[0] for v in VERDICTS.values()]}. "
                           f"Put qualifiers into 'note', no brackets.")
    return LOOKUP[val]


def _write(ws, headers, rows, widths, freeze="A2", center=(), fillcols=(), fillmap=None, highlight_rows=()):
    ws.append(headers)
    for c in ws[1]:
        c.fill, c.font, c.alignment, c.border = HDR_FILL, HDR_FONT, HDR_ALIGN, BORDER
    for r in rows:
        ws.append(r)
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.font, c.alignment, c.border = CELL_FONT, WRAP, BORDER
        row[0].font = BOLD_FONT
        for ci in center:
            row[ci].alignment = MID
        for ci in fillcols:
            cell = row[ci]
            cell.alignment, cell.font = MID, BOLD_FONT
            val = str(cell.value)
            assert val in fillmap, f"unregistered label {val!r} (row {cell.row} col {cell.column})"
            cell.fill = PatternFill("solid", fgColor=fillmap[val])
    for i in highlight_rows:
        ws.cell(row=i, column=1).fill = HL_FILL
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[1].height = 34
    ws.freeze_panes = freeze
    ws.auto_filter.ref = ws.dimensions


def _banner(ws, text, ncols, height=30):
    ws.insert_rows(1)
    ws["A1"] = text
    ws["A1"].font = Font(name=FT, size=10, bold=True)
    ws["A1"].alignment = Alignment(vertical="center", wrap_text=True)
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=ncols)
    ws.row_dimensions[1].height = height
    ws.auto_filter.ref = None


def build(spec, out_path):
    lang = spec.get("lang", "zh")
    T, li = TXT[lang], (0 if lang == "zh" else 1)
    routes, segs = spec["routes"], spec["segments"]
    for s in segs:  # validate + normalise verdicts to the output language
        s["_vk"] = {r: verdict_key(s["verdicts"][r], f"{s['name']} / {r}") for r in routes}
    label = {k: v[li] for k, v in VERDICTS.items()}
    vcolors = {v[li]: v[2] for v in VERDICTS.values()}

    wb = Workbook()
    ws = wb.active
    ws.title = T["sheet1"]
    headers = ([T["seg"], spec["baseline"]] + [T["form"].format(r) for r in routes]
               + [T["verdict"].format(r) for r in routes] + [T["us"], T["cn"], T["note"]])
    rows, highlight = [], []
    for i, s in enumerate(segs, 2):
        rows.append([s["name"], s.get("baseline_form", "")] + [s.get("forms", {}).get(r, "") for r in routes]
                    + [label[s["_vk"][r]] for r in routes] + [s.get("us", ""), s.get("cn", ""), s.get("note", "")])
        if s.get("highlight"):
            highlight.append(i)
    n = len(routes)
    vcols = tuple(range(2 + n, 2 + 2 * n))
    _write(ws, headers, rows, [22, 26] + [30] * n + [16] * n + [54, 52, 80], freeze="B2", center=vcols,
           fillcols=vcols, fillmap=vcolors, highlight_rows=[i + 1 for i in highlight])
    banner = (spec["basis"] + " ｜ " + T["banner"]) if spec.get("basis") else T["banner"]
    _banner(ws, banner, len(headers), height=32)
    ws.freeze_panes = "B3"

    ws2 = wb.create_sheet(T["sheet2"])
    crows = [[str(i), c["title"], c["body"]] for i, c in enumerate(spec.get("conclusions", []), 1)]
    _write(ws2, [T["num"], T["concl"], T["body"]], crows, [5, 46, 132], center=(0,))
    ws2.auto_filter.ref = None

    ws3 = wb.create_sheet(T["sheet3"])
    counts = {r: Counter(s["_vk"][r] for s in segs) for r in routes}
    hdr3 = [T["mark"], T["meaning"]] + [T["count"].format(r) for r in routes]
    rows3 = [[v[li], v[3 + li]] + [counts[r].get(k, 0) for r in routes] for k, v in VERDICTS.items()]
    sep = len(rows3) + 2
    rows3 += [[k, v[1 + li]] + ["—"] * n for k, v in EVIDENCE.items()]
    _write(ws3, hdr3, rows3, [18, 88] + [18] * n, center=tuple(range(2, 2 + n)), fillcols=(0,),
           fillmap={**vcolors, **{k: v[0] for k, v in EVIDENCE.items()}})
    ws3.auto_filter.ref = None
    ws3.insert_rows(sep)
    c = ws3.cell(row=sep, column=1, value=T["sep"])
    c.font, c.alignment = Font(name=FT, size=10, bold=True), Alignment(vertical="center", wrap_text=True)
    ws3.merge_cells(start_row=sep, start_column=1, end_row=sep, end_column=2 + n)
    ws3.row_dimensions[sep].height = 24
    wb.save(out_path)
    return {r: {label[k]: v for k, v in counts[r].items()} for r in routes}


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    try:
        counts = build(spec, sys.argv[2])
    except AssertionError as e:
        sys.exit(f"ERROR {e}")
    routes, segs = spec["routes"], spec["segments"]
    print(f"Wrote: {sys.argv[2]}\nSegments: {len(segs)}   routes: {' / '.join(routes)}")
    for r in routes:
        print(f"  {r}: {counts[r]}")
    if len(routes) > 1:
        diff = [s["name"] for s in segs if len({s["_vk"][r] for r in routes}) > 1]
        print(f"\nSegments where the routes disagree: {len(diff)}/{len(segs)} - explain each in the conclusions:")
        for d in diff:
            print("  ·", d)
        neg, pos = {"na", "dec"}, {"new", "inc"}
        opp = [s["name"] for s in segs if any(s["_vk"][a] in neg and s["_vk"][b] in pos
                                               for a in routes for b in routes if a != b)]
        if opp:
            print(f"\n⭐ Of these, truly opposite (route-exclusive) {len(opp)}:")
            for d in opp:
                print("  ·", d)


if __name__ == "__main__":
    main()
