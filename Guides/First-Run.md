# First use

[简体中文](第一次使用.md)

## A vault of your own

Run this from the downloaded template to create a separate folder with the tools and guides. Write personal notes in the new folder. Notes committed and pushed to a public fork are public too.

```sh
python3 tools/workflow.py init ../My-Learning --empty
```

I use Obsidian for reading and Codex for organizing material. You can use your own editor and an assistant with local file access. The template contains the full examples. The commands need Python 3.9 or later. In Windows PowerShell, use `py -3` in place of `python3`.

## Today's cards

Ask an assistant with local command access to open today’s cards, or launch `Today.command` on macOS or `Today.cmd` on Windows from your vault. On Linux, run `sh Today.command`. Bookmark the private address that opens. After restarting the computer, run the launcher again and the same bookmark will work.

Rate a review card or just leave a question. On a new-concept card, open the answer and leave a comment underneath. Saving writes directly to your vault. For fresh cards each day, give your assistant a [daily task](Automation.md). It works through earlier comments before writing cards and publishing the deck. Read its replies and inspect revised cards under **我的留言与回复** (“My comments and replies”). If you use Codex, you can also review and submit feedback in a scheduled chat.

## Start with a source

After watching a video or reading an article, give its URL to the assistant you use with this vault. It reads the material, extracts concepts and links them to relevant notes. Add a time range or comment if you like. A transcript, text file or PDF works too.

Use the same network for the next source. When several concepts help answer the same question, your assistant brings them together in a map of content (MOC). You can open the related notes from there. Another Markdown editor, local-file assistant or source reader works too. [Sources and readers](Sources-and-tools.md)

## Work through the serving example

In the full template, open `MOCs/Streaming LLM Serving.md` to explore the finished network. To build from the sources yourself, run the command below in the template folder and open the new directory.

```sh
python3 tools/workflow.py init ../My-Learning-Trial --demo
```

1. Pick a source from `assets/demo/serving-sources.md`. Watch or read the part that interests you, then give Codex the link. For an offline start, read `assets/demo/first-token.vtt` and give it that file. Follow a link from the source note to a concept.
2. Add a second source after you’ve studied it. If you started with the captions, try reading `assets/demo/streaming-dialogue.md`. Codex can link the conversation’s wait for the first token to prefill in the captions and build a topic map around that question.
3. Ask Codex to suggest a missing concept with links to several ideas already in your vault. The worked example suggests three, covering interference, service targets and splitting the stages. Try a card on one. When you can explain your reasoning, move the concept into the network and make a review question from it.
4. To follow up on splitting the stages, open *DistServe* from the source list. Read a section with the card’s question in mind, then give Codex the paper link and see what the new reading adds to your concept notes.

In the **full example vault**, ask the assistant to open today’s cards with *Prefill-Decode Disaggregation*. It can run the command below. When working from your own sources, use a study note from your vault.

```sh
python3 .flashcards/review.py daily --publish --prefer-new sb-fc-0015 --discovery '待学概念/推理系统/Prefill-Decode Disaggregation.md'
```

Leave a specific question on a card to see what changes. Once your assistant has handled it, visit the same address to read the reply. [Daily cards and automation](Automation.md) · [Card feedback](Flashcard-Review.md)
