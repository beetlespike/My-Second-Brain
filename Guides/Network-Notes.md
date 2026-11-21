# Concepts and Topic Maps

[简体中文](网络与主题地图.md)

## What to Keep from One Studied Source

A single lecture on generative inference might cover three separate mechanisms worth explaining cleanly: prefill explains when the model produces its first output token, KV cache explains how subsequent steps reuse past key/value tensors, and continuous batching explains how finished sequences free slots for waiting requests. One source note can point to all three concept pages. Give each concept page its own mechanism, applicability conditions, and a self-contained example so any reader arriving from another path can follow it directly.

## Explain Every Link in Prose

Start links from concrete causal explanations. For example: *“Retrieval-augmented generation places selected chunks into the prompt, which increases the sequence length handled during prefill.”* That sentence works naturally both inside a RAG note and linked back from Prefill. State which assumption a method relies on, what counterexample reveals a boundary, or how one change shifts a measurement. Always use standard relative Markdown links (`[Concept Name](../Concepts/...md)`) so any Markdown editor or graph view can traverse them.

Before creating a new page, see what concepts an incoming source adds or refines. If a synonymous concept already exists, add a derivation, concrete example, or boundary condition there. Keep topically similar notes separate if you cannot yet state their specific relationship.

## Maps of Content (MOCs)

When several connected concepts together answer a broader question, organize them into a Map of Content (`MOCs/`). A map frames the working answer, selects the concepts that explain it, and leaves explicit room for open questions. The same concept can appear in multiple maps when it plays different roles.

For instance, tracing *Retrieval and Generation* focuses on which evidence enters the prompt, while tracing *Inference Systems* asks why the first token waits—and both paths meet at Prefill. One map can point readers across to the other, keeping scheduling and memory details where they belong.

The first map your assistant drafts can be short: pose a question as the title, summarize what you worked out so far, and link the supporting concepts. Put commonly confused alternatives side by side, and jot down open doubts to update as understanding deepens.

Store concept pages under `Concepts/` with `type: concept` and `status: active` (and optional `stage: seed | working | hub`). Store maps under `MOCs/` with `type: moc` and `status: active`, linking each map into `MOCs/Knowledge-Index.md` (or `MOCs/知识库入口.md`) or neighboring maps.

## Discovering Missing Concepts from Existing Links

Questions left open on one map often point to bridges with another. Retrieval and reranking order passages; prefill computes the expanded prompt; generation relies on evidence surviving selection. When context windows or budgets tighten, the *Retrieval Context Budget* gap becomes clear. Ask your assistant to explain what a candidate concept changes at each connected node, and deduplicate by meaning and aliases—sometimes an existing note simply missed a relationship.

When a genuine discovery emerges, draft a standalone study note under `Study-Queue/` (or `待学概念/` in Chinese/bilingual vaults) with a clear definition, linked concepts, and a concrete exercise. Tag it `ai-suggested` (and track study state cleanly). Add a [Study Card](Flashcard-Review.en.md#new-concept-cards) section to surface it alongside your daily review cards.

## After You Learn It

When [walking through a new concept](../Prompts/study-concept.md), record your own explanation and open questions; mark it as in progress if you pause midway. Once you can explain the mechanism, finish the exercise, or confirm understanding explicitly, fold the note into `Concepts/`, merge any duplicate aliases, update incoming links and topic maps, and prepare review cards. Always preserve handwritten notes and past card feedback.
