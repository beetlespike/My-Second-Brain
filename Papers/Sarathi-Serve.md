---
type: paper
source_url: https://www.usenix.org/conference/osdi24/presentation/agrawal
source_kind: public_source
evidence_status: anchored
status: distilled
---

# Taming Throughput-Latency Tradeoff in LLM Inference with Sarathi-Serve

Agrawal et al. · OSDI 2024 · [Original / 原文](https://www.usenix.org/conference/osdi24/presentation/agrawal)

顺着调度器的一轮 iteration 就能看清矛盾在哪：连上[连续合批](../Concepts/推理系统/Continuous%20Batching.md)以后，一条刚进来的长提示词如果想一口气跑完预填充，就会把同批里正在正常输出的老请求全卡住；用[分块预填充](../Concepts/推理系统/Chunked%20Prefill.md)把长提示切小块塞进每轮空闲预算，老请求的解码每轮也能分到机会，视频、PPT 和论文主页都在会议链接里。[OSDI talk on YouTube](https://www.youtube.com/watch?v=S8rq3pYboZY)

Tracing a single scheduler iteration shows why raw throughput and streaming smoothness collide: under [Continuous Batching](../Concepts/推理系统/Continuous%20Batching.md), admitting a huge prompt in one shot can delay the next token for streams that share the GPU. [Chunked Prefill](../Concepts/推理系统/Chunked%20Prefill.md) slices long prompts into bounded chunks so ongoing decodes keep piggybacking on each step, making the actual [Prompt Length Distribution](../Concepts/推理系统/Prompt%20Length%20Distribution.md) key to sizing that token budget.
