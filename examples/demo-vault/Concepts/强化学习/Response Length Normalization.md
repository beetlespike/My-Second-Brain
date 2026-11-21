---
type: concept
aliases: ["回答长度归一化"]
tags: [case-rlvr]
status: active
stage: working
---

# Response Length Normalization

先把一条回答内各 token 的贡献相加，再除以该回答长度。若改为整批按 token 平均，不同长度回答的相对权重会变。

In one form of [GRPO](GRPO.md), sum the token contributions within each response and divide by its length before averaging responses. A batch-wide token denominator gives a different relative weight to long and short completions.

[DAPO: An Open-Source LLM Reinforcement Learning System at Scale](../../Papers/DAPO.md)
