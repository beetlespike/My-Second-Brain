---
type: concept
aliases: ["每个输出 token 的平均时间"]
tags: [case-serving]
status: active
stage: working
---

# TPOT

拿首 token 到最后一个 token 的总输出窗口，除以这中间新增的 `M - 1` 个 token 数，就是后续阶段「平均多久吐一个字」。它适合对比整体吐字吞吐快慢，但很容易骗过体感：四个间隔 `5、5、65、5 ms` 的平均 TPOT 照样是看似很稳的 20 ms，要抓出中途突然卡住半拍的那一下，还得逐 token 打到达时间戳。

Average time per output token after the first—`(t_last - t_first) / (M - 1)` for `M > 1` output tokens—summarizes steady streaming pace cleanly, but averages out mid-stream hitches (`5, 5, 65, 5 ms` yields the same 20 ms TPOT as steady 20 ms steps). Always log per-token arrival timestamps when checking streaming smoothness alongside [TTFT](TTFT.md).

[计时一条流式回答 · Timing a streamed answer](../../Chats/Timing%20a%20Stream.md)
