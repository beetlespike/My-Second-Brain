---
type: concept
aliases: ["生成预算"]
tags: [case-rlvr]
status: active
stage: working
---

# Generation Budget

一次评测允许的尝试数、每次输出长度或总生成 token 数。比较两组结果时，要说明约束具体落在哪一项。

An evaluation may limit attempts, maximum new tokens per attempt, or total sampled tokens. At fixed attempts, longer answers use more compute. Record truncations when comparing models with [pass@k](../模型评测/pass@k.md).

[Does Reinforcement Learning Really Incentivize Reasoning Capacity in LLMs Beyond the Base Model?](../../Papers/RLVR%20at%20Large%20k.md)
