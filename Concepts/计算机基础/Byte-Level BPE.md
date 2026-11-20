---
type: concept
tags: [case-tokenizers]
aliases:
  - 字节级 BPE
  - 字节级BPE
  - Byte-Level BPE
status: active
stage: working
---

# 字节级BPE

字节级 BPE 从 256 种单字节条目出发，把语料中频繁相邻的片段合并为新 token。词表保存每个 ID 对应的字节串，合并表保存哪些相邻条目可以合成一个。

## 训练频次怎样变成合并规则

在一个教学例子中，先约定字母串和空格各自成段。语料为“ab ab ab bc bc”，相邻对只在各段内部计数。

第一轮，“a、b”出现三次，“b、c”出现两次，因此先学习合并 ab。假设它的新 ID 为 256。应用规则以后，再统计剩余相邻对，第二轮学习 bc，赋予 ID 257。

这里的 256、257 是教学词表的编号，其他分词器可能使用不同编号。训练中的并列取舍也需要固定规则。

## 编码新文本为什么不重新统计词频

现在编码单独一段“abc”。ab 和 bc 两条规则都可以用，按已学好的优先级先合并 ab，结果成为 ab、c，也就是这个词表中的 [256,99]。因为没有继续合并 ab 与 c 的规则，编码结束。

训练决定合并规则和顺序；编码使用固定的规则。minbpe 的实现先跨预切分片段累计训练频次，编码时选择当前可用且学习顺序最早的相邻对。[训练与编码实现](https://github.com/karpathy/minbpe/blob/1acefe89412b20245db5a22d2a02001e547dc602/minbpe/regex.py)

## 计数与实际替换次数

“aaaa”含三处相邻的 aa。一轮从左到右执行不重叠合并，只能替换两处，得到 aa、aa。下一轮才会看到一对 aa、aa。因此，相邻对频次与实际替换次数可能不同。[计数与合并实现](https://github.com/karpathy/minbpe/blob/1acefe89412b20245db5a22d2a02001e547dc602/minbpe/base.py)

预切分边界也会影响哪些片段可以合并。例子把空格单独分段；另一套规则可能允许前导空格与后面的词合并。训练与使用时须保持配套规则。

初始字节来自[[Concepts/计算机基础/UTF-8 Encoding|UTF-8变长编码]]。token 边界可以落在字符内部，生成之后需要按[[Concepts/计算机基础/Reversible Decoding|可逆解码]]的顺序恢复原文。

阅读路径：[[MOCs/文本编码与分词|文本编码与分词]]。

## Byte-Level BPE

Training starts from individual bytes and learns ordered pair merges. Once the rules are fixed, encoding applies them to the permitted adjacent pairs. Changing [Vocabulary Size](Vocabulary%20Size.md) changes which merges can be included.

[Let's build the GPT Tokenizer](../../Videos/Karpathy%20on%20Tokenization.md)
