# Cost-benefit: what each way of running a skill costs, and what it buys

`evaluation/` asks **how good** the output is (against the analyst's hand-written work, and run to run). This folder asks the product question next to it: **a cheaper way to run a skill saves X - does quality drop by more than we accept?** A cheaper way can mean a smaller model, fewer inputs, fewer repeated runs, a cleaned transcript, or reusing an earlier output instead of regenerating it.

| | `evaluation/` | `cost-benefit/` |
|---|---|---|
| Question | Is the output right / consistent? | Is the extra cost worth the extra quality? |
| Varies | the skill's rules (tuning) | how the skill is run: model, inputs, repetitions |
| Fixed | how it is run | the skill's rules |
| Decision rule | `gate.py`: accept a rule change only if held-out quality is not worse | `cost.py decide`: accept a cheaper setup only if no quality metric is worse than the baseline's by more than a tolerance |

Both use the same idea of "not worse", so a cheaper setup and a better rule are judged the same way.

## What is measured

**Cost.**
- Tokens, tool calls and wall time per run, as reported by the runner (each run is a fresh Claude Code sub-agent, which reports its own usage).
- For inputs: characters and an estimated token count (about 4 characters per token for English, 1 per CJK character - for comparing options, not for billing).

**Quality** - the repository's existing metrics:
- validator pass;
- quotes found word for word in the source;
- numbers traceable to the source;
- judgment marks matching the reference;
- for call logs, section structure;
- number overlap with the reference run.

## Files

| File | Purpose |
|---|---|
| `cost.py` | `inputs` (size and clean / split savings), `quality` (one run), `add` (score a finished run from any model and record it), `table` and `decide` (per experiment), `repeats` (would fewer repeated runs show the same thing?) |
| `runs.json` | every run: experiment, config, tokens, tool calls, time, quality |
| `reports/` | one report per experiment date |

```bash
python cost-benefit/cost.py inputs "TSEM 2026Q2.txt"
python cost-benefit/cost.py table cost-benefit/runs.json
python cost-benefit/cost.py decide cost-benefit/runs.json --experiment model-tier-digest --candidate sonnet
```

## Running the experiments on other models

Nothing in the measurement is specific to Claude: the skills are markdown rules plus Python scripts, and every metric is computed from the output file. To put another model (GPT, Gemini, a local model) in the same table:

1. **Same input.** Give the model the skill's `SKILL.md` as its instructions and the same input file, in a fresh session, and have it write the output file the skill specifies.
2. **Record cost.** Take input and output tokens from the provider's API usage report. Note the time and the price per token relative to the baseline.
3. **Score and append.**

```bash
python cost-benefit/cost.py add cost-benefit/runs.json OUTPUT.md \
  --experiment model-tier-reader --config gpt --run gpt-1 --format log \
  --source "TSEM 2026Q2.txt" --ref baseline_run1.md --ref baseline_run2.md \
  --tokens 91000 --duration 120 --model "<model name>" --price-ratio <price vs baseline>
python cost-benefit/cost.py decide cost-benefit/runs.json --experiment model-tier-reader --candidate gpt
```

Run at least two runs per config: `decide` stays PROVISIONAL with fewer.

**Keep it fair.** The Claude runs executed the skill's validator and fixed what it flagged (up to three rounds here). A model in a plain chat window cannot run scripts and only produces a first draft. Either run every model where it can execute code (an API agent loop or a coding agent), or compare first drafts only, with self-checking switched off for all models. Use the same language, the same input file and a fresh session each time.

## Reports

- [2026-11-23 — cost vs quality, first round](reports/2026-11-23_cost-vs-quality.md): input preprocessing, local vs web transcript, input ablation, reuse vs fetch, model tier (Opus / Sonnet / Haiku) for earnings-call-reader and earnings-digest, and the number of repeated runs.

Raw run outputs stay in the private workspace; reports carry aggregates only.

---

# 成本效益：每种运行方式花多少、换来什么

`evaluation/` 问的是**输出好不好**（和分析师手写的对比、多次运行是否一致）。这个文件夹问的是旁边那个产品问题：**换一种更便宜的跑法能省 X，质量掉得是否超出可接受范围？** 更便宜的跑法包括：更小的模型、更少的输入、更少的重复次数、清理过的 transcript，或者沿用已有输出而不是重新生成。

| | `evaluation/` | `cost-benefit/` |
|---|---|---|
| 问题 | 输出对不对、稳不稳 | 多花的成本值不值 |
| 变的是 | skill 的规则（调优） | 运行方式：模型、输入、重复次数 |
| 固定的是 | 运行方式 | skill 的规则 |
| 判定规则 | `gate.py`：held-out 质量没变差才采纳规则修改 | `cost.py decide`：没有任何质量指标比基准差出容差，才采纳更便宜的跑法 |

两边"没变差"的标准是同一条，所以更便宜的跑法和更好的规则用同一把尺子判断。

## 测什么

**成本。**
- 每次运行的 token 数、工具调用次数和用时，由运行方报告（每次运行都是一个新的 Claude Code 子任务，会报告自己的用量）。
- 输入：字符数和估算的 token 数（英文约 4 字符一个，中文 1 字一个；用于比较方案，不是计费数字）。

**质量** —— 沿用仓库已有的指标：
- 校验是否通过；
- 引用是否在原文中逐字找到；
- 数字能否在原文中找到；
- 判断标记是否与基准一致；
- 电话会日志的章节结构；
- 与基准运行的数字重合度。

## 文件

| 文件 | 用途 |
|---|---|
| `cost.py` | `inputs`（输入大小与清理 / 拆分能省多少）、`quality`（单次运行的质量）、`add`（给任何模型跑完的结果打分并录入）、`table` 和 `decide`（按实验汇总与判定）、`repeats`（少跑几次是否能看出同样的结论） |
| `runs.json` | 每次运行：实验、配置、token、工具调用、用时、质量 |
| `reports/` | 每个实验日期一份报告 |

## 在其他模型上运行这些实验

整套测量不依赖 Claude：skill 是 markdown 规则加 Python 脚本，所有指标都从输出文件算出。要把另一个模型（GPT、Gemini、本地模型）放进同一张表：

1. **同一份输入。** 把 skill 的 `SKILL.md` 作为指令、给同一份输入文件、在全新会话里运行，让模型写出 skill 规定的输出文件。
2. **记录成本。** 输入和输出 token 取自该厂商 API 的用量报告；记下用时，以及相对基准的单价比。
3. **打分并录入。** 用上面那条 `cost.py add` 命令，再用 `decide` 和基准比较。

每个配置至少跑 2 次；少于 2 次，`decide` 只会给 PROVISIONAL。

**注意公平。** 这次的 Claude 运行会执行 skill 的校验脚本，并按提示修改（这里最多 3 轮）。在普通聊天窗口里跑的模型不能执行脚本，只能交第一稿。要么所有模型都在能执行代码的环境里跑（API agent 循环或编程 agent），要么所有模型都关掉自检、只比第一稿。语言、输入文件相同，每次都用全新会话。

## 报告

- [2026-11-23 — 成本与质量，第一轮](reports/2026-11-23_cost-vs-quality.md)：输入预处理、本地与网页 transcript、输入消融、复用与现场抓数、模型档位（Opus / Sonnet / Haiku）对 earnings-call-reader 和 earnings-digest 的影响、重复运行次数。

原始运行输出留在私有工作区；报告只放汇总数字。
