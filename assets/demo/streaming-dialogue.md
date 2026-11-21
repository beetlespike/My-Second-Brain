# 计时一条流式回答 · Timing a streamed answer

一段实际排查推理流式卡顿的学习对话，按公开示例要求保留客户端计时口径、数字已重设。

**我**　我在看一条流式请求的日志，网页上看得出输出中途突然卡了一下，但面板里报的单 token 平均耗时只有 20 ms。已知请求发出后 120 ms 吐出第一个 token，200 ms 吐出第 5 个 token——只盯这个平均值是不是把那次卡顿掩盖过去了？

**助手**　是的，而且它把两段完全不同的耗时也搅在一起看漏了。先拆分账：从请求发出到第 1 个 token 到手的 120 ms，完全属于首字等待；第 2 到第 5 个这四个 token 一共走了 `200 - 120 = 80 ms`，按个数摊平就是每个 `20 ms`。

**我**　所以哪怕那四个间隔不是均匀的 20 ms，平均数还是 20？

**助手**　对。比如这四个间隔实际上是 `5、5、65、5 ms`，加起来照样是 80 ms，平均值依然报 20 ms——但用户眼里会实实在在卡住 65 ms。要想抓出这种单步抖动，客户端必须记录每个 token 的实际到达时间戳，而不能只存首尾时间相减。还要留心一个坑：如果网关把几个 token 攒成一块再按 SSE 推过来，日志里就得注明测到的是「分块到达间隔」，不是单 token 间隔。

## English

A reconstructed debugging conversation on streaming LLM latency (numbers reset for public release, keeping client-side timestamp semantics).

**Me**　Looking at a trace from a streaming run: the UI visibly hitched mid-sentence, yet the dashboard still shows a healthy 20 ms per token on average. With token 1 landing at 120 ms and token 5 at 200 ms, is the average metric hiding what users actually feel?

**Assistant**　Yes—it collapses two separate things, and any mid-stream stall disappears into the mean. The first 120 ms wait before token 1 arrives is strictly time to first token. Tokens 2 through 5 then took 80 ms combined (`200 - 120`), which averages out to 20 ms per step.

**Me**　So a nasty single-step stall wouldn’t budge that 20 ms number at all?

**Assistant**　Not at all. Suppose the true gaps were `5, 5, 65, 5 ms` instead of steady 20 ms ticks: they still sum to 80 ms and average 20 ms, even though the stream froze for 65 ms on one step. To spot stalls like that, log individual token arrival timestamps instead of subtracting just the first and last. One caveat: if the server or proxy flushes multi-token chunks together, mark explicitly in your trace that you recorded chunk gaps rather than per-token gaps.
