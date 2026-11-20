---
type: concept
tags: [case-serving]
aliases:
  - KV缓存
  - KV 缓存
status: active
stage: working
---

# KV 缓存

因果 Transformer 的每一层都需要用新位置的查询向量 Q 与此前位置的键向量 K 比较，再对值向量 V 加权。旧位置在因果掩码下看不到后来的 token。模型、位置和上下文保持一致时，可以把每层已经算好的 K、V 保留下来，下一步直接读取。

## 一个三步例子

[Prefill 与 Decode](Prefill%20and%20Decode.md)中的 a、b、c 都算完后，下一轮给 d 计算自己的 Q、K、V。它用 Q 查看 a、b、c、d 四个位置，保存 d 的 K、V，以便预测 e 之后继续用。输入不断增长，缓存也会占更多内存。

[连续合批](Continuous%20Batching.md)允许不同请求在不同轮次完成，缓存却要随各自进度保留。[PagedAttention](PagedAttention.md)把每条请求的缓存分块管理，空出的块可以分给其他请求。

[Transformers 的缓存计算说明](https://huggingface.co/docs/transformers/v4.56.1/en/cache_explanation)

## KV Cache

A decoder keeps attention keys and values for previous positions so each new query can attend to them. [PagedAttention](PagedAttention.md) assigns physical storage as a sequence grows. If the next decoding step runs on a different GPU, those cached bytes must be accessible there.

[6分钟速通大模型KV Cache](../../Videos/KV%20Cache%20in%20Six%20Minutes.md)
