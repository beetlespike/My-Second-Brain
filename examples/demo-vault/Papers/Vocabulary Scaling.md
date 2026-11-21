---
type: paper
source_url: https://arxiv.org/abs/2407.13623
source_kind: public_source
evidence_status: anchored
status: distilled
---

# Scaling Laws with Vocabulary: Larger Models Deserve Larger Vocabularies

Tao et al. · NeurIPS 2024 · [Original / 原文](https://arxiv.org/abs/2407.13623)

词表改变序列长度，也改变与词表有关的参数和计算量。比较不同词表时，训练 token 数相同只能对齐一项预算。

A larger [Vocabulary Size](../Concepts/计算机基础/Vocabulary%20Size.md) can shorten an encoded corpus. It also changes the input and output matrices. The paper varies vocabulary and model size under fixed training compute. Its comparison motivates [Training FLOPs](../Concepts/计算机基础/Training%20FLOPs.md) alongside the token count.
