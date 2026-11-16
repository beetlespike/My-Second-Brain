# First use

[简体中文](第一次使用.md)

Start with your own material or the included examples. Adapt these prompts as you go. If you already have concept notes, you can begin with a network review or card review.

## Organize a source

Open the same folder in Obsidian and Codex. Give Codex a link, text, PDF, transcript, or selected conversation, and describe your question:

> Follow AGENTS.md to organize this material. I want to understand… Add the relevant concepts to my existing network, keep the sources, and suggest a question worth studying next. Explain and write notes in English.

Open `MOCs/知识库入口.md` to follow the links between sources and concepts. A recurring concept can usually be added to its existing page. The assistant should report unread text, attachments, or images. See [sources and tools](Sources-and-tools.md) for reading options.

For a ready-made example, use `assets/demo/文章原文.md` and `assets/demo/教学字幕.vtt`. Both cover the sample mean, standard error, and sample size, so you can see how two sources share concepts.

## Choose something to study

Intake may already produce a study suggestion. You can also ask:

> Look for a missing explanation between these concepts. Suggest one supported topic I can start studying, and explain which existing ideas it connects.

The statistics example assumes independent sampling, so one follow-up is “What changes when observations are correlated?” Choose a study note that interests you and ask Codex to teach through an example, derivation, or discussion. A variation can help check your understanding. Point out any step that is unclear.

Your explanations and applications can support a record of learning; AI-generated answers cannot substitute for them. Once understood, a topic can join the main concept network, with incoming links updated and useful questions made into cards.

## Review and give feedback

> Follow Prompts/每日复习.md to prepare cards for these topics I have studied. Check the sources and give me a review page I can open in a browser.

Try recalling the answer before flipping the card. Choose a rating or write a question, then click “导出反馈文件” (export feedback file). Give the downloaded JSON to Codex to save. Feedback affects later reviews after a successful import; duplicate imports are detected.

A day's review set keeps its original content. Running it again opens the same set; later cards wait for a subsequent set. For a first trial, it helps to finish studying and creating cards before generating the review set. The [card guide](Flashcard-Review.md) contains the format and details.

## Adjust the setup

To start your own vault, ask Codex to initialize a separate empty folder beside the project. Copy the two sample sources if you want to use them there. Folder names, source types, and prompts can change to suit you; see the [tool guide](工具与扩展.md). Once the workflow suits you, consider [periodic organization](Automation.md).
