---
type: paper
source_url: https://arxiv.org/abs/2503.14476
source_kind: public_source
evidence_status: anchored
status: distilled
---

# DAPO: An Open-Source LLM Reinforcement Learning System at Scale

Yu et al. · [Original / 原文](https://arxiv.org/abs/2503.14476)

对照论文的 token-level policy gradient loss，按回答先平均和按整批有效 token 平均，给长短回答的权重不同。

The token-level policy-gradient loss aggregates over tokens across sampled responses. Compare its weighting with [Response Length Normalization](../Concepts/强化学习/Response%20Length%20Normalization.md) in GRPO. The denominator changes how long and short responses contribute to the batch.
