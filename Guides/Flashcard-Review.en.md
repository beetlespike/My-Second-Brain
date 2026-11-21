# Knowledge cards and explicit feedback

[简体中文](Flashcard-Review.md)

Cards ask you to recall an answer first, then check a concise explanation. Each card focuses on one concrete question. The short answer should stand on its own with the required symbols and conditions clearly stated; longer derivations or worked examples can live in the expandable detail section.

Review cards live under `Flashcards/` and must cite sources inside your active knowledge directories. A second kind of card—a study (discovery) card—comes from a note in `待学概念/` and introduces a missing concept connected to ideas you already know. Your learning status is governed by your own explanations, exercises or explicit confirmation.

## One review cycle

1. Your assistant runs `python3 .flashcards/review.py daily` and handles any outstanding written comments first. It can answer directly, revise the card or attach a related card, then record each resolution with `resolve --input -`.
2. Once pending comments reach zero, it runs `scan` to check added or modified sources, creates or updates cards, checks format, sources and eligibility with `audit`, and publishes the deck to your vault’s fixed private URL with `daily --publish` (optionally adding `--discovery <study-note>` to include one new-concept card).
3. At that private URL, you flip cards, rate recall or write questions. Saving in the browser writes directly back to your vault. Ratings feed the review schedule; written comments queue for the assistant’s next run (or you can ask it to handle them immediately). **My comments and replies** keeps the original question, the assistant’s reply and any revised card. If you receive cards in a scheduled Codex chat, the order and records are identical.

[Daily task prompt and resolution schema](../Prompts/每日复习.md)

By default each daily deck includes up to 10 review cards, at most 6 first-time (`new`) cards, and at most 2 per concept, plus one optional new-concept card. When no review cards are due or eligible, the tool skips saving a review snapshot. Re-running on the same day reuses the existing deck.

The three ratings—**Again** (`1` day), **Shaky** (`3` days) and **Familiar** (`14` days)—re-enter the candidate pool after those configurable fixed intervals (stored in `.secondbrain.json`; FSRS is not implemented yet, and learning gains under these intervals have not been empirically validated). Daily caps can push back when a due card actually appears. Without explicit feedback, cards only rotate and personal mastery stays unknown.

## New-concept cards

To include a study note in today’s deck, add a card section to that note. Card front and back prose can be written in English, Chinese or both, while keeping the required section headings `## 知识卡`, `### 正面` and `### 简答`.

```markdown
## 知识卡

### 正面

If every row in a dataset is duplicated once, how does the standard error of the sample mean change?

### 简答

Both the sum and the row count double on every draw, so the sampling distribution of the mean is unchanged and the standard error stays the same.
```

Run `python3 .flashcards/review.py daily --publish --discovery '待学概念/数理基础/Correlated Sampling.md'`. Open your private URL to view that card, expand its explanation and leave a comment—even on days with no due review cards. A new-concept card only collects written comments; viewing or commenting on it does not change familiarity scores.

## Card format and versioning

Each flashcard file uses `type: flashcard_set`. Separate cards with H2 (`##`) headings, followed immediately by a `<!-- card: {...} -->` comment holding `id`, `version`, `status`, `concept`, `topic` and `sources`. Place the prompt and short answer under `### 正面` and `### 简答`, with optional `### 展开` (details) and `### 来源` (clickable source links).

IDs take the form `sb-fc-0001` and stay stable across revisions. `status` is `active`, `paused` or `retired`. Each source entry stores a repo-relative `path`, an exact `heading` and that section’s `sha256`.

Read the source section first and verify that it supports the card, then compute its hash:

```sh
python3 .flashcards/review.py source-hash 'Concepts/数理基础/Standard Error.md' '定义与条件'
```

If a source section changes, disappears or stops having a unique heading, the card drops out of future decks until reviewed. Update the card text, source hash and increment `version`. Hashes only detect local text changes—they do not verify scientific correctness or remote upstream edits. `audit` checks card format, source hashes and eligibility, while modifying a registered card’s text or sources without bumping `version` is rejected when registering cards (for example during `session` or `daily --publish`).

You can use the same structure in an empty vault: pick a section in `Concepts/` you have already studied, write your own question and short answer, fetch the actual `source-hash` and assign an unused ID in `Flashcards/`.

```markdown
---
type: flashcard_set
status: active
---

# Correlated Sampling Review

## Duplicate observations

<!-- card: {"id":"sb-fc-0001","version":1,"status":"active","concept":"Correlated Sampling","topic":"Statistical Estimation","sources":[{"path":"Concepts/数理基础/Correlated Sampling.md","heading":"重复记录的计算","sha256":"replace-with-output-from-source-hash"}]} -->

### 正面

If each independent observation is duplicated three times, does the variance of the sample mean drop to one third?

### 简答

Let each of the $m$ original independent observations have variance $\sigma^2$. Duplicating every row multiplies both numerator and denominator by three, leaving the sample mean identical—so its variance remains $\sigma^2/m$. The extra rows are perfectly correlated with the originals; treating $3m$ rows as independent is what wrongly gives $\sigma^2/(3m)$.

### 展开

$\bar X=3\sum_iY_i/(3m)=\sum_iY_i/m$. The count of independent draws is still $m$; duplication only adds repeated records.

### 来源

[Duplicate-record calculation](../Concepts/数理基础/Correlated%20Sampling.md#重复记录的计算)
```

Run `python3 .flashcards/review.py audit` after writing a card to inspect `total`, `eligible`, `errors` and `needs_review`. If a newly written card shows `total: 0`, verify it lives under `Flashcards/` with `type: flashcard_set` and valid metadata. Never overwrite hashes to bypass review when a source needs checking.

In the example vault, graph concept filenames are in English while original card IDs are preserved; cards whose source paths changed have had their versions bumped. Historical decks keep the original wording and version, flagging if the source changed since. Feedback on an older version stays in history without directly rescheduling the newer version; retired cards keep their history. Revision previews do not create new decks or accept ratings.

## Feedback and saving

Feedback payloads bind strictly to the deck’s `workspace_id`, `session_date`, `card_id` and `version`, with natural-language notes matched against the original `position`. Batches are deduplicated by `batch_id` and rolled back atomically if any card ID or version is invalid. Feedback from one vault cannot be imported into another.

Drafts are kept locally in the browser as you flip or switch tabs, while saved ratings and notes live in the vault’s SQLite store. If you ever need a standalone offline HTML deck, run `session` and later import an exported JSON file with `feedback --input <file>`. Written questions are stored separately and never converted into ratings automatically. When correcting an error, verify the primary source first and update related guides or cards if a pattern recurs.

`daily` returns unresolved comments in pages of up to 20 (passing `--after <next_after>` to continue if more remain), including questions left on older card versions. A direct reply, a card revision or a linked follow-up card counts as a resolution, and related or revised cards can be expanded under the comment thread. A deck already published for today keeps its snapshot; inspect the last 20 notes anytime with `notes`.

`.flashcards/local/review.sqlite3` holds card versions, published decks, feedback and processed source hashes—treat it as personal data worth backing up. Generated HTML can always be rebuilt. Never copy `.flashcards/local/` when templating a new vault; back up and restore your database whole rather than mixing imports across vaults.
