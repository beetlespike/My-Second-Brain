---
type: concept
aliases: ["每个输出 token 的平均时间"]
tags: [case-serving]
status: active
stage: working
---

# TPOT

从首 token 到末 token 的时间，除以其间新到达的 token 数。这个平均值会把一次很长的停顿摊薄。

For a request with M > 1 output tokens, average time per output token after the first is (last-token time − first-token time)/(M − 1). If four more tokens arrive over 80 ms, TPOT is 20 ms. Seeing individual stalls requires the arrival times of those tokens. [TTFT](TTFT.md) covers the earlier wait.

[计时一条流式回答 · Timing a streamed answer](../../Chats/Timing%20a%20Stream.md)
