---
type: chat
source_path: assets/demo/streaming-dialogue.md
source_kind: anonymized_reconstruction
evidence_status: anchored
status: distilled
---

# 计时一条流式回答 · Timing a streamed answer

公开改写后的对话原文见 [streaming-dialogue](../assets/demo/streaming-dialogue.md)（保留客户端计时口径，数字已为公开示例重设）。

这段排查其实就钉死了一件容易看走眼的事：看板报 20 ms 平均耗时不等于流式输出顺滑。在例子里，第 1 个 token 等了 120 ms（[TTFT](../Concepts/推理系统/TTFT.md)），后 4 个总共耗时 80 ms，算出平均每个 20 ms（[TPOT](../Concepts/推理系统/TPOT.md)）——但如果实际间隔是 `5、5、65、5 ms`，平均数照样 20 ms，而那一下 65 ms 的卡顿只有留着逐 token 到达时间戳才看得见。另外，如果客户端收到的是按块合并发送的响应，还得标明量的是分块间隔。

A trace with token 1 at 120 ms ([TTFT](../Concepts/推理系统/TTFT.md)) and token 5 at 200 ms yields an 80 ms window across four tokens, so average [TPOT](../Concepts/推理系统/TPOT.md) sits at 20 ms either way—whether arrivals are steady `20 ms` ticks or `5, 5, 65, 5 ms` hiding a 65 ms stall. Per-token arrival timestamps catch the hitch; if chunks are batched before delivery, record that gap granularity explicitly.
