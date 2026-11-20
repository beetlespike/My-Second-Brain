# My Second Brain

[简体中文](README.md) · English

My Second Brain is a local Markdown template for building a knowledge network in Obsidian. Codex helps connect the concepts you’ve learned and uses those connections to suggest new ones for your daily cards.

[Start with your own material](Guides/First-Run.md) · [Explore the example in Obsidian](Guides/Graph-View.md)

## An ordinary week

I send Codex a Bilibili video I’ve watched and tell it what I learned. Two notes come out of it, *KV Cache* and *Prefill and Decode*. A WeChat article I read the next day gives me an example for my note on memory bandwidth. [KV cache video](https://www.bilibili.com/video/BV1jAZwBGEwi/) · [Article on pretraining engineers](https://mp.weixin.qq.com/s/Wt_HyaK98tPF39p1y6eMow)

I also watch part of a lecture on tokenizers. While reading *Sarathi-Serve*, I ask ChatGPT how to measure a pause halfway through a reply. [Lecture on YouTube](https://www.youtube.com/watch?v=zduSFxRajkE&t=1430s) · [Paper](https://www.usenix.org/conference/osdi24/presentation/agrawal) · [Rewritten conversation](assets/demo/streaming-dialogue.md)

## Sunday notes

I’ve set Codex to revisit the study chats I choose. Looking back on Sunday, I see how the timing example fits with the cache and bandwidth notes. LLM serving turns out to be one subject I’ve been studying. I gather those pages into a map of content (MOC) for a closer look at the pause. Tokenization gets its own map. [LLM serving](MOCs/Streaming%20LLM%20Serving.md) · [Multilingual tokenizers](MOCs/Multilingual%20Tokenizers.md)

![Native Obsidian graph of LLM serving. Blue-gray marks concepts learned from sources. Pale gold marks three suggested study nodes.](assets/demo/obsidian-serving.png)

## Two cards in the morning

One card revisits the pause. Another introduces *prefill-decode disaggregation*, one of the pale gold nodes Codex suggested from my notes on caching and scheduling. Once I’ve studied it, it can join the review deck.

I flip the review card, mark it “a little hazy” and leave a note underneath asking for a different example. I send that feedback to Codex so it can revise the question and schedule the next review. [Try the cards](Guides/First-Run.md#work-through-the-serving-example)

![Full native Obsidian graph, including LLM serving, multilingual tokenization and reinforcement learning.](assets/demo/obsidian-graph.png)

The notes work with other Markdown editors and assistants. Set up scheduled tasks locally, or share material by hand. [Source readers](Guides/Sources-and-tools.md) · [Automation and daily cards](Guides/Automation.md)

[More topic maps](MOCs/知识库入口.md) · [MIT license](LICENSE) · [Third-party materials](THIRD-PARTY.md) · [Feedback](https://github.com/beetlespike/My-Second-Brain/issues)
