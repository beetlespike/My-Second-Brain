---
type: concept
tags: [case-tokenizers]
aliases:
  - UTF-8 编码
  - UTF-8变长编码
  - UTF-8
status: active
stage: working
---

# UTF-8变长编码

为什么“你”是一个码点，却占三个字节？Unicode 为字符分配编号，UTF-8 再把可编码的码点写成一到四个字节。ASCII 范围的字母与空格沿用单字节数值。

## 从码点算出字节

UTF-8 的首字节前缀说明序列长度，后续字节以二进制 10 开头。“你”的码点为 U+4F60，属于三字节范围。

把十六进制 4F60 展开为二进制，再按 4、6、6 位分组：

    0100 | 111101 | 100000

三字节编码的模板为：

    1110xxxx 10xxxxxx 10xxxxxx

依次填入，得到：

    11100100 10111101 10100000
    E4       BD       A0

解码时可以反过来去掉前缀，恢复码点。合法 UTF-8 还要求使用规定的最短编码长度，并排除代理码点及超过 U+10FFFF 的值。[RFC 3629 第 3、4 节](https://datatracker.ietf.org/doc/html/rfc3629#section-3)

## 四个码点怎样占九个字节

| 内容 | UTF-8 字节 |
| --- | --- |
| 你 | E4 BD A0 |
| 空格 | 20 |
| A | 41 |
| 👋 | F0 9F 91 8B |

这段文本共有 $3+1+1+4=9$ 个字节。[[Concepts/计算机基础/Byte-Level BPE|字节级BPE]]可以从这些字节学习或应用合并规则，最终 token 数还取决于词表。

码点数、用户感知的字符数和字节数是不同单位；组合字符还可能让一个可见字符由多个码点组成。本例选择的四个字符各占一个码点。进入[[Concepts/计算机基础/Tokenization|分词]]后，还会出现 token 这个单位。怎样避免在还原时丢失跨 token 的字节，见[[Concepts/计算机基础/Reversible Decoding|可逆解码]]。

阅读路径：[[MOCs/文本编码与分词|文本编码与分词]]。

## UTF-8 Encoding

UTF-8 encodes a Unicode scalar as one to four bytes. Byte length stays fixed for the identical encoded text even when [Byte-Level BPE](Byte-Level%20BPE.md) merges different sequences of bytes.

[Let's build the GPT Tokenizer](../../Videos/Karpathy%20on%20Tokenization.md)
