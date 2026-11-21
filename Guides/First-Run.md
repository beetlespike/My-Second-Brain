# First use

[简体中文](第一次使用.md)

## A vault of your own

Run this command from the cloned template directory to create a clean personal vault beside it—containing only the tools, English/Chinese prompts, and guides, with zero author examples to clear out:

```sh
python3 tools/workflow.py init ../My-Learning --empty
```

*(Requires Python 3.9+, or `py -3` in Windows PowerShell. Notes committed and pushed to a public fork are public too.)*

An `--empty` vault has bilingual map indexes (`MOCs/Knowledge-Index.md` and `MOCs/知识库入口.md`), starts with `0` example notes and `0` cards, and stays out of your way. Open it in any Markdown editor (Obsidian is optional if you want Graph View), and open the folder with any local AI assistant that can read/write files and run commands. Root `AGENTS.md` (with its Chinese mirror `AGENTS.zh.md`) holds the workspace rules; **Codex, Cursor, and Antigravity** read `AGENTS.md` directly, and **Claude Code** imports it via `CLAUDE.md`.

## Start with your own source

1. **Hand your assistant one source you actually just studied**: After finishing a video, article, paper, or helpful AI chat, paste the URL or saved file into your assistant inside the new vault—adding any timestamp range or angle you care about. Subtitles, plain text, and PDFs work too (online video captions use `yt-dlp`, PDFs use `pdftotext`, and web articles need only Python 3.9+).
2. **Keep the map honest**: Your assistant follows [the intake prompt](../Prompts/intake.md) to extract concepts into `Concepts/`, explain why concepts connect using standard relative Markdown links, and record the source under `Videos/`, `Articles/`, `Papers/`, or `Chats/`. Trim or correct anything you haven’t really understood yet so the vault remains a faithful map of *your* knowledge.
3. **Add a second source and let gaps surface**: As you feed in more pieces on related questions, your assistant connects shared concepts across sources, builds topic maps under `MOCs/`, and places connected candidate concepts you haven’t studied yet into `Study-Queue/` (or `待学概念/`). [Sources and readers](Sources-and-tools.md)

## Today's cards

You do **not** write card metadata or manage queues by hand. Your vault serves all daily cards and comments on **one fixed private local browser URL** (bookmark it once and reuse it every day):

1. **Set up a daily run.** Choose a time using the [automation guide](Automation.md). You can then just share links to things you’ve studied. Each run handles earlier questions, makes or updates review cards, and adds a personalized discovery card when the assistant finds a useful gap. Bookmark the private webpage it returns.
2. **Try on demand right now**: Before setting up automation, just tell your assistant inside the vault:
   > Make 2–3 review cards from the concepts I just added, check them, and open Today’s Cards.
   Your assistant prepares the cards, runs verification, starts the vault’s local web server, and prints your private browser URL.

While the local service is running, open the bookmark directly. To start the service yourself, for example after a reboot, launch `Today.command` on macOS, `sh Today.command` on Linux or `Today.cmd` on Windows. The launcher opens the same page.

The webpage lets you toggle **EN / 中文** in the header (or pass `?lang=en` / `?lang=zh`). Flip a review card to rate recall or write a question; clicking **Save** writes to the vault’s SQLite database and schedules intervals right away (ratings on older card versions stay in history). On a discovery card, expand the explanation and leave a comment underneath. Your assistant’s answers, card revisions, or linked follow-up cards appear under **My comments and replies**.

## Browsing the example vault

In the downloaded repository, open `examples/demo-vault/` in your editor or as an Obsidian vault. Start with `MOCs/Knowledge-Index.md`. To browse the sample cards, start the launcher at the **repository root**. The first deck selects six of the fifteen sample cards.

For the exact pair shown in the screenshot, run the following from the downloaded repository. It creates an independent copy, then publishes the TPOT review question alongside the *Prefill–Decode Disaggregation* study card. Open the private URL it prints. Run this before opening cards in that copy, because later visits on the same day keep its first review deck.

```sh
python3 tools/workflow.py init ../My-Demo
cd ../My-Demo
python3 .flashcards/review.py daily --publish --prefer-new sb-fc-0015 --discovery '待学概念/推理系统/Prefill-Decode Disaggregation.md'
```

[Automation](Automation.md) · [Card feedback](Flashcard-Review.en.md)
