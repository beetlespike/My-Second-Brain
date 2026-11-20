---
type: paper
source_url: https://aclanthology.org/2024.findings-naacl.247/
source_kind: public_source
evidence_status: anchored
status: distilled
---

# Tokenizer Choice For LLM Training: Negligible or Crucial?

Ali et al. · Findings of NAACL 2024 · [Original / 原文](https://aclanthology.org/2024.findings-naacl.247/)

论文同时比较分词统计和任务表现。按语言记录固定词数的切分长度，再把它与训练用量、下游效果分别比较。

The tokenizer comparison reports measures of segmentation alongside language-model and downstream results. A [Training Token Budget](../Concepts/计算机基础/Training%20Token%20Budget.md) covers different amounts of raw text across languages and tokenizers. [Language Mixture](../Concepts/计算机基础/Language%20Mixture.md) and [Downstream Evaluation](../Concepts/计算机基础/Downstream%20Evaluation.md) matter when interpreting a change in segmentation.
