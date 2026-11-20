---
type: paper
source_url: https://arxiv.org/abs/2309.06180
source_kind: public_source
evidence_status: anchored
status: distilled
---

# Efficient Memory Management for Large Language Model Serving with PagedAttention

Kwon et al. · SOSP 2023 · [Original / 原文](https://arxiv.org/abs/2309.06180)

论文的缓存管理设计解释了请求如何逐块申请显存。省下的容量允许调度器容纳更多请求，每轮花多久仍由这一轮的工作决定。

The memory-manager design explains how a sequence grows by allocating physical blocks on demand. [PagedAttention](../Concepts/推理系统/PagedAttention.md) reduces wasted capacity. A scheduler using [Continuous Batching](../Concepts/推理系统/Continuous%20Batching.md) can admit another request when blocks and compute allow.
