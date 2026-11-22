---
type: concept
aliases: ["预填充与解码分离"]
tags: [ai-suggested, case-serving]
status: active
stage: working
学习状态: 待学
---

# Prefill-Decode Disaggregation

预填充吃算力、延迟容易打断别人，解码吃显存带宽、怕排队；硬塞在一张卡或同一个 GPU 池里就互相掐架。把两步拆到各自独立扩缩容的 GPU 池后，批内抢占是消掉了，但也多出来一笔硬开销：提示词算出的 KV 缓存要交给解码池。两组 GPU 在同一台机器时可以走机内互连，分在不同机器时才需要跨机。传输延迟和接收端可能新堆起来的队列，合起来决定这场分家划不划算。

Separating [Prefill and Decode](../../Concepts/推理系统/Prefill%20and%20Decode.md) onto separate GPU pools removes [Prefill-Decode Interference](Prefill-Decode%20Interference.md) and lets each pool scale its own bottleneck. The bill shifts to [KV Cache](../../Concepts/推理系统/KV%20Cache.md) shipping: every request must send its prompt cache across [Interconnect Bandwidth](../../Concepts/推理系统/Interconnect%20Bandwidth.md) before decoding starts, so net gain depends on saved stalls minus transfer time and handoff queuing.

[DistServe: Disaggregating Prefill and Decoding for Goodput-optimized Large Language Model Serving](../../Papers/DistServe.md)

## 知识卡

### 正面

拆池本来能帮一条请求省下 30 ms 的等待，但要把 2 GB KV 缓存搬过去。如果卡间有效链路只有 40 GB/s（不考虑传输重叠与其他开销），这笔分家账划算吗？链路翻倍到 80 GB/s 呢？

Splitting prefill and decode saves 30 ms of queuing, while moving 2 GB of KV cache to the decode pool. Ignoring overlap and extra overhead, does the split pay off on a 40 GB/s link—or on an 80 GB/s link?

### 简答

按有效带宽直算：40 GB/s 链路光传输就要花 `2 GB / (40 GB/s) = 0.05 s = 50 ms`，比省下的 30 ms 还倒亏 20 ms；换到 80 GB/s 后传输降到 25 ms，扣除才开始净省 5 ms。

At 40 GB/s, shipping 2 GB takes `2 GB / (40 GB/s) = 0.05 s = 50 ms`—20 ms slower than staying put, since only 30 ms was saved. At 80 GB/s, transfer drops to 25 ms, flipping the split into a net 5 ms win under those same assumptions.

### 相关概念

- Prefill & Decode（预填充与解码）：Prefill processes the prompt and builds its KV cache. Each decode step reuses the cache to predict the next token.｜预填充处理提示词并建立 KV 缓存。解码时，每一步都复用缓存来预测下一个 token。
- KV Cache（KV 缓存）：Each attention layer keeps keys and values for earlier tokens so later steps can reuse them.｜每层注意力都会保存已处理 token 的键和值，供后续步骤直接使用。
- Interconnect Bandwidth（卡间互连带宽）：The rate at which the link between GPU pools can carry data. Transfer time equals cache size divided by effective bandwidth.｜两组 GPU 之间的链路每秒实际能传多少数据。缓存大小除以有效带宽，就是传输时间。
