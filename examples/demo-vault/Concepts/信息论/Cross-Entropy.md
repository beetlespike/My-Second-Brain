---
type: concept
tags: [case-tokenizers]
aliases:
  - 交叉熵
status: active
stage: working
---

# 交叉熵

假设结果按分布 p 出现，模型却用分布 q 预测它。每次观察到结果 i，就计算模型给它的对数损失 $-\log_2 q_i$。按实际结果的出现概率取平均，得到交叉熵。

## 权重和预测概率分别来自哪里

$$H(p,q)=-\sum_i p_i\log_2 q_i.$$

p 决定哪些结果经常进入平均，q 决定这些结果分别承担多大的损失。两者需要描述相同的事件；p 为正的事件如果被 q 赋予零概率，交叉熵会变为无穷。

沿用[信息熵](Entropy.md)的例子，令 $p=(0.75,0.25)$，而模型预测 $q=(0.5,0.5)$。模型对两个结果都付出 1 bit 的损失，因此：

$$H(p,q)=0.75\times1+0.25\times1=1\ \text{bit}.$$

目标分布自身的熵约为 0.811 bit，二者相差约 0.189 bit。这部分差额就是[KL散度](KL%20Divergence.md)。[交叉熵与熵、相对熵的关系](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.entropy.html)

## 从一个标签到一批数据

单个样本的正确类别为 y 时，可以把目标写成只有第 y 项为 1 的 one-hot 分布。代入公式，损失就是 $-\log_2 q_y$。对多个样本取平均，得到经验交叉熵。这里用的是观察到的标签，有限样本平均会随数据变化。

语言模型在每个位置为实际出现的 token 分配概率，按有效位置计算平均损失，再取对应底数的指数，就得到[困惑度](Perplexity.md)。

用交叉熵比较两个方法时，应使用相同的评测样本和计分条件。怎样保留每道题的差异，见[配对评测](../研究方法/Paired%20Evaluation.md)。如果损失改用自然对数，所有比较须采用同一单位。

阅读路径：[信息与预测](../../MOCs/信息与预测.md)。

## Cross-Entropy

For language modeling, average the negative log probability of the next observed token at the positions being scored. Summing over the sequence gives the total loss for that tokenization. Exponentiating the mean loss in nats gives [Perplexity](Perplexity.md).

[nanochat · evaluate_bpb](../../Articles/Measuring%20Bits%20per%20Byte.md)
