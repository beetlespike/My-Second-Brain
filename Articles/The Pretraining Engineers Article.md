---
type: article
source_url: https://mp.weixin.qq.com/s/Wt_HyaK98tPF39p1y6eMow
source_kind: public_source
evidence_status: anchored
status: distilled
---

# 【AI架构原理】预训练工程师在干什么——从 Karpathy 加入 Anthropic 说起

靳岩岩 / 微信公众号 · [Original / 原文](https://mp.weixin.qq.com/s/Wt_HyaK98tPF39p1y6eMow)

文中讨论算力优化时，把小批量推理和预训练放在一起看。解码每次只多几个 token，读取权重花的时间可能占大头。这个观察给连续合批提供了一个动机。

In the article’s discussion of compute efficiency, small-batch generation reads a large set of weights for very few new tokens. That observation belongs under [Memory Bandwidth](../Concepts/推理系统/Memory%20Bandwidth.md). Reusing weights across several requests changes the arithmetic per byte. The serving workload determines how much that helps.
