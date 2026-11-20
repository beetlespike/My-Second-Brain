---
type: concept
aliases: ["组相对策略优化"]
tags: [case-rlvr]
status: active
stage: working
---

# GRPO

对同一道题采样多份回答，用同组的奖励估计相对优势，再据此更新策略。不同实现可能采用不同的归一化。

Group Relative Policy Optimization samples several completions per prompt. Each one's reward is compared with a [Group Baseline](Group%20Baseline.md). In the original objective, [Advantage Normalization](Advantage%20Normalization.md) rescales the centered rewards and [Response Length Normalization](Response%20Length%20Normalization.md) averages token contributions within each response.

[Understanding R1-Zero-Like Training: A Critical Perspective](../../Papers/Understanding%20R1-Zero-Like%20Training.md)
