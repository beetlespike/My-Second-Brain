---
type: video
source_url: https://www.bilibili.com/video/BV1jAZwBGEwi/
source_kind: public_source
evidence_status: anchored
status: distilled
---

# 6分钟速通大模型KV Cache

月球大叔 / Bilibili · [Original / 原文](https://www.bilibili.com/video/BV1jAZwBGEwi/)

00:17–01:17 看两阶段的分界，01:52–02:32 看历史 K、V 怎样复用，03:49–04:24 看长上下文与并发怎样占用显存。

At 00:17–01:17, a prompt produces its first token and the model starts decoding. At 01:52–02:32, the next query reuses earlier keys and values. At 03:49–04:24, increasing the history or the number of live requests takes more memory. These sections motivate [Prefill and Decode](../Concepts/推理系统/Prefill%20and%20Decode.md) and [KV Cache](../Concepts/推理系统/KV%20Cache.md).
