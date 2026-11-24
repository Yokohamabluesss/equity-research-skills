---
name: quarterly-financials-dashboard
description: 用于把一家上市公司过去 N 个季度（默认 10 个季度）的关键财务数据做成结构化仪表盘 (xlsx)，包含 Non-GAAP 利润表 + GAAP 利润表 + Non-GAAP vs GAAP 对比 + 资产负债表的库存与订单代理项 (deferred revenue / customer deposits / 合同负债 contract liabilities) + 现金流，并附一份关键观察 (key observations)。当用户说「列张表」「过去 N 个季度的财务数据」「Non-GAAP 历史季度数据」「按季度拉一下 XX 公司的财报」「财务仪表盘 / quarterly dashboard / financial summary」「附上库存/合同负债/现金流」「做成一个 skill / 沉淀成模板」，或者任何明显是「想看一家公司多个季度横向对比、不只是单季总结」的请求，使用此 skill。**与 earnings-call-reader 的区别**：earnings-call-reader 输入的是单份电话会 transcript（纵向深读一个季度的业务进展），输出的是 markdown 笔记；本 skill 输入的是公司 ticker（横向对比 N 个季度的财务数字），输出的是 xlsx 表格 + 关键观察。两个 skill 互补使用：先用本 skill 看清财务节奏，再用 earnings-call-reader 看每个季度业务发生了什么。
---

# Quarterly Financials Dashboard（季度财务数据仪表盘）

本 skill 用于把一家上市公司过去 N 个季度 (默认 10 个) 的关键财务数据沉淀成一份 xlsx 仪表盘 + 一份关键观察 (key observations)。目标是让用户在打开表格的 **30 秒内**看清楚一家公司目前所处的周期位置——靠的是把"Non-GAAP 利润表 + GAAP 利润表 + 库存/订单代理项 + 现金流"多层数据**横向**铺在同一张表上。

## 约定（固定不变）

- **版式来自脚本，不靠记忆**：把查到的数字写进 JSON，运行 `python scripts/build_financials_xlsx.py data.json {TICKER}_Financials_{N}Q_Dashboard.xlsx`。脚本按下文规格写出每一行、公式、配色、备注和关键观察表；JSON 格式见脚本开头注释。
- **交付前检查**：`python scripts/check_financials_xlsx.py 文件.xlsx`——LibreOffice 重算、公式错误、sheet 顺序、必需行、"必须是公式而不是手填数"、税率注释、关键观察。所有 FAIL 必须修掉。
- **语言**：行标签和 sheet 名是固定英文字符串（其他 skill 要读）；Notes 用用户提问的语言；关键观察永远**中英两列**。
- **季度标签**：用公司财年口径，`FY26 Q3` 格式。

## 核心原则

1. **横向对比，不是纵向深读**。本 skill 不是写公司研究报告，也不是单季业绩总结——是把多个季度的数字拉出来做趋势观察。**xlsx 是主交付物**，关键观察 (key observations) 是辅助交付物。
2. **Non-GAAP 与 GAAP 并列展示 (Non-GAAP + GAAP side-by-side)** —— **必须**给出两套完整的利润表：Non-GAAP 是管理层视角（剔除 SBC / 摊销 / 重组等），GAAP 是投资者最终看到的账面结果。**对科技类公司这两个口径经常差别显著**（尤其是有近期收购/大额 SBC 的公司），只看 Non-GAAP 会严重高估盈利质量。
3. **三层数据缺一不可 (three layers of data, all required)**：
   - **利润表层 (P&L layer)**：Revenue / YoY / QoQ / Gross Margin / Op Income / **Op Margin (%)** / Net Income / Diluted EPS —— Non-GAAP 与 GAAP 分开两页展示
   - **资产负债表层 (Balance Sheet layer)**：库存 (Inventories)、合同负债代理 (Deferred Revenue + Customer Deposits / 合同负债 contract liabilities)、应收账款 (AR)
   - **现金流层 (Cash Flow layer)**：经营现金流 (Cash from Operations, CFO)、季末现金及短投 (Cash & ST Investments EOP)
4. **「订单代理项」是这张表的灵魂 (order-proxy items are the soul)**。大多数美股半导体设备/工业品公司**不正式披露 backlog (在手订单)**，所以要从资产负债表里凑出最接近 backlog 的代理项：
   - **Deferred Revenue (递延收入)** — 已开票未确认的部分，通常对应已签合同未交付的服务/安装
   - **Customer Deposits (客户押金)** — 设备类公司收到的预付款，代表已下单未发货的订单
   - **Contract Liabilities (合同负债)** — 在 ASC 606 / IFRS 15 下的合同负债，A 股公司常用此口径
   - 这三个加总 (或单看其中一个口径) **领先于 revenue 1-2 个季度**，是判断订单拐点的最佳代理变量
5. **数据要有出处 (cite everything)**。每个数字底下要有备注，标明来自哪份 8-K / 10-Q / 10-K，至少标到 quarter level。
6. **数据源优先级 (data source priority)**：
   - **美股**：8-K Exhibit 99.1 (单季财报新闻稿) > 10-Q Note "Balance Sheet Components" (有库存/递延收入分项) > 10-K (年度全景) > 业绩说明会 transcript (用来交叉验证 CFO 等没明确披露的数字)
   - **A 股 / 港股**：定期报告（季报 / 半年报 / 年报）合并资产负债表 > 现金流量表 > 业绩说明会纪要 / 业绩快报 > 巨潮资讯 / 港交所披露易
   - 关键数字尽量两处对得上 (cross-check across at least two sources)

## 触发后的工作流

### Step 0：搞清楚 scope（5 秒）

确认两件事：
- **公司 (company)**：股票代码 / 中英文名 / 交易所
- **季度数 (number of quarters)**：默认 10 个季度，如果用户说「过去 8 个季度」「最近 4 年」就听用户的

如果用户在前序对话已经在讨论某家公司（**例如刚刚做完它的 earnings call summary，或者之前刚研究过它**），就直接默认那家公司，**不要**反问。

### Step 1：拉数据（最大头的工作量）

按时间顺序从最早到最近一个季度，对每个季度用 `web_search` + `web_fetch` 拉 8-K Exhibit 99.1 (美股) 或定期报告 (A 股 / 港股)。

**美股 SEC EDGAR 的 8-K Exhibit 99.1 是黄金来源**——每个季度的 Non-GAAP 表（gross margin、operating income、net income、diluted EPS）和 Condensed Balance Sheet 都在里面。但要注意：8-K 通常只给汇总的 balance sheet，**库存/递延收入/客户押金的明细要去 10-Q Note 6 "Balance Sheet Components" 里挖**。

**Non-GAAP + GAAP 数据都要拉**——两套要点：
- Non-GAAP: gross margin / OpEx / operating income / operating margin / net income / diluted EPS
- GAAP: 同上，但用 GAAP 口径

**搜索模板 (search query templates)**：
- `"{Company}" Q{n} {YYYY} non-GAAP EPS revenue adjusted` — 拿 Non-GAAP P&L
- `"{Company}" Q{n} {YYYY} GAAP net income EPS diluted` — 拿 GAAP P&L
- `"{Company}" 10-Q {month} {YYYY} inventory deferred revenue customer deposits` — 拿资产负债表明细
- `"{Company}" Q{n} {YYYY} cash from operations earnings release` — 拿 CFO

如果某个季度的某个数据点 **8-K + 10-Q 都查不到**（最常见的是当季 8-K 已发但 10-Q 还没发，或者 10-K 把 Q4 的资产负债表细项藏在不同的 note 里），**标 None / N/A，并在备注里说明原因**。**不要**编数字。

**Non-GAAP 有效税率的处理 (Non-GAAP effective tax rate)**：一般无需单独展示为一列（占空间），但**必须**在 Notes 区域标注：例如"公司 Non-GAAP 有效税率约 X%"。这是从 Op Income 反推 Adj Net Income 的关键参数，也是理解为什么 Adj NI 不完全等于 Adj Op Income × (1 - 常规税率) 的关键（还有利息、少数股东权益等）。

**对于资产负债表项目的特别注意 (special attention to balance sheet items)**：10-Q 里的资产负债表明细通常是「当季末」vs「上一财年末」两列对比，所以拉某一季度的数据时只需要看那一份 10-Q 的当季末列。但如果想拉某个 Q4 的数据，要去 10-K（不是 8-K，因为 8-K 不一定给细项）。

### Step 2：构建 xlsx（用 `scripts/build_financials_xlsx.py`，不要手写 openpyxl）

输出到 `{RESEARCH_ROOT}/{TICKER}/{TICKER}_Financials_{N}Q_Dashboard.xlsx`（有本地研究目录时），否则放会话输出目录。文件名去掉 "Non-GAAP" 字眼，因为现在同时包含 GAAP。

**四个 sheet**（从左到右）：
1. **Sheet 1: "Non-GAAP"** — Non-GAAP 利润表数据主表（含 Op Margin）
2. **Sheet 2: "GAAP"** — GAAP 利润表数据主表（含 GAAP Op Margin）
3. **Sheet 3: "GAAP vs Non-GAAP"** — 两套口径的 delta 对比（Net Income 差额、EPS 差额、delta 占 Adj NI 比例）
4. **Sheet 4: "BS + CF + Observations"** — 资产负债表明细 + 现金流 + 关键观察（Excel 的 sheet 名最多 31 个字符，原来的 "Balance Sheet + CF + Observations" 有 33 个字符会被截断，所以改用这个名字）

**Sheet 1 (Non-GAAP) 结构（横向，metric 为行、quarter 为列）**：

```
Row 1   : 标题 (公司 — Non-GAAP Quarterly Dashboard (N Quarters))
Row 2   : 数据源说明 (Source: 8-K filings, ...)
Row 3   : (空)
Row 4   : 表头 (项目 / Metric | Q(N-9) | Q(N-8) | ... | Q(now) | TTM)
Row 5   : Period End
Row 6   : Revenue ($M)
Row 7   : Revenue YoY %                       ← Excel 公式，YoY 需 helper 行
Row 8   : Revenue QoQ %                       ← Excel 公式
Row 9   : Adj Gross Margin %
Row 10  : Adj OpEx ($M)
Row 11  : Adj Operating Income ($M)           ← =Revenue * GM - OpEx（Excel 公式）
Row 12  : Adj Op Margin %                     ← =Op Income / Revenue（Excel 公式）⭐必须
Row 13  : Adj Net Income ($M)
Row 14  : Adj NI YoY %                        ← Excel 公式
Row 15  : Adj NI QoQ %                        ← Excel 公式
Row 16  : Adj Net Margin %                    ← =NI / Revenue（Excel 公式）
Row 17  : Adj EPS ($)

Row 30-35: Helper rows（prior-year quarterly revenues/NI 用于 YoY 公式）
Row 38+ : Notes（含 Non-GAAP 有效税率注释）
```

**Sheet 2 (GAAP) 结构（与 Non-GAAP 平行）**：

```
Row 6-17 与 Non-GAAP 完全平行，但用 GAAP 数字：
- GAAP Gross Margin % — 如果不容易拉到，可暂时留空 or 用相同 Rev × Non-GAAP GM 近似（注明估算）
- GAAP OpEx / Op Income / Op Margin — 尽量拉全
- GAAP Net Income / EPS — 必填
```

**Sheet 3 (GAAP vs Non-GAAP Reconciliation) 结构**：

```
Row 4   : 表头
Row 5   : Adj Net Income ($M)                 ← 从 Sheet 1 硬拷（不用公式跨表引用，减少 fragility）
Row 6   : GAAP Net Income ($M)                ← 从 Sheet 2 硬拷
Row 7   : Delta ($M)                          ← =Row 5 - Row 6（公式）
Row 8   : Delta / Adj NI %                    ← =Row 7 / Row 5（公式）
Row 10  : Adj EPS ($)                         ← 从 Sheet 1 硬拷
Row 11  : GAAP EPS ($)                        ← 从 Sheet 2 硬拷
Row 12  : Delta EPS ($)                       ← =Row 10 - Row 11（公式）

Row 15+ : Notes 解释 Delta 的构成（SBC / 摊销 / 重组 / 一次性收购费用等）
```

**Sheet 4 (Balance Sheet + Cash Flow + Observations) 结构**：

```
[Section: BALANCE SHEET — Inventory & Demand Signals]
Row 6   : Inventories, net ($M)
Row 7   : Deferred Revenue (current) ($M)
Row 8   : Customer Deposits or Contract Liabilities ($M)
Row 9   : Accounts Receivable, net ($M)

[Section: CASH FLOW]
Row 12  : Cash from Operations ($M)
Row 13  : Cash & ST Investments (EOP) ($M)

[Section: COMPUTED METRICS] (Excel 公式)
Row 16  : Inventory Days (= Inventory / Revenue × 90)
Row 17  : Order-related Liab. (= Deferred Revenue + Customer Deposits)
Row 18  : CFO / Adj NI ratio（现金转化率）
Row 19  : Cash conversion cycle days（如果能拉全 AR + AP + Inventory）

[Section: Key Observations] — Sheet 底部或单独 tab
参见下面「Key Observations」章节
```

**格式标准**：
- 字体：Arial 10pt
- **硬编码数据**：蓝色字体 (RGB 0,0,255) — 财务行业惯例
- **公式**：黑色字体 (RGB 0,0,0)
- **章节标题行 (section headers)**：浅蓝底 (D9E1F2) + 深蓝字 (1F4E79) 加粗
- **Non-GAAP sheet 表头**：深蓝底 (305496) + 白字加粗
- **GAAP sheet 表头**：深紫底 (8064A2) + 白字加粗 —— 视觉上快速区分两个口径
- **最新季度列高亮**：淡黄底 (FFF2CC)
- 数字格式：
  - 美元金额：`#,##0.0;(#,##0.0);-` (零显示为破折号)
  - 百分比：`0.0%;[Red](0.0%);-` (负数红色括号)
  - EPS：`$0.00;($0.00);-`
  - 倍数：`0.00"x";(0.00"x");-`
- 列宽：A 列 26-28（Metric），B-K 列 12（季度），L 列 14（TTM）
- **Freeze panes**：固定在 `B5`（保留第一列 metric label 和前 4 行）
- 用细灰边框 (BFBFBF) 增加可读性
- **自动换行 (auto-wrap) 必做**：所有有文字内容的 cell **必须** `Alignment(wrap_text=True)`，**且不要硬编码 `row_dimensions[r].height`**——硬编码行高会让 Excel 不按内容自动撑开，导致中文长段落被裁掉。让 Excel 在打开时按内容自动 fit。如果某些行需要最小高度（例如标题行），用 `height = 22` 这种**起始最小值**，但内容多的行（key observations、notes）一律不设 height

**关键计算项 (computed metrics — must use Excel formulas, not hardcoded)**：

```python
# Revenue YoY (uses helper row for prior-year same-quarter revenue)
=IFERROR(current_qtr_rev / prior_year_same_qtr_rev - 1, "")

# Revenue QoQ
=IFERROR(current_qtr_rev / prev_qtr_rev - 1, "")

# Op Income = Revenue × GM - OpEx
=Revenue * Gross_Margin - OpEx

# Op Margin
=Op_Income / Revenue

# Net Margin
=Net_Income / Revenue

# Inventory Days (proxy)
=IFERROR(inventory / revenue * 90, "")

# Order-related Liabilities
=IFERROR(deferred_revenue + customer_deposits, "")

# Cash conversion
=IFERROR(CFO / non_gaap_NI, "")

# TTM (Trailing 12 Months)
=SUM(last_4_quarters)
```

**必带的 Notes（Non-GAAP sheet）**：

1. 财年口径说明（例：公司财年截止某月，FY 标签以结束年为准）
2. 数据来源说明（例：SEC 8-K 财报新闻稿）
3. **凡是估算/派生的数据必须逐条说明**（例：FY25 Q4 Adj NI 由全年隐含 Adj NI - Q1-Q3 累计 反推）
4. Op Income 与 Op Margin 是 Excel 公式（不硬编码），依赖 Revenue × GM - OpEx
5. **必带税率注释**：`公司 Non-GAAP 有效税率 X%`（用于理解 Op Income → Net Income 的差异 + 后续估值 skill 的税收假设）
6. YoY 公式依赖 helper 行说明（如果用 helper 行做 prior-year 参照）
7. 最新季度高亮说明

**必带的 Notes（GAAP vs Non-GAAP sheet）**：

1. Delta 的构成拆解：SBC + 无形资产摊销 + 重组 + 收购相关一次性费用 + 税收调整
2. 是否有异常季度（如 CIEN FY25 Q4 Delta 因 Nubis 收购一次性费用异常放大）
3. Delta 的正常化 run-rate 估算（帮用户对 GAAP → Non-GAAP 未来趋势有感觉）
4. TTM Delta 汇总（帮用户快速看到"整体 Non-GAAP 溢价"）

### Step 2.5：输出路径约定

有本地研究目录时输出到 `{RESEARCH_ROOT}/{TICKER}/{TICKER}_Financials_{N}Q_Dashboard.xlsx`（按 ticker 归档，便于叠加每季的电话会笔记、研报和图表）；在不能持久化的沙盒里输出到会话的 outputs 目录让用户下载；终端会话放在当前目录 `./`，不要擅自建子文件夹。不确定时问用户一次存到哪里。

### Step 3：交付

1. 运行 `python scripts/check_financials_xlsx.py {file}`（**必做**，含 LibreOffice 重算），必须 PASS——重算后其他 skill 读缓存值才能看到数字
2. 把 xlsx 交给用户（展示文件 / 给出路径）
3. 在 chat 里给一段简短的说明（不要重复 xlsx 里已经写的内容）：
   - 关键观察用 **3-5 句话**总结（不重复表格里的数字，而是讲故事）
   - **必提**一句 GAAP vs Non-GAAP 的 delta 结论（例："TTM GAAP 净利只有 Non-GAAP 的 66%，主要因为 Nubis 收购一次性费用 + SBC 上升"）
   - 主动提一句**值得做的下一步**（例如「需不需要用 company-valuation skill 基于这套数据做个 PE / PEG 估值」）

## Key Observations 结构（可以放在 Sheet 4 底部或单独 tab）

**最顶部必须有一个「The Story / 一句话总结」高亮框 (highlighted summary box)**——浅黄底 (FFF2CC) + 深蓝字 (1F4E79)，merge 跨整行，**英文 + 中文各一段**（每段 3-5 句）。这是整张表最先被读到的内容，**必须**包含：① 周期起点 / 终点的关键季度 ② 收入/EPS 的高低点数字 ③ 最值得抓的一个 leading indicator 拐点 ④ 展望下一季度的 1 句话。

下面再接 8 个主题表格，**列结构必须是三列**：

| Theme / 主题 | Observation (English) | Observation (中文) |
|---|---|---|
| 1. Revenue cycle / 收入周期 | 周期处于哪一段（peak / trough / recovery）+ 数据支持 | 同左，中文版 |
| 2. Margin compression / 利润率压力 | Non-GAAP 与 GAAP 毛利率 + 营业利润率的变化幅度，原因 | 同左，中文版 |
| 3. Non-GAAP vs GAAP delta / 两套口径的差距 ⭐必须 | delta 的规模、原因、是否会正常化 | 同左，中文版 |
| 4. Inventory tells the cycle story / 库存讲周期故事 | 库存高点/低点、destocking/restocking 节奏 | 同左，中文版 |
| 5. Order-proxy = leading indicator / 订单代理 = 领先指标 | 递延收入+客户押金的拐点 vs 收入拐点的 lead time | 同左，中文版 |
| 6. Cash conversion / 现金转化 | CFO / NI 比率，working capital 变化 | 同左，中文版 |
| 7. Guidance trajectory / 指引轨迹 | 下季度 / 下一年指引 vs 本季实际 | 同左，中文版 |
| 8. Things to monitor / 后续跟踪 | 接下来 1-2 个季度需要重点跟踪的 leading indicator | 同左，中文版 |

**新增主题 3（Non-GAAP vs GAAP delta）**是这次升级的核心内容——对科技类公司，GAAP 与 Non-GAAP 的 delta 本身就是一个独立的观察维度：

- SBC 占比是否在膨胀（薪酬结构问题）
- 无形资产摊销是否为并购一次性 vs 结构性（新增 vs 存量摊销）
- 有没有异常季度（如收购当季一次性费用）
- delta 是否有 mean reversion 趋势

**双语规则 (bilingual rules)**：
- 主题名 (Theme) 是英中并列，用「 / 」分隔（例：`1. Revenue cycle / 收入周期`）
- Observation 列**必须**英文一栏、中文一栏，分两列展示，**不要**把中英文塞在同一个 cell 里——这样英语读者和中文读者各看一列，不会被对方的文字干扰
- 中英文内容**互为意译，不是直译** (paraphrase, not literal translation)。同一个 observation 在两种语言里都要读起来自然
- 数字、ticker、产品代号 (Q3 25, $266.6M, HBM VPA, Dragonfly® 3Di) 在两栏里都保持原样，不翻译

**Key Observations 的写法要求**：
- 每个 observation **必须**带具体数字（不接受「margin 提升」这种废话，必须是「op margin 从 21.1% 反弹到 25.2%，回升 410bp」）
- 每个 observation **必须**指出 leading indicator 还是 lagging indicator（订单类是 leading，营收是 coincident，毛利率是 lagging）
- 在 Things to monitor 里要给出**接下来要看的具体科目**（不是「关注业绩」，而是「关注 Q1 26 10-Q 里递延收入 + 客户押金这一行有没有反映 $240M HBM VPA」）

## 关于「订单代理项」更深的 context（Why this matters）

很多用户和卖方分析师拿到一份单季财报新闻稿就开始写总结，这种做法会**严重 underweight balance sheet 数据**。事实上：

- **递延收入 + 客户押金 (Deferred Revenue + Customer Deposits)** 通常领先 revenue 1-2 个季度。例如 ONTO 的递延收入在 Q4 24 跳到 $33.8M (前一个季度才 $26.8M)，紧接着 Q1 25 收入就出了创纪录的 $266.6M
- **库存 (Inventory)** 是滞后指标也是状态指标。库存连续下降通常意味着 destocking / 周期下行；库存配合 revenue 同步上升才是健康扩张
- **CFO / Non-GAAP NI 比率** 是质量指标。半导体设备类公司这个比率长期应在 1.0-1.3x，如果掉到 0.5x 以下要警惕（通常是应收+库存双膨胀，意味着营收质量在恶化）

把这三层数据放在同一张 N 季度的横向对比表上，是判断**周期位置**的最有效工具——这也是本 skill 与单季 earnings call 总结最大的区别。

## 与其他 skills 的接力关系

本 skill 是 **公司研究的"基础事实层"**，通常与以下 skills 联动使用：

1. **earnings-call-reader**（前置或后续）：把某季度电话会读厚，与本表的数字互相印证
2. **company-research**（前置）：首次覆盖时先建立赛道 + 客户 + 产品的定性框架，本 skill 再补上定量节奏
3. **company-valuation**（后续）：用本表的 Non-GAAP + GAAP EPS 作为**估值 skill 的输入基础**，避免估值 skill 重复拉数据

因此 **Non-GAAP + GAAP 双套表**特别重要——不只是"表格好看"，而是**下游 valuation skill 需要两套口径分别算 PE / PEG**。

## 模板 / 历史使用记录

- **第一次使用本 skill 的对话（ONTO）**：用户要 ONTO 过去 10 个季度 Non-GAAP 数据，附上库存、合同负债代理项、现金流，并把流程沉淀成 skill。
- **升级后使用（CIEN 2026Q2）**：加入 GAAP 页 + Op Margin 明示 + 税率注释 + GAAP vs Non-GAAP delta 页。输出 `CIEN_Financials_10Q_Dashboard.xlsx`，共 157 个公式，Non-GAAP 与 GAAP 两页平行结构，第三页汇总 delta。
- **当前版本**：版式移入 `scripts/build_financials_xlsx.py`；交付前跑 `scripts/check_financials_xlsx.py`；Sheet 4 改名为 `BS + CF + Observations`（31 字符限制）。
