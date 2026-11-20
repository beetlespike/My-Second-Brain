---
type: concept
aliases: ["预填充与解码分离"]
tags: [ai-suggested, case-serving]
status: active
stage: working
学习状态: 待学
---

# Prefill-Decode Disaggregation

将两个阶段交给不同 GPU 池，排队和配卡可以分别调整。解码池要接到提示词对应的 KV 才能继续，传输和两边的排队时间一起决定拆分是否合算。

Place the two stages of [Prefill and Decode](../../Concepts/推理系统/Prefill%20and%20Decode.md) on different GPU groups. Each pool can schedule and scale its own work, removing the shared GPU contention described by [Prefill-Decode Interference](Prefill-Decode%20Interference.md). The receiving worker needs the prompt’s [KV Cache](../../Concepts/推理系统/KV%20Cache.md) before it can continue generation. [Interconnect Bandwidth](../../Concepts/推理系统/Interconnect%20Bandwidth.md) bounds the transfer time, and imbalance between pools can move the queue to the handoff.

[DistServe: Disaggregating Prefill and Decoding for Goodput-optimized Large Language Model Serving](../../Papers/DistServe.md)

## 知识卡

### 正面

A handoff moves 2 GB over a 40 GB/s link and saves 30 ms of waiting. With no overlap or other overhead, does it pay off? What if the link runs at 80 GB/s?

拆分能省 30 ms 的等待。2 GB 的 KV 走 40 GB/s 的链路，传输没有重叠，忽略其他开销。这笔账划算吗？换成 80 GB/s 呢？

### 简答

At 40 GB/s the transfer takes 50 ms, so splitting costs 20 ms more than it saves. At 80 GB/s it takes 25 ms, leaving a net saving of 5 ms. Both estimates use the effective transfer rate and the same 30 ms of waiting saved.

按实际可用带宽计算，40 GB/s 时传输用 50 ms，比省下的等待多 20 ms。换成 80 GB/s，传输只用 25 ms，拆分就能净省 5 ms。两次比较都假定能省下同样的 30 ms 等待。
