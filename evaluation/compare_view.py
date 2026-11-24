#!/usr/bin/env python3
"""
compare_view.py - compare a skill-generated investment view with a hand-written one.

The hand-written view is the reference (a "label"); the generated view is the
skill's output for the same company and the same inputs. The script reports
proxies, not a quality score:

  blocks     lines / characters per block (verbosity and style drift)
  labels     whether each quarter block has the fixed parts (upside drivers,
             verdict, five dimensions, product table, Other)
  marks      the five dimension marks for EVERY quarter both files have,
             side by side, plus the agreement rate
  numbers    value-based matching: "$1.3B" = "13亿" = "$1,300M", "430bps" =
             "4.3pp", "CY27" = "2027", ranges split into both ends; recall
             (share of the reference's numbers found) and precision
  terms      products / companies / technologies, case-insensitive, with an
             alias table (INTEL = Intel, NV = NVIDIA, TSM = TSMC ...)
  lines      for each reference line, how much of it (CJK bigrams, words,
             numbers) appears anywhere in the generated file: covered /
             partial / missed. Also the generated lines the reference has
             nothing like ("skill-only").
  tables     product-table rows matched by their first cell

Text and tables are measured separately, because tables are often copied
from the call log while the text is where the judgment lives.

Usage:
  python compare_view.py GENERATED.md REFERENCE.md [--json] [--alias A=B ...]
         [--show-lines N]

Exit code 0 unless a file cannot be read. Python 3, standard library only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DIMS = {"财务": "Financials", "细分产业": "Sub-industry", "订单": "Orders",
        "客户": "Customers", "业绩节奏": "Momentum"}
LABELS = {"upside": ("下一季超预期点", "下次超预期点", "Next-quarter upside drivers"),
          "verdict": ("判断", "Verdict"),
          "other": ("其他", "Other")}
QH = re.compile(r"^#\s*---\s*(?:FY ?(\d{2}) ?Q([1-4])|(\d{2}) ?FY ?Q([1-4]))\s*---\s*(.*)$")
MARK = r"(✅️|✅|⚠️|⚠|🔻)"
ALIASES = {"intel": "intel", "nv": "nvidia", "nvda": "nvidia", "tsm": "tsmc", "台积电": "tsmc",
           "英伟达": "nvidia", "nvswitch": "nvlink switch", "sk": "sk hynix", "hynix": "sk hynix",
           "co-packaged": "cpo", "transceivers": "transceiver", "optical": "optics"}
STOP = {"q1", "q2", "q3", "q4", "fy", "cy", "yoy", "qoq", "eps", "pe", "peg", "gm", "om", "opm",
        "opex", "ceo", "cfo", "cto", "evp", "vs", "ok", "h1", "h2", "ai", "fcf", "fcff", "lta",
        "non-gaap", "gaap", "ttm", "ntm", "tam", "sam", "pp", "bps", "the", "and", "for", "of", "to"}
# common English words that are capitalised in mixed Chinese / English notes but are not terms
COMMON = set("""about after all also base based before both but can components core customers driven
engaged every first focus from growth has have into its just largest leading main more most new next
now one only other our over previously revenue shifting since some story that their them there these
they this through track two upside very was we what when where which while will with within year
technology vertically entire previously general generally initial broad overall today total""".split())

# ---------------------------------------------------------------- parsing

def blocks(text: str) -> dict:
    """Split a view into blocks keyed core / Q:FY26 Q2 / events / est / notes."""
    out, cur = {}, None
    for line in text.splitlines():
        if line.startswith("# "):
            m = QH.match(line)
            if m:
                fy, q = (m.group(1), m.group(2)) if m.group(1) else (m.group(3), m.group(4))
                cur = f"Q:FY{fy} Q{q}"
                out[cur] = {"head": m.group(5).strip(), "lines": []}
                continue
            h = line.lstrip("# ").strip("- ").strip()
            cur = ("core" if h.startswith(("核心", "Core")) else
                   "events" if h.startswith(("其他会议", "Other Events")) else
                   "est" if h.startswith(("测算", "Estimates")) else
                   "notes" if h.startswith(("其他说明", "Other Notes")) else h)
            out[cur] = {"head": "", "lines": []}
        elif cur:
            out[cur]["lines"].append(line)
    return out


def clean(line: str) -> str:
    line = re.sub(r"!\[\[[^\]]*\]\]|!\[[^\]]*\]\([^)]*\)|https?://\S+", " ", line)   # images, links
    return line


def is_table(line: str) -> bool:
    return line.strip().startswith("|")


def split_text_table(lines):
    text = [clean(l) for l in lines if not is_table(l)]
    rows = [l for l in lines if is_table(l) and not re.fullmatch(r"\|?[\s:|\-]+\|?", l.strip())]
    return text, rows

# ---------------------------------------------------------------- numbers

UNIT_SCALE = {"亿": ("usd", 100.0), "万": ("usd", 0.01), "b": ("usd", 1000.0), "bn": ("usd", 1000.0),
              "billion": ("usd", 1000.0), "million": ("usd", 1.0), "thousand": ("usd", 0.001), "percent": ("pct", 1.0),
              "m": ("usd", 1.0), "mn": ("usd", 1.0), "k": ("usd", 0.001),
              "%": ("pct", 1.0), "pp": ("pct", 1.0), "个百分点": ("pct", 1.0), "bps": ("pct", 0.01),
              "x": ("mult", 1.0), "倍": ("mult", 1.0), "g": ("spec", 1.0), "t": ("spec", 1000.0)}
DATE = re.compile(r"\b(20\d{2})-(\d{2})-(\d{2})\b|^\s*(\d{1,2})/(\d{1,2})\s*(?=$|（|\()", re.M)   # M/D only as a heading line ("9/7"); 2/3 is a fraction
PERIOD = re.compile(r"\b([12])H ?(?:CY|FY)?'?(\d{2,4})\b|\bCY ?'?(\d{2})\b|(?<![\dA-Za-z])(\d{2})年|"
                    r"\b(20\d{2}) ?Q([1-4])\b|\bC?Q([1-4]) ?'?(\d{2})\b|\bQ([1-4]) (20\d{2})\b")
NUM = re.compile(r"(\$)?(\d+(?:,\d{3})*(?:\.\d+)?)(?:\s*[–\-~至到]\s*\$?(\d+(?:,\d{3})*(?:\.\d+)?))?"
                 r"\s*(个百分点|亿|万|billion|million|thousand|percent|bps|bn|mn|pp|%|倍|[xBMKGT])?(?![A-Za-z0-9])", re.I)


def numbers(text: str) -> list:
    """Return normalized (class, value) tuples found in text."""
    out = []
    t = text

    def take(m, items):
        out.extend(items)
        return " " * len(m.group(0))

    t = DATE.sub(lambda m: take(m, [("date", f"{int(m.group(2)):02d}-{int(m.group(3)):02d}")]
                                if m.group(1) else
                                [("date", f"{int(m.group(4)):02d}-{int(m.group(5)):02d}")]
                                if 1 <= int(m.group(4)) <= 12 and 1 <= int(m.group(5)) <= 31 else []), t)

    def yr(s):
        s = s.lstrip("'")
        return int(s) if len(s) == 4 else 2000 + int(s)

    def per(m):
        if m.group(1):
            return take(m, [("half", f"{yr(m.group(2))}H{m.group(1)}"), ("year", float(yr(m.group(2))))])
        if m.group(3):
            return take(m, [("year", float(yr(m.group(3))))])
        if m.group(4):
            return take(m, [("year", float(yr(m.group(4))))])
        if m.group(5):
            return take(m, [("qtr", f"{m.group(5)}Q{m.group(6)}"), ("year", float(m.group(5)))])
        if m.group(7):
            return take(m, [("qtr", f"{yr(m.group(8))}Q{m.group(7)}")])
        return take(m, [("qtr", f"{m.group(10)}Q{m.group(9)}"), ("year", float(m.group(10)))])

    t = PERIOD.sub(per, t)
    t = re.sub(r"\bFY ?\d{2}\b|\bQ[1-4]\b", " ", t)               # fiscal labels are not facts
    for m in NUM.finditer(t):
        cur, a, b, unit = m.group(1), m.group(2), m.group(3), (m.group(4) or "").lower()
        vals = [float(a.replace(",", ""))] + ([float(b.replace(",", ""))] if b else [])
        if unit in UNIT_SCALE:
            cls, k = UNIT_SCALE[unit]
        elif cur:
            cls, k = "usd", 1e-6                                   # bare dollars -> $M
        else:
            cls, k = "plain", 1.0
        for v in vals:
            if cls == "plain":
                if 1900 <= v <= 2100 and v == int(v):
                    out.append(("year", v))
                    continue
                if v < 10 and v == int(v):                          # list markers, counts like "3"
                    continue
            if cls == "usd" and cur and not unit and v < 1000:      # "$0.82" per-share figures
                cls2, v2 = "per_share", v
                out.append((cls2, v2))
                continue
            out.append((cls, round(v * k, 6)))
    return out


def num_match(a, b) -> bool:
    if a[0] != b[0]:
        return False
    if isinstance(a[1], str):
        return a[1] == b[1]
    x, y = a[1], b[1]
    if a[0] in ("year",):
        return x == y
    return abs(x - y) <= max(abs(x), abs(y)) * 0.005 + 1e-9


def coverage(ref: list, gen: list):
    ref_u = list(dict.fromkeys(ref))
    gen_u = list(dict.fromkeys(gen))
    hit_r = [r for r in ref_u if any(num_match(r, g) for g in gen_u)]
    hit_g = [g for g in gen_u if any(num_match(g, r) for r in ref_u)]
    miss = [r for r in ref_u if r not in hit_r]
    return (len(hit_r), len(ref_u), len(hit_g), len(gen_u), miss)


def fmt_num(n):
    c, v = n
    if c == "usd":
        return f"${v:g}M"
    if c == "pct":
        return f"{v:g}%"
    if c == "mult":
        return f"{v:g}x"
    if c == "per_share":
        return f"${v:g}/sh"
    if c == "year":
        return f"{int(v)}"
    return f"{v}" if isinstance(v, str) else f"{v:g}"

# ---------------------------------------------------------------- terms

TOK = re.compile(r"[A-Za-z][A-Za-z0-9+.&\-]*[A-Za-z0-9+]|[A-Za-z]")


def terms(text: str, aliases: dict) -> set:
    out = set()
    for line in text.splitlines():
        for m in TOK.finditer(line):
            w = m.group(0)
            caps = sum(ch.isupper() for ch in w)
            keep = caps >= 2 or (any(ch.isdigit() for ch in w) and caps >= 1) or (w[0].isupper() and len(w) > 2)
            if not keep:
                continue
            for part in w.split("/"):
                p = part.strip(".-").lower()
                p = aliases.get(p, p)
                if (len(p) > 1 and p not in STOP and not (caps == 1 and p in COMMON)
                        and not re.fullmatch(r"(?:fy|cy)\d{2,4}|q[1-4]|\d+[a-z]?", p)):
                    out.add(p)
    return out

# ---------------------------------------------------------------- lines

MARKUP = re.compile(r"[*_`>#|]|✅️|✅|⚠️|⚠|🔻|🔼|🔽|🆕|➡️|📌|⭐️|└")


def feats(line: str) -> set:
    s = MARKUP.sub(" ", clean(line)).lower()
    f = set()
    cjk = re.findall(r"[一-鿿]+", s)
    for run in cjk:
        f.update(run[i:i + 2] for i in range(len(run) - 1))
    f.update(w for w in re.findall(r"[a-z][a-z0-9+.\-]+", s) if w not in STOP)
    f.update(fmt_num(n) for n in numbers(line))
    return f


def line_report(ref_lines, gen_lines, min_feats=4):
    gen_all = set().union(*[feats(l) for l in gen_lines]) if gen_lines else set()
    ref_all = set().union(*[feats(l) for l in ref_lines]) if ref_lines else set()
    res = {"covered": 0, "partial": 0, "missed": 0, "missed_lines": [], "skill_only_lines": []}
    for l in ref_lines:
        f = feats(l)
        if len(f) < min_feats:
            continue
        c = len(f & gen_all) / len(f)
        k = "covered" if c >= 0.5 else "partial" if c >= 0.25 else "missed"
        res[k] += 1
        if k == "missed":
            res["missed_lines"].append(l.strip())
    for l in gen_lines:
        f = feats(l)
        if len(f) >= min_feats and len(f & ref_all) / len(f) < 0.25:
            res["skill_only_lines"].append(l.strip())
    res["skill_only"] = len(res["skill_only_lines"])
    return res

# ---------------------------------------------------------------- per-block

def marks(lines):
    res = {}
    for l in lines:
        s = l.strip().lstrip("*")
        for zh, en in DIMS.items():
            m = re.match(rf"^{MARK}?\s*\**({zh}|{en})\**\s*(（[^）]*）|\([^)]*\))?\s*([：:]|$)", s)
            if m and zh not in res:
                res[zh] = (m.group(1) or "—").rstrip("️")
    return res


def labels(lines):
    body = [l.strip().lstrip("⭐️").strip() for l in lines]
    have = {k: any(b.startswith(v) for b in body for v in vs) for k, vs in LABELS.items()}
    have["dims"] = len(marks(lines))
    have["product_table"] = sum(1 for l in lines if is_table(l)) >= 3
    return have


def table_rows(rows):
    keys = []
    for r in rows:
        cells = [c.strip() for c in r.strip().strip("|").split("|")]
        if cells and cells[0] and not re.fullmatch(r"产品.*|Product.*|产品 / 业务线|里程碑|指标|环节.*", cells[0]):
            keys.append(cells[0])
    return keys


def compare_block(g_lines, r_lines, aliases):
    gt, gr = split_text_table(g_lines)
    rt, rr = split_text_table(r_lines)
    out = {}
    for part, gl, rl in (("text", gt, rt), ("tables", gr, rr)):
        if not rl:
            continue
        gtx, rtx = "\n".join(gl), "\n".join(rl)
        hr, nr, hg, ng, miss = coverage(numbers(rtx), numbers(gtx))
        gw, rw = terms(gtx, aliases), terms(rtx, aliases)
        out[part] = {"num_recall": hr / nr if nr else None, "num_hit": hr, "num_ref": nr,
                     "num_precision": hg / ng if ng else None, "num_gen": ng,
                     "num_missed": [fmt_num(m) for m in miss],
                     "term_recall": len(gw & rw) / len(rw) if rw else None,
                     "term_hit": len(gw & rw), "term_ref": len(rw),
                     "term_missed": sorted(rw - gw)}
    out["lines"] = line_report([l for l in rt if l.strip()], [l for l in gt if l.strip()])
    gk, rk = table_rows(gr), table_rows(rr)
    if rk:
        gkf = [feats(k) for k in gk]
        hit = [k for k in rk if any(len(feats(k) & f) / max(1, len(feats(k))) >= 0.5 for f in gkf)]
        out["table_rows"] = {"ref": len(rk), "gen": len(gk), "matched": len(hit),
                             "ref_only": [k for k in rk if k not in hit]}
    return out


def size(b):
    if not b:
        return None
    return {"lines": sum(1 for l in b["lines"] if l.strip()), "chars": sum(len(l) for l in b["lines"])}


def compare(gen_path: Path, ref_path: Path, aliases: dict) -> dict:
    tick = re.match(r"[A-Z]{2,6}", ref_path.name)
    if tick:
        STOP.add(tick.group(0).lower())
    G = blocks(gen_path.read_text(encoding="utf-8"))
    R = blocks(ref_path.read_text(encoding="utf-8"))
    rep = {"generated": gen_path.name, "reference": ref_path.name, "blocks": {}, "quarters": {}, "sections": {}}
    order = lambda x: (0 if x == "core" else 1 if x.startswith("Q:") else 2, [-ord(c) for c in x] if x.startswith("Q:") else x)
    for k in sorted(set(G) | set(R), key=order):
        rep["blocks"][k] = {"generated": size(G.get(k)), "reference": size(R.get(k))}
    common = sorted([k for k in G if k.startswith("Q:") and k in R], reverse=True)
    for k in common:
        gm, rm = marks(G[k]["lines"]), marks(R[k]["lines"])
        rep["quarters"][k[2:]] = {
            "tag": {"generated": G[k]["head"], "reference": R[k]["head"]},
            "marks": {zh: {"generated": gm.get(zh), "reference": rm.get(zh)} for zh in DIMS},
            "agree": sum(1 for zh in DIMS if zh in gm and gm.get(zh) == rm.get(zh)),
            "compared": sum(1 for zh in DIMS if zh in gm and zh in rm),
            "labels": {"generated": labels(G[k]["lines"]), "reference": labels(R[k]["lines"])},
        }
        rep["sections"][k] = compare_block(G[k]["lines"], R[k]["lines"], aliases)
    for name in ("core", "events", "est"):
        if name in G and name in R:
            rep["sections"][name] = compare_block(G[name]["lines"], R[name]["lines"], aliases)
    rep["missing_in_generated"] = [k for k in R if k not in G and k != "notes"]
    # whole-file line coverage: content placed in another block still counts here
    allg = [l for b in G.values() for l in b["lines"] if l.strip() and not is_table(l)]
    allr = [l for k, b in R.items() if k != "notes" for l in b["lines"] if l.strip() and not is_table(l)]
    lr = line_report(allr, allg)
    rep["file_lines"] = {k: lr[k] for k in ("covered", "partial", "missed", "skill_only")}
    return rep

# ---------------------------------------------------------------- output

def pct(x):
    return "—" if x is None else f"{x:.0%}"


def to_markdown(rep: dict, show_lines: int) -> str:
    o = [f"# Comparison: {rep['generated']}  vs  {rep['reference']}", "",
         "| block | generated | reference |", "|---|---|---|"]
    for k, v in rep["blocks"].items():
        f = lambda s: f"{s['lines']} lines / {s['chars']:,} chars" if s else "—"
        o.append(f"| {k} | {f(v['generated'])} | {f(v['reference'])} |")
    if rep["missing_in_generated"]:
        o += ["", f"Blocks in the reference only: {', '.join(rep['missing_in_generated'])}"]
    for q, d in rep["quarters"].items():
        o += ["", f"## {q}: tag, labels and marks", "",
              f"- generated tag: `{d['tag']['generated']}`", f"- reference tag: `{d['tag']['reference']}`", "",
              "| dimension | generated | reference |", "|---|---|---|"]
        for zh, m in d["marks"].items():
            o.append(f"| {zh} | {m['generated'] or '—'} | {m['reference'] or '—'} |")
        o.append(f"\nmark agreement: {d['agree']}/{d['compared']} (dimensions present in both)")
        lg, lr_ = d["labels"]["generated"], d["labels"]["reference"]
        o.append("labels (gen / ref): " + ", ".join(f"{k} {lg[k]}/{lr_[k]}" for k in lg))
    for name, s in rep["sections"].items():
        o += ["", f"## {name}: coverage of the reference", ""]
        for part in ("text", "tables"):
            if part in s:
                p = s[part]
                o.append(f"- {part} numbers: recall {pct(p['num_recall'])} ({p['num_hit']}/{p['num_ref']}), "
                         f"precision {pct(p['num_precision'])} ({p['num_gen']} in generated)")
                o.append(f"- {part} terms:   recall {pct(p['term_recall'])} ({p['term_hit']}/{p['term_ref']})")
                if p["num_missed"]:
                    o.append(f"  - numbers not found: {', '.join(p['num_missed'][:30])}")
                if p["term_missed"]:
                    o.append(f"  - terms not found: {', '.join(p['term_missed'][:30])}")
        L = s["lines"]
        o.append(f"- reference lines: {L['covered']} covered / {L['partial']} partial / {L['missed']} missed; "
                 f"skill-only lines: {L['skill_only']}")
        if show_lines:
            for l in L["missed_lines"][:show_lines]:
                o.append(f"  - missed: {l[:90]}")
            for l in L["skill_only_lines"][:show_lines]:
                o.append(f"  - skill-only: {l[:90]}")
        if "table_rows" in s:
            t = s["table_rows"]
            o.append(f"- table rows: {t['matched']}/{t['ref']} reference rows matched ({t['gen']} rows generated)")
            if t["ref_only"]:
                o.append(f"  - reference-only rows: {'; '.join(t['ref_only'][:15])}")
    fl = rep["file_lines"]
    o += ["", f"Whole file (any block): {fl['covered']} covered / {fl['partial']} partial / {fl['missed']} missed "
          f"reference lines; {fl['skill_only']} skill-only lines."]
    return "\n".join(o)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("generated", type=Path)
    ap.add_argument("reference", type=Path)
    ap.add_argument("--json", action="store_true", help="print the full report as JSON")
    ap.add_argument("--alias", action="append", default=[], metavar="A=B", help="extra term alias, e.g. SA=scale-across")
    ap.add_argument("--show-lines", type=int, default=5, help="missed / skill-only lines to print per block (0 = none)")
    a = ap.parse_args()
    aliases = dict(ALIASES)
    for s in a.alias:
        k, _, v = s.partition("=")
        aliases[k.strip().lower()] = v.strip().lower()
    try:
        rep = compare(a.generated, a.reference, aliases)
    except OSError as e:
        print(f"ERROR {e}", file=sys.stderr)
        return 2
    print(json.dumps(rep, ensure_ascii=False, indent=1) if a.json else to_markdown(rep, a.show_lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
