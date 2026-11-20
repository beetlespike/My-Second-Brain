# My Second Brain

[简体中文](README.md) · English

> When answers are within reach, where does judgment come from?

Two people using the same AI can see different questions in the same material. What they’ve studied along the way, and the connections they notice, can take their work in different directions. In research, creative work and decision-making, *human in the loop* means people guide their work with AI, from framing the question to judging what good work looks like. As AI takes part in more kinds of work, human knowledge, taste and judgment matter more. This private vault is meant to help you build on what you learn and gradually develop a perspective of your own.

After you’ve watched a video, read an article or a paper or worked through a question in a conversation, give your AI assistant the link or transcript. It writes up the concepts in local Markdown and links related ideas across sources. Following those links, it can spot a concept you haven’t studied that connects several you already know. A study card introduces it before you encounter the idea in your next reading.

[Start with your own material](Guides/First-Run.md) · [Today’s cards](Guides/First-Run.md#todays-cards) · [Explore the example in Obsidian](Guides/Graph-View.md)

![An example with Obsidian and Codex. You watch videos, read articles or papers, and learn through conversations before adding the source links to your private vault. Codex organizes the concepts, finds a missing node and makes a study card. The card comes back to you, and you take the new concept into your next reading. The taste and judgment you develop over time also shape what you and AI do together.](assets/demo/human-ai-loop.en.png)

## An ordinary week

> Some themes only get a name when you look back.

After watching [a six-minute Bilibili video on the KV cache](https://www.bilibili.com/video/BV1jAZwBGEwi/), I paste just the URL into a Codex chat in the vault. Codex uses a local model to transcribe the video and gives *KV Cache* and *Prefill and Decode* a note each. The next day I read the WeChat article [《预训练工程师在干什么》 (“What Do Pretraining Engineers Do?”)](https://mp.weixin.qq.com/s/Wt_HyaK98tPF39p1y6eMow) and send that link too. Codex finds my existing note on memory bandwidth and adds an example from the article.

Around the same time I watch part of [a tokenization lecture on YouTube](https://www.youtube.com/watch?v=zduSFxRajkE&t=1430s). While reading [*Sarathi-Serve*](https://www.usenix.org/conference/osdi24/presentation/agrawal), I [work through the timing with GPT](assets/demo/streaming-dialogue.md) to find out how long a reply paused midway through.

## Rereading my notes over the weekend

> Sometimes a discovery lies between two familiar concepts.

I set up an automation so Codex can periodically read the study conversations I choose. Codex adds the worked example from the conversation to my concept notes, then builds a map of content (MOC) from concepts that help explain the same question. When I open [the LLM serving map](MOCs/Streaming%20LLM%20Serving.md) over the weekend, I see how the cache, bandwidth and that pause fit together. The tokenization notes have [a map of their own](MOCs/Multilingual%20Tokenizers.md).

![Native Obsidian graph of LLM serving. Blue-gray nodes are concepts already studied. The three pale-gold nodes are concepts Codex suggests learning next.](assets/demo/obsidian-serving.png)

## Morning cards

> What else can we learn from what we already know?

Alongside the old question about the pause, my morning cards include *prefill–decode disaggregation*, shown in pale gold on the graph. Codex found this new concept by following the connections between caching and scheduling. I pick that card first.

[The two worked examples on the card](待学概念/推理系统/Prefill-Decode%20Disaggregation.md#简答) change only the bandwidth. Splitting the stages costs time in one case and saves it in the other. When I read [*DistServe*](Papers/DistServe.md) next, I’ll look at where the two stages run and which link the cache has to cross. Once I’ve read the paper, I’ll give Codex its link. That reading starts the next round.

Each vault has a private address you can bookmark on the computer where it lives. Use the same page every day to flip cards, rate them and leave questions. Ratings go straight into the review schedule. Before preparing the next deck, your assistant works through outstanding comments, revises a card, adds one or replies. Open **我的留言与回复** (“My comments and replies”) to see the result. I also use a scheduled Codex chat for my cards. Both places share the same records.

[Try the cards](Guides/First-Run.md#work-through-the-serving-example) · [Leave a comment on a review card](Guides/Flashcard-Review.md#反馈与保存)

![Full native Obsidian graph, including LLM serving, multilingual tokenization and reinforcement learning.](assets/demo/obsidian-graph.png)

For your own material, you can [create a separate private vault](Guides/First-Run.md#a-vault-of-your-own) alongside the public template. Your notes live on your computer. A cloud assistant sends the material it reads to its service. You can give it material from just one topic.

You can try [the bundled practice captions](assets/demo/first-token.vtt) offline. Install readers for online video and PDFs as needed. For a page that requires a login, you can use text you’ve exported yourself. For a scan, you can use OCR text. To receive morning cards, set up a scheduled task in a client that can read local files. [Sources and tools](Guides/Sources-and-tools.md) · [Automation settings](Guides/Automation.md)

[More topic maps](MOCs/知识库入口.md) · [MIT license](LICENSE) · [Third-party materials](THIRD-PARTY.md) · [Feedback](https://github.com/beetlespike/My-Second-Brain/issues)
