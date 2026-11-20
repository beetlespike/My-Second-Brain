---
type: paper
source_url: https://arxiv.org/abs/2504.13837
source_kind: public_source
evidence_status: anchored
status: distilled
---

# Does Reinforcement Learning Really Incentivize Reasoning Capacity in LLMs Beyond the Base Model?

Yue et al. · [Original / 原文](https://arxiv.org/abs/2504.13837)

论文在给定模型、题集和采样条件下比较大小 k，检查哪些题至少有一次正确答案。曲线描述的是这些设置下实际采到的解。

Across the model and benchmark pairs studied, the curve for [pass@k](../Concepts/模型评测/pass@k.md) can favor a different model as k grows. Reproducing that comparison requires a common [Generation Budget](../Concepts/强化学习/Generation%20Budget.md) and [Sampling Temperature](../Concepts/强化学习/Sampling%20Temperature.md). A finite sample only covers solutions observed under those settings.
