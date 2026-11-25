#!/usr/bin/env python3
"""
stability.py - layer 3 of the evaluation: same input, same output?

Each group is a folder holding N outputs that one skill version produced from
the SAME input in N separate sessions (for example the old earnings-digest
three times on TSEM's call log, and the new one three times). The script
measures, per group:

  valid       share of runs that pass the skill's current validator
              (check_digest.py for digests, check_view.py for investment views)
  tag         share of runs that give the most common beat / in-line / miss tag
  marks       for each of the five dimensions, share of runs that give the most
              common mark, averaged over the dimensions
  numbers     mean pairwise Jaccard overlap of the numbers the runs cite
              (value-based, as in compare_view.py)
  length cv   coefficient of variation of the output length (lower = steadier)
  sections    (call logs) share of section / product headings that have a counterpart
              in the other runs (key tokens; wording and bracketed notes may differ)
  quotes      with --source: share of quoted English passages (4+ words) found
              verbatim in the source transcript or log
  traceable   with --source: share of the output's numbers that appear in the source

The first two describe conformance to the fixed template; the last three
describe run-to-run variance. Comparing an old-skill group with a new-skill
group on the same input measures what the repository's rewrite (fixed strings,
builder scripts, validators) did for consistency.

Usage:
  python stability.py --format digest|view|log GROUP_DIR [GROUP_DIR ...]
                      [--source TRANSCRIPT_OR_LOG] [--json]

Each GROUP_DIR contains the run files (*.md) and nothing else. Python 3,
standard library only.
"""
from __future__ import annotations

import argparse
import itertools
import json
import re
import statistics
import subprocess
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from compare_view import numbers  # noqa: E402

DIMS = {"zh": ["财务", "细分产业", "订单", "客户", "业绩节奏"],
        "en": ["Financials", "Sub-industry", "Orders", "Customers", "Momentum"]}
TAGS = ["超预期", "符合预期", "不及预期", "Beat", "In line", "Miss"]
MARK = r"(✅️|✅|⚠️|⚠|🔻)"
VALIDATORS = {"log": "skills/earnings/earnings-call-reader/scripts/check_earnings_log.py",
              "digest": "skills/earnings/earnings-digest/scripts/check_digest.py",
              "view": "skills/synthesis/investment-view/scripts/check_view.py"}


def latest_quarter(text: str, fmt: str) -> str:
    """The newest quarter block: the part the runs should agree on."""
    rx = r"^#\s*---\s*FY\d{2} ?Q[1-4]\s*---" if fmt == "view" else r"---\s*FY\d{2} Q[1-4]\s*---"
    heads = [m.start() for m in re.finditer(rx, text, re.M)]
    if not heads:
        return ""
    nxt = re.search(r"^#\s", text[heads[0] + 1:], re.M) if fmt == "view" else None
    end = heads[0] + 1 + nxt.start() if nxt else (heads[1] if len(heads) > 1 else len(text))
    return text[heads[0]:end]


QUOTE = re.compile(r"[\"“]([A-Za-z][^\"”\n]{15,}?)[\"”]")
CJK = re.compile(r"[\u3400-\u9fff]")


def norm(t: str) -> str:
    return re.sub(r"[^a-z0-9%$.]+", " ", t.lower()).strip()


def source_scores(text: str, src: str | None) -> dict:
    if not src:
        return {}
    ns = norm(src)
    # English quotes only: a quoted span with CJK characters is the skill's own
    # Chinese wording that happens to start with a Latin token (e.g. "FY27 订满 ...")
    quotes = [q for q in QUOTE.findall(text) if len(q.split()) >= 4 and not CJK.search(q)]
    # an elided quote ("A ... B") counts as verbatim when every part is
    found = [q for q in quotes if all(norm(part) in ns for part in re.split(r"\.\.\.|…", q) if part.strip())]
    src_nums = set(numbers(src))
    out_nums = set(numbers(text))
    return {"quotes": len(found) / len(quotes) if quotes else None,
            "traceable": len(out_nums & src_nums) / len(out_nums) if out_nums else None}


def features(text: str, fmt: str, src: str | None = None) -> dict:
    if fmt == "log":
        heads = [h.strip() for h in re.findall(r"^#{2,3}\s+(.+)$", text, re.M)
                 if not re.search(r"FY\d{2}|20\d{2}|Q[1-4]", h)]
        return {"tag": None, "marks": {}, "numbers": set(numbers(text)), "chars": len(text),
                "sections": heads, **source_scores(text, src)}
    q = latest_quarter(text, fmt)
    lang = "zh" if re.search(r"[一-鿿]", q or text) else "en"
    first = q.splitlines()[0] if q else ""
    tag = next((t for t in TAGS if t in first), None)
    marks = {}
    for d in DIMS[lang]:
        m = re.search(rf"^\s*{MARK}?\s*\**{re.escape(d)}\**", q, re.M)
        marks[d] = (m.group(1) or "none").rstrip("️") if m else None
    return {"tag": tag, "marks": marks, "numbers": set(numbers(q)), "chars": len(text), **source_scores(text, src)}


def modal_share(values: list) -> float | None:
    vals = [v for v in values if v is not None]
    return Counter(vals).most_common(1)[0][1] / len(values) if vals else None


def validator_pass(path: Path, fmt: str, repo: Path) -> bool:
    script = repo / VALIDATORS[fmt]
    r = subprocess.run([sys.executable, str(script), str(path)], capture_output=True, text=True)
    return r.returncode == 0


def head_tokens(h: str) -> set:
    """Key tokens of a heading: English words and CJK bigrams, without bracketed notes."""
    core = re.sub(r"[（(【\[][^）)】\]]*[）)】\]]", " ", h).lower()
    toks = {w for w in re.findall(r"[a-z][a-z0-9+\-]+", core) if len(w) >= 3}
    for run in re.findall(r"[\u4e00-\u9fff]+", core):
        toks |= {run[i:i + 2] for i in range(max(1, len(run) - 1))}
    return toks or {core.strip()}


def section_match(runs: list) -> float | None:
    """Mean over pairs of runs: share of headings that have a counterpart (sharing a key token) in the other run.
    Wording and bracketed notes may differ; a section missing or split differently counts against it."""
    scores = []
    for a, b in itertools.combinations(runs, 2):
        ta, tb = [head_tokens(h) for h in a], [head_tokens(h) for h in b]
        if not ta and not tb:
            continue
        hit = sum(any(x & y for y in tb) for x in ta) + sum(any(y & x for x in ta) for y in tb)
        scores.append(hit / (len(ta) + len(tb)))
    return sum(scores) / len(scores) if scores else None


def jaccard_mean(sets: list) -> float | None:
    j = [len(a & b) / len(a | b) for a, b in itertools.combinations(sets, 2) if a | b]
    return sum(j) / len(j) if j else None


def group_stats(folder: Path, fmt: str, repo: Path, src: str | None = None) -> dict:
    runs = sorted(folder.glob("*.md"))
    feats = [features(p.read_text(encoding="utf-8"), fmt, src) for p in runs]
    n = len(runs)
    out = {"group": folder.name, "runs": n}
    if n == 0:
        return out
    out["valid"] = sum(validator_pass(p, fmt, repo) for p in runs) / n
    out["tag"] = modal_share([f["tag"] for f in feats])
    if fmt == "log":
        out["sections"] = section_match([f["sections"] for f in feats])
    for k in ("quotes", "traceable"):
        vals = [f[k] for f in feats if f.get(k) is not None]
        out[k] = sum(vals) / len(vals) if vals else None
    dims = list(feats[0]["marks"])
    shares = [modal_share([f["marks"].get(d) for f in feats]) for d in dims]
    shares = [s for s in shares if s is not None]
    out["marks"] = sum(shares) / len(shares) if shares else None
    out["numbers"] = jaccard_mean([f["numbers"] for f in feats])
    lens = [f["chars"] for f in feats]
    out["length_cv"] = statistics.pstdev(lens) / statistics.mean(lens) if n > 1 and statistics.mean(lens) else None
    out["mark_table"] = {d: [f["marks"].get(d) for f in feats] for d in dims}
    return out


def cv(x):
    return "—" if x is None else f"{x:.2f}"


def pct(x):
    return "—" if x is None else f"{x:.0%}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--format", choices=["log", "digest", "view"], required=True)
    ap.add_argument("--source", type=Path, help="the transcript (for logs) or call log (for digests) the runs were made from")
    ap.add_argument("groups", nargs="+", type=Path)
    ap.add_argument("--repo", type=Path, default=HERE.parent, help="repository root (for the validators)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    src = a.source.read_text(encoding="utf-8", errors="ignore") if a.source else None
    rows = [group_stats(g, a.format, a.repo, src) for g in a.groups]
    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=1))
        return 0
    print("| group | runs | valid | same tag | same marks | same sections | number overlap | quotes verbatim | numbers traceable | length cv |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        print(f"| {r['group']} | {r['runs']} | {pct(r.get('valid'))} | {pct(r.get('tag'))} | {pct(r.get('marks'))} | "
              f"{pct(r.get('sections'))} | {pct(r.get('numbers'))} | {pct(r.get('quotes'))} | {pct(r.get('traceable'))} | "
              f"{cv(r.get('length_cv'))} |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
