---
name: earnings-call-reader
description: "用于阅读和总结上市公司财报电话会（earnings call）纪要的 skill。transcript 先找公司文件夹里的本地文件，没有再从 Yahoo Finance 获取（核对公司与季度），仍没有则请用户提供。当用户提供一段英文或中文的电话会 transcript（通常是纯文本或 Markdown），并希望得到结构化的总结、业绩展望提炼、产品进度梳理、在手订单/产能情况汇总、或新客户动态时，使用此 skill。触发词包括但不限于：「总结这份电话会」「读一下这个 transcript」「conf call 纪要」「财报电话会」「earnings call」「业绩说明会」「summarize this call」。即使用户没有明确说「总结」，只要输入内容明显是一份电话会纪要（有 Operator / CEO / CFO / Analyst 等发言人标记，或有 Q&A 环节），都应当使用此 skill。本 skill 还支持跨季度对比：当工作目录下存在该公司的 {TICKER}_Earnings.md 历史笔记文件时，自动进入跨季度对比模式，把本季内容追加到对应板块的对应位置，并对客户进度、业绩展望、订单可见度、细分产业等关键信号的变化用 emoji + 加粗高亮。"
---

# Earnings Call Reader

一个用来读财报电话会 transcript 并输出结构化复盘笔记的 skill。

## Goal

快速捕捉投资视角下最有用的几类信号:

1. Outlook
2. Drivers of current quarter profitability
3. Product-level demand and industry dynamics
4. Orders and backlog
5. Customers
6. Revenue ramp timing
7. Capacity constraints

## 约定（固定不变——这是输出一致的关键）

- **目录**：每家公司一个文件夹，文件夹名 = TICKER；每家公司只有一份 `{RESEARCH_ROOT}/{TICKER}/{TICKER}_Earnings.md`，所有季度追加进同一个文件。用户保存的 transcript 也放在这个文件夹。
- **季度标签**：一律写 `FY{YY} Q{n}`，按公司**财年**（如 `FY26 Q3`）。速览（TL;DR）的季度标题再加电话会日期：`FY26 Q3 (2026-10-28)`。这与 Yahoo/Quartr transcript 的财年标注一致（"Q3 FY2026"）。用户说"2026Q3"按财年 FY26 Q3 理解；如果 transcript 标题与用户要的季度不一致，两者都列出来请用户确认。
- **输出语言**：新建笔记时用用户提问所用的语言；**追加到已有笔记时一律沿用该文件的语言**。标题是固定字符串（见下表），不得改写。
- **脚本**（`scripts/` 下，Python 3，不联网）：
  - `transcript_tool.py find | verify | clean`——查找、核对、精简 transcript。
  - `check_earnings_log.py`——写完后校验笔记骨架、覆盖度和"旧内容不可改"规则。

| 元素 | 英文笔记 | 中文笔记 |
|---|---|---|
| 标题 | `# {TICKER} Earnings Call Log` | `# {TICKER} Earnings Call Log` |
| H2 | `## TL;DR` | `## 速览（TL;DR）` |
| H2 | `## Guidance` | `## 业绩展望（Guidance）` |
| H2 | `## Drivers of Profitability` | `## 当季盈利驱动因素 (Drivers of Profitability)` |
| H2 | `## Product Breakdown` | `## 分产品 / 分业务线进展 (Product Breakdown)` |
| H3（分产品板块第一个） | `### Company-wide Demand / Order Book / Capacity Overview` | `### 整体 Demand / Order Book / Capacity 总览（全公司层面）` |
| H5（按此顺序） | `##### Demand / Industry Dynamics` · `##### Order Book / Backlog` · `##### Customers` | 同左 |
| H2 | `## Product Summary Table` | `## Product Summary Table` |
| H2（可选） | `## Other` → `### FY26 Q3` → `#### Capacity` · `#### Pricing` · `#### Other Notable Points` | `## Other` → `### FY26 Q3` → `#### Capacity` · `#### Pricing` · `#### 自由发挥` |

## Step 0：获取 transcript（先本地，再 Yahoo，最后请用户提供）

先确定**公司 + TICKER** 和**财季**。用户没说季度时，默认最近一次电话会。

**0a. 用户直接贴了文本**——直接用，不另存文件。

**0b. 本地文件（永远先查）**：不用联网，来源可复现。

```bash
python scripts/transcript_tool.py find --ticker FORM --quarter "FY26 Q3" --dir "{RESEARCH_ROOT}/FORM"
```

- `FOUND`（按 transcript 自带的标题行匹配）→ 再跑一次 `verify` 后使用。工具提示文件名有笔误时告诉用户，但不要擅自改名。
- `CANDIDATE`（文件名匹配但没有标准标题行，或是本环境读不了的 pdf/docx）→ 先打开前几行（pdf/docx 用对应的文件 skill），确认写明了公司和季度才使用。
- `NOT FOUND` → 0c。

**0c. Yahoo Finance（默认网络来源）**

1. 用 WebFetch 打开列表页 `https://finance.yahoo.com/quote/{TICKER}/earnings-calls/`，取所有标题和链接。标题形如 `FORM Q3 FY2026 earnings call transcript`。
2. 只选 ticker 和 `Q{n} FY{YYYY}` **都**完全一致的那条；没有就转 0d，**不要拿相邻季度凑数**。
3. 用**浏览器工具**（内置浏览器或 Claude in Chrome）打开 transcript 链接。**先检查，再读全文**——在页面里运行下面这段（javascript 工具），只看返回的小结果：
   ```js
   (() => { const t = (document.querySelector('main') || document.body).innerText.split(/Copyright ©/)[0];
     return { title: document.title, head: t.slice(0, 300), chars: t.length,
              paywall: /Upgrade to unlock|subscription plan is required/i.test(t), tail: t.slice(-400) }; })()
   ```
   只有同时满足才使用：标题 / 开头包含所要季度的 `({TICKER}) Q{n} FY{YYYY}`（如 `FormFactor, Inc. (FORM) Q3 FY2026 earnings call transcript`）；`paywall` 为 false；`chars` 在常见的 3.5 万–8 万字符之间；`tail` 以结束语结尾（"This concludes…"、"disconnect"）。公司名也要和用户指的公司对上（注意不同股份类别、相近 ticker）。
4. 再用 `get_page_text` 读取全文，`max_chars` 设到 150000 以上。**不要用 WebFetch 读正文**：它返回的是模型写的摘要而不是原文，引用会不可靠（而且 Yahoo 的 transcript 页面经常拒绝它）。没有 javascript 工具时，读页面后对开头和结尾几行做同样的检查。（已保存的文件用 `transcript_tool.py verify` 做这些检查。）
5. **付费墙**：Yahoo 通常只免费开放最近一次电话会；更早的只显示开头一段和 "Upgrade to unlock … A Silver or Gold subscription plan is required"。**绝不能拿预览片段做总结**，转到 0d。
6. 在本季笔记开头记下来源（URL + 获取日期）。**不要把 transcript 重新打字存成文件**来"缓存"——那和 transcript 本身一样耗 token。用户想留本地副本的话，建议他把页面另存为 `{TICKER} {YYYY}Q{n}.txt` 放进公司文件夹，下次 0b 就能直接找到。

**0d. 都拿不到** → 明确告诉用户是哪一步失败（本地没有 / Yahoo 没有对应季度 / 付费墙 / 浏览器不可用），请他把 transcript（txt、md、pdf 或 docx）放进 `{RESEARCH_ROOT}/{TICKER}/` 或直接贴进来，然后停下等待。

**可选省 token**：`transcript_tool.py clean FILE -o FILE.clean.txt` 去掉时间戳、重复的发言人标题和页面杂项（已存的 txt 约省 4%，原始网页文本更多）。不改动任何发言原文，引用依然准确。

`verify` 的警告需要判断：*没有结束语*（可能被截断——检查最后一段，缺内容要在笔记里说明）；*没有 Q&A 标记*（只有管理层发言——在速览里注明）。

## 使用前的准备工作

### Step 1: 识别公司与期间

- **公司名称及股票代码**（TICKER，如 NVDA / LITE / AVGO）
- **财季**（统一写成 `FY{YY} Q{n}`，如 FY26 Q3）
- **电话会日期**
放在输出的最上方。

### Step 2: 检测跨季度模式（重要）
 
在写入任何内容之前，**必须先检查工作目录下是否存在历史笔记文件**：

#### 目录约定
 
本 skill 假设用户的目录组织如下：
 
```
{RESEARCH_ROOT}/
├── NVDA/
│   └── NVDA_Earnings.md
├── LITE/
│   └── LITE_Earnings.md
└── ...
```
 
每家公司一个子文件夹，文件夹名 = TICKER；每家公司**只有一份** `{TICKER}_Earnings.md`，所有季度都追加进同一个文件。用户在跑 skill 前应当已经 `cd` 到目标公司的子文件夹
 

#### 检查历史笔记文件是否存在

```bash
ls {TICKER}_Earnings.md 2>/dev/null
```

- **文件不存在** → 单季度模式（first run）。新建 `{TICKER}_Earnings.md`.
- **文件存在** → 跨季度对比模式。读取整份历史文件，识别已有的季度数据，把本季内容追加到对应板块的对应位置。**严禁修改任何旧季度的内容**。
- 跨季度模式写入前，先把文件复制为 `{TICKER}_Earnings.backup.md`（写入流程第 5 步的"旧内容未改动"检查要用，检查通过后删除）。
判断模式后再开始写作。下面的 [Output Structure](#output-structure) 描述初次运行的结构；[跨季度对比模式](#跨季度对比模式) 描述追加逻辑。


## 输出格式要求

### 双语原文引用规则

每一个关键论点后面都要附上**原文 + 翻译**，格式是：

> "Demand for our AI accelerators remains significantly ahead of supply, and we expect this to continue through fiscal 2026." 我们 AI 加速器的需求显著超过供给，预计这一情况将持续到 2026 财年

规则：
- 英文原文用引号包起来
- 翻译**直接跟在英文后面**，中间用空格或换行分隔，**不要写"翻译："两个字**，也**不要单独分行列出**
- 如果原文本身就是中文，则只保留原文，不需要重复
- **英文笔记**：只保留英文原文，不加翻译

### 数据呈现规则

所有涉及数字的结论都必须带上具体数据(除非文中没有)，不能只说"增长很快"。例如：
-  营收同比 +47%，达到 $35.1B，超出指引上限 $33B
-  营收同比大幅增长

## Output Structure

文件按**主题分大块**组织。**两种嵌套规则并存**：

- **大多数板块（TL;DR / Guidance / Drivers / Product Summary Table / Other）**：板块 → 季度。每个板块下用季度作为子标题并列，本季内容追加在该板块底部。
- **分产品板块（核心）**：板块 → 产品 → 季度。每个产品下用季度作为子标题并列，本季内容追加在该产品的**最后一季之后**，**让同一产品的所有季度连续展示，便于跨季度对比同一产品的进度演化**。

旧季度内容一律**不动**。

文档骨架长这样：
 
```
# {TICKER} Earnings Call Log
 
## 速览（TL;DR）
### {季度A}（日期）
...
### {季度B}（日期）   ← 本季追加
...
 
## 业绩展望（Guidance）
### {季度A}
...
### {季度B}   ← 本季追加，含 vs 上季变化标注
...
 
## 当季盈利驱动因素
### {季度A}
...
### {季度B}
...
 
## 分产品 / 分业务线进展                    ← 关键：先全公司总览 → 产品级（二级归类）
### 整体 Demand / Order Book / Capacity 总览（全公司层面）   ← 本季 H4 / 跨季度时按季度细分
#### {季度A}
#### {季度B}                              ← 本季追加在总览下方

### Product A
#### {季度A}
##### Demand / Industry Dynamics
##### Order Book / Backlog
##### Customers
#### {季度B}                              ← 本季追加在 Product A 下方
##### Demand / Industry Dynamics（含 vs 上季）
##### Order Book / Backlog（含 vs 上季）
##### Customers（含 vs 上季）

### Product B
#### {季度A}
...
#### {季度B}                              ← 本季追加在 Product B 下方
...
 
## Product Summary Table
### {季度A}
| 表 |
### {季度B}   ← 本季新表，追加在下面，不改旧表
 
## Other（如有）
### {季度A}
#### Capacity
#### Pricing
#### 自由发挥
### {季度B}
...
```

> 季度标签示例：`### FY26 Q2 (2026-07-29)`（速览）、`### FY26 Q2`（其他板块）、`#### FY26 Q2`（分产品板块）。

> **为什么分产品板块用"产品 → 季度"而不是"季度 → 产品"？**
> 投资视角下最关键的对比维度是"同一产品在不同季度的进度变化"——例如 EML 从 Q1 sold out → Q2 sold out + LTA 锁到 CY27 末。把同一产品的多季度内容并列展示，能让读者一眼看到节点演化、不用前后翻找。其他板块（如 Guidance）的核心维度是"同一季度内的多个指标全貌"，所以按季度分组更合适。
 
---
 
下面是每个板块的**填写规则**。这些规则对单季度模式和跨季度模式都适用——区别只在于跨季度模式下要追加内容并加变化标注，详见 [跨季度对比模式](#跨季度对比模式)。
 
---

## 速览（TL;DR）

用 3–5 行 bullet 概括本次电话会最重要的信号。适合一眼看完就知道这家公司本季度的核心故事是什么。

---

## 业绩展望（Guidance）

1.列出管理层对**下一季度**和**全年**的指引。如果管理层给了多年展望（例如 CY26、FY27），也一起列出。
2.如果对整体出货量、Demand trend有所指引，也需列出。

格式建议：

| 指标 | 本季实际 | 下季指引 | 全年/长期指引 | 原文引用 |
|---|---|---|---|---|
| Revenue | $35.1B | $37.5B ± 2% | FY26 达 $160B+ | （附原文+翻译） |
| 毛利率 | 75.0% | 75.5% | — | （附原文+翻译） |
| 资本开支 | — | — | CY26 $X00B | （附原文+翻译） |

展望部分如果管理层提到**上调 / 下调 / 维持**（raise / lower / reiterate）指引，一定要明确标出。

---

## 当季盈利驱动因素 (Drivers of Profitability)

解释"为什么这个季度是这个成绩"。管理层通常会给出 2–4 个原因，全部列出，每条附原文。

格式：
1. **[驱动因素 1 标题]**：一句话概括 + 具体数据
   > "原文..." 翻译...

2. **[驱动因素 2 标题]**：...

---

## 分产品 / 分业务线进展 (Product Breakdown) —— 核心

MUST break down by major product categorie (比如Lumentum可能分 EML / OCS / CPO).
- If company does NOT clearly break down: 标注"公司未明确按产品拆分"
- 如果某一个分类公司**没有单独披露数据或评论**，也要列出来并注明「本次会议未单独说明」。

### 归属层级规则 (Scope Attribution Rule) —— 极其重要

**这是本 skill 最容易出错、也最影响投资判断的地方。**

电话会议里管理层的每一句话，按"针对的范围"分**两种归属层级**：

| 层级 | 含义 | 该放在哪里 |
|---|---|---|
| **全公司层面** (whole-company) | 针对整家公司、所有产品线、总 Backlog、总产能、整体供给、跨多产品的应用场景叙事等 | **放在"分产品板块"的最上方**，新建一个 `### 整体 Demand / Order Book / Capacity 总览` 子板块。也可同步归入 TL;DR / Other → Capacity 等顶层板块 |
| **单一产品层面** (product-level) | 明确只针对某一条产品线（如 "EML 营收 +80%"、"RLS shipments 连续两季创纪录"） | 放在对应的 `### Product X` 板块下 |

**核心原则**：**整体 > 产品**。**如果是针对整体产品 / 整体业务的，放在细分的上面（更高一层）；只有真正提到细分业务相关的东西，才放到细分的里面。**

#### 判断每一句话归属的三步法

1. **先看主语 (subject)**：管理层说的是"我们" (we / the company) ？还是具体产品名 (RLS / EML / Waveserver)？
2. **再看证据 (evidence)**：原文里有没有点名某个产品？如果只说 "demand"、"backlog"、"orders"、"capacity" 这种**通用名词**，几乎都是全公司层面。
3. **多产品联供的 trap**：如果原文里同时提到 "RLS **as well as** 800G ZR pluggable"、"Waveserver **and** modems"——**这也是全公司层面**（因为不是某一条单一产品），归到"整体总览"。**不要因为它在讲 RLS 就全塞进 RLS 板块**。可以在 RLS 板块用一句指针标注"详见整体总览中的 scale-across 应用"。

#### 三种典型错误（务必避免）

**错误 1：把"全公司 Backlog / 供给"塞进单一产品板块**
- 反例：CFO 说 "we expect demand will continue to outstrip supply at least for the next several quarters" → 这是全公司供给紧张
- 反例：CFO 说 "nearly all new orders we are taking now will be for fulfillment in fiscal 2027" → 这是全公司 Backlog 可见度
- 正解：放在"整体 Demand / Order Book / Capacity 总览"子板块下。**不**重复塞进 RLS / EML / Waveserver 任何单一产品板块

**错误 2：把"多产品联供的应用故事"塞进单一产品板块**
- 反例：CEO 说 "three hyperscalers ramping for scale-across, **with our RLS platform as well as 800G ZR pluggable**" → 由两条产品线共同供应，不是单一产品故事
- 正解：放在"整体总览"板块里——在总览的 Demand / Customers 段落记录"三家 hyperscaler 在 scale-across 应用上 ramp（由 RLS + 800G ZR pluggable 联合供应）"。RLS 和 ZR pluggable 单产品板块可分别用一句指针标注"详见整体总览中 scale-across 客户进度"

**错误 3：把"指引上调"塞进单一产品板块**
- 反例：CFO 说 "we are raising FY26 revenue guidance to $5.9-6.3B" → 这是整体指引
- 正解：放在"业绩展望 (Guidance)"板块。**不**重复写到产品板块下

#### 正确的板块顺序示意

```
## 分产品 / 分业务线进展

### 整体 Demand / Order Book / Capacity 总览（全公司层面）
  ← 这里放：总 Backlog、整体供需关系、整体产能、整体客户口径、跨多产品的应用场景叙事
  ← 例如：
    - "Backlog QoQ +$2B 至 $7B"、"新订单几乎全部 FY27 交付"、"未来几个季度需求继续超过供给"
    - "三家 hyperscaler 在 scale-across 应用 ramp（由 RLS + 800G ZR pluggable 联合供应）"

### Product A（如 RLS）
  ← 只放真正点名 RLS 的内容：RLS shipments YoY +80%、连续两季创纪录、Hyper-rail 路线图
  ← 如有跨产品联供的应用故事，用一句指针："scale-across 客户进度详见整体总览"

### Product B（如 Waveserver）
  ← 只放真正点名 Waveserver 的内容

### Product C（如 800G ZR Pluggable）
  ← 只放真正点名 pluggable 的内容
```

#### 兜底规则

- 拿不准是全公司还是产品级 → **默认归到上一级（全公司总览）**，因为这样不会误导用户高估单一产品的可见度
- 跨多产品的应用故事（如 scale-across）→ 归到"整体总览"，在叙述时**显式标注"由哪些产品联合供应"**（例：scale-across 由 RLS + 800G ZR pluggable 联合供应），避免读者误以为是单一产品故事
- 总览段落按 H3（`### 整体 Demand / Order Book / Capacity 总览`）排列，与单产品板块**并列**

### 嵌套规则（重要）

**每个产品作为 H3（`### Product X`），季度作为 H4（`#### {季度}`），Demand / Order / Customers 作为 H5（`##### …`）**。**整体总览段落同样使用 H3，与单产品板块并列；其内部也用 H4 区分季度**。

跨季度时：本季内容追加在**该产品 / 该总览段落**的最后一个季度子标题之后，让同一产品 / 总览的多季度内容连续展示。

### 详略分级规则

与**光通信 / AI / 数据中心**相关的产品或业务线，尽可能详细地展开（但不要过分）。其余产品尽可能省略，只保留核心数据和关键变化即可。

IF 用户提供了 **光通信 / optical** 等相关关键词，要在分产品的时候先从会议原文中分析这个产品是否和光通信相关，如果是，提示用户"这个产品是光通信相关"，并且要更加细节一些。

---

### 整体 Demand / Order Book / Capacity 总览（全公司层面）

#### {季度A}

放本季所有**全公司层面**的信号，按以下结构：

- **整体 Demand 措辞**：管理层对整体需求环境的定性表述
- **总 Backlog / RPO / 合同负债**：整体规模、QoQ/YoY 变化、可见度（延伸到哪个财年）
- **整体供给 / 产能口径**：全公司层面的供给紧张程度、CapEx 节奏、扩产路径
- **整体客户口径（如有）**：10%+ 客户数量、cloud 占比、地域口径

格式与产品板块的 Demand / Order / Customers 保持一致——每条结论紧跟原文 + 翻译。

---

### Product A / Category A (比如 EML)

#### {季度A}

- **当季营收及增速**（环比 / 同比）
- **该产品的业绩展望/贡献**
- **公司产品的相关进展**

---

##### Demand / Industry Dynamics

**格式要求：每一条结论都必须紧跟原文+翻译，不允许先列一堆要点再统一贴原文。** 这样做的原因是，投资者需要快速核实每个判断的依据——如果原文和结论分离，核查成本会大幅上升。格式与"当季盈利驱动因素"一致：

1. **[要点标题]**：一句话概括 + 具体数据
   > "原文..." 翻译...

2. **[要点标题]**：...
   > "原文..." 翻译...

按以下维度逐条展开（每条附原文，没有相关内容的维度跳过）:

- **产业需求 Demand strength**：是否提到产品需求火爆 / 产业整体供不应求。写清楚**是哪类产品/哪个子领域**的需求强劲，以及管理层用了什么程度的措辞
- **产品差异化与价值主张**：管理层是否解释了产品**为什么**受欢迎——比如性能优势、成本优势、空间节省、功耗降低、相对竞争对手的优势等。这些细节对投资判断至关重要，因为它们决定了需求的可持续性和定价权，**必须展开描述而非一句话概括**
- **细分数据**：如果管理层披露了不同子类别/渠道/客户群的增速差异（例如企业 vs 运营商、超大规模 vs 一般企业），逐一列出并附原文
- **产业进度/变化 Industry Dynamics**：是否提到加速渗透 / 技术路线变化 / 新的应用场景出现 / 产业结构性转变等
- **竞争格局变化**：如果管理层提到了相对竞争对手的份额变化或差异化优势，记录原文

**注意**：只放**真正点名该产品**的内容。如果管理层只说"整体 demand 强劲"没点名产品，这条应该归入**整体总览板块**，不要重复塞到这里。

Summarize:

- 从这个产品的细分产业来看，产业进度是否准备/正在爆发

---

##### Order Book / Backlog

Identify signals(**一旦出现务必原文保留**):

关键词(包括但不限于):

- **"供不应求" / demand exceeds supply / demand outpacing supply**
- **"爆单" / sold out / overwhelming demand**
- **"需求能见度" / demand visibility of X years/quarters**
- **"锁定未来 X 季度(年)订单 / booked / locked for X quarters**
- **"产能不足" / capacity constrained / supply-constrained**

关键内容(以及其他你认为非常重要的内容):

- **backlog 规模及同比变化**
- **RPO（Remaining Performance Obligations）**、**未交付合约金额**

**注意**：这里只放**针对该产品 / 该产品线的订单和 backlog 信号**。整体公司 backlog 应该归入**整体总览板块**。如果公司只披露总 backlog 不拆分产品级，这里写"本产品 backlog 未单独披露，参见整体总览"。

格式：

| 指标 | 数值 | 同比/环比变化 | 原文 |
|---|---|---|---|
| Backlog | $XXB | +XX% YoY | （附原文+翻译） |
| 已锁定订单时长 | 未来 X 个季度 | — | （附原文+翻译） |
| 关键表述 | "demand significantly exceeds supply" | — | （附原文+翻译） |

Summarize:

- 是否供不应求
- 订单可见度

---

##### Customers

Focus on **客户侧的节奏** :

- **送样 / sampling**
- **通过验证 / qualified / certified**
- **小批量生产 / pilot production**
- **量产爬坡 / ramp**
- **放量出货 / volume shipment**
- **独家供应 / sole source**

- **新客户 / new customers / hyperscalers**
如果管理层提到"**新增 X 家客户**"但没点名，也要列出

**注意**：只放**明确针对该产品的客户进度**。如果客户故事是"在某个应用场景下采购了多个产品"（例如 scale-across 三家 hyperscaler 同时买 RLS + ZR），归入**整体总览板块**（并在叙述中注明"由 RLS + ZR pluggable 联合供应"），不要重复塞到单产品下；可在单产品板块用一句指针："scale-across 客户进度详见整体总览"。

格式：

- **[客户名]**：当前处于 [节点]。原文：
  > "..." 翻译...
- **[客户名]**：...

---

#### {季度B}（跨季度时本季追加在此处，含 vs 上季标注）

（与 {季度A} 同样的子结构：当季营收 / 进展 → ##### Demand / ##### Order Book / ##### Customers）

---

(Repeat for each product: Product B, Product C, ...)

---

### Product Summary Table (TABLE)

这是**整份笔记里最有价值的一张表**。把所有产品 × 所有进度节点汇总成一个二维视图，方便判断未来 2–4 个季度哪些收入会兑现。

| 产品 | 当前节点 | 预计放量时间 | 预计贡献体量(如有) |
|---|---|---|---|
| Product A | 量产 ramp | 已在 Q3 贡献收入 | - |
| Product B | 送样 | H2 FY26 | - |
| Product C | 研发中 | FY27 | - |

如果某一格信息缺失就填 `—`。**宁可留空，不要臆测**。

**跨季度模式下：旧表保留不动，本季新表追加在旧表正下方，用季度子标题区分。** 详见 [跨季度对比模式](#跨季度对比模式)。

---

### Other (没有就不用加这一块了)

每个季度都先写 `### {季度}`，下面再放 H4 的 Capacity / Pricing / 自由发挥。

#### Capacity

If mentioned:

- **当前产能&利用率 / capacity&utilization**
- **扩产计划**：新建厂房、设备采购、CapEx 规模、投产时间
- **代工 / foundry 合作方**：TSMC / Samsung / SMIC 等，先进制程分配情况
- **缓解时间表**(最重要)：管理层预计什么时候供需平衡

> 注意：这里的 Capacity 是**全公司层面**的产能 / CapEx / 扩产路径。**与"整体 Demand / Order Book / Capacity 总览"板块互补**——总览板块侧重"现状口径与本季信号"，Other → Capacity 侧重"扩产计划与时间表"。如果两边内容重叠，可以在总览板块只放一句指针："详见 Other → Capacity"。

---

#### Pricing

If mentioned:

- **涨价**
- **价格预期**

---

#### 自由发挥

你认为这篇电话会议中重点但不在上面范围内的点，概括1-2句话即可

---

## 跨季度对比模式
 
仅当 `{TICKER}_Earnings.md` 已存在时进入此模式。
 
### 核心原则
 
1. **旧内容不可修改**。任何已有季度的文字、表格、引用都保留原状。如果发现旧内容有错，也只在本季的对应位置说明，不去改旧内容。
2. **追加位置取决于板块类型**：
   - 大多数板块（TL;DR / Guidance / Drivers / Product Summary Table / Other）：在该板块的最后一季之后追加 `### {本季}` 子标题。
   - 分产品板块：在**对应产品 / 整体总览**下的最后一季之后追加 `#### {本季}` 子标题（H4 级别），让同一产品 / 总览的所有季度连续展示。
3. **只有 4 个板块需要做变化标注**：业绩展望、产品下的 Demand / Industry Dynamics、产品下的 Customers、产品下的 Order Book / Backlog。整体总览板块下的 Backlog / Demand 变化也需要做 vs 上季标注。其他板块（TL;DR、Drivers、Capacity、Pricing、自由发挥）正常追加，不做对比标注。

### 高亮规则
 
变化标注用 **emoji + 加粗** 表达，统一符号（只用下表 6 个，不用其他符号）：
 
| 符号 | 含义 | 用例 |
|---|---|---|
| 🔼 | 进展/上调/利好变化 | 客户从 qualification → ramp |
| 🔽 | 倒退/下调/利空变化 | 指引下调、客户推迟 |
| ➡️ | 维持/无变化 | guidance reiterated |
| 🆕 | 新增条目 | 新客户、新产品线 |
| ⚠️ | 警示/拐点信号 | 从供不应求 → 需求疲软 |
| 📌 | 只是值得对照看，不一定是好坏 | 口径变了、指标改了 |

### 各板块的具体追加规则
 
#### A. 业绩展望
 
把每个指标和上季的指引/实际做对照，在表格里**新增一列"vs 上季"**：
 
| 指标 | 本季实际 | 下季指引 | 全年/长期指引 | vs 上季 | 原文 |
|---|---|---|---|---|---|
| Revenue | $35.1B | $37.5B | FY26 $160B+ | **🔼 全年指引上调（上季 $150B）** | ... |
| 毛利率 | 75.0% | 75.5% | — | **➡️ 维持** | ... |
| 资本开支 | — | — | CY26 $X00B | **🆕 首次披露 CY26 数字** | ... |
 
如果管理层明确说 raise / lower / reiterate，原话务必引出来。
 
#### B. 整体总览 → Backlog / Demand / Capacity

整体总览板块下，本季也需要做 vs 上季对照：

- 总 Backlog 金额：本季 $XXB（上季 $YYB）→ **🔼 +X% QoQ**
- 整体可见度：本季锁定到 FY27（上季锁定到 FY26 H2）→ **🔼 +X 季度**
- 整体供给措辞：本季"显著供不应求"（上季"供不应求"）→ **🔼 紧张程度加剧**

#### C. Product → Demand / Industry Dynamics
 
本季内容追加在**该产品**最后一季之后（`#### {本季}` 下，H4 级别）。在本季的 Summarize 段落里，加一行 **"vs 上季"**：
 
> **vs 上季**：🔼 行业景气度从"稳健"升级为"加速渗透"；管理层首次使用 "structural shift" 一词
 
如果某个产品上季提到、本季完全没提，也要在本季对应位置写一行：
 
> **vs 上季**：⚠️ 本季管理层未提及该产品的产业动态
 
#### D. Product → Customers
 
**逐客户对照**。本季客户列表中，对每一个**上季已经出现过的客户**，在节点描述后用引用块附上变化：
 
- **AWS**：当前处于 **量产 ramp 🔼**
  > 原文："AWS is now ramping into volume production..." AWS 进入量产爬坡
  > **vs 上季**：上季处于 qualification 阶段

如果上季出现过的客户**本季完全没提**，在本产品 Customers 板块末尾加一行：
 
> ⚠️ **未提及客户**：上季提到的 [客户 X] 本季未在 transcript 中出现
 
#### E. Product → Order Book / Backlog
 
在 Summarize 末尾加 vs 上季：
 
- 是否供不应求：本季"显著供不应求"（上季"供不应求"）→ **🔼 紧张程度加剧**
- 订单可见度：本季 4 个季度（上季 3 个季度）→ **🔼 +1 季度**
- Backlog 金额：本季 $XXB（上季 $YYB）→ **🔼 +X% QoQ**

### Product Summary Table 的处理
 
**新表追加在旧表正下方**，季度子标题区分：
 
```
## Product Summary Table
 
### 2025Q3
| 产品 | 当前节点 | 预计放量时间 | 预计贡献体量 |
|---|---|---|---|
| EML | 量产 ramp | Q3 已贡献 | - |
| OCS | 通过验证 | Q1 FY26 小批量 | - |
 
### 2026Q1   ← 本季新表
| 产品 | 当前节点 | 预计放量时间 | 预计贡献体量 |
|---|---|---|---|
| EML | 放量出货 | 已贡献，Q4 加速 | $XXM |
| OCS | 小批量生产 | Q2 FY26 ramp | - |
| CPO | 送样 🆕 | H2 FY26 | - |
```
 
**不要在新表里加 vs 上季列**——表格本身已经并列展示，对比由用户自己做。新条目可以在产品名后加 🆕。后续用户会手动删除旧表。

### 写入流程
 
跨季度模式下，按以下顺序处理，避免出错：
 
1. 读完整份历史文件，识别已有季度（注意：分产品板块下季度标题是 `#### {季度}`，其他板块下是 `### {季度}`）
2. 找到**最近一季**的内容作为对比基准
3. 在内存中起草本季内容，包括所有 vs 上季标注；**先按归属层级规则把每一句话归类到整体总览 / 单产品**
4. **不要用整文件覆盖**。用定点插入或追加的方式：
   - 大多数板块：在板块最后一个季度内容**之后**插入本季 `### {本季}` 子标题块
   - 分产品板块（含整体总览 / 单产品）：在**对应板块**最后一个季度内容**之后**插入本季 `#### {本季}` 子标题块（H4 级别，注意不是 H3）
5. 运行校验脚本，修掉本季所有 FAIL，然后删除备份：
   ```bash
   python scripts/check_earnings_log.py {TICKER}_Earnings.md --before {TICKER}_Earnings.backup.md
   ```
   （首次运行：`python scripts/check_earnings_log.py {TICKER}_Earnings.md`。）LEGACY 是旧季度里的问题——需要时向用户提一次，绝不在原处修改。
6. 再通读一遍本季内容，确认本季所有内容都按归属层级规则正确放置（**没有把全公司信号 / 多产品联供的应用故事塞进单产品板块**）
### 模式判断的边界情况
 
- **transcript 是更早季度的（穿插历史）**：例如已经写了 Q3 的笔记，用户又喂了 Q1 的 transcript。检测到本季比文件中已有任一季度都早 → **不要追加**，先告诉用户："文件里已有 Q3 笔记，你提供的是更早的 Q1，建议确认是否要插入到时间线中间。"等待用户指示。
- **同一季度二次运行**：检测到本季和文件中最新季度相同 → 询问用户："文件里已有 {季度} 的笔记，是要替换、追加为修订版、还是中止？"
- **TICKER 不匹配**：本次 transcript 识别出的 ticker 和文件名 ticker 不一致 → 中止，提示用户检查文件名。

---

## Rules: 

**MOST IMPORTANT: Do NOT hallucinate** - 除非后续追问，否则所有来源必须限制在transcript内，不允许自行查询（Step 0 获取 transcript 本身是唯一允许的联网操作）

1. **克制**：不加入自己没有依据的判断；不说"这对股价是利好"这种话
2. **忠实**：原文翻译要准，不做意译扩写；数字一个都不能错; 比如 "we're cautiously optimistic" 要翻成"我们审慎乐观"，不要翻成"我们非常看好"
3. **语言**: 见「约定」——新建笔记用提问语言，追加时沿用已有文件的语言
4. **归属层级 (Scope attribution)**：严格按"整体 > 产品"两级归类。**全公司层面的内容（含跨多产品联供的应用故事）必须放在分产品板块的最上方（整体总览），绝对不能塞进任何单一产品板块下面**——这会让读者误判某条产品线的可见度。


5. **固定字符串**：标题、季度标签、变化符号一律照抄本文件，不改写。


最后提醒：这是一份**给投资决策用**的笔记，不是给公司做公关用。原文引用是为了可核查，翻译是为了可读，结构化是为了可对比。三者缺一不可。

