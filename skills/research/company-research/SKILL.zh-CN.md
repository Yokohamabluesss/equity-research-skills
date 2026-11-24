---
name: company-research
description: 用于首次研究一家上市公司的结构化研究流程 (initial coverage / first-time deep dive)，围绕用户指定的某个细分业务展开（例如光通信 optical communication、AI 服务器 AI server、固态电池 solid-state battery、CRO、功率半导体 power semi 等）。当用户说"研究一下 XX 公司"、"扒一下 XX 的 YY 业务"、"首次覆盖 XX (initial coverage)"、"看看 XX 这家公司"、"XX 公司 + 某个具体业务方向"，或者抛出一个公司名加上一个细分领域（例如「中际旭创 光模块」、「天孚通信 光器件」、「沪电股份 AI PCB」、「LITE EML」、「Coherent silicon photonics」）时，使用此 skill。本 skill 会按四步走：① 基本财务结构 (financial snapshot & revenue mix) ② 近 10 季 Non-GAAP 报表 (10-Q Non-GAAP dashboard xlsx) ③ 深度财务信号 (forward-looking signals: gross margin / inventory / contract liabilities) ④ 重点业务深度剖析 (segment deep dive: product definition / market position / key customers)，并且会**在赛道下钻到产品级**（例如"光通信"会自动拆成 EML / CW / DFB / VCSEL / SiPh / 光模块 等具体产品分别展开）。即使用户没有明确说"研究"二字，只要意图明显是想首次了解一家公司在某个赛道的情况，也应该使用本 skill。本 skill 还内置「追问模式 / QA Mode」：当用户在已经生成研究笔记之后输入「追问模式」「QA」「QA 模式」中的任一触发词时，进入只在对话里回答、不修改已生成 md 文件的精准追问状态，输入「退出 / exit」即退出该模式——所以**只要用户输入这几个触发词，也必须使用本 skill**。
---

# Company Research（公司首次研究）

本 skill 用于把"我想首次研究一下某家公司在某个赛道的情况"这件事，做成一份结构化、有重点、信息可信的研究笔记。

## 约定（固定不变）

- **语言**：笔记用用户提问的语言。固定文件名：中文 `{公司简称}_{重点业务}_首次研究.md`，英文 `{TICKER}_{Segment}_Initial_Coverage.md`。报表固定为 `{TICKER}_Financials_10Q_Dashboard.xlsx`（见 Step 1.5）。
- **目录**：有本地研究目录时放 `{RESEARCH_ROOT}/{TICKER}/`，否则放会话输出目录。
- **步骤标题是固定字符串**（便于后续 skill 和复读时定位）：`## Step 1：基本财务画像`、`## Step 1.5：近 10 季报表`、`## Step 2：深度财务信号`、`## Step 3：{重点业务}深度剖析`、`## 信息缺口与未解决问题`（英文见英文版）。

## 核心原则

1. **重点业务优先 (focus on the target segment)**。用户每次会指定一个想研究的业务方向（例如光通信、AI 服务器、固态电池）。其他业务一笔带过，**不要**平均用力把每个业务都展开。
2. **拆到产品级 (drill down to product level) —— 极其重要**。用户给的关键词通常是**赛道级别**（"光通信"、"AI 服务器"、"功率半导体"），而公司自己在年报、电话会议、IR 材料里通常是按**产品级别**披露的（例如光通信里的 **EML / CW (Continuous Wave laser) / DFB / VCSEL / SiPh / 光模块 / 光器件**；AI 服务器里的 **GPU 模组 / HBM / NVLink switch / 液冷板**；功率半导体里的 **SiC MOSFET / GaN HEMT / IGBT 模块**）。**研究时必须从赛道下钻到产品**，对每个产品分别走 Step 3 的"产品定位 / 行业地位 / 客户"三问。如果不确定该怎么拆，先用一次 web search 看公司自己在最新年报或电话会上是怎么拆的，**跟着公司的口径拆**。
3. **数据要有出处 (cite everything)**。每个具体数字、每个客户名都要带行内引用——工具提供引用格式时用工具的引用，否则紧跟在论断后写 `[来源：文件名/期间/URL]`。找不到的就承认找不到，不要编。
4. **推测要标注 (mark speculation explicitly)**。Step 3 的客户信息如果是基于公开信息推测的（比如从产业链上下游、招标公告、产能配套关系倒推），必须明确写"⚠️ 推测 (speculation)：……"。
5. **数据源优先级 (data source priority)**：
   - **A 股/港股 (China A-share / HK)**：公司公告（巨潮资讯、港交所披露易）> 公司年报/季报 (annual report / quarterly report) > 电话会议 transcript / 业绩说明会 (earnings call) > 雪球/东方财富 > 券商研报摘要 (sell-side notes)
   - **美股 (US)**：SEC 10-K / 10-Q / 8-K > Earnings Call Transcript（Seeking Alpha、Motley Fool、Yahoo Finance）> 公司 IR 网站 (investor relations) > 财经媒体 (Bloomberg / Reuters / CNBC)
   - 避免单一来源，关键数字最好两处对得上 (cross-check key numbers across at least two sources)。

## 触发后的工作流

### Step 0：搞清楚研究对象 (Scope the target)

在动手前先确认两件事，如果用户的提问里**已经说清楚**就直接进入 Step 1，**不要**多问：

- **公司 (company)**：股票代码 (ticker) / 中英文全称 / 所在交易所 (exchange)
- **重点业务 (target segment)**：用户明确指定要研究的细分业务方向

如果用户只给了公司名没说研究什么业务，简短问一句："想重点看 XX 公司的哪块业务？"

如果用户给了明显的业务方向暗示（例如说"中际旭创 800G"——显然就是光模块），就**不要**反问，直接默认那就是研究对象。

**确认完之后，先用一次 web search 摸清楚"这家公司在这个赛道里实际怎么拆产品"**——例如搜 `{公司} 年报 收入构成 {赛道}` 或 `{TICKER} product breakdown {segment}`。这一步是为了拿到 Step 1 的收入拆分粒度和 Step 3 的产品清单，**不要**跳过；如果公司在赛道下分了 EML / CW / DFB 这种产品级别，后续 Step 3 必须分别展开。

---

### Step 1：基本财务信息 + 收入结构 (Financial Snapshot & Revenue Breakdown)

**目标 (goal)**：让用户在 30 秒内对这家公司"是干嘛的、靠什么挣钱、规模多大"有一个清晰画像。

**必须包含**：

1. **公司一句话定位 (one-line positioning)**：主业是什么、在产业链 (value chain) 的什么位置。
2. **最新一期收入与利润 (latest revenue & earnings)**：营收 (revenue)、归母净利润 (net income attributable to shareholders)、同比 (YoY) 增速。优先用**最新季度**，其次是**最新年报**。说明数据期间（例如"2025Q3 单季度"或"2024 年全年 (FY2024)"）。
3. **收入结构 (revenue breakdown) —— 重点**：按业务/产品/地区拆分，给出绝对值和占比 (% of total)。
   - **如果公司拆得细，就细着说**——不要主动合并。例如公司年报披露了"800G 光模块 / 400G 光模块 / 200G 及以下 / 其他"四档，那就四档全列出来。
   - **特别地，重点业务 (target segment) 内部如果还能再拆产品（如光通信里的 EML / CW / DFB），也要拆出来**——这是 Step 3 的基础。
   - 如果只能找到比较粗的拆分（例如只有"通信业务/数据中心业务"），就按粗的来，但说明"公司未进一步拆分 (not further disclosed)"。
   - **重点业务的收入占比要专门点出来**。
4. **利润结构 (margin / profitability mix)**：哪块业务利润率最高/最低（如果披露）、是否有明显的拖累项 (drag)。

**Step 1 输出格式**：

```markdown
## Step 1：基本财务画像 (Financial Snapshot)

**公司定位 (positioning)**：[一句话]

**最新业绩 (latest results)**（2025Qx / FY2024）：
- 营收 (revenue)：xxx 亿元，同比 (YoY) +/-x%
- 归母净利润 (net income)：xxx 亿元，同比 +/-x%
- 毛利率 (gross margin)：xx%

**收入结构 (revenue mix)**（按 [业务/产品/地区]）：
| 板块 | 收入 | 占比 | 同比 |
|---|---|---|---|
| **[重点业务]** ⭐ | xxx | xx% | +x% |
| └ 子产品 A (e.g. EML) | xxx | xx% | +x% |
| └ 子产品 B (e.g. CW) | xxx | xx% | +x% |
| 业务 B | xxx | xx% | +x% |
| ... | ... | ... | ... |

**利润结构亮点 (margin highlights)**：[1-2 句话]
```

> 不写市值 (market cap)、PE、PB、目标价 (price target)、股价走势 (price action)——本 skill 不做估值与择时 (no valuation, no timing)。

---

### Step 1.5（强制）：近 10 季 Non-GAAP 报表 (10-Quarter Non-GAAP Dashboard) —— **必须附上的标准交付物**

**目标 (goal)**：在文字研究之外，给用户一份**横向对比节奏的硬数字表**。Step 1 是单期画像，Step 1.5 是 10 期节奏，两者互补。

**强制要求 (mandatory)**：每一份首次研究都**必须附上一个 xlsx 报表**，命名 `{TICKER}_Financials_10Q_Dashboard.xlsx`，保存到与 md 同一目录。不能省略，不能用 markdown 表代替。

**列要求 (required columns)**：

| 列 | 字段 | 说明 |
|---|---|---|
| 1 | Quarter | 财季标签（如 FY26 Q1） |
| 2 | Period End | 财季截止日（YYYY-MM-DD） |
| 3 | Revenue ($M / 亿元) | 单期营收，单位与公司报表口径一致 |
| 4 | Revenue YoY | 营收同比，百分比 |
| 5 | Revenue QoQ | 营收环比，百分比 |
| 6 | Adj Gross Margin | Non-GAAP 毛利率 |
| 7 | Adj Net Income ($M / 亿元) | Non-GAAP 净利润 |
| 8 | Adj NI YoY | 净利润同比 |
| 9 | Adj NI QoQ | 净利润环比 |
| 10 | Adj Net Margin | Non-GAAP 净利率（= Adj NI / Revenue，用 Excel 公式计算） |
| 11 | Adj EPS ($) | 调整后每股收益（美股必填；A 股可放 EPS 元/股） |

> 如果公司只披露 GAAP（A 股常见），按 GAAP 口径走，把表头改成"GAAP"——但**口径必须明示**，不要 GAAP / Non-GAAP 混用。

**实现方法 (implementation)**：

- 优先：**调用 `quarterly-financials-dashboard` skill** 完成这一步（如果该 skill 在用户环境中可用）——它专门做这件事，自带建表脚本和检查脚本，并补上 GAAP、资产负债表订单代理项和现金流。
- 兜底：如果 `quarterly-financials-dashboard` 不可用，**自己用 xlsx skill 按上面 11 列的模板生成**。

**关键纪律 (discipline)**：

1. **YoY / QoQ 必须用 Excel 公式，不要用 Python 算完写值**——这样后续用户改一个数字全表自动联动。
2. **如果 YoY 需要的去年同期数据不在显示的 10 季内，用 helper rows 提供参考数据**（CIEN 模板示例了 FY22Q4 + FY23 Q1-Q3 作为 helper），不要留空 YoY 列。
3. **最新一季要高亮**（淡黄色 `FFF2CC`），让用户一眼看到对比基准。
4. **每个数字加来源 cite（在 Notes 区或 cell comment）**：来源应该是公司 SEC 8-K / 季报 / 年报，不是新闻媒体。
5. **派生数字必须说明派生方法**——例如 CIEN FY25 Q4 Adj NI 是用 "全年 EPS - 前 3 季 EPS" 反推的，要在 Notes 写清楚。
6. **冻结表头 + 列宽合理**，确保打开即可阅读，无需用户再调格式。
7. 交付前跑检查（quarterly-financials-dashboard 的 `check_financials_xlsx.py`，至少要用 LibreOffice 重算一遍）。

**Step 1.5 在 md 中的呈现**：在 md 的 Step 1 之后、Step 2 之前插入一段简短说明，**不要把 xlsx 表格的内容复制到 md 里**（会重复），只写：

```markdown
## Step 1.5：近 10 季 Non-GAAP 报表 (10-Q Non-GAAP Dashboard)

详见 `{TICKER}_Financials_10Q_Dashboard.xlsx`（与本笔记同目录）。表中包含近 10 个财季的营收 / Non-GAAP 毛利率 / Non-GAAP 净利 / Non-GAAP 净利率 / Adj EPS，以及 YoY / QoQ。

**关键观察 (3 条以内)**：
1. [例如：营收 YoY 从 FY24 Q4 的 -0.5% 加速至 FY26 Q1 的 +33.1%，连续 5 季加速]
2. [例如：Adj 毛利率底部出现在 FY25 Q2 的 41.0%，FY26 Q1 重回 44.7%]
3. [例如：Adj 净利率从 FY25 Q2 的 5.4% 跃升至 FY26 Q1 的 13.8%，3 季提升 8.4pp]
```

完成 Step 1.5 后再进入 Step 2。

---

### Step 2：深度财务信号 (Forward-Looking Financial Signals)

**目标 (goal)**：找出对未来业绩有领先性 (leading indicators) 的财务信号。这一步**不是把所有财务数据罗列一遍**，而是挑能反映"业务景气度趋势 (segment momentum)"的指标。

> Step 2 与 Step 1.5 的分工：Step 1.5 是**纵向节奏表**（YoY/QoQ 看趋势）；Step 2 是**前瞻信号分析**（库存、合同负债、Backlog 等领先指标），重点是"为什么会变 + 这意味着什么"。

**必须包含**：

1. **毛利率 / 净利率的季度变化 (quarterly gross margin & net margin trend，近 4-6 个季度)**：
   - 用表格或简单趋势描述，不要画图。Step 1.5 的 xlsx 表已经覆盖了数字，这里**重点解释变化原因**——是产品结构升级 (product mix upgrade)？是上游原材料涨跌 (raw material cost)？是规模效应 (scale / operating leverage)？还是产品降价 (ASP decline / price cuts)？
   - 如果公司在电话会议里对此有过解释，引用一下。

2. **库存 / 存货 (inventory)**：
   - 最新一期存货金额，环比 (QoQ)、同比 (YoY) 变化。
   - **背景对比 (context check)**：存货增长 vs 收入增长——存货增速远超收入增速通常意味着备货 (build-up，可能预示订单充足，也可能是滞销)；存货大幅下降通常意味着供应紧张 (supply-constrained) 或订单消化 (drawdown)。
   - 如果有原材料/在产品/库存商品 (raw materials / WIP / finished goods) 的进一步拆分，重点看**原材料和在产品的变化**——这两项更能反映备货意图 (forward-looking build)。

3. **合同负债 / 预收账款 (contract liabilities / advances from customers)**：
   - 最新金额，环比、同比变化。
   - **重要**：合同负债大幅增长通常意味着在手订单 (order book / backlog) 充足，是非常硬的领先指标 (strong leading indicator)。
   - 如果是 to B 长周期业务 (long-cycle B2B)，这一项尤其关键。

4. **其他视情况包含的信号 (other optional signals)**（不一定全有，挑相关的写）：
   - **应收账款 (accounts receivable, AR)**：变化是否合理、是否远超收入增速 = 信用风险 (credit risk)
   - **资本开支 / 在建工程 (capex / construction-in-progress, CIP)**：产能扩张节奏 (capacity expansion)，对应未来的供给
   - **研发费用率 (R&D as % of revenue)**：对科技公司很重要
   - **经营性现金流 vs 净利润 (operating cash flow vs net income)**：净利润含金量 (earnings quality)
   - **存货 / 应收周转 (inventory turnover / receivables turnover)**：运营效率变化

**输出格式建议**：用小标题 + 短段落，不要纯堆数据。每个指标至少给一句"这意味着…… (read-through:)"的解读。

---

### Step 3（重点）：研究业务的深度剖析 (Deep Dive on the Target Segment)

**这是整份研究的核心。前三步是铺垫，这一步要写得最厚最深。**

**关键原则 (cardinal rule) —— 必须拆到产品级**：

用户给的关键词通常是**赛道级 (segment-level)**，例如"光通信"、"AI 服务器"、"功率半导体"、"CRO"。但公司的**实际产品组合 (product portfolio) 通常更细**，常见拆分举例：

| 用户关键词 | 公司实际产品级拆分（举例） |
|---|---|
| 光通信 (optical communication) | 光模块 (optical transceiver: 800G / 1.6T / 400G) / EML / CW (Continuous Wave laser) / DFB / VCSEL / SiPh (silicon photonics) / 光芯片 / 光器件 |
| AI 服务器 (AI server) | GPU 模组 / HBM (High Bandwidth Memory) / NVLink switch / 液冷板 (cold plate) / PCB / BBU |
| 功率半导体 (power semi) | SiC MOSFET / GaN HEMT / IGBT 模块 / Si MOSFET |
| 储能 (energy storage / ESS) | 电芯 (cell) / PCS (power conversion system) / BMS / 系统集成 |
| CRO | 临床前 (preclinical) / 临床 (clinical I/II/III) / CDMO / 安评 |

**Step 3 的展开规则**：
- **如果这家公司在用户关注的赛道下有 ≥2 个明确产品 (sub-products)，必须分别展开 3.1 / 3.2 / 3.3**——每个产品都走一遍"产品定位 / 行业地位 / 客户"三问。
- **不要混着说**。例如不要写"公司光通信业务整体的客户包括 NVIDIA、Google……"——而要分别写 EML 的客户、光模块的客户、SiPh 的客户。
- **公司没有的产品就不写**。如果公司只做光模块、不做光芯片，那就只展开光模块这一条。
- **如果公司确实没有进一步拆产品（例如年报里只笼统披露"光通信收入 xxx 亿"），也要明确说一句"公司未在此赛道下进一步拆分产品 (no sub-product disclosure)"再展开**——这种情况按一个整体走三问即可。

#### 3.1 产品是什么、做什么用、产业链地位如何 (Product Definition & Value Chain Position)

针对每个产品分别说清楚：

- **产品本质 (what it is)**：是什么东西（用 1-2 句通俗说明，不堆术语）。
- **在用户关注领域内的用途 (use case)**：例如"800G 光模块用于 AI 数据中心交换机之间的高速互联 (high-speed interconnect)，是 GPU 集群东西向流量 (east-west traffic) 的核心载体"。
- **产业链位置 (value chain position)**：上游是谁（关键原材料 / 零部件供应商，upstream suppliers）、下游是谁（应用场景 / 直接客户类型，downstream customers）。
- **重要性 / 不可替代性 (criticality / moat)**：这个环节是产业链的"卡脖子 (bottleneck)"位置吗？还是同质化竞争激烈 (commoditized)？技术壁垒主要在哪 (technical barriers)？

#### 3.2 公司在行业内的地位与竞争力 (Market Position & Competitive Edge)

- **市场份额 (market share)**：能查到就给数字（注明数据来源和年份），查不到就给定性描述（"国内龙头 (domestic leader)"/"前三 (top 3)"/"二线追赶者 (tier-2 challenger)"）。
- **核心竞争力 (core competence)**：技术领先 (tech leadership)？产能领先 (capacity)？客户绑定 (customer lock-in)？成本优势 (cost advantage)？要给出**具体证据 (concrete evidence)**，例如"率先量产 1.6T 光模块"、"独家配套 (sole source) NVIDIA 某代际方案"。
- **是否为下游核心供应商 (Tier 1 supplier?)**：是 Tier 1 还是 Tier 2？是否进入头部客户的核心料号 (key BOM)？是否独供 (sole source)？
- **主要竞争对手 (key competitors)**：列 2-4 家，如果能拿到对比就简单对比一下（例如规模、技术节点 (process node)、客户结构差异）。

#### 3.3 主要客户 (Key Customers)

- **直接列出公开披露的大客户 (disclosed top customers)**：年报里"前五大客户 (top 5 customers)"如果有名称就直接引用，没有名称（很多 A 股只披露占比不披露名称，"customer A / 第一大客户"这种）就说明这一点。
- **从电话会议 / 调研纪要中提取客户线索 (signals from earnings calls)**：管理层提到"我们配套北美某大型云厂商 (a major North American hyperscaler)"、"已通过 H 客户认证 (qualified at customer H)"这种线索都要抓。
- **如果找不到明确客户，可以推测，但必须明确标注 (mark as speculation)**：
  - 推测的依据要交代清楚（产业链配套、招标公告 (tender / RFQ)、行业惯例、地理位置邻近等）。
  - 用 "⚠️ 推测 (speculation)："开头。
  - 例如："⚠️ 推测 (speculation)：公司未直接披露客户名称，但其主要产能位于苏州工业园，且 2024 年新增产线规格与 X 客户公开招标参数高度吻合，推测 X 为前两大客户之一。"
- **重点业务相关客户全列**，其他业务的客户**只列 Top 5 总体**或一笔带过。
- **如果业务下分了多个产品，客户也要分产品列**（例如 EML 的客户群和光模块的客户群完全不同——EML 的客户是 Lumentum / Coherent / 旭创自己这种**模块厂 (module makers)**，而光模块的客户是 NVIDIA / Google / Meta 这种**云厂商 (hyperscalers)**）。

---

## 追问模式 / QA Mode

**触发词 (trigger)**：用户输入「追问模式」「QA」「QA 模式」中的任何一个，即进入 QA 模式。

**模式定位 (purpose)**：研究笔记 (.md) 已经生成完毕之后，用户对里面的某个细节、某个数字、某个客户、某个产品想进一步追问。这个模式的作用是**只在对话里回答问题**，**不去改动已经生成的 md 文件**。

### QA 模式下的行为规则

1. **直接在对话里回答，不动 md 文件**。除非用户明确说「更新到 md」「写进文件」「补到第 X 段」之类的话，否则**绝对不要**重新打开 md 文件、不要重新生成、不要重新交付文件。
2. **回答深度看问题分量 (length matches the question)**：
   - 简单事实型问题（"它毛利率多少"、"前五大客户是谁"）→ 1-3 句话直接给答案。
   - 复杂分析型问题（"为什么 800G 毛利率比 400G 高"、"它和 Coherent 的客户重叠度怎么看"）→ 完整展开，结构化分点。
   - **不要**为了显得专业把简单问题答成长篇。
3. **保持原 skill 的严谨度 (cite & speculation marking)**：
   - 涉及具体数字、客户名、市场份额等**事实**，仍然要带引用。
   - 涉及推测，仍然要用 "⚠️ 推测 (speculation)：" 前缀，并交代推测依据。
   - 找不到的就承认找不到，不要编。
4. **可以在线补充检索**：如果问题超出了已生成 md 的范围（例如 md 只覆盖到 2025Q3，用户问"那 2025Q4 业绩出了吗"），可以即时 web search 后回答，但仍然只在对话里给答案。
5. **不需要每次重新走 Step 1/2/3 的全流程**。QA 模式是**针对单点问题精准回答**，不要把一个简单追问扩展成又一份完整研究。

### 退出 QA 模式

用户输入「退出」或「exit」即退出 QA 模式，回到普通对话状态。退出后如果用户提出新的研究需求（例如要研究另一家公司），按 skill 正常流程从 Step 0 开始走。

### QA 模式示例

> 用户：QA
>
> 助手：已进入 QA 模式，可以针对刚才的研究继续追问。
>
> 用户：800G 模块的客户里 NVIDIA 占比大概多少？
>
> 助手：年报和电话会议都没有直接披露按客户的收入拆分（A 股公司一般只披露"前五大客户合计占比"而不点名）。已知前五大客户合计占比约 xx% [来源：2024 年报]。⚠️ 推测 (speculation)：结合 2024 年 NVIDIA H100/H200 整机出货节奏与公司 800G 出货量的对应关系，推测 NVIDIA 单一客户口径占公司光模块业务收入约 xx%-xx% 区间，但这是间接测算，公司未直接确认。
>
> 用户：1.6T 啥时候放量？
>
> 助手：管理层在 2025Q3 业绩说明会上提到计划于 2026 年上半年开始批量出货 [来源：2025Q3 业绩说明会]，目前处于送样阶段。
>
> 用户：退出
>
> 助手：已退出 QA 模式。

---

## 输出形式 (Output Format)

**默认生成两个文件并交付给用户**：

1. **md 笔记**：`{公司简称}_{重点业务}_首次研究.md`（英文为 `{TICKER}_{Segment}_Initial_Coverage.md`），例如 `中际旭创_光通信_首次研究.md`、`AMD_AI加速卡_首次研究.md`、`LITE_EML_首次研究.md`。
2. **xlsx 报表**：`{TICKER}_Financials_10Q_Dashboard.xlsx`，与 md 同目录。**不能省略**。

md 文件结构按 Step 1 → Step 1.5 → Step 2 → Step 3 的顺序组织。文件开头加一个简短的元信息块 (metadata block)：

```markdown
# {公司全称} ({TICKER}) 首次研究 (Initial Coverage) —— {重点业务 / target segment}

> 研究日期 (date)：YYYY-MM-DD
> 重点关注业务 (target segment)：xxx
> 数据截止期 (data as of)：xxxx Qx
> 交易所 (exchange)：xxx
> 附件 (attached)：{TICKER}_Financials_10Q_Dashboard.xlsx
```

文件末尾加一个简短的"信息缺口与未解决问题 (Open Questions / Information Gaps)"列表——把研究过程中没找到的关键信息列出来（例如"未找到 800G 模块单独的毛利率拆分"、"主要客户名称未披露"），方便用户后续补充调研。

生成完文件后，在对话里给一段简短的口头总结（3-5 句），点出最值得关注的 2-3 条信号 (key takeaways)，但**不要**把整份报告再复述一遍。

## 引用规范

- 每一个具体数字、每一个客户名、每一个市场份额数据，都要带引用（工具引用或 `[来源：…]`）。
- 推测的内容**不要**加引用——引用是给有出处的事实用的；推测要用 "⚠️ 推测：" 前缀。
- 如果某段内容来自电话会议 transcript，明确说"在 2025Q3 业绩说明会上，管理层表示……"再加引用。

## 不要做的事

- ❌ 不要在不知道答案时编造数据。宁可写"该数据未在公开信息中找到"。
- ❌ 不要给买卖建议、目标价、估值结论。**完全不写**市值、PE、PB、PS、PEG、股价表现、技术分析——本 skill 只研究业务和财务结构本身，不做估值与择时。
- ❌ 不要把 Step 1 写成"百度百科风格"——只写跟核心业务相关的财务画像，不要展开讲创始人故事、历史沿革之类。
- ❌ 不要在 Step 3 里平均用力讲所有产品。用户只关心一个细分赛道，其他产品提一句就够了。
- ❌ 不要忘记"公司拆得细就跟着细说"——这是用户明确强调过的。
- ❌ **不要省略 Step 1.5 的 xlsx 报表**——这是强制交付物，任何首次研究都必须附上。
- ❌ **不要在 md 里把 xlsx 报表的 10 行数据完整复制粘贴**——只在 md 里写关键观察 3 条以内 + 指向 xlsx 文件名。复制全表只会让 md 冗长且与 xlsx 失去单一信息源。
- ❌ **进入 QA 模式后，绝对不要再修改、重新生成或重新 present 已经生成好的 .md / .xlsx 文件**——除非用户明确说"更新到 md / 写进文件"。QA 模式只在对话里回答。

## 一个完整的小例子（光通信场景 / Optical Communication）

> 用户：研究一下中际旭创，重点看光通信业务

注意：用户给的关键词是**赛道级**的"光通信"，所以 Step 0 要先 search 一下，发现公司在这个赛道下其实拆了多个产品（按速率分了 800G / 1.6T / 400G / 200G 及以下；同时还有自研光器件 / 光芯片业务）。Step 3 必须**对每个产品**分别走一遍三问。

预期输出骨架：

```
## Step 1：基本财务画像 (Financial Snapshot)
公司定位：全球光模块 (optical transceiver) 龙头，AI 数据中心高速互联核心供应商。
2025Qx 营收 xxx 亿，同比 +x%，归母净利润 xxx 亿……
收入结构 (revenue mix)：
| 板块 | 收入 | 占比 |
| **光通信业务** ⭐ | xxx | xx% |
| └ 800G 光模块 | xxx | xx% |  ← 跟着公司口径拆到产品级
| └ 1.6T 光模块 | xxx | xx% |
| └ 400G 光模块 | xxx | xx% |
| └ 200G 及以下 | xxx | xx% |
| └ 自研光器件 / 光芯片 (in-house optical components) | xxx | xx% |
| 其他业务 | xxx | xx% |

## Step 1.5：近 10 季 Non-GAAP 报表
详见 `300308_Financials_10Q_Dashboard.xlsx`。
关键观察：① 营收 YoY 从 2023Q4 +xx% 加速至 2025Q3 +xx%；② 毛利率 mix-driven 上行 xx pp；③ 净利率扩张 xx pp。

## Step 2：深度财务信号 (Forward-Looking Signals)
- 毛利率从 2024Q4 的 xx% 提升到 2025Q3 的 xx%，主要受益于 800G 占比提升 (mix shift)……（解读，不复述 Step 1.5 数字）
- 存货环比 +xx%，原材料环比 +xx%，与下半年 1.6T 备货节奏吻合……
- 合同负债环比 +xx 亿，订单可见度延伸至 2026 上半年……

## Step 3：光通信业务深度 (Deep Dive)

### 产品 1：800G 光模块
#### 3.1 产品与产业链地位
用于 AI 训练集群中 GPU 之间、Spine-Leaf 交换机之间的高速互联 (east-west traffic)……
产业链：上游 EML 激光芯片（来自日厂 Lumentum、Coherent 旧 II-VI），下游 NVIDIA、AWS、Google、Meta……
#### 3.2 行业地位
全球市占率约 xx%（按 2024 年出货量），与 Coherent、新易盛构成第一梯队……
#### 3.3 主要客户
- 年报披露前五大客户合计占比 xx%，未披露具体名称 (anonymized as Customer A/B/C)。
- 2025Qx 电话会议管理层提到"主要北美客户需求保持强劲"。
- ⚠️ 推测 (speculation)：结合产业链调研和公开招标信息，推测前两大客户为 NVIDIA 与 Google（或 AWS）。

### 产品 2：1.6T 光模块
#### 3.1 产品与产业链地位
下一代 (next-gen) 高速模块，对应 NVIDIA Rubin / B300 时代的网络需求……
#### 3.2 行业地位
预计 2026 年开始放量 (ramp)，公司是首批送样厂商之一 (early sampling)……
#### 3.3 主要客户
- 仍在送样阶段 (sampling)，尚未披露具体客户……

### 产品 3：自研光器件 / 光芯片
#### 3.1 产品与产业链地位
公司向上游延伸的 vertical integration 尝试，主要供自家模块使用，少量外销……
#### 3.2 行业地位
体量较小但战略意义重要 (strategic upstream exposure)，缓解上游 EML 供应紧张 (EML supply tightness)……
#### 3.3 主要客户
- 主要内销 (captive use)，外销客户未披露……
```

注意这份例子的关键点：**用户说"光通信"，但 Step 3 拆成了三个产品分别走三问**。每个产品的客户群可能完全不同（800G 的客户是 hyperscaler，自研光器件的客户是模块厂），所以**绝对不能混着写**。同时 **Step 1.5 强制附 xlsx 报表**——这是与单期 Step 1 画像互补的纵向节奏视图。

这就是一份合格的"首次研究"应该有的样子——重点突出、产品级拆分、数据有出处、推测有标注、不平均用力、附 10 季 Non-GAAP 节奏表。
