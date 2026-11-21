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

因果解码有个非常讨巧的性质：因为前面的 token 根本看不见后面才出现的词，只要前缀上下文不动，每一层算过的 Key 和 Value 向量就不会再变。把旧位置的 K、V 留在显存里，下一步就能直接复用。新 token 仍要算自己的 Q、K、V，把新的 K、V 追加进缓存，再用 Q 对它能看到的所有位置做注意力计算。

## 用显存换回来了什么，又欠下了什么

拿 [Prefill 与 Decode](Prefill%20and%20Decode.md) 里常见的三步场景看：输入 a、b、c 算出首输出 d 以后，预测 e 时只需要送入 d 的最新计算，读回 a–c 的缓存并追加写入 d。算力是省下来了，账本却立刻转移到了显存——并发流一多、上下文一拉长，缓存会膨胀到吃光显存；同时在[连续合批](Continuous%20Batching.md)里请求随时进出，还可以用 [PagedAttention](PagedAttention.md) 这类分页机制防止显存碎片，或者如果拆开预填充和解码，还得想办法把整份缓存在卡间送过去。

[Transformers 的缓存计算说明](https://huggingface.co/docs/transformers/v4.56.1/en/cache_explanation)

## KV Cache

Autoregressive layers reuse previously computed key and value tensors because past positions stay fixed under causal masking: each step computes Q, K and V for the new token, appends its K and V to the cache, and uses its query to attend over the prefix including the current position. That trade shifts bottlenecks from redundant compute to HBM footprint and block management ([PagedAttention](PagedAttention.md))—and to link bandwidth whenever decoding moves to another GPU pool.

[6分钟速通大模型KV Cache](../../Videos/KV%20Cache%20in%20Six%20Minutes.md)
