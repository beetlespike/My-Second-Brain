---
type: video
source_url: https://www.bilibili.com/video/BV1jAZwBGEwi/
source_kind: public_source
evidence_status: anchored
status: distilled
---

# 6分钟速通大模型KV Cache

月球大叔 / Bilibili · [Original / 原文](https://www.bilibili.com/video/BV1jAZwBGEwi/)

视频最值钱的是把两段耗时一眼拆开：00:17–01:17 先并行算完提示词、吐出第一个 token，01:52–02:32 讲到解码怎样复用旧位置的 K、V。新位置仍要算出自己的 Q、K、V，写入新的 K、V 后再计算注意力；到 03:49–04:24 账风一转——输入拉长或并发一多，这批缓存本身就把显存吃紧了。

Useful split in six minutes: 00:17–01:17 draws the boundary between parallel prompt processing and step-by-step generation, 01:52–02:32 traces how reusing prior K and V tensors avoids recomputing history, and 03:49–04:24 points out the catch—long prompts and higher concurrency turn that saved history into the main GPU memory footprint. Feeds directly into [Prefill and Decode](../Concepts/推理系统/Prefill%20and%20Decode.md) and [KV Cache](../Concepts/推理系统/KV%20Cache.md).
