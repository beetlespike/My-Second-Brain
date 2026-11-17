# My Second Brain

[简体中文](README.md) · English · [MIT](LICENSE)

Use Obsidian for your notes and Codex to work through the material with you. When a video, an article, or a conversation explains the same idea, add it to the same Markdown note. As those notes build up, Codex can look for an assumption they share and suggest what to study next.

## Try it with something of your own

On GitHub, choose **Code → Download ZIP**. Unzip it and open the same folder in Obsidian and Codex. Give Codex a transcript, an article, or a PDF, along with a question you want to answer.

> Read AGENTS.md first. Help me understand [your question]. Put reusable explanations in concept notes and keep the sources. Add to existing notes when they already cover the idea. If you find a question worth studying next, show me which notes led you to it.

You can also start with a short transcript and article included in the download and turn them into a review card. [First-use guide](Guides/First-Run.md)

## Explore the graph in Obsidian

Open Graph view in the example vault to browse seven groups of notes. Follow the evidence through [retrieval and generation](MOCs/检索与生成.md), check what went wrong with [model evaluation](MOCs/模型评测.md), and see how extra context affects waiting time in [inference serving](MOCs/推理系统.md).

Pale gold marks study topics suggested by the AI. In [comparing RAG under a latency budget](待学概念/模型评测/延迟预算下比较RAG.md), you can compare retrieval, answer quality, and time to the first output. Which setup would you choose given a limit on how long users can wait? [Graph view and colors](Guides/Graph-View.md)

## From standard error to correlated observations

A lesson transcript derives the variance of the mean of independent observations. An article explains why taking four times as many observations cuts the standard error of the mean in half. The derivation and the example go on one standard error page, with a link back to each source. Both materials are synthetic. [Video note](Videos/抽样次数与误差.md) · [Article note](Articles/重复抽样与标准误.md) · [Standard error](Concepts/数理基础/标准误.md)

Both sources assume independent observations. Ask Codex what changes when that assumption fails. It can suggest a lesson on correlated observations. Try the opening question yourself. If you copy every row of your data once, does the standard error of the mean get smaller? [Study note](待学概念/数理基础/相关抽样.md)

<details>
<summary>Reveal the answer</summary>

The sum and the number of rows both double, so the mean stays exactly the same. Its standard error across repeated samples stays the same too. Each copy is perfectly correlated with its original, so the formula for independent observations does not apply.

</details>

Ask Codex to change the example and wait for your reasoning. If you stop halfway through, leave the unresolved step on the study page. Once you understand it, link the concept back to standard error and make a review card. A question left during review can bring you back to the source note next time. [Walk through the example](MOCs/统计估计.md) · [Browse the other topics](MOCs/知识库入口.md)

## Use the tools you have

The notes are local Markdown. You can edit them by hand or use another assistant with file access. The review tool needs Python 3.9 or later and writes an HTML page you can open offline. Use your own tools for subtitles, web pages, or PDFs, or supply the text directly. Ask Codex for a blank folder if you want to start fresh, or to add a source type or change the review intervals. The sample notes and card interface are in Chinese. You can ask the assistant to write new notes in your language. [Sources and tools](Guides/Sources-and-tools.md) · [Commands and settings](Guides/工具与扩展.md)

I keep a personal vault for things I learn in different places, including conversations with ChatGPT and Codex. The same question keeps coming up in different sources. I gave each concept a page so I could add to it and pick up where I'd left off. I also review selected conversations periodically and look at what the notes still leave unexplained. Scheduled collection depends on which conversations your client can read and whether it can write to your local folder. [Periodic organization](Guides/Automation.md)

## Feedback and license

If you find a broken link, an unclear step, or a source you'd like to use, open an issue and describe what you tried. A public or synthetic example is enough to reproduce a problem. If the workflow fits the way you learn, a Star on GitHub is welcome. [Issues](https://github.com/beetlespike/My-Second-Brain/issues)

The project code, template, documentation, and examples are under the MIT License. Bundled components and materials you import retain their own licenses. Check note contents and attachments before sharing your own vault. [MIT License](LICENSE) · [Examples and third-party components](THIRD-PARTY.md)
