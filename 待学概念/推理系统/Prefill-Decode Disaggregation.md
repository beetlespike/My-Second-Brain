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

A handoff moves 2 GB over a 40 GB/s link. It saves 30 ms of waiting. With no overlap, is the transfer paid for? / 拆分省下 30 ms 的等待，搬 2 GB 的 KV，传输能回本吗？

### 简答

The transfer alone takes at least 50 ms. With no overlap the handoff costs at least 20 ms more than it saves. Other workloads, faster links or overlap can change the comparison. / 至少要 50 ms。按题设，传输比省下的等待多花至少 20 ms。
