---
type: concept
aliases: ["输入长度分布"]
tags: [case-serving]
status: active
stage: working
---

# Prompt Length Distribution

同样的平均输入长度，既可能来自长度接近的一批请求，也可能来自大量短提示和少数极长提示。两种负载对调度器的要求不同。

A workload with mostly short prompts and a few very long ones can have the same mean length as a workload of uniform prompts. Long arrivals create large bursts of work during [Prefill and Decode](Prefill%20and%20Decode.md). Their token lengths depend on [Tokenization](../计算机基础/Tokenization.md).

[DistServe: Disaggregating Prefill and Decoding for Goodput-optimized Large Language Model Serving](../../Papers/DistServe.md)
