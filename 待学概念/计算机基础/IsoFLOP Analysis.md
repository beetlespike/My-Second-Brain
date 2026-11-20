---
type: concept
aliases: ["等计算量比较"]
tags: [ai-suggested, case-tokenizers]
status: active
stage: working
学习状态: 待学
---

# IsoFLOP Analysis

在相同训练计算量下改变词表大小，同时记录各自读过的原始文本量与下游表现，才能看见较大词表带来的压缩收益是否抵过计算开销。

Compare configurations at matched estimated [Training FLOPs](../../Concepts/计算机基础/Training%20FLOPs.md). Changing [Vocabulary Size](../../Concepts/计算机基础/Vocabulary%20Size.md) can shorten encoded text and change the output projection cost per token. Choose the number of training positions for each run to meet the compute budget, then compare [Downstream Evaluation](../../Concepts/计算机基础/Downstream%20Evaluation.md) on held-out tasks.

[Scaling Laws with Vocabulary: Larger Models Deserve Larger Vocabularies](../../Papers/Vocabulary%20Scaling.md)

## 知识卡

### 正面

Two runs train on the same number of tokens. One uses a larger dense output projection. What should you measure before calling them compute-matched? / 还需核对哪笔账？

### 简答

Estimate FLOPs per position including the output layer and multiply by scored training positions using the same accounting rules. Adjust the budget until the total FLOPs agree. / 用同一口径计入输出层，按实际训练位置加总；必要时调整训练长度以对齐总量。
