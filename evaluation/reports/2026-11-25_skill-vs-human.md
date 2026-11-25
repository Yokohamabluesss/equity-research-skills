# Skill vs human on held-out companies: investment-view v1.7.0 on AEHR, CIEN and GLW (2026-11-25)

[English](#english) | [中文](#中文)

<a id="english"></a>

**Question.** On three companies the rules were never tuned on, how close is investment-view v1.7.0 to the analyst's hand-written views, and does the gap look like the in-sample gap in the [first report](2026-11-22_skill-vs-human.md)?

**Short answer.** The gap carries over. On judgment, 12 of 14 dimension marks agree, about the same as in-sample (17 of 20). Line coverage is also about the same: 82–89% of the analyst's lines are covered or partly covered, against 83–92% in-sample. Two things change. **Orders now agrees on all three companies**, and both disagreements are on **Customers**, where the skill is more cautious than the analyst. The skill's **Core and estimates run long**: the Core is 1.5–3.7x the analyst's length and about twice the 8–15 lines its own rule asks for.

## Setup

| Run | Skill | Inputs available to the skill | Blind? |
|---|---|---|---|
| AEHR-v1.7 | investment-view v1.7.0 | FY26 Q4 transcript, call log, initial coverage note, financials dashboard, valuation workbook | yes: never read while the rules were written |
| CIEN-v1.7 | v1.7.0 | three transcripts (FY26 Q1–Q3), call log, digest, initial coverage note, financials dashboard, valuation workbook | yes |
| GLW-v1.7 | v1.7.0 | FY26 Q2 transcript, call log, digest, valuation brief, initial coverage note, financials dashboard, valuation workbook | yes |

- **Point-in-time replay.** Each run treated the date of the analyst's estimate as "today" (AEHR 2026-09-25, CIEN 2026-10-01, GLW 2026-10-13), had no web access, and used the latest price found in the valuation workbook or brief.
- **What was withheld.** A backup note in which the analyst had written their own view for an earlier quarter was not given to the skill, because it would leak the answer.
- **One run per company**, each in a fresh session (model: Opus). All three files pass `check_view.py`.
- In `manifest.json` these runs have `split: heldout`: they can judge a rule change, but are not evidence for one.

## Results

<!-- summary:start -->
| run | skill | marks | quarter numbers (text) | quarter terms | table numbers | core terms | estimates numbers | event numbers | ref lines covered / partial / missed | skill-only lines | core length vs human |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AEHR-v1.7 | investment-view v1.7.0 | 4/5 | 75% | 25% | 73% | 0% | 83% | — | 44% / 38% / 18% | 42 | 1.5x |
| CIEN-v1.7 | investment-view v1.7.0 | 4/5 | 75% | 75% | 100% | 42% | 64% | — | 47% / 41% / 12% | 40 | 3.7x |
| GLW-v1.7 | investment-view v1.7.0 | 4/5 | 100% | 100% | 100% | 57% | 84% | — | 47% / 42% / 11% | 34 | 2.7x |
<!-- summary:end -->

GLW's "4/5" is 4 of 4: the analyst left one dimension (Momentum) unmarked. The analyst's file for CIEN and GLW also holds earlier quarters and events; the skill wrote only the latest quarter, so those blocks are not scored.

### Held-out vs in-sample

| | in-sample (2026-11-22, v2 rules) | held-out (this report, v1.7.0) |
|---|---|---|
| mark agreement | 17 / 20 | 12 / 14 |
| where marks disagree | Orders (3 of 3) | Customers (2 of 2) |
| reference lines covered + partial | 83–92% | 82–89% |
| quarter-text number recall | 80–93% | 75–100% |
| table number recall | 83–100% | 73–100% |
| Core term recall | 46–82% | 0–57% |
| Core length vs human | 0.4–2.3x | 1.5–3.7x |

## Findings

**1. Judgment transfers.** Agreement on marks is the same as in-sample. On Orders, where all in-sample disagreements were, the two sides now agree on all three companies: each company here publishes hard backlog or order figures, so the skill's "hard data" reading and the analyst's "strong demand" reading point the same way. The Orders rule question from the first report is still open, but these three companies do not test it.

**2. The new disagreement is Customers.** On AEHR and CIEN the skill marks Customers ⚠️ and the analyst ✅️. The skill's reasons are concentration (a few customers above 10% of revenue, a rising share from hyperscalers), a slipped program at a key customer, and customer news from the previous quarter that management did not repeat. The analyst weighs more customers and more volume per customer. The [stability report](2026-11-25_stability-5co.md) shows the same dimension is the least stable one across repeated digests (it flipped on 2 of 5 companies). So this is a borderline rule, not noise in one run, and it is for the analyst to decide (see Next).

**3. Facts transfer, and the gaps are mostly inputs.** The quarter blocks hold up (number recall 75–100%, tables 73–100%). The Core is where coverage drops, as in-sample. AEHR's Core term recall is 0% because the analyst's Core rests on facts outside the inputs: product specifications from trade press, and in CIEN a market-share ranking from a research firm. The skill's "facts from the inputs only" rule blocks these by design.

**4. Who sees what.** The pattern from the first report repeats.
- The analyst adds outside knowledge, management's spoken shape of the coming quarters ("Q1 good, Q2 big ..."), short valuation adjectives the skill is not allowed to use, and an overall verdict that can differ from the marks: on GLW the analyst called the quarter ordinary while marking every dimension ✅️.
- The skill adds anchor numbers, ⚠️ caveats inside ✅️ dimensions, and dated prices. In 2 of 3 companies it also found an inconsistency inside the analyst's own valuation workbook: a price cell that no longer matched the price used in the rest of the workbook, and a growth rate in the notes that differed from the input cell. Both were checked against the workbooks and are real.

**5. Inherited marks.** For GLW the skill was given an existing digest written by an older version of the digest rules, and investment-view carries a digest's marks over unchanged. That digest had five ✅️. The current earnings-digest, run twice on the same call log in the stability test, marks Sub-industry ⚠️ both times, which is closer to the analyst's lukewarm verdict. So the view's marks depend on which digest it is given.

**6. Length.** The Core runs 22–32 Chinese lines against the rule's 8–15, and the analyst's Core is shorter still. Estimates run 2–6x the analyst's, which is intended (the v2 rules carry estimates at full resolution), but the Core length is a rule the skill does not keep and `check_view.py` does not check.

## Limits

- **One run per company**, so mark differences on a borderline dimension may partly be run-to-run variation (the stability report puts digest marks at 80% identical across runs).
- **The inputs are not identical to the analyst's.** The analyst wrote over time and with web access; the replay sees only the files. For CIEN the analyst's estimate used an earlier price date than the one in the workbook.
- **The CIEN run** stopped at a rate limit after writing its file; the file is complete and passes the validator.
- **Lexical proxies undercount paraphrase**, as in the first report. Missed lines were read by hand for this report; per-run files that quote the references stay in the private workspace.
- **The reference is not ground truth.**

## Next

1. **Customers rule (analyst decides).** One option: ⚠️ only for a new negative customer fact (a loss, a slip, concentration that rose), and a 📌 note, not a ⚠️ mark, when earlier customer news is simply not repeated. Decide together with the open Orders rule.
2. **Core length.** Add a `check_view.py` warning when the Core goes beyond the existing 8–15-line rule. This enforces a rule that already exists; it needs the analyst's approval like any rule edit.
3. **Re-run GLW with a fresh digest** to separate the input effect in finding 5.
4. These three companies are now the held-out set for `gate.py`: any rule change is re-run on them and kept only if they do not get worse.

---

<a id="中文"></a>

# 留出公司上的 skill vs 人：investment-view v1.7.0 在 AEHR、CIEN、GLW 上的对比（2026-11-25）

**问题。** 在规则从未调过的三家公司上，investment-view v1.7.0 和分析师手写判断有多接近？差距是否和[第一份报告](2026-11-22_skill-vs-human.md)里样本内的差距一样？

**简短结论。** 差距基本延续。判断上，14 个维度标记中 12 个一致，与样本内（20 个中 17 个）相当。行覆盖也相当：分析师的行有 82–89% 被覆盖或部分覆盖，样本内是 83–92%。有两处变化：**订单维三家全部一致**，两处分歧都在**客户维**，skill 比分析师更谨慎；skill 的**核心和测算偏长**：核心是分析师的 1.5–3.7 倍，约为它自己规则要求的 8–15 行的两倍。

## 设置

| 运行 | skill | skill 拿到的输入 | 是否盲测 |
|---|---|---|---|
| AEHR-v1.7 | investment-view v1.7.0 | FY26 Q4 transcript、电话会日志、首次研究笔记、财务表、估值表 | 是：写规则时从未读过 |
| CIEN-v1.7 | v1.7.0 | 三份 transcript（FY26 Q1–Q3）、电话会日志、速读、首次研究笔记、财务表、估值表 | 是 |
| GLW-v1.7 | v1.7.0 | FY26 Q2 transcript、电话会日志、速读、估值速读、首次研究笔记、财务表、估值表 | 是 |

- **按时点回放。** 每次运行都把分析师测算的日期当作"今天"（AEHR 2026-09-25、CIEN 2026-10-01、GLW 2026-10-13），不上网，价格用估值表或估值速读里最新的一个。
- **没给的材料。** 一份分析师写过某个早期季度自己判断的备份笔记没有给 skill，因为它会泄露答案。
- **每家公司跑一次**，每次都在新会话里（模型：Opus）。三份文件都通过 `check_view.py`。
- 在 `manifest.json` 里这些运行标为 `split: heldout`：它们可以用来评判规则修改，但不作为修改规则的证据。

## 结果

（自动生成的表见英文部分）

GLW 的"4/5"实际是 4/4：分析师有一个维度（业绩节奏）没有打标。CIEN 和 GLW 的手写文件还包含更早的季度和会议；skill 只写了最新一季，这些块不计分。

### 留出 vs 样本内

| | 样本内（2026-11-22，v2 规则） | 留出（本报告，v1.7.0） |
|---|---|---|
| 标记一致 | 17 / 20 | 12 / 14 |
| 分歧所在维度 | 订单（3 处全部） | 客户（2 处全部） |
| 手写行 覆盖 + 部分覆盖 | 83–92% | 82–89% |
| 季度正文数字召回 | 80–93% | 75–100% |
| 表格数字召回 | 83–100% | 73–100% |
| 核心术语召回 | 46–82% | 0–57% |
| 核心长度 vs 人 | 0.4–2.3x | 1.5–3.7x |

## 结论

**1. 判断能迁移。** 标记一致率与样本内相同。样本内的分歧全在订单维，这次三家双方都一致：这三家公司都公布硬的积压或订单数字，所以 skill 的"看硬数据"和分析师的"看需求强度"指向同一方向。第一份报告里的订单规则问题仍待定，但这三家检验不到它。

**2. 新的分歧在客户维。** AEHR 和 CIEN 上 skill 给客户 ⚠️，分析师给 ✅️。skill 的理由是集中度（几家客户各占收入 10% 以上、来自 hyperscaler 的占比上升）、关键客户的项目推迟、上季的客户进展管理层这次没再提。分析师更看重客户数和单客户用量都在增加。[稳定性报告](2026-11-25_stability-5co.md)显示，客户维也是重复运行速读时最不稳定的维度（5 家中有 2 家翻转）。所以这是一条处在边界上的规则，不是一次运行的偶然，交给分析师决定（见下一步）。

**3. 事实能迁移，缺口主要是输入。** 季度块表现稳定（数字召回 75–100%，表格 73–100%）。和样本内一样，覆盖率下降在核心部分。AEHR 核心的术语召回为 0%，因为分析师的核心建立在输入之外的事实上：行业媒体上的产品参数，以及 CIEN 中一家研究机构的市场份额排名。skill 的"事实只来自输入"规则有意挡住了这些。

**4. 各自看到什么。** 第一份报告里的模式重复出现。
- 分析师补上外部知识、管理层口头描述的后几个季度走势（"一季度不错、二季度很大……"）、skill 不允许用的简短估值形容词，以及可能和标记不一致的总体判断：GLW 上分析师说这季一般，但五个维度都标 ✅️。
- skill 补上锚点数字、✅️ 维度里的 ⚠️ 提示、带日期的价格。3 家中有 2 家，它还发现了分析师自己估值表里的不一致：一个价格单元格与表中其余部分用的价格不同；说明页里的一个增速与输入单元格不同。两处都已对照估值表核实，确实存在。

**5. 继承的标记。** GLW 给 skill 的是一份用旧版速读规则写的速读，而 investment-view 会原样沿用速读的标记。那份速读是五个 ✅️。当前版本的 earnings-digest 在稳定性测试里对同一份日志跑了两次，两次都把细分产业标为 ⚠️，更接近分析师"一般"的判断。所以 view 的标记取决于给它的是哪一份速读。

**6. 长度。** 核心有 22–32 行中文，规则要求 8–15 行，分析师的核心更短。测算是分析师的 2–6 倍，这是有意的（v2 规则要求测算保留完整精度）；但核心长度是 skill 没有遵守、`check_view.py` 也没有检查的一条规则。

## 局限

- **每家公司只跑一次**，所以边界维度上的标记差异可能部分来自运行之间的波动（稳定性报告中速读标记在两次运行间 80% 相同）。
- **输入与分析师并不完全相同。** 分析师是在一段时间内、可以上网时写的；回放只看文件。CIEN 的手写测算用的价格日期早于估值表里的价格。
- **CIEN 这次运行**在写完文件后因调用额度中断；文件完整，通过校验。
- **字面指标会低估改写**，与第一份报告相同。遗漏的行已人工读过；引用了手写版的逐次运行文件留在私人工作区。
- **手写版不是标准答案。**

## 下一步

1. **客户维规则（由分析师决定）。** 一个方案：只有出现新的负面客户事实（流失、推迟、集中度上升）才给 ⚠️；上季的客户进展只是没再提，写一条 📌 说明，不打 ⚠️。与待定的订单规则一起决定。
2. **核心长度。** 在 `check_view.py` 里加一条警告：核心超过现有的 8–15 行规则时提示。这是执行已有规则，但和任何规则修改一样需要分析师批准。
3. **用新跑的速读重跑 GLW**，把结论 5 里的输入影响分离出来。
4. 这三家公司现在是 `gate.py` 的留出集：任何规则修改都要在它们上面重跑，不变差才保留。
