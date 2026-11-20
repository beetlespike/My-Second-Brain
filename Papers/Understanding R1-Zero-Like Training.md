---
type: paper
source_url: https://arxiv.org/html/2503.20783v2#S3.SS1
source_kind: public_source
evidence_status: anchored
status: distilled
---

# Understanding R1-Zero-Like Training: A Critical Perspective

Liu et al. · §3.1, Eq. 3 and Fig. 4 · [Original / 原文](https://arxiv.org/html/2503.20783v2#S3.SS1)

式 3 的两个分母分别随回答长度和同题奖励的离散程度而变。图 4 适合检查改变哪一个分母会影响哪类样本。

In Eq. 3 the objective divides a response’s tokenwise sum by its own length, while the group advantage divides by the standard deviation for that question. [Response Length Normalization](../Concepts/强化学习/Response%20Length%20Normalization.md) and [Advantage Normalization](../Concepts/强化学习/Advantage%20Normalization.md) therefore change different weights. Figure 4 shows them separately.
