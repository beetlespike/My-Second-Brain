---
type: concept
aliases: ["下游任务评测"]
tags: [case-tokenizers]
status: active
stage: working
---

# Downstream Evaluation

把模型放到同一组实际任务上，固定提示、计分和上下文规则，再逐语言、逐题比较结果。

Evaluate models on the same held-out tasks with matched prompts, scoring and context policies. Compare outcomes per language. [Paired Evaluation](../研究方法/Paired%20Evaluation.md) exposes questions solved by one model and missed by the other even when their mean scores coincide.

[Tokenizer Choice For LLM Training: Negligible or Crucial?](../../Papers/Tokenizer%20Choice.md)
