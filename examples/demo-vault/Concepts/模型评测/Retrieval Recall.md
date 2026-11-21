---
type: concept
aliases:
  - 检索召回率
status: active
stage: working
---

# 检索召回率

对一个问题，先标注可以用来核对答案的证据段。Recall@k 用全部已标注证据作分母，衡量前 k 个结果找回了多少证据。Precision@k 用 k 作分母，衡量前 k 个位置有多少放对了。

## 改候选集还是改排序

假设标准证据有四段。前五个结果命中三个不同的证据段，且其余两段不相关，召回率是 3/4，精确率是 3/5。如果第四段已经进了前二十名，[重排](../智能体与检索/Retrieval%20and%20Reranking.md)还有机会把它提到前五名。如果前二十名里也没有，就要看检索器或索引漏了什么。

这道题假设片段和标准证据一一对应。真实评测要先约定重复切片、等价证据和标注不全怎么处理。找到了证据以后，还要看模型有没有把它用对。[答案正确性与证据支持](Answer%20Correctness%20and%20Support.md)

[ir_measures 的 Recall 定义](https://ir-measur.es/en/latest/measures.html#recall)
