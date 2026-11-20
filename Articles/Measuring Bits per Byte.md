---
type: article
source_url: https://github.com/karpathy/nanochat/blob/master/nanochat/loss_eval.py
source_kind: public_source
evidence_status: anchored
status: distilled
---

# nanochat · evaluate_bpb

Andrej Karpathy / nanochat implementation · [Original / 原文](https://github.com/karpathy/nanochat/blob/master/nanochat/loss_eval.py)

先累计被评分 token 的负对数似然和相应字节数，最后才做除法。特殊 token 和遮蔽位置须采用一致口径。

In evaluate_bpb, losses and the byte lengths of scored tokens are summed separately before division. Tokens that represent no scored text are excluded. This is an implementation of [Bits per Byte](../待学概念/计算机基础/Bits%20per%20Byte.md) using the same test text.
