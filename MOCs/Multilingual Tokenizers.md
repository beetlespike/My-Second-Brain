---
type: moc
status: active
---

# 换了词表，两个模型还在比同一件事吗？ · Comparing multilingual tokenizers

在 YouTube 看完 Karpathy 手写分词器的推导后，一个直觉顺理成章浮了出来：两套分词器读同一段话，原始字节数一模一样，切出来的 token 数却可以差出很远。如果训练评测时强行对齐在“相同 token 数”，两个模型其实压根没看过等量的信息。[Let's build the GPT Tokenizer](../Videos/Karpathy%20on%20Tokenization.md)

| Question | Start with | Suggested concept |
| --- | --- | --- |
| 两种语言实际各读进了多少文本？ | [Tokenization](../Concepts/计算机基础/Tokenization.md), [Byte-Level BPE](../Concepts/计算机基础/Byte-Level%20BPE.md), [Training Token Budget](../Concepts/计算机基础/Training%20Token%20Budget.md), [Language Mixture](../Concepts/计算机基础/Language%20Mixture.md) | [Tokenizer Fertility](../待学概念/计算机基础/Tokenizer%20Fertility.md) measures tokens per word (or character) by language so a coarse vocab isn’t mistaken for more data. [Tokenizer Choice Paper](../Papers/Tokenizer%20Choice.md) |
| 词表切法不同，怎么比验证集 loss？ | [UTF-8 Encoding](../Concepts/计算机基础/UTF-8%20Encoding.md), [Cross-Entropy](../Concepts/信息论/Cross-Entropy.md), [Perplexity](../Concepts/信息论/Perplexity.md) | [Bits per Byte](../待学概念/计算机基础/Bits%20per%20Byte.md) puts losses onto raw bytes as a shared denominator instead of apples-to-oranges per-token perplexity. [nanochat evaluation notes](../Articles/Measuring%20Bits%20per%20Byte.md) |
| 大词表把参数和投影算力吃掉了，总训练算力拉齐了吗？ | [Vocabulary Size](../Concepts/计算机基础/Vocabulary%20Size.md), [Training FLOPs](../Concepts/计算机基础/Training%20FLOPs.md), [Downstream Evaluation](../Concepts/计算机基础/Downstream%20Evaluation.md) | [IsoFLOP Analysis](../待学概念/计算机基础/IsoFLOP%20Analysis.md) locks total compute across candidate vocabulary sizes before judging downstream scores. [Vocabulary Scaling](../Papers/Vocabulary%20Scaling.md) |

这三笔账合在一起才完整：各语种喂进去了多少原文、loss 按哪套分母折算、以及大词表多出来的 FLOPs 有没有放进同一把尺子里比。
