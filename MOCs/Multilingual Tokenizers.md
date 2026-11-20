---
type: moc
status: active
---

# 换了词表，两个模型还在比同一件事吗？ · Comparing multilingual tokenizers

Karpathy 在 YouTube 演示怎样从 UTF-8 字节学出合并规则。两种词表可以编码完全相同的句子，产生的 token 数却不同。训练若都停在同一 token 数，两个模型见过的原文可能已经不同。[Let's build the GPT Tokenizer](../Videos/Karpathy%20on%20Tokenization.md)

| Question | Start with | Suggested concept |
| --- | --- | --- |
| How much text did each language contribute? | [Tokenization](../Concepts/计算机基础/Tokenization.md), [Byte-Level BPE](../Concepts/计算机基础/Byte-Level%20BPE.md), [Training Token Budget](../Concepts/计算机基础/Training%20Token%20Budget.md), [Language Mixture](../Concepts/计算机基础/Language%20Mixture.md) | [Tokenizer Fertility](../待学概念/计算机基础/Tokenizer%20Fertility.md) measures the token count per segmented word for each language. [Tokenizer Choice For LLM Training: Negligible or Crucial?](../Papers/Tokenizer%20Choice.md) |
| Can we compare held-out losses under two segmentations? | [UTF-8 Encoding](../Concepts/计算机基础/UTF-8%20Encoding.md), [Cross-Entropy](../Concepts/信息论/Cross-Entropy.md), [Perplexity](../Concepts/信息论/Perplexity.md) | [Bits per Byte](../待学概念/计算机基础/Bits%20per%20Byte.md) uses a common denominator on identical scored text. [nanochat’s evaluation code](../Articles/Measuring%20Bits%20per%20Byte.md) |
| Did one training run cost more? | [Vocabulary Size](../Concepts/计算机基础/Vocabulary%20Size.md), [Training FLOPs](../Concepts/计算机基础/Training%20FLOPs.md), [Downstream Evaluation](../Concepts/计算机基础/Downstream%20Evaluation.md) | [IsoFLOP Analysis](../待学概念/计算机基础/IsoFLOP%20Analysis.md) matches total compute before comparing downstream results. [Scaling Laws with Vocabulary: Larger Models Deserve Larger Vocabularies](../Papers/Vocabulary%20Scaling.md) |

这三项分别回答原文读了多少、损失按什么单位算、训练花费是否相当。可以从第二张卡算起，同一段文本上的每 token 损失不同，每字节损失却可能恰好相同。
