# Prepare Daily Knowledge Cards

[简体中文](每日复习.md)

Run these commands inside the authorized vault directory so the reader only needs to drop studied links and open one fixed private webpage URL. User ratings, comments, and assistant replies all live in the same vault.

1. **Read unresolved comments first.** Run `python3 .flashcards/review.py daily`. When `status` is `feedback_pending`, read `items` in order, oldest first. Each item identifies the issue date (`session_date`), card ID and version and provides the original question, answer and sources when available. `pending_count` is the total backlog. A page holds up to 20 items. If `next_after` is present, pass that value to `daily --after <id>`.
2. **Resolve each comment to a concrete outcome.** Compare the issued card with the current card and its source. Answer the question, revise the card, or write a focused follow-up. Replies can include inline `$...$` and display `$$...$$` formulas. Keep review card IDs stable. After changing the question, answer, details, concept, topic or sources, increment `version` and verify the sources (`source-hash`). Glossary and `author` edits alone preserve the version. For a discovery card, edit the card section in its study note (`Study-Queue/` or `待学概念/`). Treat each comment as feedback about the card. If evidence is missing, leave the comment pending and resolve the others.
3. **Deliver resolutions visibly.** Pipe UTF-8 JSON to `python3 .flashcards/review.py resolve --input -` using the `workspace_id` and comment `id` from `daily`, for example:

```json
{"workspace_id":"<vault-id>","items":[{"id":12,"outcome":"revised","version":3,"reply":"Added link bandwidth to the prompt and listed prefill vs. transfer latencies on the back."}]}
```

   Give every outcome a `reply` that the reader can use. For `answered`, that completes the resolution. For `revised`, provide the revised review card’s `version`, or update the discovery card’s question or short answer in the study note. For `linked`, include the related review card’s `card_id` and `version` and explain the connection in your reply. The reader sees the result under **My comments and replies**.
4. **Create, update, audit, and publish.** Run `daily` again to confirm `ready_to_prepare`. Run `scan` to inspect newly studied or changed concepts under active `source_dirs`, revise affected cards, and create review cards from concepts the reader has studied (call `ack-sources` only after actually verifying source changes). Where prerequisite terminology might trip up recall, you can include 2–3 short `- Term: concise explanation` bullets under `### Key Terms` or `### 相关概念`. Run `python3 .flashcards/review.py audit` to check formatting, sources, and eligibility. When one connected gap in `Study-Queue/` or `待学概念/` bridges recent reading well, pass `--discovery <study-note>` to `daily --publish`. On success, `status` is `published` and `url` is the vault’s fixed private address. The previous deck stays available during preparation. If a new comment arrives, publication returns `feedback_pending`. Resolve it and retry.

When the user simply wants to open or recover their fixed webpage bookmark, run `python3 .flashcards/review.py today --no-open`. Browser saves write to local SQLite. Written comments appear in the pending list.

*(Optional host widget support: if a desktop chat host supports embedded interactive cards and the user enables `--chat-output <html-path>` on `daily --publish`, display the returned `fragment` and pass explicit chat submissions verbatim to `python3 .flashcards/review.py feedback --input -`, verifying `saved`, `duplicates`, and `historical_only`. Both interfaces share the same database.)*
