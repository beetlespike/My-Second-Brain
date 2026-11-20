---
type: concept
aliases: ["词表大小"]
tags: [case-tokenizers]
status: active
stage: working
---

# Vocabulary Size

词表大小是可选 token ID 的数量。扩充 BPE 词表可能缩短同一段文本，也会扩大稠密输出层。

The number of distinct IDs determines the width of a dense output projection. More BPE merges may shorten sequences. Both the projection cost and the number of positions enter an estimate of [Training FLOPs](Training%20FLOPs.md).

[Scaling Laws with Vocabulary: Larger Models Deserve Larger Vocabularies](../../Papers/Vocabulary%20Scaling.md)
