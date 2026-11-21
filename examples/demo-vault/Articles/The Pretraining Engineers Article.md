---
type: article
source_url: https://mp.weixin.qq.com/s/Wt_HyaK98tPF39p1y6eMow
source_kind: public_source
evidence_status: anchored
status: distilled
---

# 【AI架构原理】预训练工程师在干什么——从 Karpathy 加入 Anthropic 说起

靳岩岩 / 微信公众号 · [Original / 原文](https://mp.weixin.qq.com/s/Wt_HyaK98tPF39p1y6eMow)

算力优化那一节算了笔很直观的账：小批量推理每解码一个 token，几乎都要把整份模型权重从显存搬一遍，计算单元反而在等数据；把多条请求合到一起分摊读取成本，才算得过来这笔带宽账。

The compute-efficiency section makes the hardware bottleneck concrete: when decoding at a small batch size, each step streams large model weights from HBM just to emit a tiny slice of tokens—putting the constraint squarely in [Memory Bandwidth](../Concepts/推理系统/Memory%20Bandwidth.md). Batching multiple sequences amortizes those weight reads across requests, though real serving traffic sets how much you can pack before latency pushes back.
