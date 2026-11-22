# My Second Brain

English · [简体中文](README.zh.md)

My Second Brain is an open-source learning framework that lets your AI assistant connect what you’ve studied in local Markdown notes, **discover related concepts you haven’t learned yet**, and make personalized discovery and review cards for one private webpage you can bookmark.

> When answers are within reach, where does judgment come from?

Two people using the same AI can look at the same material and come away with very different questions. What each person has learned along the way, and the connections they know to look for, shape where their work goes next. In research, writing, and everyday decisions, *human in the loop* means you stay the one steering—from framing what matters to judging whether an answer holds up. The more work AI can shoulder, the more your own knowledge, taste, and judgment count.

This private vault keeps formal concept notes only for what you have genuinely learned, because at heart it is a faithful map of your own knowledge—letting AI summarize things you never studied breaks that map—while a separate study queue holds candidate concepts your assistant proposes along your existing links. Hand your assistant links to videos, articles, papers, or AI chats you’ve worked through; it writes concepts into plain Markdown and connects them across media and languages into a knowledge network unique to you. On a schedule you set once (or whenever you ask), it prepares review cards from your own notes and surfaces connected new concepts tailored to what you already know—so what you absorb strengthens the judgment you bring back to real work with AI.

[Start in 5 minutes](#start-in-5-minutes) · [Today’s cards](Guides/First-Run.md#todays-cards) · [Explore in Obsidian](Guides/Graph-View.md)

![Two glowing infinity loops meeting at an illuminated neural brain representing Your Mind. On the left, after learning from videos, articles, papers, or AI chats, you share sources with your AI assistant to build a private knowledge network and generate daily cards for reviewing learned knowledge and exploring new concepts; ratings and questions return to revise both notes and cards. On the right, a stronger mind brings sharper framing, taste, and judgment to working with AI, while execution feeds new puzzles back into learning.](assets/demo/human-ai-loop.en.png)

## How it works

1. **Share what you studied**: Paste links to videos, articles, papers, or saved AI chats—or set up an optional scheduled task to sweep selected AI learning chats. Built-in readers fetch the text, and your assistant connects each concept into your Markdown notes and topic maps (MOCs).
2. **Open your daily bookmark.** Set a schedule once, or ask when you want to review. Your assistant makes review cards from your notes, adds a discovery card when it finds a useful connection, and publishes the deck at the same private address. Saving a rating updates the schedule for the current card version. Leave a question there and read the reply or revised card under **My comments and replies** after the assistant’s next run.
3. **Bring sharper judgment to real work with AI**: With more connected knowledge in mind, you frame clearer questions, spot shallow answers faster, and carry the puzzles you hit in real work straight into the next round of learning.

## Start in 5 minutes

Clone the repository and create a clean personal vault beside it—containing only the tools, English/Chinese prompts, and guides, with zero example clutter:

```sh
git clone https://github.com/beetlespike/My-Second-Brain.git
cd My-Second-Brain
python3 tools/workflow.py init ../My-Learning --empty
```

*(Requires Python 3.9+, or `py -3` on Windows. Web articles and local Markdown/text work out of the box; online video captions use `yt-dlp` and PDF text extraction uses `pdftotext`.)*

Open `../My-Learning` with your AI assistant and paste a link or file from **something you actually just studied**. After organizing a couple of sources, configure a daily card schedule once so you never think about card maintenance again—or say: *"Make a few review cards from my recent notes and open Today’s Cards."* Your assistant starts the vault’s local webpage and gives you one fixed bookmark to reuse every day (`Today.command` on macOS, `sh Today.command` on Linux, or `Today.cmd` on Windows simply starts that same local server if you want to open cards directly, such as after rebooting). If you only want to browse a populated showcase first, open the `examples/demo-vault/` folder from this download.

Notes are plain Markdown files on your computer using standard relative links, and your review history lives in a local SQLite database. Open the vault in any Markdown editor, or in Obsidian for its graph view. Codex, Cursor, and Antigravity read root `AGENTS.md`, and Claude Code imports it via `CLAUDE.md`. Scheduled chat-history sweeping depends on whether your host client exposes conversation history. When using a cloud model, the provider receives whatever your permissions and tools put into its context.

See the [First-use guide](Guides/First-Run.md#a-vault-of-your-own) to start your own vault, or check [Sources and tools](Guides/Sources-and-tools.md) and [Automation settings](Guides/Automation.md).

## A worked example: one week, two loops

I read in Obsidian and use Codex with a daily schedule to maintain my own vault, opening the vault’s fixed webpage whenever I review cards. Over one week I studied four serving pieces—[a six-minute Bilibili video on the KV cache](https://www.bilibili.com/video/BV1jAZwBGEwi/), the WeChat essay [《预训练工程师在干什么》 (“What Do Pretraining Engineers Do?”)](https://mp.weixin.qq.com/s/Wt_HyaK98tPF39p1y6eMow), the [*Sarathi-Serve*](https://www.usenix.org/conference/osdi24/presentation/agrawal) paper, and [an AI chat with GPT on stream timing](examples/demo-vault/assets/demo/streaming-dialogue.md) (a public rewrite with reset numbers)—plus [a tokenization lecture on YouTube](https://www.youtube.com/watch?v=zduSFxRajkE&t=1430s). My assistant pulled them through the built-in readers and connected those four serving sources into [the LLM serving map](examples/demo-vault/MOCs/Streaming%20LLM%20Serving.md), while the YouTube lecture fed [the tokenization map](examples/demo-vault/MOCs/Multilingual%20Tokenizers.md).

![Native Obsidian graph of LLM serving. Blue-gray nodes are concepts already studied. The three pale-gold nodes are concepts suggested to learn next.](assets/demo/obsidian-serving.png)

Along those links, my assistant spotted connected gaps I hadn’t studied yet and surfaced one as a discovery card alongside my morning review deck: [*prefill–decode disaggregation*](examples/demo-vault/待学概念/推理系统/Prefill-Decode%20Disaggregation.md#简答). Grasping that card’s tradeoff sharpens how you read [*DistServe*](examples/demo-vault/Papers/DistServe.md), and the next time you design a serving setup with AI, you already know what to ask back—starting with: once prefill and decode sit on separate GPU pools, which link actually carries the KV cache?

The screenshot shows the example vault’s card page in dark mode. Its cards use both English and Chinese, as mine do. You can write yours in the language you use for learning. Saving a rating updates your local review schedule, and earlier card versions keep their rating history. If you leave a question, your assistant can answer it, revise the card, or link a related card on its next run. You’ll find the result under **My comments and replies**.

<p align="center"><img src="assets/demo/today-cards.en.png" width="460" alt="Dark card page from the example vault. The expanded prefill–decode study card has three glossary buttons. Below it, the back of a review card explains a 65 ms token gap, with recall ratings and a comment box."></p>

[Peek at the example cards](Guides/First-Run.md#browsing-the-example-vault) · [Leave a comment on a review card](Guides/Flashcard-Review.en.md#feedback-and-saving)

![Full native Obsidian graph across LLM serving, multilingual tokenization, evaluation, and reinforcement learning.](assets/demo/obsidian-graph.png)

[More topic maps](examples/demo-vault/MOCs/Knowledge-Index.md) · [MIT license](LICENSE) · [Third-party materials](THIRD-PARTY.md) · [Feedback](https://github.com/beetlespike/My-Second-Brain/issues)
