---
type: moc
status: active
---

# 单次正确率涨了，模型究竟多会了哪些题？ · RLVR and coverage

一轮 GRPO 训练后，单次答对的题变多了，错误回答也变长了。如果给两个模型同样多的尝试机会，它们各自能解出哪些题？训练目标与评测曲线分别提供一半线索。

| Observation | Concepts already in the vault | What to study |
| --- | --- | --- |
| Failed responses get longer. | In [Policy Gradient](../Concepts/强化学习/Policy%20Gradient.md) and [GRPO](../Concepts/强化学习/GRPO.md), a response has an outcome score. [Response Length Normalization](../Concepts/强化学习/Response%20Length%20Normalization.md) changes the coefficient of each token. | [Response-Level Length Bias](../待学概念/强化学习/Response-Level%20Length%20Bias.md) predicts a different weighting for equally unsuccessful responses of different lengths. [Liu et al., §3.1](../Papers/Understanding%20R1-Zero-Like%20Training.md) · [DAPO’s alternative aggregation](../Papers/DAPO.md) |
| Some prompts contribute little signal. | [Group Sampling](../Concepts/强化学习/Group%20Sampling.md) yields several [Verifiable Rewards](../Concepts/强化学习/Verifiable%20Rewards.md) per prompt. Subtract the [Group Baseline](../Concepts/强化学习/Group%20Baseline.md), then apply [Advantage Normalization](../Concepts/强化学习/Advantage%20Normalization.md). | [Question-Level Difficulty Bias](../待学概念/强化学习/Question-Level%20Difficulty%20Bias.md) asks how much weight a rare success gets, and what happens if the entire group fails. [Stanford CS336 lecture and notes](../Videos/CS336%20on%20Policy%20Gradients.md) |
| A gain at k = 1 shrinks as k grows. | Match [Sampling Temperature](../Concepts/强化学习/Sampling%20Temperature.md) and [Generation Budget](../Concepts/强化学习/Generation%20Budget.md). Use [pass@k](../Concepts/模型评测/pass@k.md) for each model and compare the solved sets per question. | [Sampling Efficiency and Coverage](../待学概念/强化学习/Sampling%20Efficiency%20and%20Coverage.md) separates more frequent successes on familiar tasks from newly observed successes on other tasks. [Yue et al., large-k experiments](../Papers/RLVR%20at%20Large%20k.md) |

长度偏差、题目权重和解题覆盖可以分别检验。一次跑分足以打开这三个问题，要归因还需要固定评测条件并查看逐题结果。
