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

## 同一提示的两条续写

第 4.4 节讨论并行采样。两条序列的块表最初可以指向同一份提示词缓存。追加时若尾块仍被另一条序列引用，vLLM 给写入的一方另分一块，复制旧内容并更新块表。已经写满的前缀块仍可共用。[论文正文 §4.4](https://arxiv.org/html/2309.06180) · [用六个提示词位置走一遍](../Concepts/推理系统/PagedAttention.md#sharing-a-partial-block)

Section 4.4 describes block-level copy-on-write. Two continuations can read the same prompt cache. Appending to a shared, partially filled block gives the writer a private copy while earlier full blocks remain shared.
