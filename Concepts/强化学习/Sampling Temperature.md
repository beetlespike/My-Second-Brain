---
type: concept
aliases: ["采样温度"]
tags: [case-rlvr]
status: active
stage: working
---

# Sampling Temperature

采样前将 logits 除以正温度再取 softmax。温度会改变低概率解被采到的机会。

At positive temperature T, sampling uses logits divided by T before softmax. Changing T changes the chance of seeing a low-probability correct solution in [Group Sampling](Group%20Sampling.md) and in a [pass@k](../模型评测/pass@k.md) evaluation.

[Does Reinforcement Learning Really Incentivize Reasoning Capacity in LLMs Beyond the Base Model?](../../Papers/RLVR%20at%20Large%20k.md)
