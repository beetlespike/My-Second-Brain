---
type: concept
status: active
stage: working
---

# GraphRAG

有些查询需要横跨多篇资料归纳，例如“这批推理论文主要解决哪几类瓶颈？”只取和问题最相似的几段，可能集中在同一个方法上。Microsoft 的 GraphRAG 从文本提取实体和关系，对实体图中的社区分别做摘要，再综合与问题有关的摘要。

## 先问清楚需要哪种证据

查某篇报告的一个数字，可以用 [RAG](RAG.md) 和[检索与重排](Retrieval%20and%20Reranking.md)直接定位。归纳多份报告的共同主题时，图中的实体关系能把相邻概念放在一起。跨文档抽取可能漏掉关系，也可能把不相同的实体当成同一个。输出仍应保留可复查的来源。

[From Local to Global](https://arxiv.org/abs/2404.16130)
