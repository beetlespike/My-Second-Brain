---
type: article
source_url: https://vllm.ai/blog/2023-06-20-vllm
source_kind: public_source
evidence_status: anchored
status: distilled
---

# vLLM: Easy, Fast, and Cheap LLM Serving with PagedAttention

vLLM authors · [Original / 原文](https://vllm.ai/blog/2023-06-20-vllm)

作者的块表示意图说明了缓存如何随序列增长。多条续写最初可以共用同一段历史，分支需要写入共享块时再复制。

The section *The Secret Sauce: PagedAttention* illustrates a growing sequence with a logical block table. [PagedAttention](../Concepts/推理系统/PagedAttention.md) lets a request use noncontiguous blocks for its [KV Cache](../Concepts/推理系统/KV%20Cache.md). The parallel-sampling illustration shows how separate continuations can read common blocks until one needs to write.
