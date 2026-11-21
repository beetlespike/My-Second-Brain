---
type: concept
aliases: ["训练语料的语言配比"]
tags: [case-tokenizers]
status: active
stage: working
---

# Language Mixture

按文档数、字节数或 token 数配比，多种语言在训练中占的份额可能完全不同。换词表后尤其值得重新计数。

Sampling equal numbers of tokens from two languages can expose a model to different amounts of raw text in each. State whether mixture weights are specified in documents, bytes, words or tokens. Recheck the weights after changing [Tokenization](Tokenization.md).

[Tokenizer Choice For LLM Training: Negligible or Crucial?](../../Papers/Tokenizer%20Choice.md)
