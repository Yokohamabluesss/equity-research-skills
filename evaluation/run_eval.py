#!/usr/bin/env python3
"""
run_eval.py - run compare_view.py over every pair listed in a manifest.

The manifest lists skill outputs and the hand-written references they are
compared with. Paths in the manifest are relative to --root (a private
workspace: the references are personal notes and are not part of this
repository). Each run records the input condition, because a gap caused by a
missing input is not a skill error.

  python run_eval.py --experiment ID --root ../../workspace --out OUT_DIR

The manifest is a list of experiments. One experiment = one question asked at
one time (e.g. "v2 vs the human on three companies"); it can cover several
companies. Every experiment has its own report, reports/{ID}.md: a new
experiment always means a new report. The runner creates the report from a
skeleton the first time, and afterwards refreshes only the generated table
between the summary markers, so the hand-written findings are never
overwritten. An experiment marked "status": "closed" is a point-in-time record
and is refused; open a new experiment instead.

Writes, for every run, OUT_DIR/{ID}/{run}.md (full comparison, including the
reference lines the skill missed) and .json, plus summary.md / summary.json.
Only the report is meant to be published; the per-run files quote the reference.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from compare_view import ALIASES, compare, to_markdown  # noqa: E402


def avg(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def summarize(run: dict, rep: dict) -> dict:
    q = rep["quarters"]
    s = rep["sections"]
    qkeys = [k for k in s if k.startswith("Q:")]
    pick = lambda part, metric, keys: avg([s[k][part][metric] for k in keys if part in s[k]])
    blk = rep["blocks"]
    ratio = lambda k: (blk[k]["generated"]["chars"] / blk[k]["reference"]["chars"]
                       if k in blk and blk[k]["generated"] and blk[k]["reference"] else None)
    fl = rep["file_lines"]
    n_ref = fl["covered"] + fl["partial"] + fl["missed"]
    return {
        "id": run["id"], "ticker": run["ticker"], "skill_version": run.get("skill_version"),
        "quarters": len(q),
        "marks_agree": sum(d["agree"] for d in q.values()),
        "marks_compared": sum(d["compared"] for d in q.values()),
        "mark_diffs": [f"{qq} {zh}: skill {m['generated']} / human {m['reference']}"
                       for qq, d in q.items() for zh, m in d["marks"].items()
                       if m["generated"] and m["reference"] and m["generated"] != m["reference"]],
        "quarter_text_num_recall": pick("text", "num_recall", qkeys),
        "quarter_text_term_recall": pick("text", "term_recall", qkeys),
        "quarter_table_num_recall": pick("tables", "num_recall", qkeys),
        "core_term_recall": s["core"]["text"]["term_recall"] if "core" in s and "text" in s["core"] else None,
        "est_num_recall": s["est"]["text"]["num_recall"] if "est" in s and "text" in s["est"] else None,
        "events_num_recall": s["events"]["text"]["num_recall"] if "events" in s and "text" in s["events"] else None,
        "lines_covered": fl["covered"] / n_ref if n_ref else None,
        "lines_partial": fl["partial"] / n_ref if n_ref else None,
        "lines_missed": fl["missed"] / n_ref if n_ref else None,
        "skill_only_lines": fl["skill_only"],
        "core_len_ratio": ratio("core"),
        "missing_blocks": rep["missing_in_generated"],
        "inputs": run.get("inputs", {}),
        "notes": run.get("notes", ""),
    }


def pct(x):
    return "—" if x is None else f"{x:.0%}"


def ratio_s(x):
    return "—" if x is None else f"{x:.1f}x"


START, END = "<!-- summary:start -->", "<!-- summary:end -->"

REPORT_SKELETON = """# {title}

[English](#english) | [中文](#中文)

<a id="english"></a>

**Question.** {question}

## Setup

{setup}

## Results

{START}
{END}

## Findings

(to be written after reading the per-run files in the workspace)

## Limits

## Next

---

<a id="中文"></a>

# {title}

**问题。** {question_zh}

## 设置

## 结果

（同上表）

## 结论

## 局限

## 下一步
"""


def table(rows):
    hdr = ("| run | skill | marks | quarter numbers (text) | quarter terms | table numbers | core terms | "
           "estimates numbers | event numbers | ref lines covered / partial / missed | skill-only lines | core length vs human |")
    out = [hdr, "|" + "---|" * (hdr.count("|") - 1)]
    for x in rows:
        out.append(f"| {x['id']} | {x['skill_version']} | {x['marks_agree']}/{x['marks_compared']} | "
                   f"{pct(x['quarter_text_num_recall'])} | {pct(x['quarter_text_term_recall'])} | "
                   f"{pct(x['quarter_table_num_recall'])} | {pct(x['core_term_recall'])} | {pct(x['est_num_recall'])} | "
                   f"{pct(x['events_num_recall'])} | {pct(x['lines_covered'])} / {pct(x['lines_partial'])} / "
                   f"{pct(x['lines_missed'])} | {x['skill_only_lines']} | {ratio_s(x['core_len_ratio'])} |")
    return "\n".join(out)


def update_report(path: Path, exp: dict, tbl: str) -> str:
    """One report per experiment: create it from the skeleton, or refresh only the
    generated table between the markers. Hand-written findings are never touched."""
    if not path.exists():
        setup = "\n".join(f"- {r['id']}: {r.get('skill_version', '')}; inputs {r.get('inputs', {})}; {r.get('notes', '')}"
                           for r in exp["runs"])
        path.write_text(REPORT_SKELETON.format(title=exp.get("title", exp["id"]), question=exp.get("question", ""),
                                               question_zh=exp.get("question_zh", ""), setup=setup,
                                               START=START + "\n" + tbl, END=END), encoding="utf-8")
        return "created"
    s = path.read_text(encoding="utf-8")
    if START not in s or END not in s:
        return "no markers - table not inserted"
    a, b = s.index(START) + len(START), s.index(END)
    path.write_text(s[:a] + "\n" + tbl + "\n" + s[b:], encoding="utf-8")
    return "table refreshed"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, default=Path(__file__).with_name("manifest.json"))
    ap.add_argument("--experiment", required=True, help="experiment id from the manifest (one report per experiment)")
    ap.add_argument("--root", type=Path, required=True, help="workspace folder the manifest paths are relative to")
    ap.add_argument("--out", type=Path, required=True, help="private output folder (per-run files quote the references)")
    ap.add_argument("--reports", type=Path, default=Path(__file__).with_name("reports"))
    a = ap.parse_args()
    man = json.loads(a.manifest.read_text(encoding="utf-8"))
    exps = {e["id"]: e for e in man["experiments"]}
    if a.experiment not in exps:
        print(f"ERROR unknown experiment {a.experiment!r}; known: {', '.join(exps)}")
        return 2
    exp = exps[a.experiment]
    if exp.get("status") == "closed":
        print(f"ERROR experiment {exp['id']} is closed: its results are a point-in-time record. "
              "Add a new experiment (new id, new report) instead.")
        return 2
    out = a.out / exp["id"]
    out.mkdir(parents=True, exist_ok=True)
    rows, bad = [], 0
    for run in exp["runs"]:
        g, r = a.root / run["generated"], a.root / run["reference"]
        if not g.exists() or not r.exists():
            print(f"SKIP  {run['id']}: missing {g if not g.exists() else r}")
            bad += 1
            continue
        aliases = dict(ALIASES)
        aliases.update({k.lower(): v.lower() for k, v in run.get("aliases", {}).items()})
        rep = compare(g, r, aliases)
        (out / f"{run['id']}.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
        (out / f"{run['id']}.md").write_text(to_markdown(rep, 50), encoding="utf-8")
        rows.append(summarize(run, rep))
        print(f"OK    {run['id']}")
    (out / "summary.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    tbl = table(rows)
    (out / "summary.md").write_text(tbl + "\n", encoding="utf-8")
    a.reports.mkdir(parents=True, exist_ok=True)
    print(f"report {a.reports / (exp['id'] + '.md')}: {update_report(a.reports / (exp['id'] + '.md'), exp, tbl)}")
    print(tbl)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
