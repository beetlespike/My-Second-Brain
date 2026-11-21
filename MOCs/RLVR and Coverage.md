---
type: moc
status: active
---

# 单次正确率涨了，模型究竟多会了哪些题？ · RLVR and coverage

跑完一轮 GRPO 训练，经常看到两个现象一起发生：`pass@1` 涨了，做错时的思考过程也跟着变长了。可这到底是模型真正啃下了原本完全不会的新题，还是只是把原本偶发能对的题考稳了？可以从训练目标和逐题的采样结果找线索。

| 现象 | 已学概念 | 接下来值得深挖的缺口 |
| --- | --- | --- |
| 错题回答越来越长 | [Policy Gradient](../Concepts/强化学习/Policy%20Gradient.md)、[GRPO](../Concepts/强化学习/GRPO.md) 里每条采样共享结果打分，但 [Response Length Normalization](../Concepts/强化学习/Response%20Length%20Normalization.md) 直接改了每个 token 的梯度权重 | [Response-Level Length Bias](../待学概念/强化学习/Response-Level%20Length%20Bias.md)：同样拿了负分的两条错答，按 token 均摊还是按整条均摊，会让模型学出截然不同的废话偏好。[Liu et al., §3.1](../Papers/Understanding%20R1-Zero-Like%20Training.md) · [DAPO 写法对比](../Papers/DAPO.md) |
| 难易题梯度权重不对等 | 同题多采（[Group Sampling](../Concepts/强化学习/Group%20Sampling.md)）拿[可验证奖励](../Concepts/强化学习/Verifiable%20Rewards.md)减掉[组内基线](../Concepts/强化学习/Group%20Baseline.md)再做[优势归一化](../Concepts/强化学习/Advantage%20Normalization.md) | [Question-Level Difficulty Bias](../待学概念/强化学习/Question-Level%20Difficulty%20Bias.md)：整组几乎全错但偶发对了一次的题、以及全对/全错的零方差组，分别占了多少更新量？[Stanford CS336 笔记](../Videos/CS336%20on%20Policy%20Gradients.md) |
| 只看 `k = 1` 涨了，放宽采样却赶上 | 对齐[采样温度](../Concepts/强化学习/Sampling%20Temperature.md)和[生成预算](../Concepts/强化学习/Generation%20Budget.md)后再比各家的 [pass@k](../Concepts/模型评测/pass@k.md) 与解出题集合 | [Sampling Efficiency and Coverage](../待学概念/强化学习/Sampling%20Efficiency%20and%20Coverage.md)：分别数一数原本偶尔答对、现在更稳的题，以及只在这一轮采样中见过正确答案的题。[Yue et al. 大 k 实验](../Papers/RLVR%20at%20Large%20k.md) |

固定题集、温度和输出上限，分别列出更常答对的题，以及这次才第一次抽到正确答案的题。前一列能看出哪些题做稳了。后一列值得加大采样预算复查，看看基座是否偶尔也能答对。
