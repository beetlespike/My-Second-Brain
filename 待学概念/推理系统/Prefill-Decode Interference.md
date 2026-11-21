---
type: concept
aliases: ["预填充与解码干扰"]
tags: [ai-suggested, case-serving]
status: active
stage: working
学习状态: 待学
---

# Prefill-Decode Interference

连续合批允许新请求随到随插队，这给吞吐带来大好处，可代价也很直接：一条超长提示词挤进来要做预填充，这一轮计算会占住 GPU，原本正在平稳吐字的老请求也跟着硬生生停一拍。单看均值很难揪出它，得把每个请求的时间线与调度器迭代对齐，再缩小分块验证。

Under [Continuous Batching](../../Concepts/推理系统/Continuous%20Batching.md), admitting a huge new prompt saturates GPU compute for a turn and stalls every active decode stream in the batch. A low average [TPOT](../../Concepts/推理系统/TPOT.md) easily masks one ugly mid-stream hitch, so isolating interference requires lining up scheduler prefill iterations against per-token arrival timestamps across controlled [Prompt Length Distribution](../../Concepts/推理系统/Prompt%20Length%20Distribution.md) replays and smaller [Chunked Prefill](../../Concepts/推理系统/Chunked%20Prefill.md) caps.

[Taming Throughput-Latency Tradeoff in LLM Inference with Sarathi-Serve](../../Papers/Sarathi-Serve.md)

## 知识卡

### 正面

一条 8k 长输入刚塞进批里时，旁边正在流式输出的老请求突然卡顿了一下。排查时你要对齐哪两份时间记录，怎么做一组对照实验确认就是批内干扰？ / A running stream stalls right as a new 8k-token prompt enters the batch. What two traces do you line up, and what replay confirms colocation interference?

### 简答

把新请求的 prefill 调度轮次，跟老请求每个 token 的到达时间戳对齐；如果总卡在 prefill 执行时刻，用相同到达记录缩小分块预算再跑一次，如果卡顿也跟着缩短，就多了一条支持批内干扰的证据。 / Line up the new prompt’s prefill steps with per-token arrival timestamps on active decodes; then replay the exact arrival trace under a smaller chunk budget and check whether those spikes shrink.
