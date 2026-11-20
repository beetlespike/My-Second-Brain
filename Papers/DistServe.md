---
type: paper
source_url: https://www.usenix.org/conference/osdi24/presentation/zhong-yinmin
source_kind: public_source
evidence_status: anchored
status: distilled
---

# DistServe: Disaggregating Prefill and Decoding for Goodput-optimized Large Language Model Serving

Zhong et al. · OSDI 2024 · [Original / 原文](https://www.usenix.org/conference/osdi24/presentation/zhong-yinmin)

引言给出每卡有效服务率的口径。第 6 节在不同到达率下分别画出两个延迟门槛和二者同时达标的比例。[作者图解 / companion article](https://haoailab.com/blogs/distserve/)

The introduction defines the latency targets and per-GPU goodput. Sections 3–4 explain why the size of the [KV Cache](../Concepts/推理系统/KV%20Cache.md) and the available [Interconnect Bandwidth](../Concepts/推理系统/Interconnect%20Bandwidth.md) matter to placement. In §6, compare the joint attainment curve with the two curves for [TTFT](../Concepts/推理系统/TTFT.md) and [TPOT](../Concepts/推理系统/TPOT.md) separately.
