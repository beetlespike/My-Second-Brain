---
type: video
source_url: https://www.youtube.com/watch?v=zduSFxRajkE&t=1430s
source_kind: public_source
evidence_status: anchored
status: distilled
---

# Let's build the GPT Tokenizer

Andrej Karpathy / YouTube · [Original / 原文](https://www.youtube.com/watch?v=zduSFxRajkE&t=1430s)

从一个词到一串 UTF-8 字节，再到几枚 token。换了合并规则，词和字节都没换，token 数可以变。

Follow UTF-8 at 18:15, the merge algorithm at 23:50 and compression at 34:58. [UTF-8 Encoding](../Concepts/计算机基础/UTF-8%20Encoding.md) gives the initial bytes, [Byte-Level BPE](../Concepts/计算机基础/Byte-Level%20BPE.md) learns frequent pairs, and the same bytes can then require a different number of tokens. The author's [minbpe implementation](https://github.com/karpathy/minbpe) accompanies the lecture.
