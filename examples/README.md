# Examples

Sample outputs produced by the skills. Each output exists in English (`en/`) and Chinese (`zh/`); the skills follow the language of the request, so the two versions are separate runs with the same inputs, not one file in two languages. The quarterly financials dashboard is already bilingual (its Key Observations have English and Chinese columns), so there is one copy.

## TSEM (Tower Semiconductor) — data through FY26 Q3, price as of 2026-11-23

| File | Skill | What it shows |
|---|---|---|
| `{en,zh}/TSEM_Earnings.md` | earnings-call-reader | Three calls in cross-quarter mode: FY26 Q1 written first, then Q2 and Q3 appended. Every new entry is marked against the prior quarter (🔼 🔽 🆕 ➡️ ⚠️ 📌), and older quarters are not edited (`check_earnings_log.py --before` passes). |
| [`TSEM_Financials_10Q_Dashboard.xlsx`](TSEM/TSEM_Financials_10Q_Dashboard.xlsx) | quarterly-financials-dashboard | FY24 Q2–FY26 Q3: non-GAAP and GAAP P&L, the GAAP-vs-non-GAAP gap, inventory, customers' advances, cash flow, and bilingual Key Observations. |
| `{en,zh}/TSEM_Valuation_Dashboard.xlsx` | company-valuation | The 10-sheet workbook: method verdict, guidance-vs-assumption sources (guidance coverage 16.5%), a quarterly build to FY27 EPS, consensus back-out, PE / PEG, three-scenario FCFF with reverse DCF, and a peer check. Price $136.81 (2026-11-23 close). |
| `en/TSEM_Investment_View.md`, `zh/TSEM_投资判断.md` | investment-view | The Core block, then FY26 Q3 on top of Q2 and Q1. The five dimensions follow earnings-digest's rules; the estimate entry follows valuation-brief's rules and is read from the valuation workbook. Each quarter was added on top of the saved previous version, and `check_view.py --before` confirms that only lines were added. |

**Sources.**
- Transcripts: FY26 Q1 (2026-05-13), Q2 (2026-08-04) and Q3 (2026-11-02) calls, from Quartr via Yahoo Finance. They are not included in this repository.
- Quarterly figures: TSEM's Form 6-K Exhibit 99.1 press releases on SEC EDGAR. The balance-sheet and cash-flow series were cross-checked with stockanalysis.com.
- Price, consensus and peers: Yahoo Finance, read on 2026-11-23.
- US 10-year yield: Dow Jones / Morningstar, 2026-11-19.

**Limits.**
- 2027 Q3–Q4 revenue in the valuation is the model's own assumption. The capacity-use and start-to-ship-lag settings drive the result; the Base case is 13% above consensus FY27 EPS, and the workbook explains why.
- The minority interest in the FCFF is an estimate. Capex for Track 1, Track 2 and the next 200mm tranche has not been disclosed.
- Consensus and peer data come from a single source.
- Nothing here is a buy or sell view, a price target, or a cheap-or-expensive judgment. The FCFF per-share values are model outputs, not targets.

## Evaluation cases · AEHR, CIEN and GLW

Each company was held out while the rules were written. The [investment-view report](../evaluation/reports/2026-11-25_skill-vs-human.md) compares the skill’s marks with the analyst’s. The [five-company stability report](../evaluation/reports/2026-11-25_stability-5co.md) compares repeated runs of the call reader and digest, with a row for each company. Source materials, hand-written references and individual run files stay in the private workspace.

---

# 示例

各 skill 的输出示例。每份输出都有英文（`en/`）和中文（`zh/`）两版；skill 跟随提问语言，所以两版是用同一份输入分别运行的结果，不是一个文件里放两种语言。10 季财务表本身就是双语（Key Observations 分中英两栏），只有一份。

## TSEM（Tower Semiconductor）— 数据到 FY26 Q3，股价取 2026-11-23

| 文件 | Skill | 展示什么 |
|---|---|---|
| `{en,zh}/TSEM_Earnings.md` | earnings-call-reader | 三次电话会的跨季度模式：先写 FY26 Q1，再追加 Q2、Q3。每条新内容都相对上季标注（🔼 🔽 🆕 ➡️ ⚠️ 📌），旧季度不改动（`check_earnings_log.py --before` 通过）。 |
| [`TSEM_Financials_10Q_Dashboard.xlsx`](TSEM/TSEM_Financials_10Q_Dashboard.xlsx) | quarterly-financials-dashboard | FY24 Q2–FY26 Q3：Non-GAAP 与 GAAP 损益表、两套口径的差距、存货、客户预收款、现金流，以及中英双栏的 Key Observations。 |
| `{en,zh}/TSEM_Valuation_Dashboard.xlsx` | company-valuation | 10 页估值表：方法结论、指引与假设的来源分级（指引覆盖率 16.5%）、逐季推到 FY27 EPS、反解一致预期、PE / PEG、三情景 FCFF 与反推、可比公司。股价 $136.81（2026-11-23 收盘）。 |
| `en/TSEM_Investment_View.md`、`zh/TSEM_投资判断.md` | investment-view | 核心，然后 FY26 Q3 放在 Q2、Q1 之上。五维按 earnings-digest 的规则写；测算按 valuation-brief 的规则、从估值表读取。每一季都加在保存好的上一版之上，`check_view.py --before` 确认只新增了行。 |

**来源。**
- Transcript：FY26 Q1（2026-05-13）、Q2（2026-08-04）、Q3（2026-11-02）电话会，来自 Quartr（经 Yahoo Finance），不放进仓库。
- 季度数据：SEC EDGAR 上 TSEM 的 6-K Exhibit 99.1 财报新闻稿；资产负债表和现金流序列与 stockanalysis.com 交叉核对过。
- 股价、一致预期与可比公司：Yahoo Finance，2026-11-23 读取。
- 美国 10 年期国债收益率：Dow Jones / Morningstar，2026-11-19。

**局限。**
- 估值里 2027 Q3–Q4 的营收是模型自建假设。产能利用率和投片到出货的滞后决定结果；Base 的 FY27 EPS 比一致预期高 13%，估值表里写了原因。
- FCFF 里的少数股东权益是估计值；Track 1、Track 2 和新一批 200mm 扩产的资本开支金额都没有公布。
- 一致预期和可比公司数据只来自一个来源。
- 这里没有买卖观点、目标价，也没有贵或便宜的判断；FCFF 每股价值是模型输出，不是目标价。

## 评估案例 · AEHR、CIEN、GLW

写规则时留出了这三家公司。[投资判断对照报告](../evaluation/reports/2026-11-25_skill-vs-human.md#中文)逐家公司比较 skill 与分析师的判断标记。[五家公司稳定性报告](../evaluation/reports/2026-11-25_stability-5co.md#中文)列出了电话会解读和速读在相同输入上重复运行的结果。原始资料、手写参照和逐次运行文件保存在私有工作区。
