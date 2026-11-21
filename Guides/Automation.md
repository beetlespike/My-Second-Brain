# Periodic organization and maintenance

[简体中文](自动整理与维护.md)

In my personal workflow, I run a Codex automation to read selected study conversations from Codex and ChatGPT and turn what I studied into concept updates, topic maps, and candidate study notes. Any local AI assistant paired with a scheduler (or your OS scheduler) can drive the same core vault workflow for browser cards and local files, while chat-history sweeping depends on whether your client exposes history.

## Daily knowledge cards

Each vault has a fixed private local browser address (`Today.command` / `Today.cmd`). Open Today’s Cards once on the computer holding the vault and bookmark it. Review, rate, or leave questions whenever you like. Clicking **Save** writes to your vault and updates review intervals immediately. Written comments stay under **My comments and replies** until your assistant resolves them on its next card run (or sooner if you ask it directly).

Any AI assistant that can read and write your vault and run local commands can run this daily task (or be triggered by your system scheduler). Run it once during setup so the fixed bookmark serves published decks:

> Work in this vault using `Prompts/每日复习.md`. Start with outstanding comments. Answer the question, revise the card or add a related one, then leave me the result. Use what I’ve studied since to update review cards. When a new concept connects ideas in the vault, make a study card. Publish today’s cards at my private address.

The bookmark keeps showing the previous deck until a new one is ready. If another local process holds the port, the launcher asks you to retry once free while preserving the same address. Your assistant can check the URL anytime with `today --no-open`. For on-demand local selection without an assistant publish, `daily --on-demand` switches back to picking cards when opened. Vaults use the machine’s local date unless `timezone` is set in `.secondbrain.json`.

Open browser cards on the computer that holds the vault. If your host client also supports embedded interactive card widgets in chat (as Codex desktop does), adding `--chat-output <path>` lets you mirror cards into chat, and **Send to chat to save** writes to the same SQLite records as browser **Save feedback**. [Card format](Flashcard-Review.en.md#new-concept-cards)

## Check what your environment supports

My personal setup uses a desktop client that exposes conversation lists and history tools inside its automation sandbox, allowing incremental sweeps of authorized Codex and ChatGPT chats. That history connector comes from the host application—this repository does not bundle a chat scraper and does not assume every client provides one.

Start with a small capability check in your own tool:

> Inspect only the learning conversation I select. Which messages and attachments can you read? Can you retrieve earlier messages and write to this knowledge folder? Report the actual coverage, then suggest a recurring workflow.

| Available capabilities | A possible setup |
| --- | --- |
| Authorized history access and local file access | Schedule an incremental pass over the parts you studied in selected conversations |
| Local file access only | Process exports or excerpts you drop into a chosen folder inside the vault |
| Web or mobile chat only | Generate candidate notes for manual copy-over; direct vault writes need local file access |
| Scheduling without history access | Review existing notes/cards or process sources you studied and supplied manually |

Desktop scheduled tasks accessing local vaults generally require the machine awake, the host running, and folder permissions active; check your client’s automation docs (for example, Codex’s [automations guide](https://developers.openai.com/codex/app/automations/)). Manually refreshed exports (such as a ChatGPT [data export](https://help.openai.com/en/articles/7260999-exporting-your-chatgpt-history-and-data)) also work well as regular local input.

## A prompt to adapt

Try a manual run before picking a cadence—every few days is a reasonable baseline, scaled by how much you study.

> Resume where you left off and follow `Prompts/整理材料.md` for the parts I studied in the selected conversations or exports. Use my follow-up questions, explanations, exercises, or confirmation to tell what I covered. Keep sources and preserve my edits. Use `Prompts/回顾与补学.md` to find a missing concept that can connect several existing nodes. Write to the designated vault, check links and card sources, and track what you read and what still needs checking in `.local/` alongside your source cache.

Always constrain the allowed conversations/folders, destination vault, cadence, and budget. Tasks should read real messages rather than titles or summaries. Keeping `.local/maintenance.md` lets each run pick up cleanly from the previous cursor.

After a few runs, spot-check one updated concept note and one suggested study note to confirm every link rests on a real explanation rather than vague similarity.

## Maintaining a public repository

If you publish your own public fork or template, separate repository maintenance (issues, PRs, guide-vs-tool consistency checks in temporary directories) from any private learning vaults, keep tests isolated, and review major compatibility, license, or style changes yourself. Downloading this template does not install background tasks, read external accounts, or push anything automatically.
