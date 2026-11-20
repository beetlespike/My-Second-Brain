---
type: concept
aliases: ["首 token 延迟"]
tags: [case-serving]
status: active
stage: working
---

# TTFT

从客户端发出请求，到收到第一个输出 token。排队和处理提示词都占用这段时间。

Time to first token runs from a client's request to receipt of the first output token. It includes queuing as well as prompt processing. Two equal prompts can therefore have different TTFT at different levels of [Request Arrival Rate](Request%20Arrival%20Rate.md).

[计时一条流式回答 · Timing a streamed answer](../../Chats/Timing%20a%20Stream.md)
