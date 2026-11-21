---
type: video
source_url: https://www.youtube.com/watch?v=zduSFxRajkE&t=1430s
source_kind: public_source
evidence_status: anchored
status: distilled
---

# Let's build the GPT Tokenizer

Andrej Karpathy / YouTube · [Original / 原文](https://www.youtube.com/watch?v=zduSFxRajkE&t=1430s)

这一段把分词最反直觉的地方演了一遍：原始文本按 UTF-8 转成字节序列后，合并规则换一套，同一句话的字节一点没少，算出来的 token 数量却会差出不少——直接关系到后面多语言词表比谁吃得下更多原文。[代码参考 minbpe](https://github.com/karpathy/minbpe)

Watch 18:15 for raw [UTF-8 Encoding](../Concepts/计算机基础/UTF-8%20Encoding.md), 23:50 for the merge loop, and 34:58 for compression ratios: with [Byte-Level BPE](../Concepts/计算机基础/Byte-Level%20BPE.md), two tokenizers can look at the exact same byte stream yet turn it into very different token counts—which immediately skews token-budget comparisons across languages. Pairs neatly with Karpathy’s [minbpe implementation](https://github.com/karpathy/minbpe).
