# First use

[简体中文](第一次使用.md)

### Start with something you know

Open the same learning folder in Obsidian and Codex. Pick part of a video, article, paper or conversation you can already explain. Give your assistant a little of your own reasoning.

> I worked through this part. My understanding is … . Give each distinct concept a note and look for connections with things I already know. Explain the reason beside the link. If the concept is already here, extend its note.

Use the same network for the next source. When several concepts together explain a larger question, gather them in a map of content (MOC). Another Markdown editor, local-file assistant or source reader works too. [Sources and readers](Sources-and-tools.md)

### Work through the serving example

In the full template, open `MOCs/Streaming LLM Serving.md` to explore the finished network. To build from the sources yourself, run the command below in the template folder and open the new directory. Use `--empty` for a personal vault without samples.

```sh
python3 tools/workflow.py init ../My-Learning-Trial --demo
```

1. Open `assets/demo/serving-sources.md`. It links a Bilibili video, a WeChat article, a systems paper with an English talk, and a rewritten timing conversation. Start with the parts you understand. What does a decoder reuse? How long did the four later tokens take on average?
2. Pick one connection between sources. When a long prompt enters the batch, an active decode can have to wait. Ask your assistant to put that explanation between *Continuous Batching* and *Chunked Prefill*. Use “Why did the stream stall?” as the question for a topic map.
3. Ask which concepts are missing from your account. The worked example suggests three, covering interference, service targets and splitting the stages. Try a card on one. When you can explain your reasoning, move the concept into the network and make a review question from it.

In the **full example vault** this command builds a local HTML deck with a new-concept card and existing review questions. Open the file indicated by `output`. In a vault you built from scratch, use the path of your own proposed concept.

```sh
python3 .flashcards/review.py session --prefer-new sb-fc-0015 --discovery '待学概念/推理系统/Prefill-Decode Disaggregation.md'
```

Flip a review card to rate it or leave a comment under **补充反馈或指出问题** (“Add feedback”). In a browser, export the feedback file and give it to Codex to import. Your rating sets the next review interval. To change a question, ask Codex to use the comment you left on that card. [Daily cards and automation](Automation.md) · [Card feedback](Flashcard-Review.md)
