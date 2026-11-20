---
type: paper
source_url: https://www.usenix.org/conference/osdi24/presentation/agrawal
source_kind: public_source
evidence_status: anchored
status: distilled
---

# Taming Throughput-Latency Tradeoff in LLM Inference with Sarathi-Serve

Agrawal et al. · OSDI 2024 · [Original / 原文](https://www.usenix.org/conference/osdi24/presentation/agrawal)

从调度器的一轮看长输入何时入批，以及把它分块后，正在生成的回答何时能继续输出。论文、演讲幻灯片和作者报告都在会议页。[OSDI talk on YouTube](https://www.youtube.com/watch?v=S8rq3pYboZY)

Follow the scheduler through one iteration. With [Continuous Batching](../Concepts/推理系统/Continuous%20Batching.md), arriving requests can join work in progress. [Chunked Prefill](../Concepts/推理系统/Chunked%20Prefill.md) splits a long prompt into pieces so a scheduler can give active decodes a turn alongside a piece of the prompt. Check the workload’s [Prompt Length Distribution](../Concepts/推理系统/Prompt%20Length%20Distribution.md) when choosing the chunk budget.
