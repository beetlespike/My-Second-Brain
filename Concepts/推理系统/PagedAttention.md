---
type: concept
aliases:
  - 分页注意力
tags: [case-serving]
status: active
stage: working
---

# PagedAttention

一个请求的 [KV 缓存](KV%20Cache.md)随序列变长而增长。PagedAttention 将序列按固定大小分块，用块表记录每个逻辑块实际存在哪个物理块。这样不必给每条请求预留一整段连续缓存。

## 找到位置 5 的键和值

假设每块放四个位置，位置从 0 起算。块表为 `[7, 2]` 时，逻辑位置 5 除以 4，商为 1，余数为 1。读取物理块 2 的第 1 号槽即可。分块改变的是存储地址，位置 5 在序列中的含义不变。

当某条请求结束，它独占的物理块可以回收。[连续合批](Continuous%20Batching.md)正好在这一时点有机会让新请求进入。

[PagedAttention 论文](https://arxiv.org/abs/2309.06180)

## PagedAttention

The block table maps a sequence’s logical positions to physical blocks of [KV Cache](KV%20Cache.md). Requests can grow without reserving their maximum length up front. [Continuous Batching](Continuous%20Batching.md) can put newly freed capacity to use when scheduling its next iteration.

[Efficient Memory Management for Large Language Model Serving with PagedAttention](../../Papers/PagedAttention%20paper.md)
