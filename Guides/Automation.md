# Periodic organization and maintenance

[简体中文](自动整理与维护.md)

In my personal vault, I periodically organize authorized learning conversations from Codex and ChatGPT. Explanations, follow-up questions, and corrections go into the concept network, which I then review for topics to study. I use a separate task to maintain this public repository. The two tasks have different sources and write to different places.

## Check what your environment supports

My current desktop environment gives the AI assistant tools to list and read conversation history, so it can process authorized Codex and ChatGPT conversations incrementally. Those tools belong to the host application. This repository does not bundle a chat collector or guarantee the same interfaces in other clients.

Start with a small check:

> Inspect only the learning conversation I select. Which messages and attachments can you read? Can you retrieve earlier messages and write to this knowledge folder? Report the actual coverage, then suggest a recurring workflow.

| Available capabilities | A possible setup |
| --- | --- |
| Authorized history access and local file access | Schedule incremental processing of selected conversations or learning projects |
| Local file access only | Process exports or excerpts you place in a chosen folder |
| Web or mobile chat only | Generate notes for you to save; direct updates to a local vault require an additional file connection |
| Scheduling without history access | Review the existing network or process new materials you supply |

Local scheduled work generally needs the computer on, the app running, and the folder accessible. Web and desktop tasks may have different tools; check the [official scheduling guide](https://developers.openai.com/codex/app/automations/). ChatGPT [data export](https://help.openai.com/en/articles/7260999-exporting-your-chatgpt-history-and-data) is another possible source, subject to account and workspace availability. You need to refresh those exports yourself.

## A prompt to adapt

Try a manual run before choosing a schedule. Every few days is one starting point; adjust for the amount of material and cost.

> Periodically organize the learning conversations or export folder I select. Write only to the designated knowledge folder. Continue from the last processed position, keeping questions, follow-ups, corrections, and sources. Update existing concepts where appropriate. Look for a missing prerequisite or method shared by related concepts and write a supported study note; wait for my choice before teaching it. Record unread messages and attachments, preserve my edits, and check links and card sources. Keep original caches and processing records in .local/. Do not publish private content.

Specify the allowed conversations, projects, or files; the destination folder; the schedule; and the cost limits. The task should read actual messages. Titles and summaries can identify material to review but cannot substitute for it. A short `.local/maintenance.md` can record the position reached in each source, missing material, and the resulting notes.

Automation can organize content and suggest topics. Answers during a lesson, exercise results, and review feedback still come from you. After a few runs, check for duplicate concepts, accurate sources, and suggestions you actually want to study.

## Maintaining a public repository

I also run a task that checks public feedback on My Second Brain, reproduces problems, and compares the guides with the tools. Related fixes are prepared and verified locally before a purposeful update is committed. I decide changes to the project's direction, license, and main writing style.

If you publish your own template, you can adapt this:

> Periodically check the chosen repository's issues, PRs, and existing check results. Prioritize reproducible bugs and first-use problems. Prepare related changes locally and verify them together, then commit and publish within my authorization. Propose major design, compatibility, licensing, or cost changes for my decision. Preserve concurrent edits, keep test data in temporary folders, and leave private knowledge bases outside the task's scope.

The repository provides these approaches and prompts. Configure scheduled tasks in your own environment. Downloading the template does not create background tasks, read other accounts, or enable automatic publishing.
