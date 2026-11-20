---
type: concept
tags: [case-serving]
aliases:
  - 分块预填充
status: active
stage: working
---

# 分块预填充

一条长提示如果用掉整轮 GPU 时间，正在生成的其他请求要等这一轮结束。分块预填充把还没处理的提示依次拆开，每处理完一部分都可以重新调度。各段沿用原序列的位置，已经算好的 [KV 缓存](KV%20Cache.md)留给下一段。

## 八个新位置怎么分

假设一轮预算是八个新 token 位置。已有 A、B 在解码，各用一个位置。新来的 C 有十个输入 token。调度器可以先给 A、B 各一个位置，再给 C 前六个，下一轮处理 C 余下四个。C 要等最后一个输入位置算完，才能预测自己的第一个输出。[Prefill 与 Decode](Prefill%20and%20Decode.md)

这样做给[连续合批](Continuous%20Batching.md)更多安排工作的机会。C 分到的份额太少时，它自己的首 token 可能要等更久。真实耗时还取决于每个位置需要读多长的上下文，所以最好一起量[首 token 延迟和输出速度](Inference%20Latency%20and%20Throughput.md)。

[Sarathi-Serve 的分块预填充](https://arxiv.org/abs/2403.02310)

## Chunked Prefill

A long prompt can occupy several scheduling iterations. For a 4,096-token prompt, chunks of up to 512 require at least eight turns. Interleaving these chunks with active decodes changes when each stream advances and when the new request reaches [TTFT](TTFT.md).

[Taming Throughput-Latency Tradeoff in LLM Inference with Sarathi-Serve](../../Papers/Sarathi-Serve.md)
