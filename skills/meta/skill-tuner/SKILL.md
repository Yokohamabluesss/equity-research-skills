---
name: skill-tuner
description: "Improves an analysis or summary skill from its comparison with the analyst's hand-written outputs, like a supervised training loop with a held-out check: runs the evaluation, sorts every difference (input gap / format / judgment / coverage / length / skill-only), proposes rule edits only for patterns seen in at least two companies, applies the edits the user approves, re-runs as a new experiment and accepts the change only if held-out results do not get worse. Use when the user says 'tune the skill from the comparison', 'update investment-view based on the results', 'what should change in the rules', 'calibrate the skill', '根据对比结果升级 skill', '调一下规则', '校准 skill'. Never changes judgment rules (dimension marks) on its own and never optimises lexical overlap."
---

# skill-tuner

Turns comparison results into rule changes for a skill, with a person approving every change. The hand-written outputs are labels, the skill's `SKILL.md` is the model, rule edits are training, and held-out companies or quarters decide whether a change is kept. The method is explained in `evaluation/TUNING.md` of the repository.

## Conventions (fixed)

- **Works on the repository plus the private workspace**: `equity-research-skills/` (rules, scripts, manifest, reports) and `workspace/` (references, inputs, runs). If either is not available, ask for it; do not continue with less.
- **One experiment = one report.** Every re-run after a rule change is a new experiment id in `evaluation/manifest.json` and a new report `evaluation/reports/{id}.md`. Earlier reports are not rewritten.
- **Run ids are unique** across the manifest. Each run has `split`: `train` (may be used as evidence) or `heldout` (only judges).
- **Proposals are files**: `workspace/runs/{skill}/proposals/{YYYY-MM-DD}_{short-name}.md`, written in the language of the request.
- Scripts (in `scripts/`, synced from the repository's `evaluation/` by `tools/build.py`):
  - `run_eval.py` - compares every run of one experiment with its reference
  - `diagnose.py` - sorts the differences into six categories and finds patterns across companies
  - `gate.py` - accepts or rejects a change from a baseline and a candidate experiment, on held-out runs only
  - `compare_view.py` - the comparison itself (investment-view format)

## Steps

### 1. Evaluate and diagnose

```bash
python evaluation/run_eval.py --experiment BASE_ID --root ../workspace --out ../workspace/runs/{skill}/eval
python evaluation/diagnose.py --experiment BASE_ID --eval-dir ../workspace/runs/{skill}/eval/BASE_ID
```

Save the diagnosis next to the per-run files. Then **read the evidence**: for every pattern marked "rule candidate", open the per-run `.md` files and read the missed and skill-only lines. A pattern is a candidate, not a conclusion. Check first whether the current rules produce the difference on purpose (for example, rows outside the thesis are dropped by design).

### 2. Route each category

| Category | Who acts | What to do |
|---|---|---|
| input_gap | the user | list the missing inputs; never write a rule to compensate |
| format | scripts | fix the validator or template; this is not a rule change |
| judgment (marks) | **the user** | put both readings side by side with the evidence and ask; never change a mark rule on your own |
| coverage / length, 2+ companies | this skill | decide which skill to change (step 3), then propose a rule edit (step 4) |
| coverage / length, 1 company | nobody yet | record in the proposal file under "watch"; do not change rules |
| skill_only | the user | list them as "possible gains"; a correct caveat the analyst skipped is not an error |

### 3. Decide which skill's rule to change

investment-view writes two of its parts with other skills' rules, so the part decides where a fix goes:

| Part of investment-view | Rules live in | Fix in |
|---|---|---|
| the five dimensions and Other of a quarter block | earnings-digest | earnings-digest |
| estimates | valuation-brief (company-valuation if the workbook itself lacks it) | that skill |
| Core, upside drivers, verdict line, product and capacity tables, events, length, layout | investment-view | investment-view |

A fix in earnings-digest or valuation-brief also changes their standalone output, so the proposal lists every skill it touches, their validators must still pass, and their framework stays unchanged.

### 4. Write the proposal

For each rule edit, in this order:

```
## {n}. {one-line name}
Category / pattern: coverage core/text/terms (train: COHR, FORM)
Skills touched: {e.g. earnings-digest (gap starts there), investment-view}
Evidence: {run ids and which kind of lines were missed, paraphrased; no copied reference text}
Rule now: {quoted from SKILL.md}
Rule proposed: {the new text, as it would appear in SKILL.md and SKILL.zh-CN.md}
Expected effect: {which metric should move, on which runs}
Risk: {what could get worse; which held-out run would show it}
```

**Anti-overfitting rules** (a proposal that breaks one is dropped):
1. Evidence from at least two companies on `train` runs. Held-out runs are never evidence.
2. The rule describes a method, not content: no company names, product names, numbers or facts from a reference, and no copied wording from the analyst's notes ("keep capacity milestones as a table when supply is the constraint", not "mention InP doubling").
3. No edit whose only purpose is to raise line coverage or term recall. These undercount paraphrase; optimising them teaches the skill to write longer and copy wording.
4. Prefer the smallest edit that explains the pattern; one edit per pattern.

### 5. Ask for approval

Show the proposals with AskUserQuestion (multi-select) or in plain text when no question tool exists. Apply only the approved ones, to both `SKILL.md` and `SKILL.zh-CN.md`. Then run:

```bash
python tools/build.py && python tools/selftest.py
```

### 6. Re-run as a new experiment

Add a new experiment to the manifest (new id, `"status": "open"`, the new skill version in every run) with the same companies and inputs as the baseline, plus at least one `heldout` run: a company or quarter that no rule was tuned on, written in a fresh session without reading its reference. Regenerate the outputs with the updated skill, then:

```bash
python evaluation/run_eval.py --experiment CAND_ID --root ../workspace --out ../workspace/runs/{skill}/eval
python evaluation/gate.py --baseline .../BASE_ID/summary.json --candidate .../CAND_ID/summary.json
```

### 7. Decide and record

- **ACCEPT**: write the findings into the new report, add a CHANGELOG entry (version, the rule changes, the gate result), mark the baseline experiment `"status": "closed"`.
- **REJECT**: revert the rule edits, keep the report (a failed change is a result too), note why in the proposal file.
- **PROVISIONAL** (no held-out pair): keep the edits marked provisional in the CHANGELOG and tell the user which held-out run is needed.

## Principles

- **Changes the user asks for directly** are always allowed: apply them as asked, without the two-company rule. Still keep the framework unless the user explicitly wants it changed, run build and self-test, record the change in the CHANGELOG as user-requested, and suggest re-running the latest experiment so its effect is measured.
- The analyst owns the target. Judgment rules, the no-buy/sell rule and the no-cheap/expensive rule are never tuned.
- **Which skills**: investment-view (fixes may land in earnings-digest or valuation-brief, whose output it carries); company-valuation and stock-discovery **additions only**: add a key output, method or company the analyst has and the skill lacks to the checklist; never change their framework (sheets, columns, section order, labels, validators). earnings-call-reader and quarterly-financials-dashboard are not tuned.
- A gain on train runs with no held-out check is not an improvement yet.
- The acceptance metrics are marks agreement, number recall (quarter text, tables, estimates) and core length within 0.5–1.5x the reference. Line coverage and term recall are reported, never used to accept.
- Public reports carry aggregate metrics and paraphrased findings only; the per-run files and proposals stay in the workspace.
