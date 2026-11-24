#!/usr/bin/env python3
"""
tools/build.py - sync shared scripts, lint every skill, package dist/*.skill

  python tools/build.py            # lint + package
  python tools/build.py --check    # lint only (CI)

Lint rules (fail the build):
  - every skill folder has SKILL.md (English, loaded by Claude) and SKILL.zh-CN.md
  - frontmatter has name == folder name and a description of 1-1024 characters
  - every Python script compiles
  - files referenced as scripts/... or references/... in SKILL.md exist
  - shared/xlsx_check.py is identical in every skill that ships it
  - evaluation/*.py are identical in skill-tuner/scripts/
  - check_digest.py / check_brief.py are identical in investment-view/scripts/
  - docs: every skill is in both README skill tables and both halves of docs/SKILLS_GUIDE.md,
    the README intro matches the number of skills, and retired names appear only in history files
Packaging: dist/{name}.skill = zip of {name}/... (the format Claude imports).
"""
from __future__ import annotations

import filecmp
import py_compile
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = sorted(p.parent for p in (ROOT / "skills").glob("*/*/SKILL.md"))
SHARED = ROOT / "shared" / "xlsx_check.py"
NEEDS_SHARED = {"company-valuation", "quarterly-financials-dashboard", "value-chain-bom",
                "valuation-brief", "company-comparison"}
EVAL = ROOT / "evaluation"
EVAL_SYNC = {"skill-tuner": ["compare_view.py", "run_eval.py", "diagnose.py", "gate.py"]}
# investment-view writes its five dimensions with earnings-digest's rules and its estimates with
# valuation-brief's rules, so it checks them with the same scripts (one copy of each rule)
CROSS_SYNC = {"investment-view": ["skills/earnings/earnings-digest/scripts/check_digest.py",
                                  "skills/valuation/valuation-brief/scripts/check_brief.py"]}


def frontmatter(text: str) -> dict:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}
    out = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip().strip('"')
    return out


# names that were retired; allowed only in history (changelog, past reports, the experiment manifest)
RETIRED = {"company-view": ("CHANGELOG.md", "evaluation/reports/", "evaluation/manifest.json", "evaluation/TUNING.md")}


def docs_consistency() -> list:
    """Keep the docs in step with the skills: every skill is listed in the README table (EN and ZH),
    has a section in docs/SKILLS_GUIDE.md (EN and ZH), the README intro states the right number of
    skills, and no retired name is used outside history."""
    errs = []
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    guide = (ROOT / "docs/SKILLS_GUIDE.md").read_text(encoding="utf-8")
    for sk in SKILLS:
        name = sk.name
        if readme.count(f"**{name}**") < 2:
            errs.append(f"{name}: not in both README skill tables (EN and ZH)")
        if guide.count(f"### {name}") < 2:
            errs.append(f"{name}: needs a section in docs/SKILLS_GUIDE.md in both languages")
    n = len(SKILLS)
    if not re.search(rf"\b{n} skills in total\b", readme) or f"共 {n} 个" not in readme:
        errs.append(f"README intro does not match the number of skills ({n})")
    for old, allowed in RETIRED.items():
        for f in list(ROOT.rglob("*.md")) + list(ROOT.rglob("*.py")):
            rel = f.relative_to(ROOT).as_posix()
            if rel.startswith(("dist/", "tools/build.py")) or any(rel.startswith(a) for a in allowed):
                continue
            if old in f.read_text(encoding="utf-8", errors="ignore") and not rel.endswith("check_view.py"):
                errs.append(f"{rel}: uses the retired name '{old}'")
    return errs


def main() -> int:
    check_only = "--check" in sys.argv
    errors = []
    for sk in SKILLS:
        name = sk.name
        if name in NEEDS_SHARED:
            dst = sk / "scripts" / "xlsx_check.py"
            if not check_only:
                dst.parent.mkdir(exist_ok=True)
                shutil.copy(SHARED, dst)
            elif not dst.exists() or not filecmp.cmp(SHARED, dst, shallow=False):
                errors.append(f"{name}: scripts/xlsx_check.py out of sync with shared/")
        pairs = [(EVAL / f, f) for f in EVAL_SYNC.get(name, [])] + \
                [(ROOT / f, Path(f).name) for f in CROSS_SYNC.get(name, [])]
        for src, fname in pairs:
            dst = sk / "scripts" / fname
            if not check_only:
                dst.parent.mkdir(exist_ok=True)
                shutil.copy(src, dst)
            elif not dst.exists() or not filecmp.cmp(src, dst, shallow=False):
                errors.append(f"{name}: scripts/{fname} out of sync with {src.relative_to(ROOT)}")
        en, zh = sk / "SKILL.md", sk / "SKILL.zh-CN.md"
        if not zh.exists():
            errors.append(f"{name}: SKILL.zh-CN.md missing")
        for f in (en, zh):
            if not f.exists():
                continue
            fm = frontmatter(f.read_text(encoding="utf-8"))
            if fm.get("name") != name:
                errors.append(f"{f.relative_to(ROOT)}: name {fm.get('name')!r} != folder {name!r}")
            d = fm.get("description", "")
            if not 0 < len(d) <= 1024:
                errors.append(f"{f.relative_to(ROOT)}: description length {len(d)} (limit 1024)")
        body = en.read_text(encoding="utf-8")
        for ref in sorted(set(re.findall(r"\b((?:scripts|references)/[\w.\-]+\.(?:py|md))", body))):
            if not (sk / ref).exists():
                errors.append(f"{name}: SKILL.md references missing file {ref}")
        for py in sk.rglob("*.py"):
            try:
                py_compile.compile(str(py), cfile=str(Path(tempfile.gettempdir()) / "build_check.pyc"), doraise=True)
            except py_compile.PyCompileError as e:
                errors.append(f"{py.relative_to(ROOT)}: {e.msg}")
    errors += docs_consistency()
    if errors:
        print("BUILD FAILED")
        for e in errors:
            print("  -", e)
        return 1
    print(f"lint OK ({len(SKILLS)} skills)")
    if check_only:
        return 0
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    for sk in SKILLS:
        out = dist / f"{sk.name}.skill"
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for f in sorted(sk.rglob("*")):
                if f.is_file() and "__pycache__" not in f.parts:
                    z.write(f, Path(sk.name) / f.relative_to(sk))
        print(f"  packaged {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
