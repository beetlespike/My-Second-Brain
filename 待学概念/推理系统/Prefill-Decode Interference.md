---
type: concept
aliases: ["预填充与解码干扰"]
tags: [ai-suggested, case-serving]
status: active
stage: working
学习状态: 待学
---

# Prefill-Decode Interference

长输入在一轮里占住 GPU，已经开始的回答也得等。把长输入分块后，可以让老请求在相邻两块之间各生成一步。对齐请求到达时间，才能分清排队和批内争用。

A long prefill admitted by [Continuous Batching](../../Concepts/推理系统/Continuous%20Batching.md) can delay the next step of streams already decoding. A request’s average [TPOT](../../Concepts/推理系统/TPOT.md) can hide a single long gap. Compare token arrival times while replaying the same [Prompt Length Distribution](../../Concepts/推理系统/Prompt%20Length%20Distribution.md). [Chunked Prefill](../../Concepts/推理系统/Chunked%20Prefill.md) changes how much prompt work a decode step can encounter in one turn.

[Taming Throughput-Latency Tradeoff in LLM Inference with Sarathi-Serve](../../Papers/Sarathi-Serve.md)

## 知识卡

### 正面

A stream pauses when a new 8k-token prompt is admitted. Which timestamps would help test for interference? / 长输入入批时老回答停了一下，你会对齐哪些时间？

### 简答

Compare the new request’s prefill iterations with token arrivals in streams already decoding. Replay the same arrivals with smaller chunks. Repeatedly shorter gaps at those iterations support interference as an explanation. / 对齐新请求的预填充轮次和老请求逐 token 的到达时间，用同一批到达记录缩小分块后再比一次。
