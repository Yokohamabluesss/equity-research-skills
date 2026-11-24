#!/usr/bin/env python3
"""
diagnose.py - turn one experiment's comparison results into an error analysis.

Reads the per-run JSON files written by run_eval.py and the manifest, and sorts
every difference between the skill's output and the hand-written reference
into one of six categories. The category decides who acts on it:

  input_gap   a block is missing because its input was missing      -> fix the inputs, not the rules
  format      a fixed part is missing (label, mark, product table)   -> validator / template fix
  judgment    a dimension mark differs                               -> the analyst decides; never auto-fitted
  coverage    a section's numbers or terms are under-covered         -> rule candidate if >= 2 companies
  length      a block is much longer / shorter than the reference    -> rule candidate if >= 2 companies
  skill_only  lines the reference has nothing like                   -> possible gains; reviewed by a human

Only runs whose manifest split is "train" (the default) count as evidence for
a rule change. Held-out runs are reported but never used as evidence, so a
rule cannot be tuned on the data that will later judge it.

Usage:
  python diagnose.py --experiment ID --eval-dir OUT/ID [--manifest manifest.json]
                     [--skill-version V] [--min-companies 2] [--json]

Writes nothing; prints markdown (or JSON). Save it next to the per-run files in
the private workspace: it quotes no reference text, but it points to lines that do.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

NUM_FLOOR = 0.75      # number recall below this is a coverage finding
TERM_FLOOR = 0.60     # term recall below this is a coverage finding
LEN_BAND = (0.5, 1.5)  # generated / reference characters outside this is a length finding
NEEDS = {"est": "valuation_workbook", "events": "event_files"}


def load(eval_dir: Path, run_id: str):
    p = eval_dir / f"{run_id}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def diagnose(exp: dict, eval_dir: Path, min_companies: int, skill_version: str | None = None) -> dict:
    """Only runs of one skill version are diagnosed (default: the latest in the experiment),
    so an old rule version's errors are not counted as evidence against the current rules."""
    versions = sorted({r.get("skill_version", "") for r in exp["runs"]})
    version = skill_version or versions[-1]
    found = defaultdict(list)          # category -> list of findings
    for run in [r for r in exp["runs"] if r.get("skill_version", "") == version]:
        rep = load(eval_dir, run["id"])
        if rep is None:
            found["missing_run"].append({"run": run["id"]})
            continue
        base = {"run": run["id"], "ticker": run["ticker"], "split": run.get("split", "train")}
        inputs = run.get("inputs", {})
        # input gaps / missing blocks
        for blk in rep.get("missing_in_generated", []):
            need = NEEDS.get(blk)
            cat = "input_gap" if need and inputs.get(need) is False else "format"
            found[cat].append({**base, "section": blk, "detail": f"block missing (input {need}={inputs.get(need)})"})
        for q, d in rep.get("quarters", {}).items():
            g = d["labels"]["generated"]
            missing = [k for k in ("upside", "verdict", "other", "product_table") if not g.get(k)]
            if g.get("dims", 0) < 5:
                missing.append(f"dims={g.get('dims')}")
            if not d["tag"]["generated"]:
                missing.append("tag")
            if missing:
                found["format"].append({**base, "section": f"Q:{q}", "detail": "missing " + ", ".join(missing)})
            for dim, m in d["marks"].items():
                if m["generated"] and m["reference"] and m["generated"] != m["reference"]:
                    found["judgment"].append({**base, "section": f"Q:{q}", "dimension": dim,
                                              "detail": f"skill {m['generated']} / human {m['reference']}"})
        for sec, s in rep.get("sections", {}).items():
            kind = "quarter" if sec.startswith("Q:") else sec
            for part in ("text", "tables"):
                p = s.get(part)
                if not p:
                    continue
                if p["num_recall"] is not None and p["num_ref"] >= 5 and p["num_recall"] < NUM_FLOOR:
                    found["coverage"].append({**base, "section": sec, "key": f"{kind}/{part}/numbers",
                                              "detail": f"number recall {p['num_recall']:.0%} ({p['num_hit']}/{p['num_ref']})"})
                if p["term_recall"] is not None and p["term_ref"] >= 5 and p["term_recall"] < TERM_FLOOR:
                    found["coverage"].append({**base, "section": sec, "key": f"{kind}/{part}/terms",
                                              "detail": f"term recall {p['term_recall']:.0%}; missing e.g. "
                                                        + ", ".join(p["term_missed"][:6])})
            tr = s.get("table_rows")
            if tr and tr["ref"] and tr["matched"] / tr["ref"] < 0.8:
                found["coverage"].append({**base, "section": sec, "key": f"{kind}/table rows",
                                          "detail": f"{tr['matched']}/{tr['ref']} reference rows"})
            if s.get("lines", {}).get("skill_only"):
                found["skill_only"].append({**base, "section": sec, "detail": f"{s['lines']['skill_only']} lines"})
        for blk, sz in rep.get("blocks", {}).items():
            g, r = sz.get("generated"), sz.get("reference")
            if g and r and r["chars"] >= 200:
                ratio = g["chars"] / r["chars"]
                if not LEN_BAND[0] <= ratio <= LEN_BAND[1]:
                    found["length"].append({**base, "section": blk,
                                            "key": f"{'quarter' if blk.startswith('Q:') else blk}/length",
                                            "detail": f"{ratio:.1f}x the reference ({'longer' if ratio > 1 else 'shorter'})",
                                            "direction": "longer" if ratio > 1 else "shorter"})
    # patterns: the same finding across companies, counted on train runs only
    patterns = []
    for cat, keyf in (("coverage", lambda f: f["key"]),
                      ("length", lambda f: f"{f['key']}/{f['direction']}"),
                      ("judgment", lambda f: f"marks/{f['dimension']}")):
        groups = defaultdict(set)
        heldout = defaultdict(set)
        for f in found[cat]:
            (groups if f["split"] == "train" else heldout)[keyf(f)].add(f["ticker"])
        for k in sorted(set(groups) | set(heldout)):
            n = len(groups.get(k, ()))
            if cat == "judgment":
                action = "ask the analyst (rule question)" if n >= min_companies else "note; ask if it recurs"
            else:
                action = "rule candidate" if n >= min_companies else "record only (single company)"
            patterns.append({"category": cat, "key": k, "train_companies": sorted(groups.get(k, ())),
                             "heldout_companies": sorted(heldout.get(k, ())), "action": action})
    return {"experiment": exp["id"], "skill_version": version, "other_versions": [v for v in versions if v != version],
            "findings": found, "patterns": patterns,
            "thresholds": {"number_recall": NUM_FLOOR, "term_recall": TERM_FLOOR, "length_band": LEN_BAND,
                           "min_companies": min_companies}}


ROUTE = {"input_gap": "fix the inputs, not the rules", "format": "validator or template fix",
         "judgment": "the analyst decides; never fitted automatically",
         "coverage": "rule candidate only with >= 2 companies", "length": "rule candidate only with >= 2 companies",
         "skill_only": "possible gains: a human reads them", "missing_run": "re-run run_eval"}


def to_markdown(d: dict) -> str:
    o = [f"# Diagnosis: {d['experiment']} ({d['skill_version']})", "",
         *([f"Not diagnosed (other skill versions): {', '.join(d['other_versions'])}", ""] if d["other_versions"] else []),
         "## Patterns (train runs are evidence; held-out runs are not)", "",
         "| category | finding | train companies | held-out companies | action |", "|---|---|---|---|---|"]
    for p in d["patterns"]:
        o.append(f"| {p['category']} | {p['key']} | {', '.join(p['train_companies']) or '—'} | "
                 f"{', '.join(p['heldout_companies']) or '—'} | {p['action']} |")
    for cat in ("input_gap", "format", "judgment", "coverage", "length", "skill_only", "missing_run"):
        items = d["findings"].get(cat, [])
        if not items:
            continue
        o += ["", f"## {cat} ({len(items)}): {ROUTE[cat]}", ""]
        for f in items:
            o.append(f"- {f.get('run')} [{f.get('split', '')}] {f.get('section', '')}: {f.get('detail', '')}")
    t = d["thresholds"]
    o += ["", f"Thresholds: number recall < {t['number_recall']:.0%}, term recall < {t['term_recall']:.0%}, "
              f"length outside {t['length_band'][0]}-{t['length_band'][1]}x, pattern = {t['min_companies']}+ companies. "
              "Line coverage is not a finding on its own: it undercounts paraphrase."]
    return "\n".join(o)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, default=Path(__file__).with_name("manifest.json"))
    ap.add_argument("--experiment", required=True)
    ap.add_argument("--eval-dir", type=Path, required=True, help="run_eval output folder of this experiment")
    ap.add_argument("--min-companies", type=int, default=2)
    ap.add_argument("--skill-version", help="diagnose only runs of this skill version (default: the latest)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    man = json.loads(a.manifest.read_text(encoding="utf-8"))
    exps = {e["id"]: e for e in man["experiments"]}
    if a.experiment not in exps:
        print(f"ERROR unknown experiment {a.experiment!r}")
        return 2
    d = diagnose(exps[a.experiment], a.eval_dir, a.min_companies, a.skill_version)
    print(json.dumps(d, ensure_ascii=False, indent=1) if a.json else to_markdown(d))
    return 0


if __name__ == "__main__":
    sys.exit(main())
