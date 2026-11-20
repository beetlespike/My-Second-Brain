---
type: concept
aliases: ["显存带宽"]
tags: [case-serving]
status: active
stage: working
---

# Memory Bandwidth

GPU 每秒能从显存读写多少字节，决定了搬运数据的时间下界。小批量解码时，同一批权重可能只用于很少的 token。

A GPU that must read W bytes at sustained bandwidth B needs at least W/B seconds for those reads. Small decode batches often reuse each weight across few tokens. [Continuous Batching](Continuous%20Batching.md) can increase reuse, while the attention step still reads the history of each request from its [KV Cache](KV%20Cache.md).

[【AI架构原理】预训练工程师在干什么——从 Karpathy 加入 Anthropic 说起](../../Articles/The%20Pretraining%20Engineers%20Article.md)
