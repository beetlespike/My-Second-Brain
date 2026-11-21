---
type: concept
aliases: ["优势归一化"]
tags: [case-rlvr]
status: active
stage: working
---

# Advantage Normalization

将中心化后的奖励除以题内奖励标准差。组间方差不同，相同大小的中心化奖励也可能得到不同的更新权重。

In the GRPO objective studied here, divide each centered reward by the group reward standard deviation, with a numerical guard for zero. Two groups with the same centered difference can receive different update scales. Inspect the [Group Baseline](Group%20Baseline.md) and the scale separately.

[Understanding R1-Zero-Like Training: A Critical Perspective](../../Papers/Understanding%20R1-Zero-Like%20Training.md)
