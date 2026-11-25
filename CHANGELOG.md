# Changelog

[English](#english) | [中文](#中文)

<a id="english"></a>

Versions apply to the whole skill set. Every change that can alter outputs is recorded here, so that examples and evaluation results can always be traced to the version that produced them.

## v1.7.1 — 2026-11-25

**Evaluation** (no skill changed)
- Held-out experiment [2026-11-25_skill-vs-human](evaluation/reports/2026-11-25_skill-vs-human.md): investment-view v1.7.0 on AEHR, CIEN and GLW, point-in-time replays. 12 of 14 marks agree; both disagreements on Customers; Core longer than its 8–15-line rule. Registered in `manifest.json` as `split: heldout`.
- Stability on five companies: [2026-11-25_stability-5co](evaluation/reports/2026-11-25_stability-5co.md). 20 runs, all valid; digest tags always identical, 20 of 25 marks identical.
- `stability.py`: quoted spans that contain Chinese characters are no longer counted as English quotes (TSEM call-log quote fidelity 99% → 100%).

## v1.7.0 — 2026-11-23

- **New meta skill `research-workflow`**: the entry point. Checks the company folder with `scripts/status.py`, offers fixed workflows (first coverage / new quarter / event / find companies / review) and optional add-ons (comparison with the analyst's note, stability check, cost-quality record, rule proposals), then runs the skills in order with their validators. No analysis rules of its own.
- **New `cost-benefit/` folder**: `cost.py` (input sizes and preprocessing savings, per-run quality, `add` for runs from any model, `table`, `decide`, `repeats`), `runs.json`, and the first report (model tier, inputs, repeated runs).
- **Examples**: TSEM through FY26 Q3 in English and Chinese, including the financials dashboard and the valuation workbook.
- Other skills unchanged.

## v1.6.1 — 2026-11-23

**Evaluation**
- First stability experiment: [reports/2026-11-23_stability-tsem.md](evaluation/reports/2026-11-23_stability-tsem.md). earnings-call-reader and earnings-digest, three fresh-session runs each on TSEM FY26 Q2: all valid; identical digest tags and marks; call-log sections 97% matched, quotes 99% verbatim.
- `compare_view.py`: numbers written as "$1.3 billion", "$138 million" and "13 percent" are now recognised (affects number recall and traceability).
- `stability.py`: section headings are matched by key tokens, so wording and bracketed notes may differ while a missing or moved section still counts.

## v1.6.0 — 2026-11-23

**Added**
- `evaluation/stability.py`: layer 3 of the evaluation (same input, same output?). For groups of runs of one skill version on one input: validator pass rate, tag and mark agreement across runs, number overlap, section / product-split overlap for call logs, length variation, and with `--source` quote fidelity and number traceability. Protocol in `evaluation/README.md`; the old-vs-new runs are next.
- `tools/build.py`: a docs check: every skill appears in both README skill tables and both halves of `docs/SKILLS_GUIDE.md`, the README intro states the right number of skills, and retired names (company-view) appear only in history files.
- `tools/selftest.py`: 46 cases, including one that keeps the README's stated case count true.

## v1.5.0 — 2026-11-23

**Changed**
- **company-view renamed investment-view.** Output files are now `{TICKER}_投资判断.md` / `{TICKER}_Investment_View.md`; the old names (`{TICKER}_财报前瞻判断.md` / `{TICKER}_Company_View.md`) are still recognised and updated in place, with an offer to rename. Earlier experiment records keep the old name.
- **One copy of each rule.** investment-view no longer repeats the judgment rules: the five dimensions and Other of a quarter block are written with earnings-digest's rules, the estimates with valuation-brief's rules, directly into the view (no separate digest or brief file; an existing one is carried over). `check_view.py` runs earnings-digest's `check_dims` and valuation-brief's `check` (both refactored into functions and synced into investment-view by `tools/build.py`), so the checks are identical too.
- earnings-digest: the typical Financials anchors now name revenue and EPS against the guided range.
- skill-tuner / TUNING.md: where a fix lands is now decided by the part: five dimensions → earnings-digest, estimates → valuation-brief, everything else → investment-view.
- `tools/selftest.py`: 44 cases. The existing v2 outputs pass the new checks; the dimension rules did not change in substance, so the 2026-11-22 comparison was not re-run.

## v1.4.0 — 2026-11-23

**Added**
- `evaluation/TUNING.md`: how comparison results become rule changes, with guards against overfitting (two-company evidence, method not content, held-out data never trains) and against gaming the metrics (acceptance on marks, number recall and a length budget; line coverage reported only).
- `evaluation/diagnose.py`: sorts differences into input gap / format / judgment / coverage / length / skill-only, diagnoses only the current skill version, finds patterns across companies on train runs.
- `evaluation/gate.py`: ACCEPT / REJECT / PROVISIONAL for a rule change, decided on held-out pairs only.
- `skills/meta/skill-tuner`: the skill that runs the loop and writes rule proposals; the analyst approves every edit; judgment rules are never tuned. `tools/build.py` syncs the evaluation scripts into it.
- Manifest runs carry `split` (`train` / `heldout`).
- skill-tuner: a step that finds where a company-view gap starts (earnings-digest, valuation-brief, company-valuation or company-view itself) and fixes it there; changes the user asks for directly are always allowed and recorded as user-requested.
- README: the evaluation section is now a short "evaluate → tune" loop that links to TUNING.md, plus a section on extending to other industries. TUNING.md: what to use without a hand-written reference, and which skills are tuned (company-view; company-valuation and stock-discovery additions only, framework unchanged).

**Changed**
- `tools/selftest.py`: 43 cases (diagnosis and the three gate verdicts).

## v1.3.0 — 2026-11-23

**Changed**
- `evaluation/`: the manifest is now a list of experiments. One experiment (one question at one time, possibly several companies) has one report, `reports/{id}.md`; a new experiment always gets a new report. `run_eval.py --experiment ID` creates the report from a skeleton and afterwards refreshes only the generated table, so written findings are kept; closed experiments are refused.
- company-view: the language rule is now explicit (a new file follows the request language; an existing file keeps its own).
- Price date: company-valuation, valuation-brief and company-view always use the latest price on the day the skill is called (also when reusing an older workbook), and company-valuation's Conclusion sheet reads price, multiples and FCFF from cells. Still no cheap / expensive judgments.
- `tools/selftest.py`: 38 cases.

**Evaluation**
- FORM re-run with the same inputs as the analyst (call log, initial coverage, valuation workbook); the transcripts-only run is kept as an input ablation. The 2026-11-22 report was updated, including a correction: FORM's low line coverage is not mainly an input gap.

## v1.2.0 — 2026-11-22

**Added**
- `evaluation/`: skill output vs the analyst's hand-written judgment, as a check of the skills' results. `compare_view.py` moved here from company-view's scripts and was rewritten: marks for every common quarter, value-based number matching (`$1.3B` = `13亿`, `430bps` = `4.3pp`, `CY27` = `2027`, ranges), case-insensitive terms with aliases, line-level coverage in both directions, text and tables scored separately, `--json`. `run_eval.py` scores every pair in `manifest.json`, which records each run's input condition.
- First report: `evaluation/reports/2026-11-22_skill-vs-human.md` (TSEM v1 / v2, COHR, FORM).

**Changed**
- Hand-off notes in earnings-digest, company-valuation and valuation-brief now name company-view as the next step; thesis-check also reads the company view.
- `tools/selftest.py`: 36 cases (adds the evaluation scripts).

**Removed**
- `docs/CALIBRATION.md`; its content is now in `evaluation/README.md` and the first report.

**Skill output**: no change to any skill's output rules in this version.

## v1.1.0 — 2026-11-22

**Added**
- `company-view` (new `synthesis/` group): one living judgment file per company, combining the Core (from earnings-digest's logic & narrative), one judged block per quarter, notes from non-earnings events (investor days, launches, trade shows, broker conferences, meeting notes), and dated estimates (from valuation-brief).
- `company-view` scripts: `check_view.py` (structure and append-only check), `split_bilingual.py` (keeps the English side of interleaved English / Chinese transcripts, about 25% fewer characters), `compare_view.py` (compares a generated view with a hand-written reference).

**Calibration v1 → v2 of company-view** (details in `evaluation/reports/2026-11-22_skill-vs-human.md`)
- The Core is a summary of about 8–15 lines; the company is placed in its peer tier when sources support it.
- The product table keeps every row of the thesis-relevant product lines and drops the other segments.
- Capacity tables (utilisation by fab, expansion tracks) are carried in full when supply is the constraint.
- Estimates are carried at the valuation brief's full resolution, with optional `数值` / `一致预期` labels.
- Event entries are kept to about 10–20 lines: the delta against the current view, plus new checkable facts.

**Still being tuned**: the company-view judgment rules are expected to keep changing as more hand-written references are compared, including an open question on when a stalled order figure should turn the Orders mark to ⚠️.

## v1.0.0 — 2026-11-22

- First public version of 11 skills in five groups (screening, research, earnings, valuation, review), each in English (`SKILL.md`) and Chinese (`SKILL.zh-CN.md`).
- Outputs follow the request language; fixed headings, labels and quarter format (`FY26 Q3`) in both languages.
- earnings-call-reader: transcript lookup (local file first, then Yahoo Finance, then ask the user) with header verification and paywall / truncation detection; log validator with an append-only check.
- Template builders and checkers for the xlsx skills; label validation in stock-discovery and architecture-delta-table; shared LibreOffice recalculation and error scan.
- Fixes: a hard-coded machine-specific output path (stock-discovery); a sheet name over Excel's 31-character limit (quarterly-financials-dashboard); empty citation placeholders (company-research); a duplicated ticker in a value-chain template (stock-discovery).
- `tools/build.py` (lint and packaging) and `tools/selftest.py`.

---

<a id="中文"></a>

# 版本记录

版本号针对整套 skills。所有可能改变输出的修改都记在这里，这样示例和评估结果总能对应到生成它们的版本。

## v1.7.1 — 2026-11-25

**评估**（skill 本身未改）
- 留出实验 [2026-11-25_skill-vs-human](evaluation/reports/2026-11-25_skill-vs-human.md)：investment-view v1.7.0 在 AEHR、CIEN、GLW 上按时点回放。14 个标记中 12 个一致；两处分歧都在客户维；核心超出 8–15 行的规则。在 `manifest.json` 中登记为 `split: heldout`。
- 五家公司的稳定性：[2026-11-25_stability-5co](evaluation/reports/2026-11-25_stability-5co.md)。20 次运行全部有效；速读标签始终相同，25 个标记中 20 个相同。
- `stability.py`：含中文字符的引号片段不再算作英文引用（TSEM 电话会日志的引用逐字率 99% → 100%）。

## v1.7.0 — 2026-11-23

- **新增元 skill `research-workflow`**：入口。用 `scripts/status.py` 检查公司文件夹，给出固定流程（首次覆盖 / 新季度 / 会议 / 找标的 / 复核）和可选附加项（与分析师手写版对比、稳定性检查、成本质量记录、规则修改建议），再按顺序运行各 skill 及其校验。自身不含分析规则。
- **新增 `cost-benefit/` 文件夹**：`cost.py`（输入大小与预处理节省、单次运行质量、录入任何模型运行结果的 `add`、`table`、`decide`、`repeats`）、`runs.json` 和第一份报告（模型档位、输入、重复次数）。
- **示例**：TSEM 到 FY26 Q3，中英两版，含财务表和估值表。
- 其他 skill 未改动。

## v1.6.1 — 2026-11-23

**评估**
- 第一次稳定性实验：[reports/2026-11-23_stability-tsem.md](evaluation/reports/2026-11-23_stability-tsem.md)。earnings-call-reader 和 earnings-digest 在 TSEM FY26 Q2 上各在新会话里跑三次：全部通过校验；速读标签和标记完全相同；电话会日志板块匹配 97%，引用 99% 逐字可查。
- `compare_view.py`：能识别"$1.3 billion""$138 million""13 percent"这类写法（影响数字召回率和可溯源率）。
- `stability.py`：板块标题按关键词匹配，措辞和括号注释可以不同，但缺失或挪了位置的板块仍会被计入。

## v1.6.0 — 2026-11-23

**新增**
- `evaluation/stability.py`：评估的第三层（同样输入，同样输出？）。对同一版本 skill 在同一输入上的多次运行，计算：校验通过率、各次之间标签和标记的一致性、数字重叠、电话会日志的板块 / 产品拆分重叠、篇幅波动，加 `--source` 时还计算引用忠实率和数字可溯源率。做法见 `evaluation/README.md`；旧版 vs 新版的实际运行是下一步。
- `tools/build.py`：文档检查：每个 skill 都出现在 README 中英两张 skill 表和 `docs/SKILLS_GUIDE.md` 中英两部分，README 开头写的 skill 数量正确，已弃用的名字（company-view）只出现在历史文件里。
- `tools/selftest.py`：46 个用例，其中一个保证 README 写的用例数量始终正确。

## v1.5.0 — 2026-11-23

**修改**
- **company-view 改名为 investment-view。** 产出文件改为 `{TICKER}_投资判断.md` / `{TICKER}_Investment_View.md`；旧文件名（`{TICKER}_财报前瞻判断.md` / `{TICKER}_Company_View.md`）仍能识别并原地更新，同时询问是否改名。之前的实验记录保留旧名。
- **每条规则只有一份。** investment-view 不再重复判断规则：季度块的五维和"其他"按 earnings-digest 的规则写，测算按 valuation-brief 的规则写，直接写进投资判断文件（不另外生成速读或估值速读文件；已有的直接搬过来）。`check_view.py` 直接运行 earnings-digest 的 `check_dims` 和 valuation-brief 的 `check`（两者重构为函数，由 `tools/build.py` 同步进 investment-view），检查也完全一致。
- earnings-digest：财务维常用锚点写明营收和 EPS 相对指引区间的位置。
- skill-tuner / TUNING.md：修改落在哪里按部分决定：五维 → earnings-digest，测算 → valuation-brief，其余 → investment-view。
- `tools/selftest.py`：44 个用例。现有 v2 产出能通过新检查；五维规则实质没有变化，所以 2026-11-22 的对比没有重跑。

## v1.4.0 — 2026-11-23

**新增**
- `evaluation/TUNING.md`：对比结果如何变成规则修改，含防过拟合（两家公司的证据、写方法不写内容、留出数据永不参与训练）和防刷指标（按标记、数字召回率和长度预算采纳；逐行覆盖率只报告）。
- `evaluation/diagnose.py`：把差异分为缺输入 / 格式 / 判断 / 覆盖 / 长度 / skill 独有，只诊断当前 skill 版本，在训练运行上找跨公司模式。
- `evaluation/gate.py`：对规则修改给出 ACCEPT / REJECT / PROVISIONAL，只看留出配对。
- `skills/meta/skill-tuner`：运行这个循环并写规则提案的 skill；每处修改由分析师批准；判断规则永不调整。`tools/build.py` 把评估脚本同步进去。
- 清单中的运行带 `split`（`train` / `heldout`）。
- skill-tuner：新增一步，判断 company-view 的差距源自哪里（earnings-digest、valuation-brief、company-valuation 或 company-view 本身）并在源头修改；用户直接要求的修改随时可以做，记为用户要求的修改。
- README：评估一节改为简短的"评估 → 调整"循环并链接到 TUNING.md，另加"扩展到其他行业"一节。TUNING.md：没有手写版时用什么，以及调哪些 skill（company-view；company-valuation 和 stock-discovery 只做补充，框架不变）。

**修改**
- `tools/selftest.py`：43 个用例（诊断和 gate 的三种结论）。

## v1.3.0 — 2026-11-23

**修改**
- `evaluation/`：manifest 改为实验列表。一次实验（某个时点的一个问题，可含多家公司）对应一份报告 `reports/{id}.md`；新实验一定是新报告。`run_eval.py --experiment ID` 首次按模板生成报告，之后只刷新自动生成的结果表，手写结论保留；已关闭的实验拒绝重跑。
- company-view：语言规则写明（新文件跟随提问语言，已有文件沿用其语言）。
- 股价日期：company-valuation、valuation-brief、company-view 一律使用调用 skill 当天的最新股价（复用旧估值表时也一样）；company-valuation 结论页的股价、倍数和 FCFF 一律引用单元格。仍然不判断贵或便宜。
- `tools/selftest.py`：38 个用例。

**评估**
- FORM 用与分析师相同的输入重跑（电话会日志、首次研究、估值表）；只用 transcript 的那次保留为输入消融。更新了 2026-11-22 报告，并更正一处结论：FORM 行覆盖率低主要不是输入差距。

## v1.2.0 — 2026-11-22

**新增**
- `evaluation/`：skill 产出 vs 分析师手写判断，作为对 skill 结果的检验。`compare_view.py` 从 company-view 的脚本移到这里并重写：所有共有季度的标记、按数值匹配数字（`$1.3B` = `13亿`、`430bps` = `4.3pp`、`CY27` = `2027`、区间）、不分大小写的术语和别名、双向的逐行覆盖、正文与表格分开计分、`--json`。`run_eval.py` 对 `manifest.json` 里的每一对打分，清单记录每次运行的输入条件。
- 第一份报告：`evaluation/reports/2026-11-22_skill-vs-human.md`（TSEM v1 / v2、COHR、FORM）。

**修改**
- earnings-digest、company-valuation、valuation-brief 的接力说明写明下一步是 company-view；thesis-check 也会读取公司判断文件。
- `tools/selftest.py`：36 个用例（加入评估脚本）。

**移除**
- `docs/CALIBRATION.md`；内容并入 `evaluation/README.md` 和第一份报告。

**skill 输出**：本版本没有改动任何 skill 的输出规则。

## v1.1.0 — 2026-11-22

**新增**
- `company-view`（新分组 `synthesis/`）：每家公司一份持续更新的判断文件，包括核心（来自 earnings-digest 的逻辑和叙事）、每季一个判断块、电话会以外材料的记录（投资者日、发布会、展会、券商会议、会议纪要），以及带日期的测算（来自 valuation-brief）。
- `company-view` 的脚本：`check_view.py`（结构和只追加检查）、`split_bilingual.py`（中英交替的 transcript 只保留英文，约少 25% 字符）、`compare_view.py`（把生成的判断和手写的参照版对比）。

**company-view 校准 v1 → v2**（详见 `evaluation/reports/2026-11-22_skill-vs-human.md`）
- 核心是摘要，约 8–15 行；来源支持时，把公司放进它所在的梯队并点名同业。
- 产品表保留投资逻辑相关产品线的每一行，删去其他板块。
- 供给受限时，产能表（按厂稼动率、扩产路线）完整保留。
- 测算按估值速读的原分辨率搬过来，可加 `数值` / `一致预期` 标签。
- 会议条目控制在约 10–20 行：相对当前判断的变化，加上之后可核对的新事实。

**仍在调整**：随着对比更多手写参照，company-view 的判断规则还会继续变化，其中一个待定问题是：订单金额停止更新时，订单维度何时应标 ⚠️。

## v1.0.0 — 2026-11-22

- 首个公开版本：11 个 skill，分五组（screening、research、earnings、valuation、review），每个都有英文（`SKILL.md`）和中文（`SKILL.zh-CN.md`）版本。
- 输出语言跟随提问语言；标题、标签、季度格式（`FY26 Q3`）在中英文下都固定。
- earnings-call-reader：transcript 获取（先本地，再 Yahoo Finance，最后请用户提供），带标题核对和付费墙 / 截断检测；笔记校验脚本，含只追加检查。
- xlsx 类 skill 的模板生成与检查脚本；stock-discovery 和 architecture-delta-table 的标签校验；共享的 LibreOffice 重算与错误扫描。
- 修复：写死的本机输出路径（stock-discovery）；超过 Excel 31 字符上限的 sheet 名（quarterly-financials-dashboard）；空的引用占位符（company-research）；产业链模板里重复的 ticker（stock-discovery）。
- `tools/build.py`（检查与打包）和 `tools/selftest.py`。
