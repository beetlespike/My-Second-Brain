---
type: concept
aliases: ["组内基线"]
tags: [case-rlvr]
status: active
stage: working
---

# Group Baseline

在同题组内减去平均奖励。若四份回答只有一份得 1 分，减均值后它得 0.75，另外三份各得 −0.25。

Subtract the mean reward among the responses to a prompt. For rewards 1, 0, 0, 0 the centered rewards are 0.75 and three copies of −0.25. [Advantage Normalization](Advantage%20Normalization.md) introduces an additional denominator.

[Stanford CS336 Language Modeling from Scratch | Spring 2025 | Lecture 17: Alignment - RL 2](../../Videos/CS336%20on%20Policy%20Gradients.md)
