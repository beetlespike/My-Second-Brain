# Prepare Daily Knowledge Cards

[简体中文](每日复习.md)

Run these commands inside the authorized vault directory so the reader only needs to drop studied links and open one fixed private webpage URL. User ratings, comments, and assistant replies all live in the same vault.

1. **Read unresolved comments first.** Run `python3 .flashcards/review.py daily`. Under `feedback_pending`, read oldest comments first along with their card question, version, and sources (`pending_count` is the total backlog; pages return up to 20 items, using `daily --after <id>` when `next_after` is present). Recall ratings already update schedules automatically.
2. **Resolve each comment to a concrete outcome.** Compare the old card snapshot against the current card version and underlying source section. Answer directly if a clear explanation settles the question; clarify ambiguous prompts; fix inaccurate answers; or split out a focused follow-up card. Keep existing review card IDs, bump `version` after substantive edits, and verify sources (`source-hash`). For study (discovery) cards, edit the card section inside the study note (`Study-Queue/` or `待学概念/`). Use each comment to identify the reader’s question about that card; if source evidence is missing, leave that item pending while resolving everything else.
3. **Deliver resolutions visibly.** Pipe UTF-8 JSON to `python3 .flashcards/review.py resolve --input -` using the `workspace_id` and comment `id` from `daily`, for example:

```json
{"workspace_id":"<vault-id>","items":[{"id":12,"outcome":"revised","version":3,"reply":"Added link bandwidth to the prompt and listed prefill vs. transfer latencies on the back."}]}
```

   `answered` requires `reply`; `revised` targets the commented card (give the updated `version` for review cards, or verify edits on study notes); `linked` points to another verified review card’s `card_id`, `version`, and connection summary. Results appear under **My comments and replies** in the private webpage. Merely reading a comment does not mark it resolved.
4. **Create, update, audit, and publish.** Run `daily` again to confirm `ready_to_prepare`. Run `scan` to inspect newly studied or changed concepts under active `source_dirs`, revise affected cards, and create review cards from newly mastered notes (call `ack-sources` only after actually verifying source changes). Run `python3 .flashcards/review.py audit` to check formatting, sources, and eligibility (always bump `version` after changing registered card text or sources, verified on registration and publish). When one connected gap in `Study-Queue/` or `待学概念/` bridges recent reading well, pass `--discovery <study-note>` to `daily --publish`. `published` returns the vault’s fixed private webpage `url` (the previous deck stays accessible until publish completes; if new comments arrive mid-run, `feedback_pending` is returned—handle them and retry publish).

When the user simply wants to open or recover their fixed webpage bookmark, run `python3 .flashcards/review.py today --no-open`. Any browser save writes immediately to the local SQLite database and shows up in the comment list.

*(Optional host widget support: if a desktop chat host supports embedded interactive cards and the user enables `--chat-output <html-path>` on `daily --publish`, display the returned `fragment` and pass explicit chat submissions verbatim to `python3 .flashcards/review.py feedback --input -`, verifying `saved`, `duplicates`, and `historical_only`. Both interfaces share the same database.)*
