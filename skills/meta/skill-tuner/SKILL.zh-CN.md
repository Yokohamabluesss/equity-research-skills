---
name: skill-tuner
description: "根据分析类或总结类 skill 与分析师手写结果的对比来改进 skill，相当于带留出检验的监督训练循环：运行评估，把每处差异归类（缺输入 / 格式 / 判断 / 覆盖 / 长度 / skill 独有），只对至少两家公司都出现的模式提出规则修改，按用户批准的改动修改规则，作为新实验重跑，只有留出结果不变差时才采纳。用户说「根据对比结果升级 skill」「调一下规则」「校准 skill」「tune the skill from the comparison」「what should change in the rules」时使用。不会自行修改判断规则（维度标记），也不以字面重叠为优化目标。"
---

# skill-tuner

把对比结果变成 skill 的规则修改，每一处修改都要用户批准。手写结果是标签，skill 的 `SKILL.md` 是模型，修改规则是训练，留出的公司或季度决定改动是否保留。方法说明见仓库的 `evaluation/TUNING.md`。

## 约定（固定）

- **在仓库和私人工作区上工作**：`equity-research-skills/`（规则、脚本、清单、报告）和 `workspace/`（手写参照、输入、运行结果）。缺任何一个都先问用户，不要少给输入继续做。
- **一次实验 = 一份报告。** 改规则后的每次重跑都是 `evaluation/manifest.json` 里的新实验 id 和新报告 `evaluation/reports/{id}.md`；以前的报告不改写。
- **运行 id 在整个清单内唯一。** 每次运行有 `split`：`train`（可作为证据）或 `heldout`（只用来评判）。
- **提案写成文件**：`workspace/runs/{skill}/proposals/{YYYY-MM-DD}_{简称}.md`，语言跟随提问语言。
- 脚本（在 `scripts/` 里，由 `tools/build.py` 从仓库的 `evaluation/` 同步）：
  - `run_eval.py`：把一次实验的每次运行与手写参照对比
  - `diagnose.py`：把差异分成六类，并找出跨公司的模式
  - `gate.py`：根据基线实验和候选实验决定采纳或拒绝，只看留出运行
  - `compare_view.py`：对比本身（investment-view 格式）

## 步骤

### 1. 评估和诊断

```bash
python evaluation/run_eval.py --experiment 基线ID --root ../workspace --out ../workspace/runs/{skill}/eval
python evaluation/diagnose.py --experiment 基线ID --eval-dir ../workspace/runs/{skill}/eval/基线ID
```

诊断结果和逐次运行文件放在一起。然后**读证据**：每个标为"规则候选"的模式，都要打开对应的逐次 `.md` 文件，读遗漏行和 skill 独有行。模式只是候选，不是结论；先确认这处差异是不是现有规则有意造成的（例如主线以外的产品行本来就按规则删掉）。

### 2. 按类别分流

| 类别 | 谁处理 | 怎么做 |
|---|---|---|
| 缺输入 | 用户 | 列出缺的输入；绝不写规则去弥补 |
| 格式 | 脚本 | 修校验脚本或模板；这不算改规则 |
| 判断（标记） | **用户** | 把两种读法和证据并列，问用户；绝不自行修改标记规则 |
| 覆盖 / 长度，2 家以上 | 本 skill | 先判断改哪个 skill（第 3 步），再提出规则修改（第 4 步） |
| 覆盖 / 长度，只有 1 家 | 暂不处理 | 记在提案文件的"观察"下；不改规则 |
| skill 独有 | 用户 | 列为"可能的收获"；分析师漏掉的正确风险提示不是错误 |

### 3. 判断改哪个 skill 的规则

investment-view 有两部分是按其他 skill 的规则写的，所以差距出在哪一部分，就决定改哪里：

| investment-view 的部分 | 规则所在 | 改哪里 |
|---|---|---|
| 季度块的五维和"其他" | earnings-digest | earnings-digest |
| 测算 | valuation-brief（估值表本身就缺的则是 company-valuation） | 对应 skill |
| 核心、超预期点、总判断行、产品表和产能表、会议记录、长度、版式 | investment-view | investment-view |

改 earnings-digest 或 valuation-brief 也会改变它们单独使用时的输出，所以提案要列出涉及的每个 skill，它们的校验脚本必须仍然通过，框架保持不变。

### 4. 写提案

每条规则修改按以下顺序写：

```
## {n}. {一句话名称}
类别 / 模式：coverage core/text/terms（train：COHR、FORM）
涉及的 skill：{例如 earnings-digest（差距源头）、investment-view}
证据：{运行 id，以及遗漏的是哪类内容，用转述；不复制手写原文}
现有规则：{引用 SKILL.md 原文}
建议规则：{新文字，即在 SKILL.md 和 SKILL.zh-CN.md 中的写法}
预期效果：{哪个指标、在哪些运行上应该变化}
风险：{什么可能变差；哪次留出运行能看出来}
```

**防过拟合规则**（违反任何一条的提案作废）：
1. 证据来自 `train` 运行中至少两家公司；留出运行永远不作证据。
2. 规则描述方法，不描述内容：不写参照里的公司名、产品名、数字或事实，也不照抄分析师笔记的措辞（写"供给受限时产能里程碑保持表格"，而不是"要提 InP 翻倍"）。
3. 不做唯一目的是提高逐行覆盖率或术语召回率的修改。它们会低估同义改写；以它们为目标，会教 skill 越写越长、照抄措辞。
4. 用能解释模式的最小改动；一个模式一处改动。

### 5. 请求批准

用 AskUserQuestion（多选）展示提案；没有提问工具时用文字。只把批准的改动同时写进 `SKILL.md` 和 `SKILL.zh-CN.md`，然后运行：

```bash
python tools/build.py && python tools/selftest.py
```

### 6. 作为新实验重跑

在清单里新增一个实验（新 id，`"status": "open"`，每次运行写新的 skill 版本），公司和输入与基线相同，另加至少一次 `heldout` 运行：没有任何规则针对它调过的公司或季度，在新会话中写，写之前不读它的手写参照。用更新后的 skill 重新生成输出，然后：

```bash
python evaluation/run_eval.py --experiment 候选ID --root ../workspace --out ../workspace/runs/{skill}/eval
python evaluation/gate.py --baseline .../基线ID/summary.json --candidate .../候选ID/summary.json
```

### 7. 决定并记录

- **ACCEPT（采纳）**：把结论写进新报告，在 CHANGELOG 加一条（版本、规则改动、gate 结果），把基线实验标为 `"status": "closed"`。
- **REJECT（拒绝）**：撤回规则改动，保留报告（失败的改动也是结果），在提案文件里写明原因。
- **PROVISIONAL（暂定，没有留出配对）**：改动在 CHANGELOG 里标为暂定，并告诉用户还需要哪次留出运行。

## 原则

- **用户直接要求的修改**随时可以做：按用户的要求改，不受"两家公司"规则限制。但除非用户明确要改框架，否则框架不变；要跑 build 和自测，在 CHANGELOG 里记为用户要求的修改，并建议重跑最近一次实验来衡量效果。
- 目标由分析师掌握。判断规则、不给买卖建议、不判断贵或便宜这三条永远不调。
- **调哪些 skill**：investment-view（修改可能落在 earnings-digest 或 valuation-brief，因为它承接两者的输出）；company-valuation 和 stock-discovery **只做补充**：把分析师有、skill 漏掉的关键输出、方法或公司加进检查清单，绝不改它们的框架（工作表、列、章节顺序、标签、校验脚本）。earnings-call-reader 和 quarterly-financials-dashboard 不调。
- 只在训练运行上变好、没有留出检验的，还不算改进。
- 采纳指标是：标记一致率、数字召回率（季度正文、表格、测算）、核心长度在手写版的 0.5–1.5 倍之内。逐行覆盖率和术语召回率只报告，不用来采纳。
- 公开报告只放汇总指标和转述的结论；逐次文件和提案留在工作区。
