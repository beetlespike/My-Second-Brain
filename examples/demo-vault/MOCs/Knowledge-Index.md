---
type: moc
status: active
---

# Knowledge Index

[简体中文](知识库入口.md)

Each map of content (MOC) centers on a concrete question and pulls together the concepts that explain it. The same concept can appear in several maps: retrieval decides which passages enter the prompt, while serving determines when the model finishes reading them—so both maps rely on *Prefill and Decode*.

Open this folder as a vault in Obsidian and choose **Open graph view**. To follow the serving example, filter the graph by `tag:#case-serving`.

| Topic map | Central question | Key concepts |
| --- | --- | --- |
| [Statistical Estimation](统计估计.md) | Does drawing more samples always make an estimate more accurate? | Sample Mean, Standard Error, Sample Size and Precision |
| [Information and Prediction](信息与预测.md) | How do you separate inherent uncertainty from prediction error? | Entropy, Cross-Entropy, KL Divergence, Perplexity |
| [Text Encoding and Tokenization](文本编码与分词.md) | How does text turn into token IDs and decode cleanly back to text? | Tokenization, UTF-8 Encoding, Byte-Level BPE, Reversible Decoding |
| [Research and Experiments](研究与实验.md) | How do you get clean evidence that a change actually helped? | Testable Questions, Near Miss Examples, Ablation Studies, Paired Evaluation |
| [Inference Systems](推理系统.md) | Is time spent waiting for the first token or generating the rest? | Prefill and Decode, KV Cache, Continuous Batching, PagedAttention |
| [Retrieval and Generation](检索与生成.md) | Which retrieved passage actually supports the answer? | RAG, Retrieval and Reranking, GraphRAG |
| [Model Evaluation](模型评测.md) | When RAG fails, should you fix retrieval or generation? | Retrieval Recall, Answer Correctness and Support, pass@k |

## Three worked research questions

[LLM Serving: Streaming pauses as throughput rises](Streaming%20LLM%20Serving.md) · [Multilingual Tokenizers: Three ways to read one training budget](Multilingual%20Tokenizers.md) · [RLVR: Single-pass accuracy vs. problem coverage](RLVR%20and%20Coverage.md)

## Walking from one path to another

Starting in [Retrieval and Generation](检索与生成.md) at [RAG](../Concepts/智能体与检索/RAG.md), because selected chunks enter the prompt and extend the input, following the “Prefill” link leads straight to [Prefill and Decode](../Concepts/推理系统/Prefill%20and%20Decode.md). That same node belongs to [Inference Systems](推理系统.md), where you can trace how subsequent tokens are generated.

[Perplexity](../Concepts/信息论/Perplexity.md) is computed per token, so comparing two models requires checking [Tokenization](../Concepts/计算机基础/Tokenization.md) first. [Paired Evaluation](../Concepts/研究方法/Paired%20Evaluation.md) averages per-item score differences, which brings in [Standard Error](../Concepts/数理基础/Standard%20Error.md). Those links answer “what unit is the metric in?” and “how stable is the mean difference?”

When adding more retrieved passages, combine evidence checks from [Model Evaluation](模型评测.md) with wait times in [Inference Latency and Throughput](../Concepts/推理系统/Inference%20Latency%20and%20Throughput.md). [Latency-Constrained RAG Evaluation](../待学概念/模型评测/Latency-Constrained%20RAG%20Evaluation.md) puts both sides into one exercise.

## Discovering new concepts from existing nodes

Computing standard error, choosing sample size and estimating uncertainty in paired evaluations all depend on whether observations are independent. Working through [Correlated Sampling](../待学概念/数理基础/Correlated%20Sampling.md) shows how duplicated records or clustered test items alter those calculations.

Ask your AI assistant to discover missing nodes from the network to find unrecorded concepts that bridge several ideas you already know (stored in `Study-Queue/` or, in this showcase vault, `待学概念/`). Pick one study note and walk through its worked examples and exercises.

## Study and review

[The study queue guide](../待学概念/待学概念导读.md) tracks open questions worth exploring next. Existing review decks live in [Sampling Estimation](../Flashcards/抽样估计.md) and [Concept Connections](../Flashcards/概念之间的联系.md). At your vault’s fixed private webpage URL, try recalling the answer before flipping, rate recall, or leave a question—your assistant handles pending comments on its daily review run before publishing the next deck.

This repository includes worked example knowledge. Your own mastery and learning state are tracked solely from your discussions, exercises and explicit feedback.
