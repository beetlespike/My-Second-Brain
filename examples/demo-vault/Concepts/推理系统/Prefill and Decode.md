---
type: concept
tags: [case-serving]
aliases:
  - 预填充与解码
  - Prefill与Decode
  - Prefill 与 Decode
status: active
stage: working
---

# Prefill 与 Decode

提示词已经全部给定，模型可以并行计算这些位置的表示，这一段叫 prefill。生成的下一个 token 要看前一个输出，普通自回归解码因此逐步进行。两段之间靠每一层的 [KV 缓存](KV%20Cache.md) 接起来。

## 第一个输出什么时候出现

假设输入是 a、b、c。Prefill 读完三个位置后，用 c 的输出分布选出 d。到这一步，缓存里只有 a、b、c。接着模型把 d 当作新输入，读取旧缓存，写入 d 的键和值，再用 d 的输出分布预测 e。

这个区别会影响服务性能。接入 [RAG](../智能体与检索/RAG.md) 后，同一问题可能多带几段文档，增加了 prefill 要处理的位置。多个请求同时生成时，[连续合批](Continuous%20Batching.md)决定这一轮让哪些请求使用计算资源。

[推理系统](../../MOCs/推理系统.md) · [检索与生成](../../MOCs/检索与生成.md)

[Transformers 的缓存计算说明](https://huggingface.co/docs/transformers/v4.56.1/en/cache_explanation)

## Prefill and Decode

During prefill the model processes the prompt and produces the first output token. Each later decode step extends the sequence using the [KV Cache](KV%20Cache.md). A scheduler can split the prompt with [Chunked Prefill](Chunked%20Prefill.md) to share an iteration with active decodes.

[6分钟速通大模型KV Cache](../../Videos/KV%20Cache%20in%20Six%20Minutes.md)
