# Cost vs quality, first round (2026-11-23)

**Question.** For each cheaper way of running the skills, how much does it save, and does quality fall by more than the tolerance?

**Short answer.**
- **Free wins: transcript cleaning, the bilingual split and local transcripts.** They cost nothing in quality.
- **Model tier.** Sonnet and Haiku cost about 0.45x and 0.025x as much as Opus per run. Their outputs are still accurate: quotes verbatim, numbers traceable, validators pass. But they are about half as long and keep fewer of the facts. So earnings-call-reader stays on Opus. For earnings-digest, Haiku is a candidate, but the evidence is too thin to switch.
- **Repeated runs.** Two runs already give the same verdict as three; the third run only steadies the number-overlap estimate.

## Summary

| Experiment | Cheaper option | Saving | Quality effect | Verdict |
|---|---|---|---|---|
| Transcript cleaning | `transcript_tool clean` | 2.8%–3.9% of characters on 6 English transcripts | none (only timestamps and repeated speaker lines removed) | always on |
| Bilingual split | `split_bilingual` on a Chinese / English event transcript | 25% of characters, about 54% of estimated tokens | none (the translation is never a source) | always on |
| Transcript source | local file instead of the Yahoo page | page text ~5% longer, plus 4–6 browser calls and paywall risk | none (all 41 Q3 quotes verbatim from the page) | local first (as the skill already says) |
| Input set (FORM) | transcripts only instead of transcripts + earlier log + initial coverage + workbook | ~49k vs ~109k estimated input tokens (0.45x), without the workbook | table numbers 100% → 83%, core terms 58% → 48%, no estimate section | **keep the full input set** |
| Data reuse (valuation) | reuse a financials dashboard instead of pulling 6-Ks | ~18 web calls → ~5 (price, consensus, rates) | not measured | reuse when present (as the skill already says) |
| Model tier, earnings-call-reader | Sonnet / Haiku instead of Opus | cost 0.43x / 0.026x | length 0.53x / 0.58x; Opus's numbers kept 82% / 72% vs 94% between Opus runs | **REJECT** both |
| Model tier, earnings-digest | Sonnet / Haiku instead of Opus | cost 0.46x / 0.025x | Sonnet: one of two runs changed a mark; Haiku: same marks, half the length, half of Opus's numbers | Sonnet **REJECT**, Haiku **PROVISIONAL** |
| Repeated runs (stability test) | 2 runs instead of 3 | 1/3 of the test's cost | same verdict on validity, tags, marks, sections; number-overlap estimate spreads ±10pp | 2 runs for pass / fail, 3 when the overlap figure matters |

## 1. Model tier

Each run was a fresh Claude Code sub-agent given only the skill and the input, in its own folder. The runner reported tokens, tool calls and time. Cost is tokens × the tier's per-token price relative to Opus (Anthropic pricing page, 2026-11-23: Sonnet half of Opus, Haiku 1/40 at prompts up to 100K tokens). It ignores the input / output mix and caching, so read it as an index, not a bill.

**earnings-call-reader** - TSEM FY26 Q2 transcript → new Chinese call log. The four Opus runs are this run plus the three from the [stability test](../../evaluation/reports/2026-11-23_stability-tsem.md) on the same input. Usage was recorded only for the new run.

| config | runs | tokens | cost vs Opus | tool calls | time (s) | length vs Opus | valid | quotes verbatim | numbers traceable | Opus numbers kept |
|---|---|---|---|---|---|---|---|---|---|---|
| Opus | 4 | 115,080 | 1x | 8 | 240 | 1.00x | 100% | 99% | 90% | 94% |
| Sonnet | 2 | 98,440 | 0.43x | 6 | 97 | 0.53x | 100% | 100% | 94% | 82% |
| Haiku | 2 | 118,862 | 0.026x | 12.5 | 128 | 0.58x | 100% | 98% | 95% | 72% |

**earnings-digest** - one Opus call log of FY26 Q2 → Chinese digest. Marks are scored against the Opus run (✅⚠⚠✅✅).

| config | runs | tokens | cost vs Opus | tool calls | time (s) | length vs Opus | valid | numbers traceable | marks match | Opus numbers kept |
|---|---|---|---|---|---|---|---|---|---|---|
| Opus | 1 | 104,975 | 1x | 8 | 131 | 1.00x | 100% | 100% | 100% | — |
| Sonnet | 2 | 97,132 | 0.46x | 7.5 | 57 | 0.77x | 100% | 100% | 90% | 77% |
| Haiku | 2 | 105,945 | 0.025x | 8.5 | 85 | 0.50x | 100% | 100% | 100% | 51% |

What the numbers say:
- **Tokens hardly depend on the model.** Every run used 95–125k tokens, because the fixed context dominates: skill text, the transcript or log, and the validator output. So the cost ratio is close to the price ratio, and a cheaper tier saves almost exactly its price difference.
- **What the cheaper tiers lose is coverage, not accuracy.** Quotes stay verbatim and numbers stay traceable, but Sonnet and Haiku write about half as much. Their logs keep 82% and 72% of the numbers Opus cites; two Opus runs share 94%. Their validators pass because the validators check structure, not completeness.
- **Judgment.** Both Haiku digests gave Opus's five marks. One Sonnet digest marked Customers ⚠️ instead of ✅️, and one Sonnet digest tagged the quarter 超预期 where the others said 符合预期. That is the borderline call; the earlier Opus stability runs on a different log also marked Customers ⚠️.
- **Speed.** Sonnet finished the call log in 40% of Opus's time, Haiku in about half.
- **Behaviour outside the scores.**
  - One Haiku digest quoted an English phrase that is not verbatim in the log.
  - Another Haiku run created an unrelated scheduled task in the user's account; it was deleted.
  - Neither shows in the quality columns, but both count against unattended use of the cheaper tier.

Decisions (`cost.py decide`, same tolerances as `gate.py`):

```
model-tier-reader  sonnet  REJECT       numbers kept 82% vs 94% (-12pp, tolerance -5pp)
model-tier-reader  haiku   REJECT       numbers kept 72% vs 94% (-22pp, tolerance -5pp)
model-tier-digest  sonnet  REJECT       marks 90% vs 100% (-10pp, tolerance 0)
model-tier-digest  haiku   PROVISIONAL  only one Opus run as the baseline
```

Haiku's digest sits at the edge of the length band (0.50x). Turning PROVISIONAL into a decision needs three more Opus digest runs on the same log, and a check that a digest written from a Haiku call log still gives the same marks.

## 2. Repeated runs

`cost.py repeats` re-scores the three Opus stability runs as every pair of two.

| skill | subset | valid | same tag | same marks | sections | number overlap |
|---|---|---|---|---|---|---|
| call log | all three | 100% | — | — | 97% | 89% |
| call log | each pair | 100% | — | — | 96%–100% | 87%–93% |
| digest | all three | 100% | 100% | 100% | — | 78% |
| digest | each pair | 100% | 100% | 100% | — | 73%–82% |

Any two runs reach the same conclusions as three; only the number-overlap estimate moves (±5–10pp). A stability check can use two runs, a third only when the overlap figure itself is reported.

## 3. Inputs

| Input | Characters | Estimated tokens | `clean` saves | `split_bilingual` saves |
|---|---|---|---|---|
| TSEM 2026Q1 / Q2 transcripts | 48,525 / 51,743 | 12,131 / 12,936 | 3.0% / 3.9% | — |
| FORM 2025Q4–2026Q3 transcripts (4) | 197,199 | 49,299 | 2.8%–3.7% | — |
| COHR ECOC 2026 (Chinese / English interleaved) | 50,584 | 20,531 | 0% | 24.6% of characters, 53.5% of tokens (→ 9,538) |
| FORM earlier call log (Chinese) | 104,874 | 47,313 | — | — |
| FORM initial coverage (Chinese) | 22,988 | 11,866 | — | — |

- **Chinese text costs more tokens per character than English.** The estimator counts one token per CJK character and four English characters per token; the mixed Chinese notes come out at ~0.45 tokens per character against 0.25 for English transcripts (~1.8x). This is why the bilingual split saves twice as many tokens as characters, and why the FORM full input set (transcripts plus two Chinese notes) is ~2.2x the transcripts alone in tokens, against 1.6x in characters.
- The earlier estimate in conversation of "4%–5%" for cleaning counted bytes; in characters it is 3%–4%.
- **The FORM ablation is the clearest case where paying more is worth it.** The extra 2.2x input tokens raised table-number recall from 83% to 100% and core-term recall from 48% to 58%, and made the estimate section possible at all. Source: [skill vs human report](../../evaluation/reports/2026-11-22_skill-vs-human.md).

## 4. Local vs web, reuse vs fetch

- **TSEM Q3 transcript.**
  - The Yahoo page text was 55,857 characters against 53,046 for the transcript itself (+5%).
  - Getting it took about 5 browser calls: the index page, a header / paywall check, then reading the text in two parts.
  - A local file takes the skill's find / verify scripts and nothing else.
  - Quality is the same: every quote checked verbatim.
- **TSEM valuation, today, without an existing dashboard.** About 18 web calls built the 10-quarter history: 7 searches and 11 fetches of 6-K releases and data pages. A further ~7 fetched the price, consensus, rates and peers. With a dashboard already in the folder only that second group is needed.

## Limits

- One company, one quarter, two runs per cheaper config; the Opus digest baseline is a single run.
- Token counts are the sub-agent's total and include context re-read on each turn; they compare configurations, not bills.
- The cost index uses list prices and ignores the input / output split and caching.
- Coverage is measured as numbers kept from Opus, which treats Opus as the reference; it says nothing about which numbers matter most.

## Next

1. Three more Opus digest runs, then re-decide Haiku for earnings-digest.
2. A chained test: Haiku call log → Opus digest, to see whether the reader's lost coverage changes any judgment.
3. Repeat the model-tier test on FORM or COHR (held-out company).

---

# 成本与质量，第一轮（2026-11-23）

**问题。** 每一种更便宜的跑法能省多少？质量是否掉出容差？

**简短结论。**
- **免费的收益：transcript 清理、双语拆分、本地 transcript。** 这三项对质量没有影响。
- **模型档位。** Sonnet 和 Haiku 每次运行的成本约为 Opus 的 0.45 倍和 0.025 倍。它们的输出依然准确：引用逐字、数字可溯源、校验通过；但篇幅约一半，保留的事实更少。所以 earnings-call-reader 继续用 Opus。earnings-digest 可以考虑 Haiku，但证据还不够，暂不切换。
- **重复次数。** 跑 2 次已经能得出和 3 次一样的结论；第 3 次只让数字重合度的估计更稳。

## 汇总

| 实验 | 更便宜的做法 | 节省 | 质量影响 | 结论 |
|---|---|---|---|---|
| transcript 清理 | `transcript_tool clean` | 6 份英文 transcript 少 2.8%–3.9% 字符 | 无（只删时间戳和重复的发言人行） | 一律开启 |
| 双语拆分 | 对中英交替的会议稿用 `split_bilingual` | 字符少 25%，估算 token 少约 54% | 无（译文本来就不是信息源） | 一律开启 |
| transcript 来源 | 本地文件，而不是 Yahoo 网页 | 网页正文多约 5%，另加 4–6 次浏览器调用和付费墙风险 | 无（Q3 的 41 条引用全部逐字核对） | 本地优先（skill 本来就这样规定） |
| 输入组合（FORM） | 只给 transcript，而不是 transcript + 旧日志 + 首次研究 + 估值表 | 估算输入 token 约 49k vs 约 109k（0.45 倍，不含估值表） | 表格数字召回 100% → 83%，核心术语 58% → 48%，测算部分做不出来 | **保留完整输入** |
| 数据复用（估值） | 复用已有财务表，而不是现场抓 6-K | 约 18 次网络调用 → 约 5 次（股价、一致预期、利率） | 未测 | 有就复用（skill 本来就这样规定） |
| 模型档位：earnings-call-reader | Sonnet / Haiku 替代 Opus | 成本 0.43 倍 / 0.026 倍 | 篇幅 0.53 倍 / 0.58 倍；保留 Opus 数字 82% / 72%（Opus 之间为 94%） | 两者都 **REJECT** |
| 模型档位：earnings-digest | Sonnet / Haiku 替代 Opus | 成本 0.46 倍 / 0.025 倍 | Sonnet：两次中有一次改了一个标记；Haiku：标记相同，篇幅一半，保留 Opus 数字一半 | Sonnet **REJECT**，Haiku **PROVISIONAL** |
| 重复次数（稳定性测试） | 跑 2 次而不是 3 次 | 测试成本省 1/3 | 校验、tag、标记、章节结论相同；数字重合度估计波动 ±10pp | 判定通过 / 不通过用 2 次；要报告重合度数字时用 3 次 |

## 1. 模型档位

每次运行都是一个新的 Claude Code 子任务，只给 skill 和输入，各自在独立文件夹里运行；token、工具调用和用时由运行方报告。成本 ＝ token × 该档位相对 Opus 的单价（Anthropic 价格页，2026-11-23：Sonnet 为 Opus 的一半，Haiku 在 prompt 不超过 100K token 时为 1/40）。这个算法不区分输入和输出、不考虑缓存，只能当指数看，不是账单。

**earnings-call-reader**：TSEM FY26 Q2 transcript → 新的中文电话会日志。4 次 Opus 运行 ＝ 本次 1 次 + [稳定性测试](../../evaluation/reports/2026-11-23_stability-tsem.md)里同一输入的 3 次；用量只有本次那一次有记录。

| 配置 | 次数 | token | 成本 vs Opus | 工具调用 | 用时（秒） | 篇幅 vs Opus | 校验 | 引用逐字 | 数字可溯源 | 保留 Opus 数字 |
|---|---|---|---|---|---|---|---|---|---|---|
| Opus | 4 | 115,080 | 1 倍 | 8 | 240 | 1.00 倍 | 100% | 99% | 90% | 94% |
| Sonnet | 2 | 98,440 | 0.43 倍 | 6 | 97 | 0.53 倍 | 100% | 100% | 94% | 82% |
| Haiku | 2 | 118,862 | 0.026 倍 | 12.5 | 128 | 0.58 倍 | 100% | 98% | 95% | 72% |

**earnings-digest**：一份 Opus 写的 FY26 Q2 电话会日志 → 中文速读。标记以 Opus 那次（✅⚠⚠✅✅）为基准。

| 配置 | 次数 | token | 成本 vs Opus | 工具调用 | 用时（秒） | 篇幅 vs Opus | 校验 | 数字可溯源 | 标记一致 | 保留 Opus 数字 |
|---|---|---|---|---|---|---|---|---|---|---|
| Opus | 1 | 104,975 | 1 倍 | 8 | 131 | 1.00 倍 | 100% | 100% | 100% | — |
| Sonnet | 2 | 97,132 | 0.46 倍 | 7.5 | 57 | 0.77 倍 | 100% | 100% | 90% | 77% |
| Haiku | 2 | 105,945 | 0.025 倍 | 8.5 | 85 | 0.50 倍 | 100% | 100% | 100% | 51% |

数字说明了什么：
- **token 数几乎不随模型变。** 每次都在 95–125k，因为固定上下文占了大头：skill 正文、transcript 或日志、校验输出。所以成本比约等于单价比，换便宜一档省下的基本就是单价差。
- **便宜的档位丢的是覆盖，不是准确性。** 引用依然逐字、数字依然可溯源，但 Sonnet 和 Haiku 只写了一半左右。它们的日志分别保留了 Opus 所引数字的 82% 和 72%，而两次 Opus 之间是 94%。校验能通过，是因为校验查的是结构，不是完整度。
- **判断。** Haiku 两次速读的五个标记都和 Opus 一致。Sonnet 有一次把客户维从 ✅️ 打成 ⚠️，还有一次把季度 tag 写成"超预期"，其余都是"符合预期"。这正是那个边界判断——之前稳定性测试中 Opus 在另一份日志上也给客户维打了 ⚠️。
- **速度。** 写电话会日志，Sonnet 用时是 Opus 的 40%，Haiku 约一半。
- **分数之外的行为。**
  - 一次 Haiku 速读引用的英文短语不是日志原文。
  - 另一次 Haiku 运行在用户账户里建了一个无关的定时任务（已删除）。
  - 这两点都不体现在质量列里，但对"无人值守用便宜档位"都是扣分项。

判定（`cost.py decide`，容差与 `gate.py` 相同）：

```
model-tier-reader  sonnet  REJECT       保留 Opus 数字 82% vs 94%（-12pp，容差 -5pp）
model-tier-reader  haiku   REJECT       保留 Opus 数字 72% vs 94%（-22pp，容差 -5pp）
model-tier-digest  sonnet  REJECT       标记一致 90% vs 100%（-10pp，容差 0）
model-tier-digest  haiku   PROVISIONAL  基准只有一次 Opus 运行
```

Haiku 速读的篇幅正好在长度区间的边上（0.50 倍）。要把 PROVISIONAL 变成定论，需要在同一份日志上再跑 3 次 Opus 速读，并检查用 Haiku 写的日志做出来的速读，标记是否不变。

## 2. 重复次数

`cost.py repeats` 把 3 次 Opus 稳定性运行按每两次一组重新打分。

| skill | 组合 | 校验 | tag 一致 | 标记一致 | 章节 | 数字重合 |
|---|---|---|---|---|---|---|
| 电话会日志 | 三次 | 100% | — | — | 97% | 89% |
| 电话会日志 | 任意两次 | 100% | — | — | 96%–100% | 87%–93% |
| 速读 | 三次 | 100% | 100% | 100% | — | 78% |
| 速读 | 任意两次 | 100% | 100% | 100% | — | 73%–82% |

任意两次得出的结论都和三次相同，只有数字重合度的估计会移动（±5–10pp）。稳定性检查跑 2 次即可；只有要报告重合度这个数字本身时，才需要第 3 次。

## 3. 输入

| 输入 | 字符数 | 估算 token | `clean` 节省 | `split_bilingual` 节省 |
|---|---|---|---|---|
| TSEM 2026Q1 / Q2 transcript | 48,525 / 51,743 | 12,131 / 12,936 | 3.0% / 3.9% | — |
| FORM 2025Q4–2026Q3 transcript（4 份） | 197,199 | 49,299 | 2.8%–3.7% | — |
| COHR ECOC 2026（中英交替） | 50,584 | 20,531 | 0% | 字符 24.6%，token 53.5%（→ 9,538） |
| FORM 旧电话会日志（中文） | 104,874 | 47,313 | — | — |
| FORM 首次研究（中文） | 22,988 | 11,866 | — | — |

- **中文每个字符的 token 成本高于英文。** 估算规则是中文 1 字 1 个 token、英文约 4 字符 1 个 token；中英混排的中文笔记约 0.45 token/字符，英文 transcript 约 0.25（约 1.8 倍）。所以双语拆分省下的 token 比例是字符比例的两倍；FORM 完整输入（transcript 加两份中文笔记）按 token 算约是只给 transcript 的 2.2 倍，按字符只有 1.6 倍。
- 之前对话里说清理能省"4%–5%"，那是按字节算的；按字符是 3%–4%。
- **FORM 消融是"多花钱值得"最清楚的例子。** 多出的 2.2 倍输入 token，把表格数字召回从 83% 提到 100%、核心术语召回从 48% 提到 58%，而且没有估值表就根本做不出测算部分。来源：[skill 与手写对比报告](../../evaluation/reports/2026-11-22_skill-vs-human.md)。

## 4. 本地 vs 网页，复用 vs 现场抓

- **TSEM Q3 transcript。**
  - Yahoo 网页正文 55,857 字符，transcript 本身 53,046 字符（多约 5%）。
  - 拿到它用了约 5 次浏览器调用：打开索引页、检查标题和付费墙、分两段读正文。
  - 本地文件只需要 skill 自带的 find / verify 两个脚本。
  - 质量相同：每条引用都逐字核对过。
- **今天的 TSEM 估值（没有现成财务表）。** 建 10 季历史用了约 18 次网络调用：7 次搜索、11 次读取 6-K 新闻稿和数据页；另外约 7 次取股价、一致预期、利率和可比公司。文件夹里已有财务表的话，只需要后面这一组。

## 局限

- 一家公司、一个季度，每个便宜配置只跑 2 次；速读的 Opus 基准只有 1 次。
- token 是子任务的总量，包含每一轮重复读入的上下文；用于比较配置，不是账单。
- 成本指数用的是标价，没有区分输入 / 输出，也没考虑缓存。
- 覆盖度以"保留了多少 Opus 引用的数字"来衡量，相当于把 Opus 当基准；它说明不了哪些数字更重要。

## 下一步

1. 再跑 3 次 Opus 速读，然后重新判定 earnings-digest 能否用 Haiku。
2. 串联测试：Haiku 写日志 → Opus 写速读，看日志丢掉的覆盖会不会改变判断。
3. 在 FORM 或 COHR（held-out 公司）上重复模型档位测试。
