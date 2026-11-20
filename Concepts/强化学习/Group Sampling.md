---
type: concept
aliases: ["同题分组采样"]
tags: [case-rlvr]
status: active
stage: working
---

# Group Sampling

同一提示从同一个策略生成多份回答，保留各自的输出与结果，构成题内比较组。

Draw G responses for one prompt from the chosen policy. The resulting rewards supply a [Group Baseline](Group%20Baseline.md). When reusing a prompt in serving, all G continuations initially share a prefix that [Prefix Caching](../推理系统/Prefix%20Caching.md) can make cheaper to process.

[Stanford CS336 Language Modeling from Scratch | Spring 2025 | Lecture 17: Alignment - RL 2](../../Videos/CS336%20on%20Policy%20Gradients.md)
