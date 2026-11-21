# First use

[简体中文](第一次使用.md)

## A vault of your own

Run this command from the downloaded template directory to create a clean personal vault beside it—with only the tools, prompts, and guides, and zero example notes to clear out (requires Python 3.9+, or `py -3` in Windows PowerShell). Notes committed and pushed to a public fork are public too.

```sh
python3 tools/workflow.py init ../My-Learning --empty
```

Your new vault has an index ready for your notes and starts with no example learning material or review cards. Open it in a Markdown editor and give your assistant access to read and write files and run local commands. The project rules live in `AGENTS.md`. Claude Code imports them through `CLAUDE.md`.

## Start with your own source

1. **Hand your assistant one source you just studied**: After finishing a video, article, paper, or helpful AI chat, paste the URL or saved file into your assistant inside the new vault—along with any timestamp range or angle you care about. Subtitles, plain text, and PDFs work too.
2. **Review what it writes against what you actually know**: Your assistant extracts concepts into `Concepts/`, notes why two ideas connect in plain prose with standard relative links, and records the source under `Videos/`, `Articles/`, `Papers/`, or `Chats/`. Trim or rewrite anything you haven’t really understood yet so the vault stays an honest map of your own knowledge.
3. **Add a second source and build a map**: As you feed in another piece on a related question, your assistant connects shared concepts across sources and gathers several linked notes into a topic map under `MOCs/`—or suggests one unrecorded concept under `待学概念/` when several notes stop just short of answering a question. [Sources and readers](Sources-and-tools.md)

## Today's cards

Once you have studied concepts in `Concepts/`, ask your assistant to create your first review cards under `Flashcards/`. Then open your vault’s fixed private local URL by running `Today.command` (macOS), `sh Today.command` (Linux), or `Today.cmd` (Windows) from your vault—or asking an assistant with local command access to open today’s cards. Bookmark that URL; restarting the launcher after a reboot keeps the same address working.

The card viewer lets you switch between **English** and **中文** in the header (or with `?lang=en` / `?lang=zh`). Flip a review card to rate recall or leave a question; clicking **Save** writes directly to your vault and enters recall ratings into the local schedule immediately (ratings on older card versions stay in history). On a new-concept card, expand the explanation and leave a comment underneath. For fresh cards automatically prepared each day, give your assistant a [daily task](Automation.md): it checks unresolved comments first and can answer, revise a card or attach a related one before publishing. Read the result under **My comments and replies** (中文界面为「我的留言与回复」). Host clients that support embedded card widgets can also render and submit cards right inside chat.

## Browsing the example vault

If you want to inspect a populated vault before starting your own, open the downloaded template repository directly—do not try to rebuild its sample notes from scratch:

- Open `MOCs/Streaming LLM Serving.md` in any Markdown editor (or explore the whole graph in Obsidian) to see how notes link across media and languages.
- To browse sample cards, launch `Today.command` on macOS, `sh Today.command` on Linux, or `Today.cmd` on Windows. The first deck selects six of the fifteen sample cards.
- For the exact pair in the screenshot, run the command below **before you first open cards in a fresh copy of the example**. It prints the private URL. Open that URL to see the study card above the TPOT review question. Later visits that day keep the same review deck.

```sh
python3 .flashcards/review.py daily --publish --prefer-new sb-fc-0015 --discovery '待学概念/推理系统/Prefill-Decode Disaggregation.md'
```

[Daily cards and automation](Automation.md) · [Card feedback](Flashcard-Review.en.md)
