---
name: research-workflow
description: "Entry point for the equity-research skills: when the user does not know which skill to use, wants several skills chained ('do the full update on XX', 'new quarter for XX end to end', 'start coverage of XX', 'what should I run next for XX'), or asks what the skills can do, it checks the company folder, offers a short menu of fixed workflows (first coverage / new quarter / add an event / find companies / review a thesis) plus optional add-ons (compare with my hand-written version, stability check, cost-quality record, rule proposals), then runs the chosen skills in order and checks each output. Use for '从哪开始', '全流程', '一起用', '帮我把 XX 这季全部更新', '这些 skill 怎么用', 'research workflow'. Not for a request that clearly names one task - that skill handles it directly."
---

# research-workflow

The front door to the other skills. It does not analyse anything itself: it finds out what the user wants, shows what already exists for the company, lets the user pick a workflow, and then runs the right skills in the right order, checking each output before the next step uses it.

## Conventions (fixed)

- **Hand off single tasks.** If the request clearly names one task ("summarise this call", "value it", "check my thesis"), do not show the menu: use that skill directly.
- **Every step runs the real skill.** Load that skill's `SKILL.md` and follow it fully, including its validator. Never re-state or shortcut its rules here. If a skill is not installed, say which one and skip that step; do not improvise its output.
- **Choices.** Offer choices with the host's question tool when it has one (clickable options); otherwise as a short numbered list, asking for the number. At most two questions before work starts.
- **Language** follows the request; each skill keeps its own language rule.
- **Missing inputs or denied access.** Stop and ask the user how to proceed; never continue with fewer inputs without saying so.
- **No buy / sell advice, no price target, no cheap / expensive judgment** - the same rule as every skill underneath.
- **Script**: `scripts/status.py FOLDER [--ticker T] [--json]` lists what exists for a company (latest call log quarter, digest, financials dashboard, valuation date, investment-view quarter and estimate date, transcripts on disk) and what is stale. Python 3, standard library, no network.

## Step 0: Where are we

1. Identify the company (ticker) and the research folder `{RESEARCH_ROOT}/{TICKER}/`. If the conversation already names them, do not ask.
2. Run `python scripts/status.py "{RESEARCH_ROOT}/{TICKER}"`. Its "suggested" line is a starting point, not a decision.
3. If the folder does not exist, the company is new: suggest workflow A.

## Step 1: Choose

Show the status in two or three lines, then one question with these options (put the suggested one first):

| Option | When | Skills, in order |
|---|---|---|
| **A. First coverage** | new company | company-research (incl. the 10-quarter dashboard) → earnings-call-reader on the second-latest call, then the latest call appended → company-valuation → investment-view (core, quarter blocks, estimate written with valuation-brief's rules) |
| **B. New quarter** | a new call is out | earnings-call-reader (append) → quarterly-financials-dashboard (refresh) → company-valuation (refresh at today's price) → investment-view (new quarter block on top + new estimate) |
| **C. Add an event** | investor day, OFC / ECOC, broker conference, meeting notes | investment-view, event step (bilingual transcripts split first) |
| **D. Find companies** | a business or value chain, not a company | stock-discovery → optionally value-chain-bom or architecture-delta-table → company-comparison for names already researched |
| **E. Review** | the user has a thesis or wants two companies side by side | thesis-check, or company-comparison |

A separate earnings-digest is optional in A and B: investment-view already writes the five dimensions with earnings-digest's rules. Run it only if the user wants the one-page digest file.

Then, in the same question if the tool allows multiple selection, or as a second question, the **add-ons** (default: none):

| Add-on | Needs | Runs |
|---|---|---|
| 1. Compare with my hand-written version | the user's own note for the same quarter | the repository's `evaluation/` (`run_eval.py` → a new experiment report) |
| 2. Stability check | about 2x the cost of the step | the chosen step twice in fresh sessions → `evaluation/stability.py` |
| 3. Cost-quality record | the run's token / time report | `cost-benefit/cost.py add` → `table` |
| 4. Rule proposals | add-on 1 done on 2+ companies | skill-tuner (proposals only; the user approves every change) |

Add-ons need the repository (`evaluation/`, `cost-benefit/`). If it is not available, say so and offer to continue without them.

## Step 2: Plan, then run

1. One short plan message: the steps, the inputs found for each, anything missing, and the add-ons chosen. If an input is missing (no transcript for the new quarter, no hand-written note for add-on 1), ask before starting.
2. Run the steps in order. After each step:
   - its validator must PASS; fix FAILs inside that skill's rules before moving on;
   - the next step reads the file the previous step wrote, not a summary of it;
   - append-only files (call log, investment view) keep a backup until the check with `--before` passes.
3. If a step fails twice or needs a decision only the user can make (a judgment mark, a missing source), stop and ask; do not skip ahead.

## Step 3: Deliver

- A table: step, skill, file written, check result.
- For workflows A and B, the one thing to watch before the next report (taken from the new quarter block's next-quarter upside drivers).
- Add-on results with links to their reports.
- Files are delivered the way each skill delivers them; this skill adds nothing to their content.

## What this skill is not

- Not a program: the steps are run by the assistant, one skill at a time, and the user can stop or change course at any point.
- Not a place for analysis rules: a rule belongs in the skill that applies it, so it exists once.
