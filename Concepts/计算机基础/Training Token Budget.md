---
type: concept
aliases: ["训练 token 预算"]
tags: [case-tokenizers]
status: active
stage: working
---

# Training Token Budget

一次训练允许处理的 token 位置总数。每词切成两枚或四枚 token，即使用完同一笔预算，模型读过的词数也不同。

A budget fixes the number of token positions used in training. At two versus four tokens per segmented word, the same number of positions covers twice as many words in the former case. Measure this separately for each part of the [Language Mixture](Language%20Mixture.md).

[Tokenizer Choice For LLM Training: Negligible or Crucial?](../../Papers/Tokenizer%20Choice.md)
