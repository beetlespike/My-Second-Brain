---
type: concept
aliases: ["每字节比特数"]
tags: [ai-suggested, case-tokenizers]
status: active
stage: working
学习状态: 待学
---

# Bits per Byte

用同一段原文比较模型时，先把被评分 token 的损失加总并转成 bit，再除以对应字节数。两次评测还要采用相同的文本、归一化和遮蔽范围。

Divide the total negative log-likelihood in bits by the number of raw bytes represented by the scored tokens. On identical text, this puts [Cross-Entropy](../../Concepts/信息论/Cross-Entropy.md) from two tokenizations on a common byte denominator. [UTF-8 Encoding](../../Concepts/计算机基础/UTF-8%20Encoding.md) fixes the byte count and [Perplexity](../../Concepts/信息论/Perplexity.md) retains a token denominator.

[nanochat · evaluate_bpb](../../Articles/Measuring%20Bits%20per%20Byte.md)

## 知识卡

### 正面

Identical text occupies 240 bytes. A scores it in 120 tokens at 2 bits/token, B in 80 at 3. Which has lower BPB? / 哪个模型每字节损失更低？

### 简答

Both assign 240 bits of loss, or 1 bit/byte. Their per-token losses differ because the token counts differ. / 两边都是 240 bit，即 1 bit/byte。
