---
type: concept
aliases: ["策略梯度"]
tags: [case-rlvr]
status: active
stage: working
---

# Policy Gradient

把采样到的行动或回答的对数概率梯度按奖励或优势加权，以提高期望奖励。

A sampled response contributes its log-probability gradient weighted by a reward or advantage. A suitable baseline can reduce variance. [GRPO](GRPO.md) forms a comparison group from other responses to the same prompt.

[Stanford CS336 Language Modeling from Scratch | Spring 2025 | Lecture 17: Alignment - RL 2](../../Videos/CS336%20on%20Policy%20Gradients.md)
