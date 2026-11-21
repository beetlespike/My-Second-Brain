---
type: concept
aliases: ["首 token 延迟"]
tags: [case-serving]
status: active
stage: working
---

# TTFT

从客户端发出请求算起，到界面吐出第一个输出 token 之间的整段干等。用户发完问题觉得“模型半天没反应”，背后往往同时叠了两条账：在调度队列里等空位的排队时间，外加模型并行扫完提示词预填充本身的计算耗时。

Time to first token tracks the full wait before the very first answer token hits the client—covering both scheduler queueing and prompt prefill compute. That is why identical prompts still swing sharply in TTFT once [Request Arrival Rate](Request%20Arrival%20Rate.md) pushes batch queues deeper.

[计时一条流式回答 · Timing a streamed answer](../../Chats/Timing%20a%20Stream.md)
