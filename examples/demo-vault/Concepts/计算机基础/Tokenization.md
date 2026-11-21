---
type: concept
tags: [case-tokenizers]
aliases:
  - 分词
  - Tokenization
status: active
stage: hub
---

# 分词

语言模型需要把文字变成一串离散编号。分词器决定怎样切分文本、每个片段对应哪个 token ID，以及生成的 ID 怎样还原为文本。这里沿字节级分词器追踪一次输入。

## 同一段文字的几种单位

文本是“你 A👋”，包含中文、空格、字母和 emoji。

| 层次 | 这个例子里是什么 | 怎样继续处理 |
| --- | --- | --- |
| Unicode 码点 | 共 4 个；“你”为 U+4F60 | 按 UTF-8 编码 |
| 字节 | 共 9 个；“你”为 E4 BD A0 | 按词表与合并规则组成片段 |
| token | 每枚对应一段字节，数量取决于分词器 | 查出对应的 ID |
| token ID | 词表条目的编号 | 交给模型的嵌入层查询向量 |

[UTF-8变长编码](UTF-8%20Encoding.md)解释字符如何产生这些字节。[字节级BPE](Byte-Level%20BPE.md)解释怎样从语料中学习可合并片段；训练好的规则随后用于新文本。ID 本身是索引，其含义取决于配套词表。

## 边界可能落在一个字符内部

一枚 token 可以只包含某个字符的一部分字节。因此恢复文字时，需要先把各 token 的字节按顺序接起来。具体反例见[可逆解码](Reversible%20Decoding.md)。

分词器还会决定同一文本对应多少个预测位置。比较逐 token 的[困惑度](../信息论/Perplexity.md)时，需要把分词方式列入评测条件。

本页讨论普通文本的字节级分词。特殊控制 token、归一化和预切分也会影响输出，使用某套分词器时应保留其配套配置。实现依据见 [minbpe 的词表与字节映射](https://github.com/karpathy/minbpe/blob/1acefe89412b20245db5a22d2a02001e547dc602/minbpe/base.py)。

阅读路径：[文本编码与分词](../../MOCs/文本编码与分词.md)。

## Tokenization

The same text can become different sequences of token IDs. For an evaluation, fix the raw test text and state which tokens contribute to [Cross-Entropy](../信息论/Cross-Entropy.md). A fixed token count also changes how much raw text fits into a [Training Token Budget](Training%20Token%20Budget.md).

[Let's build the GPT Tokenizer](../../Videos/Karpathy%20on%20Tokenization.md)
