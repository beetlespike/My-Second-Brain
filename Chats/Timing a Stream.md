---
type: chat
source_path: assets/demo/streaming-dialogue.md
source_kind: anonymized_reconstruction
evidence_status: anchored
status: distilled
---

# 计时一条流式回答 · Timing a streamed answer

改写对话 / reconstructed exchange · [改写对话全文 / Rewritten exchange](../assets/demo/streaming-dialogue.md)

这组数字是为公开示例重写的。对话贡献的是一个区分：等开头、等后续 token 的平均时间和中间一次停顿，分别要看什么记录。

A client receives its first token at 120 ms, then four more by 200 ms. [TTFT](../Concepts/推理系统/TTFT.md) is 120 ms and [TPOT](../Concepts/推理系统/TPOT.md) is 20 ms. Those two times leave open the spacing of the four later arrivals. The exchange separates a stall someone can feel from an average a dashboard might report.
