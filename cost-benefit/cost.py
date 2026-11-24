#!/usr/bin/env python3
"""
cost.py - the cost side of the skills' cost-vs-quality measurements.

The question for every experiment is a product decision: a cheaper way to run a
skill (smaller model, fewer inputs, fewer repeated runs, a cleaned transcript)
saves X; does quality drop by more than we accept? Quality reuses the metrics
the repository already has (validators, stability.py, compare_view.py); this
script adds the cost columns and the decision rule.

Subcommands
  inputs FILE...                       characters and estimated tokens per input,
                                       and what transcript_tool clean /
                                       split_bilingual would save
  quality --format log|digest FILE     quality of one run: validator pass, quotes
          [--source SRC] [--ref-marks M]  found verbatim, numbers traceable, and
                                       (digests) marks matching a reference
  table RUNS.json [--experiment ID]    cost and quality per run and per config,
                                       with cost relative to the baseline config
  decide RUNS.json --experiment ID --candidate CFG
                                       ACCEPT a cheaper config only if no quality
                                       metric is worse than the baseline's by more
                                       than the tolerance (same idea as gate.py)
  repeats --format F GROUP_DIR         would fewer repeated runs have shown the
                                       same thing? stats for every subset of size N-1
  add RUNS.json --experiment ID --config CFG --run NAME --format log|digest FILE
          [--source SRC] [--ref-marks M] [--tokens N] [--tool-uses N] [--duration S]
          [--model NAME] [--price-ratio R] [--baseline CFG] [--ref BASELINE_OUTPUT ...]
                                       score one finished run (any model, any vendor)
                                       and append it to RUNS.json

Token figures without an exact count are estimates for comparing options, not
billing numbers: about 4 characters per token for Latin text and 1 token per
CJK character. Exact tokens, tool calls and time come from the runner (for
example the usage report of a Claude Code sub-agent) and are typed into RUNS.json.

Python 3, standard library only.
"""
from __future__ import annotations

import argparse
import itertools
import json
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO / "evaluation"))
import stability  # noqa: E402

CJK = re.compile(r"[㐀-鿿豈-﫿　-〿＀-￯]")
TOL = {"valid": 0.0, "quotes": 0.02, "traceable": 0.02, "marks": 0.0, "sections": 0.05, "numbers": 0.05}
LEN_BAND = (0.5, 1.5)        # same band as gate.py's core length
QUALITY = ["valid", "quotes", "traceable", "marks", "sections", "numbers"]


def est_tokens(text: str) -> int:
    cjk = len(CJK.findall(text))
    return round(cjk + (len(text) - cjk) / 4)


def _script(rel: str) -> Path:
    return REPO / "skills" / rel


def cmd_inputs(files: list[Path]) -> list[dict]:
    rows = []
    for f in files:
        text = f.read_text(encoding="utf-8", errors="replace")
        row = {"file": f.name, "chars": len(text), "tokens_est": est_tokens(text)}
        if f.suffix == ".txt":
            with tempfile.TemporaryDirectory() as d:
                for name, rel, extra in (("clean", "earnings/earnings-call-reader/scripts/transcript_tool.py", ["clean"]),
                                         ("split", "synthesis/investment-view/scripts/split_bilingual.py", [])):
                    out = Path(d) / f"{name}.txt"
                    args = [sys.executable, str(_script(rel))] + extra + [str(f), "-o", str(out)]
                    if subprocess.run(args, capture_output=True).returncode == 0 and out.exists():
                        t2 = out.read_text(encoding="utf-8", errors="replace")
                        row[f"{name}_saving"] = round(1 - len(t2) / max(len(text), 1), 4)
        rows.append(row)
    return rows


def cmd_quality(path: Path, fmt: str, src: Path | None, ref_marks: str | None) -> dict:
    text = path.read_text(encoding="utf-8")
    f = stability.features(text, fmt, _read(src))
    q = {"valid": 1.0 if stability.validator_pass(path, fmt, REPO) else 0.0,
         "quotes": f.get("quotes"), "traceable": f.get("traceable"), "chars": len(text)}
    if fmt == "digest" and ref_marks:
        got = "".join(m.rstrip("️") for m in f.get("marks", []))
        ref = ref_marks.replace("️", "")
        q["marks"] = sum(a == b for a, b in zip(got, ref)) / len(ref) if got else 0.0
        q["marks_seen"] = got
    return q


def _read(src: Path | None) -> str | None:
    return src.read_text(encoding="utf-8", errors="ignore") if src else None


def _mean(xs):
    xs = [x for x in xs if isinstance(x, (int, float))]
    return statistics.mean(xs) if xs else None


def summarize(exp: dict) -> dict:
    out = {}
    for r in exp["runs"]:
        out.setdefault(r["config"], []).append(r)
    res = {}
    for cfg, rs in out.items():
        row = {"n": len(rs)}
        for k in ("tokens", "tool_uses", "duration_s", "chars"):
            row[k] = _mean([r.get(k) for r in rs])
        row["chars"] = _mean([r.get("quality", {}).get("chars") for r in rs]) or row["chars"]
        price = exp.get("price_ratio", {}).get(cfg)
        row["cost"] = row["tokens"] * price if row.get("tokens") and price is not None else None
        for k in QUALITY:
            row[k] = _mean([r.get("quality", {}).get(k) for r in rs])
            if row[k] is None and k in exp.get("group_quality", {}).get(cfg, {}):
                row[k] = exp["group_quality"][cfg][k]
        res[cfg] = row
    return res


def fmt_num(v, pct=False):
    if v is None:
        return "—"
    return f"{v:.0%}" if pct else (f"{v:,.0f}" if v >= 100 else f"{v:.1f}")


def cmd_table(data: dict, exp_id: str | None) -> str:
    lines = []
    for exp in data["experiments"]:
        if exp_id and exp["id"] != exp_id:
            continue
        s = summarize(exp)
        base = s.get(exp.get("baseline"), {})
        lines += [f"### {exp['id']}", "", exp.get("question", ""), "",
                  "| config | runs | tokens | cost vs baseline | tool calls | time (s) | length vs baseline | " + " | ".join(QUALITY) + " |",
                  "|---|---|---|---|---|---|---|" + "---|" * len(QUALITY)]
        for cfg, r in s.items():
            ck = "cost" if r.get("cost") is not None and base.get("cost") else "tokens"
            rel = (f"{r[ck] / base[ck]:.3g}x" if r.get(ck) and base.get(ck) else "—")
            lr = (f"{r['chars'] / base['chars']:.2f}x" if r.get("chars") and base.get("chars") else "—")
            q = " | ".join(fmt_num(r.get(k), pct=True) for k in QUALITY)
            lines.append(f"| {cfg} | {r['n']} | {fmt_num(r['tokens'])} | {rel} | {fmt_num(r['tool_uses'])} | "
                         f"{fmt_num(r['duration_s'])} | {lr} | {q} |")
        lines.append("")
    return "\n".join(lines)


def cmd_decide(data: dict, exp_id: str, cand: str) -> tuple[str, list]:
    exp = next(e for e in data["experiments"] if e["id"] == exp_id)
    s = summarize(exp)
    b, c = s[exp["baseline"]], s[cand]
    reasons, worse = [], False
    for k in QUALITY:
        if b.get(k) is None or c.get(k) is None:
            continue
        d = c[k] - b[k]
        if d < -TOL[k] - 1e-9:
            worse = True
            reasons.append(f"{k}: {c[k]:.0%} vs {b[k]:.0%} ({d * 100:+.0f}pp, tolerance -{TOL[k] * 100:.0f}pp)")
    if b.get("chars") and c.get("chars"):
        lr = c["chars"] / b["chars"]
        if not LEN_BAND[0] <= lr <= LEN_BAND[1]:
            worse = True
            reasons.append(f"length {lr:.2f}x the baseline, outside {LEN_BAND[0]}-{LEN_BAND[1]}x")
    ck = "cost" if c.get("cost") is not None and b.get("cost") else "tokens"
    cheaper = bool(c.get(ck) and b.get(ck) and c[ck] < b[ck])
    if worse:
        return "REJECT", reasons
    if c["n"] < 2 or b["n"] < 2:
        return "PROVISIONAL", reasons + ["fewer than 2 runs of the baseline or the candidate"]
    if not cheaper:
        return "REJECT", reasons + ["not cheaper than the baseline"]
    return "ACCEPT", reasons or ["no quality metric worse than tolerance"]


def cmd_repeats(folder: Path, fmt: str, src: Path | None) -> list[dict]:
    files = sorted(folder.glob("*.md"))
    rows = [{"subset": "all", **_g(files, fmt, src)}]
    for k in range(2, len(files)):
        for sub in itertools.combinations(files, k):
            rows.append({"subset": "+".join(p.stem for p in sub), **_g(list(sub), fmt, src)})
    return rows


def _g(files, fmt, src):
    with tempfile.TemporaryDirectory() as d:
        for f in files:
            shutil.copy(f, Path(d) / f.name)
        st = stability.group_stats(Path(d), fmt, REPO, _read(src))
    return {k: st.get(k) for k in ("valid", "tag", "marks", "sections", "numbers", "quotes", "traceable")}


def cmd_add(path: Path, a) -> dict:
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"experiments": []}
    exp = next((e for e in data["experiments"] if e["id"] == a.experiment), None)
    if exp is None:
        if not a.baseline:
            sys.exit("new experiment: pass --baseline CFG")
        exp = {"id": a.experiment, "baseline": a.baseline, "price_ratio": {}, "runs": []}
        data["experiments"].append(exp)
    if any(r["run"] == a.run for r in exp["runs"]):
        sys.exit(f"run {a.run!r} already in {a.experiment}")
    q = cmd_quality(a.file, a.format, a.source, a.ref_marks)
    if a.ref:
        from compare_view import numbers
        mine = set(numbers(a.file.read_text(encoding="utf-8")))
        refs = [set(numbers(r.read_text(encoding="utf-8"))) for r in a.ref]
        q["numbers"] = statistics.mean(len(mine & r) / len(r) for r in refs if r)
    run = {"config": a.config, "run": a.run, "model": a.model, "tokens": a.tokens, "tool_uses": a.tool_uses,
           "duration_s": a.duration, "quality": {k: v for k, v in q.items() if k != "marks_seen"}}
    exp["runs"].append(run)
    if a.price_ratio is not None:
        exp.setdefault("price_ratio", {})[a.config] = a.price_ratio
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return run


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("inputs"); a.add_argument("files", nargs="+", type=Path)
    q = sub.add_parser("quality"); q.add_argument("file", type=Path); q.add_argument("--format", required=True, choices=["log", "digest"])
    q.add_argument("--source", type=Path); q.add_argument("--ref-marks")
    t = sub.add_parser("table"); t.add_argument("runs", type=Path); t.add_argument("--experiment")
    d = sub.add_parser("decide"); d.add_argument("runs", type=Path); d.add_argument("--experiment", required=True); d.add_argument("--candidate", required=True)
    r = sub.add_parser("repeats"); r.add_argument("group", type=Path); r.add_argument("--format", required=True, choices=["log", "digest"])
    r.add_argument("--source", type=Path)
    ad = sub.add_parser("add"); ad.add_argument("runs", type=Path); ad.add_argument("file", type=Path)
    for k in ("--experiment", "--config", "--run"):
        ad.add_argument(k, required=True)
    ad.add_argument("--format", required=True, choices=["log", "digest"]); ad.add_argument("--source", type=Path)
    ad.add_argument("--ref-marks"); ad.add_argument("--tokens", type=int); ad.add_argument("--tool-uses", type=int)
    ad.add_argument("--duration", type=float); ad.add_argument("--model"); ad.add_argument("--price-ratio", type=float)
    ad.add_argument("--baseline"); ad.add_argument("--ref", type=Path, action="append",
                                                   help="baseline output(s); 'numbers' = share of their numbers this run keeps")
    x = ap.parse_args()
    if x.cmd == "inputs":
        print(json.dumps(cmd_inputs(x.files), ensure_ascii=False, indent=1))
    elif x.cmd == "quality":
        print(json.dumps(cmd_quality(x.file, x.format, x.source, x.ref_marks), ensure_ascii=False))
    elif x.cmd == "table":
        print(cmd_table(json.loads(x.runs.read_text(encoding="utf-8")), x.experiment))
    elif x.cmd == "decide":
        verdict, reasons = cmd_decide(json.loads(x.runs.read_text(encoding="utf-8")), x.experiment, x.candidate)
        print(verdict)
        for m in reasons:
            print("  -", m)
        return {"ACCEPT": 0, "REJECT": 1, "PROVISIONAL": 3}[verdict]
    elif x.cmd == "add":
        print(json.dumps(cmd_add(x.runs, x), ensure_ascii=False))
    elif x.cmd == "repeats":
        print(json.dumps(cmd_repeats(x.group, x.format, x.source), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
