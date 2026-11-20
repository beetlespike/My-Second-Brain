# Periodic organization and maintenance

[简体中文](自动整理与维护.md)

I set up a Codex automation to read the Codex and ChatGPT study conversations I choose. Codex uses the parts I’ve studied to update concept notes, build topic maps and suggest ideas that connect to what I already know. Source intake, daily cards, and public repository maintenance can run as separate tasks.

## Daily knowledge cards

Each vault has a private address. Open Today’s Cards once on the computer that holds the vault and bookmark it. Review, rate or comment whenever you like. Ratings count toward the review schedule as soon as you save them. Written comments appear as pending in **我的留言与回复** (“My comments and replies”). Your assistant handles them the next time it prepares cards. You can ask it to run sooner.

Choose an AI assistant that can read and write your vault and run local commands. Schedule the task below for a time that suits you. If the assistant has no scheduler, the computer’s scheduler can launch it. Run the task once during setup so the bookmark starts showing decks published by your assistant.

> Work in this vault using Prompts/每日复习.md. Start with outstanding comments. Answer the question, revise the card or add a related one, then leave me the result. Use what I’ve studied since to update review cards. When a new concept connects ideas in the vault, make a study card. Publish today’s cards at my private address.

The bookmark shows the previous deck until a new one is ready. If another local program takes the address, the launcher asks you to retry once it is free and keeps your bookmark. The assistant can retrieve the address with `today --no-open`. For browser-only practice, `daily --on-demand` switches back to selecting cards when you open the page. New vaults use the computer’s local date. Set `timezone` in `.secondbrain.json` if you want a fixed time zone while travelling.

I run the same task in a Codex automation and also receive interactive cards in the chat. Add `--chat-output <path>` when publishing to use both places. **提交到聊天保存** (“Send to chat to save”) and the browser’s **保存反馈** (“Save feedback”) write to the same records. [Card format](Flashcard-Review.md#新概念卡)

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
