---
type: paper
source_url: https://www.usenix.org/conference/osdi24/presentation/zhong-yinmin
source_kind: public_source
evidence_status: anchored
status: distilled
---

# DistServe: Disaggregating Prefill and Decoding for Goodput-optimized Large Language Model Serving

Zhong et al. · OSDI 2024 · [Original / 原文](https://www.usenix.org/conference/osdi24/presentation/zhong-yinmin)

这篇的核心判断很实在：先定好要让多少比例的请求同时满足 TTFT 和 TPOT 的要求，再看每张 GPU 每秒能持续服务多少个请求（goodput）。把预填充和解码拆到不同 GPU 组虽能消掉批内互相拖累，但算总账时必须把传递 [KV Cache](../Concepts/推理系统/KV%20Cache.md) 的耗时和接收端可能新排的队一起扣回来；直接看引言和第 6 节的联合达标率图就够透彻。[作者图解 / companion article](https://haoailab.com/blogs/distserve/)

DistServe reframes serving capacity around goodput—the sustainable request rate per GPU where **both** latency limits hold at once. Splitting prefill and decode eliminates colocation interference, yet §§3–4 show the catch: you have to pay to transfer the [KV Cache](../Concepts/推理系统/KV%20Cache.md) over [Interconnect Bandwidth](../Concepts/推理系统/Interconnect%20Bandwidth.md) without queueing up the decoding pool. §6 puts it cleanly side by side: compare the standalone [TTFT](../Concepts/推理系统/TTFT.md) and [TPOT](../Concepts/推理系统/TPOT.md) curves against their joint attainment curve.
