---
type: concept
aliases:
  - 可逆解码
status: active
stage: working
---

# 可逆解码

字节级词表给每个普通 token ID 指定一串字节。解码时，先按顺序拼接各 token 的字节，再用 UTF-8 把完整字节流还原成文字。token 边界与字符边界可以不同。

## 为什么要先拼字节

“你”的 UTF-8 编码为 E4 BD A0。假设三枚 token 各带一个字节，第一枚的 E4 单独出现时还缺少后两个字节。

若把三枚分别用替换模式解码，会得到三个替换字符“�”。先拼成 E4 BD A0，再一起解码，才能恢复“你”。[UTF-8变长编码](UTF-8%20Encoding.md)解释了这个字符为什么需要三个字节。

流式输出可以用同一个增量解码器保存尚未完成的前缀。依次输入 E4、BD、A0，Python 的 UTF-8 增量解码器先返回两次空串，最后返回“你”。[增量解码接口](https://docs.python.org/3/library/codecs.html#incrementaldecoder-objects)

## 原文与ID的往返是两个问题

对于合法 UTF-8 普通文本，如果字节覆盖完整、预处理保留原文、解码也保留空白，可以要求：

    decode(encode(text)) == text

若预处理进行了有损归一化或删除内容，能够还原的只是处理后的文本。

反向往返则未必成立。设 a、b 的 ID 分别是 97、98，合并后的 ab 为 256。[97,98] 和 [256] 都能解码为“ab”；使用同一合并表重新编码，会得到 [256]。所以原文可以恢复，而原来的 ID 序列发生变化。规则的优先级见[字节级BPE](Byte-Level%20BPE.md)。

minbpe 先从词表取出字节、拼接，再进行 UTF-8 解码。[解码实现](https://github.com/karpathy/minbpe/blob/1acefe89412b20245db5a22d2a02001e547dc602/minbpe/regex.py)

阅读路径：[文本编码与分词](../../MOCs/文本编码与分词.md)。
