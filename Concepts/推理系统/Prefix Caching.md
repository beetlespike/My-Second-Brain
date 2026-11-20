---
type: concept
aliases:
  - 前缀缓存
status: active
stage: working
---

# 前缀缓存

两个请求如果以相同的 token 序列开头，模型、位置等决定注意力状态的条件也相同，可以复用这段已经算好的 [KV 缓存](KV%20Cache.md)。例如让模型围绕同一份长文回答两个不同问题，可以把文档放在问题前，让共享部分从头对齐。

## 相同六个 token，命中几个？

以只复用完整块的实现为例，每块放四个 token。两个输入分别是 `a b c d e f X` 和 `a b c d e f Y`。它们有六个共同的开头，但只有 `a b c d` 是仍可复用的完整块。第二个请求从 e 开始做剩余的 [prefill](Prefill%20and%20Decode.md)。内存中的块地址由 [PagedAttention](PagedAttention.md) 所用的块表管理。

命中时省的是前缀的输入计算。第二条请求仍要生成自己的答案。测[延迟和吞吐](Inference%20Latency%20and%20Throughput.md)时，可以分别记录冷缓存和热缓存。

[vLLM 自动前缀缓存](https://docs.vllm.ai/en/stable/features/automatic_prefix_caching/)
