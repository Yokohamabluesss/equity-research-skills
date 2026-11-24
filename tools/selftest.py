#!/usr/bin/env python3
"""
tools/selftest.py - runs every skill script on synthetic fixtures.

Each case states the expected exit code, including negative cases (a check
that should FAIL). No network, no real transcripts. Needs openpyxl;
LibreOffice is used when installed (xlsx cases fall back to --no-recalc).

  python tools/selftest.py
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SK = ROOT / "skills"
PY = sys.executable
HAS_LO = bool(shutil.which("soffice") or shutil.which("libreoffice"))
results = []


def run(name, args, expect, cwd=None):
    p = subprocess.run([PY, *map(str, args)], capture_output=True, text=True, cwd=cwd)
    ok = p.returncode == expect
    results.append(ok)
    print(f"{'ok  ' if ok else 'FAIL'}  {name}  (exit {p.returncode}, expected {expect})")
    if not ok:
        print("      " + (p.stdout + p.stderr).strip().replace("\n", "\n      ")[:1500])


def block(md: Path, heading: str) -> str:
    s = md.read_text(encoding="utf-8")
    s = s[s.index(heading):]
    a = s.index("```") + 3
    a = s.index("\n", a) + 1
    return s[a:s.index("```", a)]


T = Path(tempfile.mkdtemp(prefix="skills_selftest_"))
NR = [] if HAS_LO else ["--no-recalc"]

# ---------------------------------------------------------------- earnings-call-reader
ecr = SK / "earnings/earnings-call-reader/scripts"
tdir = T / "FORM"
tdir.mkdir()
body = "\n\n".join(["Operator\n0:00:00\n\nWelcome to the call.",
                    "Jane Doe\nCEO\n0:01:00\n\n" + "Revenue grew. " * 1500,
                    "John Roe\nAnalyst\n0:20:00\n\nFirst question on demand?",
                    "Operator\n0:50:00\n\nThis concludes today's conference call. You may now disconnect."])
(tdir / "FORM 2026Q3.txt").write_text("Acme Corp. (FORM) Q3 FY2026 earnings call transcript\nPowered by Quartr\n"
                                      "Oct 28, 2026, 4:25 PM EDT\n\n" + body, encoding="utf-8")
(tdir / "FROM 2026Q2.txt").write_text("Acme Corp. (FORM) Q2 FY2026 earnings call transcript\n\n" + body, encoding="utf-8")
(tdir / "paywall.txt").write_text("Acme Corp. (FORM) Q1 FY2026 earnings call transcript\nOperator\n0:00:00\n\nWelcome."
                                  "\nPremium\nUpgrade to unlock our full archive\n", encoding="utf-8")
run("transcript find (header match)", [ecr / "transcript_tool.py", "find", "--ticker", "FORM", "--quarter", "FY26 Q3", "--dir", tdir], 0)
run("transcript find (typo file name, header wins)", [ecr / "transcript_tool.py", "find", "--ticker", "FORM", "--quarter", "2026Q2", "--dir", tdir], 0)
run("transcript find (missing quarter)", [ecr / "transcript_tool.py", "find", "--ticker", "FORM", "--quarter", "Q4 FY2026", "--dir", tdir], 1)
run("transcript verify (right quarter)", [ecr / "transcript_tool.py", "verify", tdir / "FORM 2026Q3.txt", "--ticker", "FORM", "--quarter", "2026Q3"], 0)
run("transcript verify (wrong quarter -> FAIL)", [ecr / "transcript_tool.py", "verify", tdir / "FORM 2026Q3.txt", "--ticker", "FORM", "--quarter", "2026Q2"], 1)
run("transcript verify (paywall -> FAIL)", [ecr / "transcript_tool.py", "verify", tdir / "paywall.txt", "--ticker", "FORM", "--quarter", "2026Q1"], 1)
run("transcript clean", [ecr / "transcript_tool.py", "clean", tdir / "FORM 2026Q3.txt", "-o", T / "clean.txt"], 0)

log_q3 = """# FORM Earnings Call Log

## TL;DR
### FY26 Q3 (2026-10-28)
- Revenue $280.5M.

## Guidance
### FY26 Q3
| Metric | Actual | Next | FY | Quote |
|---|---|---|---|---|

## Drivers of Profitability
### FY26 Q3
1. **Mix**: x

## Product Breakdown
### Company-wide Demand / Order Book / Capacity Overview
#### FY26 Q3
- demand strong
### Probe Cards
#### FY26 Q3
##### Demand / Industry Dynamics
##### Order Book / Backlog
##### Customers

## Product Summary Table
### FY26 Q3
| Product | Stage | Ramp | Size |
|---|---|---|---|
"""
(T / "old.md").write_text(log_q3, encoding="utf-8")
run("earnings log: single quarter", [ecr / "check_earnings_log.py", T / "old.md"], 0)
good = (log_q3.replace("## Guidance", "### FY26 Q4 (2027-02-04)\n- new\n\n## Guidance")
        .replace("## Drivers of Profitability", "### FY26 Q4\n| Metric | vs prior quarter |\n|---|---|\n\n## Drivers of Profitability")
        .replace("## Product Breakdown", "### FY26 Q4\n1. x\n\n## Product Breakdown")
        .replace("### Probe Cards", "#### FY26 Q4\n- 🔼 tighter\n### Probe Cards")
        .replace("## Product Summary Table", "#### FY26 Q4\n##### Demand / Industry Dynamics\n##### Order Book / Backlog\n##### Customers\n\n## Product Summary Table")
        + "### FY26 Q4\n| Product | Stage | Ramp | Size |\n|---|---|---|---|\n")
(T / "new.md").write_text(good, encoding="utf-8")
run("earnings log: append + append-only check", [ecr / "check_earnings_log.py", T / "new.md", "--before", T / "old.md"], 0)
(T / "edited.md").write_text(good.replace("- Revenue $280.5M.", "- Revenue $281M."), encoding="utf-8")
run("earnings log: edited old quarter -> FAIL", [ecr / "check_earnings_log.py", T / "edited.md", "--before", T / "old.md"], 1)
(T / "skipped.md").write_text(good.replace("#### FY26 Q4\n##### Demand", "#### FY26 Q2\n##### Demand"), encoding="utf-8")
run("earnings log: product skipped this quarter -> FAIL", [ecr / "check_earnings_log.py", T / "skipped.md"], 1)

# ---------------------------------------------------------------- earnings-digest / valuation-brief
dg = SK / "earnings/earnings-digest"
for lang, f, h in (("en", "SKILL.md", "## Mini example"), ("zh", "SKILL.zh-CN.md", "## 迷你范例")):
    p = T / f"digest_{lang}.md"
    p.write_text(block(dg / f, h), encoding="utf-8")
    run(f"digest example ({lang})", [dg / "scripts/check_digest.py", p], 0)
bad = (T / "digest_en.md").read_text(encoding="utf-8").replace("Beat·beat-raise", "Great")
(T / "digest_bad.md").write_text(bad, encoding="utf-8")
run("digest with invalid tag -> FAIL", [dg / "scripts/check_digest.py", T / "digest_bad.md"], 1)
vb = SK / "valuation/valuation-brief"
for lang, f, h in (("en", "SKILL.md", "## Example (COHR"), ("zh", "SKILL.zh-CN.md", "## 示例（COHR")):
    p = T / f"brief_{lang}.md"
    p.write_text(block(vb / f, h).strip() + "\n", encoding="utf-8")
    run(f"valuation brief example ({lang})", [vb / "scripts/check_brief.py", p], 0)

# ---------------------------------------------------------------- quarterly-financials-dashboard
q = SK / "research/quarterly-financials-dashboard/scripts"
n = 10
rev = [160 + 8 * i for i in range(n)]
themes = ["1. Revenue cycle / 收入周期", "2. Margin compression / 利润率压力", "3. Non-GAAP vs GAAP delta / 两套口径的差距",
          "4. Inventory tells the cycle story / 库存讲周期故事", "5. Order-proxy = leading indicator / 订单代理 = 领先指标",
          "6. Cash conversion / 现金转化", "7. Guidance trajectory / 指引轨迹", "8. Things to monitor / 后续跟踪"]
d = {"ticker": "TEST", "company": "Test Co", "unit": "$M", "source": "synthetic fixture",
     "quarters": [f"FY{24 + (i + 1) // 4} Q{(i + 1) % 4 + 1}" for i in range(n)],
     "period_end": [f"2025-{i % 12 + 1:02d}-28" for i in range(n)],
     "nongaap": {"revenue": rev, "gross_margin": [0.45] * n, "opex": [50] * n, "net_income": [20 + i for i in range(n)], "eps": [0.3] * n},
     "gaap": {"revenue": rev, "gross_margin": [None] + [0.43] * (n - 1), "opex": [60] * n, "net_income": [10 + i for i in range(n)], "eps": [0.15] * n},
     "helper": {"prior_year_revenue": [140, 145, 150, 155], "prior_year_nongaap_ni": [15] * 4, "prior_year_gaap_ni": [5] * 4,
                "prior_quarter_revenue": 155, "prior_quarter_nongaap_ni": 18, "prior_quarter_gaap_ni": 8},
     "balance": {k: [100 + i for i in range(n)] for k in ("inventory", "deferred_revenue", "customer_deposits", "ar", "cfo", "cash_st")},
     "notes": {"nongaap": ["Non-GAAP effective tax rate ~17%"]}, "story": {"en": "story", "zh": "故事"},
     "observations": [{"theme": t, "en": "x", "zh": "y"} for t in themes]}
(T / "fin.json").write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
run("financials dashboard build", [q / "build_financials_xlsx.py", T / "fin.json", T / "fin.xlsx"], 0)
run("financials dashboard check", [q / "check_financials_xlsx.py", T / "fin.xlsx", *NR], 0)
d2 = dict(d, notes={})
(T / "fin_bad.json").write_text(json.dumps(d2, ensure_ascii=False), encoding="utf-8")
run("financials build without tax-rate note -> FAIL", [q / "build_financials_xlsx.py", T / "fin_bad.json", T / "x.xlsx"], 1)

# ---------------------------------------------------------------- company-valuation
v = SK / "valuation/company-valuation/scripts"
sys.path.insert(0, str(v))
from val_style import FILL_D, finish, header_row, new_workbook, page_header, put, section, verdict  # noqa: E402

wb = new_workbook()
for ws in wb.worksheets:
    page_header(ws, f"TEST - {ws.title}", "synthetic fixture")
    header_row(ws, 4, ["Item", "Value", "Basis and derivation"], fill=FILL_D)
    section(ws, 30, "Notes", 3)
    finish(ws, note_cols=("C",))
verdict(wb["Conclusion"], 5, "Method conclusion: PE+FCFF ... guidance coverage 10%", 6)
put(wb["FCFF Valuation"], "A6", "Terminal value share of EV")
put(wb["FCFF Valuation"], "B6", "=0.6")
wb.save(T / "val.xlsx")
run("valuation template check", [v / "check_valuation_xlsx.py", T / "val.xlsx", *NR], 0)
wb["Methodology"].freeze_panes = None
wb.save(T / "val_bad.xlsx")
run("valuation template drift -> FAIL", [v / "check_valuation_xlsx.py", T / "val_bad.xlsx", "--no-recalc"], 1)

# ---------------------------------------------------------------- stock-discovery / delta table
sd = SK / "screening/stock-discovery/scripts/build_xlsx.py"
rows = [{"company": "B", "ticker": "B", "market": "US", "products": "p", "position": "Tier 2", "stage": "Mass production", "attention": "Low", "notes": ""},
        {"company": "A", "ticker": "A", "market": "US", "products": "p", "position": "Tier 1 (in FAU)", "stage": "Sampling", "attention": "High", "notes": ""}]
(T / "sd.json").write_text(json.dumps({"mode": "business_discovery", "topic": "T", "lang": "en", "rows": rows}), encoding="utf-8")
run("stock-discovery build", [sd, T / "sd.json", "--output", T / "sd.xlsx"], 0)
rows[0]["position"] = "Leader"
(T / "sd_bad.json").write_text(json.dumps({"mode": "business_discovery", "topic": "T", "lang": "en", "rows": rows}), encoding="utf-8")
run("stock-discovery unknown label -> FAIL", [sd, T / "sd_bad.json", "--output", T / "x.xlsx"], 1)
ad = SK / "screening/architecture-delta-table/scripts/build_delta_xlsx.py"
spec = {"lang": "en", "baseline": "Pluggable", "routes": ["NPO", "CPO"],
        "segments": [{"name": "Hybrid bonding", "verdicts": {"NPO": "⊘ Not applicable", "CPO": "⭐⭐ 纯新增"}}]}
(T / "ad.json").write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
run("delta table build", [ad, T / "ad.json", T / "ad.xlsx"], 0)
spec["segments"][0]["verdicts"]["NPO"] = "❌ Decrease (WDM)"
(T / "ad_bad.json").write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
run("delta table bracketed verdict -> FAIL", [ad, T / "ad_bad.json", T / "x.xlsx"], 1)

# ---------------------------------------------------------------- investment-view
cv = SK / "synthesis/investment-view/scripts"
view_old = """# 核心
硅光代工厂
A SiPho foundry
增长主驱动
\t硅光 PIC
新叙事
\t异质集成

# ---FY26 Q2--- 超预期，爬坡中
下一季超预期点
\t利润率
判断：很好
\t✅️财务：S 曲线加速
\t\tGM 30%
\t✅️细分产业：需求强
\t⚠️订单：金额未更新
\t✅️客户
\t✅️业绩节奏：2027 放量
其他
\t产能

# ---测算---
2026-10-14（股价 $209.16）
\t指引
\t\tQ3 $520M
\t假设
\t\tQ4 $570M
\t结论
\t\t① 指引覆盖率 20%，其余目标反解
\t\t② 毛利率每季 +50bps
\t\t③ FY26 PE 40x（EPS +50%）；FY27 PE 28.9x（EPS +38%）；PEG 0.8；FCFF 反推需高增长 5 年
\t\t④ 与一致预期：FY27 EPS +3%
"""
(T / "view_old.md").write_text(view_old, encoding="utf-8")
run("investment view: valid file", [cv / "check_view.py", T / "view_old.md"], 0)
view_new = view_old.replace("# ---FY26 Q2---", "# ---FY26 Q3--- 符合预期，产能阶跃\n下一季超预期点\n\t新产能\n判断：符合\n"
                            "\t✅️财务：加速\n\t✅️细分产业：强\n\t⚠️订单：未更新\n\t✅️客户：稳定\n\t🔻业绩节奏：推迟\n其他\n\t无\n\n# ---FY26 Q2---", 1)
(T / "view_new.md").write_text(view_new, encoding="utf-8")
run("investment view: new quarter on top + append-only", [cv / "check_view.py", T / "view_new.md", "--before", T / "view_old.md"], 0)
(T / "view_edit.md").write_text(view_new.replace("\t\tGM 30%", "\t\tGM 31%"), encoding="utf-8")
run("investment view: edited old quarter -> FAIL", [cv / "check_view.py", T / "view_edit.md", "--before", T / "view_old.md"], 1)
(T / "view_noconcl.md").write_text(view_old.replace("PEG 0.8；", ""), encoding="utf-8")
run("investment view: estimate missing PEG -> FAIL (valuation-brief check)", [cv / "check_view.py", T / "view_noconcl.md"], 1)
(T / "view_order.md").write_text(view_old + "\n# ---FY26 Q3--- 超预期，x\n", encoding="utf-8")
run("investment view: quarter appended at the bottom -> FAIL", [cv / "check_view.py", T / "view_order.md"], 1)
(T / "bi.txt").write_text("Revenue grew strongly this quarter.营收本季强劲增长，我们非常满意。首席执行官All right, thanks everyone.",
                          encoding="utf-8")
run("split bilingual transcript", [cv / "split_bilingual.py", T / "bi.txt", "-o", T / "bi.en.txt"], 0)
en = (T / "bi.en.txt").read_text(encoding="utf-8")
ok = "All right" in en and "营收" not in en
results.append(ok)
print(f"{'ok  ' if ok else 'FAIL'}  split bilingual keeps English only")
# ---------------------------------------------------------------- evaluation
EV = SK.parent / "evaluation"
run("compare view (markdown)", [EV / "compare_view.py", T / "view_new.md", T / "view_old.md"], 0)
sys.path.insert(0, str(EV))
import compare_view as cvm  # noqa: E402
eq = [("$1.3B", "13亿"), ("430bps", "4.3pp"), ("CY27", "2027"), ("$1,300M", "$1.3B")]
ok = all(any(cvm.num_match(x, y) for x in cvm.numbers(a) for y in cvm.numbers(b)) for a, b in eq) \
    and not cvm.numbers("2/3 来自") and cvm.numbers("9/7") == [("date", "09-07")]
results.append(ok)
print(f"{'ok  ' if ok else 'FAIL'}  compare view: value-based number matching")
rep = cvm.compare(T / "view_new.md", T / "view_old.md", dict(cvm.ALIASES))
ok = rep["quarters"]["FY26 Q2"]["agree"] == 5 and "FY26 Q3" not in rep["quarters"]
results.append(ok)
print(f"{'ok  ' if ok else 'FAIL'}  compare view: marks compared for every common quarter")
(T / "ws/refs").mkdir(parents=True)
shutil.copy(T / "view_old.md", T / "ws/refs/AAA_view.md")
shutil.copy(T / "view_new.md", T / "ws/AAA_gen.md")
man = {"experiments": [{"id": "E1", "title": "t", "question": "q", "runs": [{"id": "AAA", "ticker": "AAA",
       "skill_version": "test", "generated": "AAA_gen.md", "reference": "refs/AAA_view.md"}]},
       {"id": "E0", "status": "closed", "runs": []}]}
(T / "man.json").write_text(json.dumps(man), encoding="utf-8")
ev = ["--manifest", T / "man.json", "--root", T / "ws", "--out", T / "ev", "--reports", T / "rep"]
run("run_eval: new experiment creates its report", [EV / "run_eval.py", "--experiment", "E1", *ev], 0)
rep_md = T / "rep/E1.md"
rep_md.write_text(rep_md.read_text(encoding="utf-8").replace("(to be written", "HAND-WRITTEN (to be written"), encoding="utf-8")
run("run_eval: re-run refreshes only the table", [EV / "run_eval.py", "--experiment", "E1", *ev], 0)
run("run_eval: closed experiment -> refused", [EV / "run_eval.py", "--experiment", "E0", *ev], 2)
ok = (T / "ev/E1/summary.md").exists() and (T / "ev/E1/AAA.json").exists() and \
    "HAND-WRITTEN" in rep_md.read_text(encoding="utf-8") and "| AAA |" in rep_md.read_text(encoding="utf-8")
results.append(ok)
print(f"{'ok  ' if ok else 'FAIL'}  run_eval keeps hand-written findings, writes per-run files")

# diagnose: sorts findings, uses only train runs as evidence
dg = subprocess.run([sys.executable, str(EV / "diagnose.py"), "--manifest", str(T / "man.json"), "--experiment", "E1",
                     "--eval-dir", str(T / "ev/E1"), "--json"], capture_output=True, text=True)
ok = dg.returncode == 0 and "patterns" in json.loads(dg.stdout)
results.append(ok)
print(f"{'ok  ' if ok else 'FAIL'}  diagnose: categories and patterns")

# gate: decided on held-out pairs only
def row(i, t, marks, num, length=1.0):
    return {"id": i, "ticker": t, "marks_agree": marks, "marks_compared": 5, "quarter_text_num_recall": num,
            "quarter_table_num_recall": num, "est_num_recall": num, "core_len_ratio": length,
            "lines_covered": 0.5, "quarter_text_term_recall": 0.5, "core_term_recall": 0.5}
gm = {"experiments": [{"id": "B", "runs": [{"id": "b1", "split": "train"}, {"id": "b2", "split": "heldout"}]},
                      {"id": "C", "runs": [{"id": "c1", "split": "train"}, {"id": "c2", "split": "heldout"}]}]}
(T / "gm.json").write_text(json.dumps(gm), encoding="utf-8")
def gate_case(name, cand_heldout, expect, base=None):
    b = base or [row("b1", "AAA", 4, 0.8), row("b2", "BBB", 4, 0.8)]
    c = [row("c1", "AAA", 5, 0.9), cand_heldout] if cand_heldout else [row("c1", "AAA", 5, 0.9)]
    (T / "gb.json").write_text(json.dumps(b), encoding="utf-8")
    (T / "gc.json").write_text(json.dumps(c), encoding="utf-8")
    run(name, [EV / "gate.py", "--baseline", T / "gb.json", "--candidate", T / "gc.json", "--manifest", T / "gm.json"], expect)
gate_case("gate: held-out unchanged -> ACCEPT", row("c2", "BBB", 4, 0.8), 0)
gate_case("gate: held-out marks drop -> REJECT", row("c2", "BBB", 3, 0.8), 1)
gate_case("gate: held-out core length runs away -> REJECT", row("c2", "BBB", 4, 0.8, 2.5), 1)
gate_case("gate: no held-out pair -> PROVISIONAL", None, 3)

# stability: identical runs are fully stable; a changed mark lowers "same marks"
for gname, variant in (("same", view_new), ("diff", view_new.replace("⚠️订单：未更新", "✅️订单：未更新", 1))):
    (T / "st" / gname).mkdir(parents=True)
    (T / "st" / gname / "r1.md").write_text(view_new, encoding="utf-8")
    (T / "st" / gname / "r2.md").write_text(variant, encoding="utf-8")
st = subprocess.run([sys.executable, str(EV / "stability.py"), "--format", "view", "--json",
                     str(T / "st/same"), str(T / "st/diff")], capture_output=True, text=True)
rows = json.loads(st.stdout) if st.returncode == 0 else []
ok = len(rows) == 2 and rows[0]["marks"] == 1 and rows[1]["marks"] < 1 and rows[0]["valid"] == 1
results.append(ok)
print(f"{'ok  ' if ok else 'FAIL'}  stability: run-to-run mark agreement")

# cost-benefit: a cheaper config is accepted only if quality holds
CB = ROOT / "cost-benefit"
def cost_case(name, cand_quality, expect, cand_tokens=50):
    runs = {"experiments": [{"id": "M", "baseline": "big", "runs": [
        {"config": "big", "run": "b1", "tokens": 100, "quality": {"valid": 1, "quotes": 0.98, "marks": 1.0}},
        {"config": "big", "run": "b2", "tokens": 100, "quality": {"valid": 1, "quotes": 0.98, "marks": 1.0}},
        {"config": "small", "run": "s1", "tokens": cand_tokens, "quality": cand_quality},
        {"config": "small", "run": "s2", "tokens": cand_tokens, "quality": cand_quality}]}]}
    (T / "cost.json").write_text(json.dumps(runs), encoding="utf-8")
    run(name, [CB / "cost.py", "decide", T / "cost.json", "--experiment", "M", "--candidate", "small"], expect)
cost_case("cost: cheaper config, same quality -> ACCEPT", {"valid": 1, "quotes": 0.97, "marks": 1.0}, 0)
cost_case("cost: cheaper config, marks drop -> REJECT", {"valid": 1, "quotes": 0.98, "marks": 0.8}, 1)

# research-workflow: the folder check finds what is behind
WF = SK / "meta/research-workflow/scripts/status.py"
(T / "wf/ACME").mkdir(parents=True)
(T / "wf/ACME/ACME 2026Q3.txt").write_text("Acme Corp. (ACME) Q3 FY2026 earnings call transcript\n", encoding="utf-8")
(T / "wf/ACME/ACME_Earnings.md").write_text("# ACME Earnings Call Log\n\n## TL;DR\n### FY26 Q2 (2026-08-01)\n- x\n", encoding="utf-8")
st = subprocess.run([PY, str(WF), str(T / "wf/ACME"), "--json"], capture_output=True, text=True)
js = json.loads(st.stdout) if st.returncode == 0 else {}
ok = js.get("call_log") == "FY26 Q2" and js.get("transcripts") == ["FY26 Q3"] and js.get("suggested", "").startswith("B.")
results.append(ok)
print(f"{'ok  ' if ok else 'FAIL'}  research-workflow: status finds a new transcript -> suggests B")
st = subprocess.run([PY, str(WF), str(T / "wf/NONE"), "--json"], capture_output=True, text=True)
ok = st.returncode == 0 and json.loads(st.stdout).get("suggested", "").startswith("A.")
results.append(ok)
print(f"{'ok  ' if ok else 'FAIL'}  research-workflow: no folder -> suggests A")

# the README states the number of self-test cases; keep it true
readme = (SK.parent / "README.md").read_text(encoding="utf-8")
stated = re.findall(r"\((\d+) cases, including expected failures\)", readme)
ok = stated == [str(len(results) + 1)]
results.append(ok)
print(f"{'ok  ' if ok else 'FAIL'}  README states the number of self-test cases ({stated} vs {len(results)})")

print(f"\n{sum(results)}/{len(results)} passed")
shutil.rmtree(T, ignore_errors=True)
sys.exit(0 if all(results) else 1)
