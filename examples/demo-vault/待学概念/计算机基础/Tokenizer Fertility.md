---
type: concept
aliases: ["分词膨胀率"]
tags: [ai-suggested, case-tokenizers]
status: active
stage: working
学习状态: 待学
---

# Tokenizer Fertility

先约定怎样分词为「词」，再统计每词平均切出几枚模型 token。同一段固定文本可以换分词器，统计单位要保留。

Measure the number of model tokens per word under a stated external word segmentation. Different tokenizers applied to identical text can give a different ratio. Read it alongside the [Language Mixture](../../Concepts/计算机基础/Language%20Mixture.md) and [Training Token Budget](../../Concepts/计算机基础/Training%20Token%20Budget.md) to estimate raw exposure per language.

[Tokenizer Choice For LLM Training: Negligible or Crucial?](../../Papers/Tokenizer%20Choice.md)

## 知识卡

### 正面

One hundred segmented words become 160 or 240 tokens. With 2,400 tokens, how many such words fit at those rates? / 两个分词器各能覆盖多少词？

### 简答

Fertilities are 1.6 and 2.4. At those average rates the budgets cover about 1,500 and 1,000 words. Measure task performance separately. / 约 1,500 和 1,000 词。这个比值描述切分长度，下游效果要另测。
