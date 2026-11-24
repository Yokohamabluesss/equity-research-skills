#!/usr/bin/env python3
"""
split_bilingual.py - keep one language of an alternating English / Chinese transcript.

Machine-translated event transcripts often interleave an English paragraph and
its Chinese translation, sometimes on the same line. The translation is not a
source, and reading both doubles the tokens. This script splits the text at
the language boundaries and keeps one side.

Usage:  python split_bilingual.py FILE -o FILE.en.txt          (English, default)
        python split_bilingual.py FILE -o FILE.zh.txt --keep zh
"""
import argparse
import re
import sys
from pathlib import Path

CJK = re.compile(r"[一-鿿]")


def split(text: str, keep: str = "en") -> str:
    # break where a Chinese sentence ends and an English one begins, and vice versa
    text = re.sub(r"(?<=[。！？」）])\s*(?=[A-Z\"(\[])", "\n", text)
    text = re.sub(r"(?<=[.?!\"])\s*(?=[一-鿿])", "\n", text)
    text = re.sub(r"(?<=[一-鿿])(?=[A-Z])", "\n", text)   # Chinese speaker title glued to English
    out = []
    for seg in text.splitlines():
        s = seg.strip()
        if not s:
            continue
        n_cjk = len(CJK.findall(s))
        is_zh = n_cjk >= 3 and n_cjk / max(1, len(s)) > 0.15
        if (keep == "zh") == is_zh:
            out.append(s)
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("-o", "--output")
    ap.add_argument("--keep", choices=["en", "zh"], default="en")
    a = ap.parse_args()
    src = Path(a.file)
    text = src.read_text(encoding="utf-8", errors="replace")
    res = split(text, a.keep)
    dst = Path(a.output) if a.output else src.with_name(f"{src.stem}.{a.keep}.txt")
    dst.write_text(res, encoding="utf-8")
    print(f"Wrote {dst}  ({len(text):,} -> {len(res):,} chars, {1 - len(res) / max(1, len(text)):.0%} smaller)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
