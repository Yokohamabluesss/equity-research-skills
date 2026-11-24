#!/usr/bin/env python3
"""
transcript_tool.py - find, verify and clean earnings-call transcripts.

Three sub-commands, all deterministic (no network):

  find    Look for a transcript of TICKER + QUARTER in a folder before going
          to the web. Matches on the transcript's own header line first
          (e.g. "FormFactor, Inc. (FORM) Q3 FY2026 earnings call transcript"),
          and only falls back to the file name. A file named "TESM 2026Q2.txt"
          whose header says "(TSEM) Q2 FY2026" is still found - and the
          file-name typo is reported.

  verify  Check that one transcript (a file, or text saved from a web page)
          is the right company and quarter, is not a paywall stub, and is not
          cut off. Run this on every transcript before summarising it.

  clean   Remove timestamps, repeated speaker headers and page chrome to save
          tokens before reading (typically 8-15% smaller). Quotes are not
          changed: only whitespace and non-content lines are removed.

Quarter labels accepted: "FY26 Q3", "Q3 FY2026", "2026Q3", "FY2026Q3", "26FYQ3".
All refer to the company's FISCAL year, which is how Yahoo/Quartr label calls.

Examples:
  python transcript_tool.py find   --ticker FORM --quarter 2026Q3 --dir .
  python transcript_tool.py verify "FORM 2026Q3.txt" --ticker FORM --quarter "FY26 Q3"
  python transcript_tool.py clean  "FORM 2026Q3.txt" -o FORM_2026Q3.clean.txt

Exit codes: 0 ok, 1 not found / failed verification, 2 usage error.
"""
from __future__ import annotations

import argparse
import re
import sys
import zipfile
from pathlib import Path

TEXT_EXT = {".txt", ".md", ".markdown", ".html", ".htm"}
OTHER_EXT = {".docx", ".pdf"}
# outputs of other skills that live in the same folder - never transcripts
SKIP_PATTERNS = re.compile(r"_(Earnings|Digest|速读|估值速读|首次研究|Initial_Coverage)\b|Dashboard", re.I)

HEADER_RE = re.compile(r"\(([A-Z][A-Z0-9.\-]{0,9})\)\s+Q([1-4])\s+FY(\d{4})", re.I)
TIMESTAMP_RE = re.compile(r"^\d{1,2}:\d{2}:\d{2}$")
PAYWALL_RE = re.compile(
    r"Upgrade to unlock|subscription plan is required|Already have a subscription|"
    r"Subscribe to (read|continue)|Premium members only", re.I)
CLOSING_RE = re.compile(
    r"(conference (call )?(has )?(now )?concluded|this concludes|you may (now )?(all )?disconnect|"
    r"thank you for (your )?participati|ends today's (call|conference)|thanks for joining)", re.I)
DATE_LINE_RE = re.compile(r"\b\d{4}, \d{1,2}:\d{2}\s*(AM|PM)")
ROLE_RE = re.compile(r"\b(CEO|CFO|COO|CTO|CMO|Analyst|President|VP|Vice President|Officer|Director|Relations|"
                     r"Chair\w*|Head|Manager|Treasurer|Founder|EVP|SVP|Controller|Executive|Secretary|General Counsel)\b", re.I)
QA_RE = re.compile(r"\b(question-and-answer|Q&A|first question|next question)\b", re.I)


# --------------------------------------------------------------------------
# quarter parsing
# --------------------------------------------------------------------------
def parse_quarter(label: str) -> tuple[int, int]:
    s = label.strip().upper().replace(" ", "").replace("_", "")
    pats = [
        (r"^FY(\d{2,4})Q([1-4])$", 1, 2),   # FY26Q3, FY2026Q3
        (r"^Q([1-4])FY(\d{2,4})$", 2, 1),   # Q3FY2026
        (r"^(\d{4})Q([1-4])$", 1, 2),       # 2026Q3
        (r"^(\d{2})FYQ([1-4])$", 1, 2),     # 26FYQ3 (earnings-digest style)
        (r"^(\d{4})FYQ([1-4])$", 1, 2),
    ]
    for pat, gy, gq in pats:
        m = re.match(pat, s)
        if m:
            y = int(m.group(gy))
            y = y + 2000 if y < 100 else y
            return y, int(m.group(gq))
    raise ValueError(f"unrecognised quarter label: {label!r} (try FY26 Q3 / 2026Q3 / Q3 FY2026)")


def canon(y: int, q: int) -> str:
    return f"FY{y % 100:02d} Q{q}"


# --------------------------------------------------------------------------
# reading
# --------------------------------------------------------------------------
def read_text(path: Path, limit: int | None = None) -> str:
    ext = path.suffix.lower()
    try:
        if ext in TEXT_EXT:
            t = path.read_text(encoding="utf-8", errors="replace")
        elif ext == ".docx":
            with zipfile.ZipFile(path) as z:
                xml = z.read("word/document.xml").decode("utf-8", "replace")
            xml = re.sub(r"</w:p>", "\n", xml)
            t = re.sub(r"<[^>]+>", "", xml)
        elif ext == ".pdf":
            import shutil
            import subprocess
            if not shutil.which("pdftotext"):
                return ""
            t = subprocess.run(["pdftotext", "-l", "3" if limit else "0", str(path), "-"],
                               capture_output=True, text=True).stdout
        else:
            return ""
    except Exception:  # noqa: BLE001
        return ""
    if ext in {".html", ".htm"}:
        t = re.sub(r"<[^>]+>", " ", t)
    return t[:limit] if limit else t


def header_info(text: str) -> dict:
    head = text[:3000]
    m = HEADER_RE.search(head)
    info = {"ticker": None, "fy": None, "q": None, "title": None, "date": None}
    if m:
        info.update(ticker=m.group(1).upper(), q=int(m.group(2)), fy=int(m.group(3)))
        line_start = head.rfind("\n", 0, m.start()) + 1
        line_end = head.find("\n", m.end())
        info["title"] = head[line_start: line_end if line_end > 0 else None].strip()
    d = re.search(r"\b([A-Z][a-z]{2,8}\.? \d{1,2}, \d{4})", head)
    if d:
        info["date"] = d.group(1)
    return info


def filename_info(name: str) -> dict:
    stem = Path(name).stem
    m = re.search(r"([A-Za-z][A-Za-z.]{0,7})[\s_\-]*(?:FY)?(\d{4})\s*Q([1-4])", stem, re.I) \
        or re.search(r"([A-Za-z][A-Za-z.]{0,7})[\s_\-]*Q([1-4])[\s_\-]*FY?(\d{2,4})", stem, re.I)
    if not m:
        return {}
    g = m.groups()
    if re.match(r"\d{4}", g[1]):
        y, q = int(g[1]), int(g[2])
    else:
        q, y = int(g[1]), int(g[2])
        y = y + 2000 if y < 100 else y
    return {"ticker": g[0].upper(), "fy": y, "q": q}


# --------------------------------------------------------------------------
# commands
# --------------------------------------------------------------------------
def cmd_find(a) -> int:
    fy, q = parse_quarter(a.quarter)
    tk = a.ticker.upper()
    root = Path(a.dir)
    files = [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in TEXT_EXT | OTHER_EXT
             and len(p.relative_to(root).parts) <= 3 and not SKIP_PATTERNS.search(p.name)]
    strong, weak, unreadable = [], [], []
    for p in sorted(files):
        hi = header_info(read_text(p, limit=4000))
        fi = filename_info(p.name)
        if hi["ticker"]:
            if hi["ticker"] == tk and hi["fy"] == fy and hi["q"] == q:
                note = ""
                if fi and fi.get("ticker") != tk:
                    note = f"  (file name says {fi.get('ticker')!r} - typo; header is authoritative)"
                strong.append(f"{p}  <- header: {hi['title']}{note}")
            continue
        if fi and fi.get("ticker") == tk and fi.get("fy") == fy and fi.get("q") == q:
            (unreadable if p.suffix.lower() in OTHER_EXT and not read_text(p, 200) else weak).append(str(p))
    target = f"{tk} {canon(fy, q)}"
    if strong:
        print(f"FOUND {target}: verified by transcript header")
        for s in strong:
            print("  ", s)
        return 0
    if weak:
        print(f"CANDIDATE {target}: file name matches but the file has no standard header.")
        print("  Open the first lines and confirm company + quarter before using:")
        for s in weak:
            print("  ", s)
        return 0
    if unreadable:
        print(f"CANDIDATE {target}: matching file name, but this environment cannot read it "
              "(read it with the pdf/docx skill and confirm company + quarter):")
        for s in unreadable:
            print("  ", s)
        return 0
    print(f"NOT FOUND {target} in {root.resolve()} - go to the web source next.")
    return 1


def verify_text(text: str, tk: str, fy: int, q: int) -> tuple[list[str], list[str], dict]:
    fails, warns = [], []
    hi = header_info(text)
    if PAYWALL_RE.search(text):
        fails.append("paywall text found (e.g. 'Upgrade to unlock') - only a preview was retrieved")
    if not hi["ticker"]:
        fails.append("UNVERIFIED: no standard header line '(TICKER) Qn FYyyyy'. Read the opening lines; "
                     "use the file only if they name the company and quarter, otherwise ask the user")
    else:
        if hi["ticker"] != tk:
            fails.append(f"ticker mismatch: header says {hi['ticker']}, expected {tk}")
        if (hi["fy"], hi["q"]) != (fy, q):
            fails.append(f"quarter mismatch: header says {canon(hi['fy'], hi['q'])}, expected {canon(fy, q)}")
    body = text.strip()
    tail = body[-1500:]
    if not CLOSING_RE.search(tail):
        warns.append("no closing line ('this concludes...' / 'disconnect') near the end - "
                     "the transcript may be truncated; check the last speaker turn")
    if not QA_RE.search(body):
        warns.append("no Q&A markers found - prepared remarks only?")
    n_chars = len(body)
    if n_chars < 15000 and not fails:
        warns.append(f"only {n_chars:,} characters - a full call is usually 35k-80k")
    stats = {"chars": n_chars, "title": hi["title"], "date": hi["date"],
             "speaker_turns": len(TIMESTAMP_RE.findall("\n".join(l.strip() for l in body.splitlines())))}
    return fails, warns, stats


def cmd_verify(a) -> int:
    fy, q = parse_quarter(a.quarter)
    text = read_text(Path(a.file)) if a.file != "-" else sys.stdin.read()
    if not text:
        print("FAIL  could not read text")
        return 1
    fails, warns, st = verify_text(text, a.ticker.upper(), fy, q)
    print(f"INFO  title: {st['title']}\nINFO  call date: {st['date']}\nINFO  {st['chars']:,} chars")
    for w in warns:
        print("WARN ", w)
    for f in fails:
        print("FAIL ", f)
    if fails:
        return 1
    print(f"PASS  transcript is {a.ticker.upper()} {canon(fy, q)}")
    return 0


def clean_text(text: str) -> str:
    lines = [l.rstrip() for l in text.splitlines()]
    # drop page chrome after the copyright footer
    for i, l in enumerate(lines):
        if re.match(r"^Copyright ©", l):
            lines = lines[:i]
            break
    lines = [l for l in lines if l.strip() not in {"Powered by Quartr", "Back to quote", "ADVERTISEMENT"}]
    ts_idx = [i for i, l in enumerate(lines) if TIMESTAMP_RE.match(l.strip())]
    speaker_at: dict[int, str] = {}
    consumed: set[int] = set()
    for i in ts_idx:
        label, j = [], i - 1
        while j >= 0 and len(label) < 2:
            s = lines[j].strip()
            if not s:
                j -= 1
                continue
            if (len(s) <= 60 and not re.search(r"[.?!:,;]$", s) and not TIMESTAMP_RE.match(s)
                    and not DATE_LINE_RE.search(s) and not HEADER_RE.search(s)
                    and (not label or ROLE_RE.search(label[0]))):
                label.insert(0, s)
                consumed.add(j)
                j -= 1
            else:
                break
        speaker_at[i] = " (".join(label) + (")" if len(label) == 2 else "") if label else "Unknown"
        consumed.add(i)
    out, current, buf = [], None, []

    def flush():
        if buf:
            out.append((f"{current}: " if current else "") + "\n".join(buf))

    for i, l in enumerate(lines):
        if i in speaker_at:
            if speaker_at[i] != current:
                flush()
                buf = []
                current = speaker_at[i]
            continue
        if i in consumed or not l.strip():
            continue
        buf.append(l.strip())
    flush()
    return "\n\n".join(out).strip() + "\n"


def cmd_clean(a) -> int:
    src = Path(a.file)
    text = read_text(src)
    if not text:
        print("FAIL  could not read text")
        return 1
    cleaned = clean_text(text)
    dst = Path(a.output) if a.output else src.with_name(src.stem + ".clean.txt")
    dst.write_text(cleaned, encoding="utf-8")
    saved = 1 - len(cleaned) / max(1, len(text))
    print(f"Wrote {dst}  ({len(text):,} -> {len(cleaned):,} chars, {saved:.0%} smaller)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("find")
    f.add_argument("--ticker", required=True)
    f.add_argument("--quarter", required=True)
    f.add_argument("--dir", default=".")
    v = sub.add_parser("verify")
    v.add_argument("file", help="transcript file, or - for stdin")
    v.add_argument("--ticker", required=True)
    v.add_argument("--quarter", required=True)
    c = sub.add_parser("clean")
    c.add_argument("file")
    c.add_argument("-o", "--output")
    a = ap.parse_args()
    try:
        return {"find": cmd_find, "verify": cmd_verify, "clean": cmd_clean}[a.cmd](a)
    except ValueError as e:
        print("ERROR", e)
        return 2


if __name__ == "__main__":
    sys.exit(main())
