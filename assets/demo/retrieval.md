# 搜到了结论，也搜到了例外

一份虚构的实验报告说某种搜索方法在长问题上更准，紧接着给出一个例外。问答系统能把这两件事都说清楚吗？

资料库里有两段直接相关的文字，甲给出结论，乙解释例外。检索器找回甲、乙，还有两个只提到“搜索”的段落。它找全了两段证据，候选集的检索召回率是 2/2。重排模型逐段比较它们对这个问题有多重要。如果排在最前面的两段里只有甲，取前两段时召回率就降到了 1/2。

检索增强生成（RAG）把选中的段落和问题一起交给语言模型。只给甲，模型能据此说出结论，却缺了能让它交代例外的那段话。一个有用的检查是看最后送进去的文字里还剩下哪些证据。

## The conclusion and its exception

In this fictional report, a search method is more accurate on long questions, with one exception. Can a question-answering system explain both?

Two passages matter. A states the conclusion and B describes the exception. The retriever returns both, along with two passages that merely mention search. It found two of two relevant passages, so recall in the candidate set is 2/2. A reranker then scores the passages against the question. If A is the only relevant passage in the top two, recall at two drops to 1/2.

Retrieval-augmented generation (RAG) puts the selected passages into the language model's input alongside the question. Given only A, the model has evidence for the conclusion. The text it would need to substantiate the exception is missing.
