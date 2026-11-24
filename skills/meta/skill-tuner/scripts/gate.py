#!/usr/bin/env python3
"""
gate.py - decide whether a rule change is accepted, from two experiments.

The baseline experiment ran the old rules; the candidate experiment ran the new
rules on the same companies and inputs. Runs are paired by (ticker, split,
input condition). The decision is made on HELD-OUT runs only: a rule change
must not make companies or quarters it was not tuned on worse.

Acceptance metrics (all on held-out pairs):
  marks agreement          must not drop
  quarter number recall    must not drop by more than the tolerance (text and tables)
  estimate number recall   must not drop by more than the tolerance
  core length ratio        must stay inside the band, or move closer to 1x

Reported but NOT used to accept: line coverage and term recall. Optimising
lexical overlap teaches a skill to write longer and copy wording (Goodhart);
these are diagnostics, not targets.

Verdicts and exit codes:
  ACCEPT       0   no held-out metric got worse, at least one held-out pair compared
  REJECT       1   any acceptance metric got worse on a held-out pair
  PROVISIONAL  3   no held-out pairs: the change can be kept for now, but cannot be accepted

Usage:
  python gate.py --baseline OUT/BASE_ID/summary.json --candidate OUT/CAND_ID/summary.json
                 [--manifest manifest.json] [--tolerance 0.02] [--json]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

LEN_BAND = (0.5, 1.5)
ACCEPT_METRICS = ("quarter_text_num_recall", "quarter_table_num_recall", "est_num_recall")
REPORT_ONLY = ("lines_covered", "quarter_text_term_recall", "core_term_recall")


def pair_key(row: dict, meta: dict) -> tuple:
    m = meta.get(row["id"], {})
    return (row["ticker"], m.get("split", "train"), json.dumps(m.get("inputs", {}), sort_keys=True))


def run_meta(manifest: Path) -> dict:
    if not manifest.exists():
        return {}
    man = json.loads(manifest.read_text(encoding="utf-8"))
    return {r["id"]: r for e in man.get("experiments", []) for r in e["runs"]}


def compare_pair(b: dict, c: dict, tol: float):
    worse, better = [], []
    mb = b["marks_agree"] / b["marks_compared"] if b["marks_compared"] else None
    mc = c["marks_agree"] / c["marks_compared"] if c["marks_compared"] else None
    if mb is not None and mc is not None:
        (worse if mc < mb else better if mc > mb else []).append(f"marks {b['marks_agree']}/{b['marks_compared']} -> "
                                                                  f"{c['marks_agree']}/{c['marks_compared']}")
    for k in ACCEPT_METRICS:
        x, y = b.get(k), c.get(k)
        if x is None or y is None:
            continue
        if y < x - tol:
            worse.append(f"{k} {x:.0%} -> {y:.0%}")
        elif y > x + tol:
            better.append(f"{k} {x:.0%} -> {y:.0%}")
    x, y = b.get("core_len_ratio"), c.get("core_len_ratio")
    if x is not None and y is not None:
        inside = LEN_BAND[0] <= y <= LEN_BAND[1]
        closer = abs(y - 1) <= abs(x - 1)
        if not inside and not closer:
            worse.append(f"core length {x:.1f}x -> {y:.1f}x (outside band, further from 1x)")
        elif closer and abs(y - 1) < abs(x - 1) - 0.05:
            better.append(f"core length {x:.1f}x -> {y:.1f}x")
    info = [f"{k} {b[k]:.0%} -> {c[k]:.0%}" for k in REPORT_ONLY if b.get(k) is not None and c.get(k) is not None]
    return worse, better, info


def gate(base_rows, cand_rows, meta, tol):
    B = {pair_key(r, meta): r for r in base_rows}
    C = {pair_key(r, meta): r for r in cand_rows}
    pairs = []
    for k in sorted(set(B) & set(C)):
        w, b, i = compare_pair(B[k], C[k], tol)
        pairs.append({"ticker": k[0], "split": k[1], "baseline": B[k]["id"], "candidate": C[k]["id"],
                      "worse": w, "better": b, "report_only": i})
    held = [p for p in pairs if p["split"] == "heldout"]
    if not held:
        verdict = "PROVISIONAL"
    elif any(p["worse"] for p in held):
        verdict = "REJECT"
    else:
        verdict = "ACCEPT"
    unpaired = sorted({r["id"] for r in base_rows + cand_rows} - {p["baseline"] for p in pairs} - {p["candidate"] for p in pairs})
    return {"verdict": verdict, "pairs": pairs, "unpaired_runs": unpaired, "tolerance": tol}


def to_markdown(g: dict) -> str:
    o = [f"# Gate: {g['verdict']}", "",
         "Decided on held-out pairs only. Train pairs show whether the change did what it aimed at; "
         "line coverage and term recall are reported, never used to accept.", "",
         "| ticker | split | baseline -> candidate | worse | better | report only |", "|---|---|---|---|---|---|"]
    for p in g["pairs"]:
        o.append(f"| {p['ticker']} | {p['split']} | {p['baseline']} -> {p['candidate']} | {'; '.join(p['worse']) or '—'} | "
                 f"{'; '.join(p['better']) or '—'} | {'; '.join(p['report_only']) or '—'} |")
    if g["unpaired_runs"]:
        o += ["", f"Unpaired runs (different ticker, split or inputs): {', '.join(g['unpaired_runs'])}"]
    if g["verdict"] == "PROVISIONAL":
        o += ["", "No held-out pair: keep the change as provisional and run a held-out experiment before accepting it."]
    return "\n".join(o)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", type=Path, required=True, help="summary.json of the baseline experiment")
    ap.add_argument("--candidate", type=Path, required=True, help="summary.json of the candidate experiment")
    ap.add_argument("--manifest", type=Path, default=Path(__file__).with_name("manifest.json"))
    ap.add_argument("--tolerance", type=float, default=0.02)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    g = gate(json.loads(a.baseline.read_text(encoding="utf-8")), json.loads(a.candidate.read_text(encoding="utf-8")),
             run_meta(a.manifest), a.tolerance)
    print(json.dumps(g, ensure_ascii=False, indent=1) if a.json else to_markdown(g))
    return {"ACCEPT": 0, "REJECT": 1, "PROVISIONAL": 3}[g["verdict"]]


if __name__ == "__main__":
    sys.exit(main())
