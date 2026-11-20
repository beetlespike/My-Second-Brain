# Periodic organization and maintenance

[简体中文](自动整理与维护.md)

I periodically go back through my Codex and ChatGPT conversations and save the parts I worked through. One discussion can leave me with several distinct concepts. After linking them to the rest of the network, I ask the assistant to look for questions my topic maps still leave open. Source intake, daily cards, and public repository maintenance can run as separate tasks.

## Daily knowledge cards

Run this in the example vault to get review cards and a card on a new concept. To use your own note, add a `## 知识卡` section with `### 正面` for the question and `### 简答` for the answer. You can write both in your own language. [Card format](Flashcard-Review.md#新概念卡)

```sh
python3 .flashcards/review.py session --discovery '待学概念/智能体与检索/Retrieval Context Budget.md'
```

With access to your local files, a scheduled task can run the command and send you the resulting `output` page path. You can also run it by hand. Omit the option for a review-only day. The page can also contain just the new concept when no review cards are due.

> Follow Prompts/每日复习.md to prepare today's cards. Use Prompts/回顾与补学.md to look for a missing concept with several meaningful links to existing nodes. Pick one supported study node that hasn't been sent before, add a knowledge card section if needed, and run session --discovery. Send me the output path and record the date and note path in .local/maintenance.md. Run session on days with only review cards. If neither kind of card is available, say so. Follow up on review questions in the original notes. Use my explanations or exercises to update progress on a study node.

## Check what your environment supports

My current desktop environment gives the AI assistant tools to list and read conversation history, so it can process authorized Codex and ChatGPT conversations incrementally. Those tools belong to the host application. This repository does not bundle a chat collector or guarantee the same interfaces in other clients.

Start with a small check:

> Inspect only the learning conversation I select. Which messages and attachments can you read? Can you retrieve earlier messages and write to this knowledge folder? Report the actual coverage, then suggest a recurring workflow.

| Available capabilities | A possible setup |
| --- | --- |
| Authorized history access and local file access | Schedule a pass over the parts you studied in selected conversations |
| Local file access only | Process exports or excerpts you place in a chosen folder |
| Web or mobile chat only | Generate notes for you to save; direct updates to a local vault require an additional file connection |
| Scheduling without history access | Review the network or organize material you've studied and supplied |

Local scheduled work generally needs the computer on, the app running, and the folder accessible. Web and desktop tasks may have different tools; check the [official scheduling guide](https://developers.openai.com/codex/app/automations/). ChatGPT [data export](https://help.openai.com/en/articles/7260999-exporting-your-chatgpt-history-and-data) is another possible source, subject to account and workspace availability. You need to refresh those exports yourself.

## A prompt to adapt

Try a manual run before choosing a schedule. Every few days is one starting point; adjust for the amount of material and cost.

> Resume where you left off and follow Prompts/整理材料.md for the parts I studied in the selected conversations or exports. Use my follow-up questions, explanations, exercises, or confirmation to tell what I covered. Keep sources and preserve my edits. Use Prompts/回顾与补学.md to find a missing concept that can connect several existing nodes. Write to the designated vault, check links and card sources, and track what you read and what still needs checking in .local/ alongside your source cache.

Specify the allowed conversations, projects, or files; the destination folder; the schedule; and the cost limits. The task should read actual messages. Titles and summaries can identify material to review but cannot substitute for it. A short `.local/maintenance.md` can record the position reached in each source, missing material, and the resulting notes.

After a few runs, read a concept note and see whether it explains something you worked out and has a meaningful link to another subject. Pick a study node and see whether each of its links to the existing concepts makes sense.

## Maintaining a public repository

I also run a task that checks public feedback on My Second Brain, reproduces problems, and compares the guides with the tools. Related fixes are prepared and verified locally before a purposeful update is committed. I decide changes to the project's direction, license, and main writing style.

If you publish your own template, you can adapt this:

> Periodically check the chosen repository's issues, PRs, and existing check results. Prioritize reproducible bugs and first-use problems. Prepare related changes locally and verify them together, then commit and publish within my authorization. Propose major design, compatibility, licensing, or cost changes for my decision. Preserve concurrent edits, keep test data in temporary folders, and leave private knowledge bases outside the task's scope.

The repository provides these approaches and prompts. Configure scheduled tasks in your own environment. Downloading the template does not create background tasks, read other accounts, or enable automatic publishing.
