---
type: concept
aliases: ["回答长度偏差"]
tags: [ai-suggested, case-rlvr]
status: active
stage: working
学习状态: 待学
---

# Response-Level Length Bias

当序列级优势相同，按各自长度平均会让长错误回答中每个 token 受到较轻的负向更新。要判断它能否解释观察到的变化，还需要对照实验。

Under [Response Length Normalization](../../Concepts/强化学习/Response%20Length%20Normalization.md), the same sequence-level advantage gives each token a coefficient proportional to 1/length. In the [GRPO](../../Concepts/强化学习/GRPO.md) objective analyzed by Liu et al., an incorrect long response can give each token a smaller negative coefficient than an equally rewarded short one. Inspect failures by length under the same [Generation Budget](../../Concepts/强化学习/Generation%20Budget.md).

[Understanding R1-Zero-Like Training: A Critical Perspective](../../Papers/Understanding%20R1-Zero-Like%20Training.md)

## 知识卡

### 正面

Away from clipping, advantages are −1 for failures of 20 and 100 tokens. What coefficient multiplies each token term? / 每个 token 项的系数各是多少？

### 简答

−1/20 and −1/100 before common factors. The magnitude per token is five times smaller in the longer response. The total gradient also depends on the individual token gradients. / 系数为 −0.05 和 −0.01。整条梯度还取决于各 token 的梯度方向。
