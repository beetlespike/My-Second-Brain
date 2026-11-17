# First use

[简体中文](第一次使用.md)

Open the same folder as an Obsidian vault and a Codex project. Try it with your own material or use the two synthetic sources below. To start a blank vault, replace `--demo` with `--empty` in the command.

## Try it with two sources

Ask Codex to run this from the unzipped template folder, or run it yourself with Python 3.9 or later.

```sh
python3 tools/workflow.py init ../My-Learning-Trial --demo
```

Open the new `My-Learning-Trial` folder in Obsidian and Codex. It contains the transcript and article. You'll make the concept notes and cards as you go. If the folder already exists, choose a fresh name.

1. Give Codex `assets/demo/教学字幕.vtt`. Ask it to read AGENTS.md and explain why the sample mean varies less with more independent observations. Ask for a concept note with the derivation and timestamps. Open the resulting notes from the knowledge index.
2. Give it `assets/demo/文章原文.md`. Ask which ideas the article and transcript share. Ask it to add the article's explanation to the existing note and keep both sources. The standard error page should now have the transcript's derivation and the article's explanation of the two kinds of variation.
3. Ask what assumption the notes share and what you could study if it fails. Check that the suggestion points back to the relevant notes. With your own material, follow whichever connection interests you.

## Work through the question and make a card

Choose a suggestion and ask Codex to start with a worked example or a question. For this one, try asking it to wait for your reasoning on whether copying every observation changes the standard error. If you pause, save what you worked out and where you'd like to pick up on the study page.

Once you can explain it, or tell Codex you've learned it, it can move the concept into the main network and update the links. Then try reviewing it.

> Use Prompts/每日复习.md to make one card from what we studied. Check the source and give me the review page to open in a browser. Write the question and answer in English and keep the card format described in the guide.

Try recalling your answer and click “翻到背面” (flip). Choose a rating or add a question under “补充反馈或指出问题” (add feedback or flag a problem). Click “导出反馈文件” (export feedback file) and give the JSON to Codex to import. After it confirms a successful save, you can ask Codex to retrieve the card question, your note, and its source next time. A day's review set stays fixed. Cards added later appear in a subsequent set. [Card format and feedback](Flashcard-Review.md)

## Use your own material

Replace the sample transcript and article with something you've watched or read. Start with the question you want to answer. If you already have notes, you can begin with a network review or card review. Relative Markdown links work with other editors, and assistants with file access can follow the same guides. You can add source types and adjust your review intervals.

[Reading tools](Sources-and-tools.md) · [Commands and settings](工具与扩展.md) · [Periodic organization](Automation.md)
