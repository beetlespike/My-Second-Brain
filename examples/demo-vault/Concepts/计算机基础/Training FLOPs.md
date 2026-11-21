---
type: concept
aliases: ["训练计算量"]
tags: [case-tokenizers]
status: active
stage: working
---

# Training FLOPs

一次训练实际或估算执行的浮点运算数。比较词表时，应说明计算口径是否包括词表投影。

FLOPs count the arithmetic operations in a run. Training for the same number of token positions may cost a different number of FLOPs after changing [Vocabulary Size](Vocabulary%20Size.md). Report the convention used for the output projection as well as the backbone.

[Scaling Laws with Vocabulary: Larger Models Deserve Larger Vocabularies](../../Papers/Vocabulary%20Scaling.md)
