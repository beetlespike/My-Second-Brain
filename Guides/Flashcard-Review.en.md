# Knowledge cards and explicit feedback

[简体中文](Flashcard-Review.md)

Cards ask you to recall an answer first, then check a concise explanation. Each card focuses on one concrete question. The short answer should stand on its own with the required symbols and conditions clearly stated; longer derivations or worked examples can live in the expandable detail section.

Review cards live under `Flashcards/` and must cite sources inside your active knowledge directories. A second kind of card—a study (discovery) card—comes from a note in `Study-Queue/` (the bundled example and some older vaults use `待学概念/`) and introduces a missing concept connected to ideas you already know. Your learning status is governed by your own explanations, exercises, or explicit confirmation.

## One review cycle

1. Your assistant runs `python3 .flashcards/review.py daily` and handles any outstanding written comments first. It can answer directly, revise the card, or attach a related card, then record each resolution with `resolve --input -`.
2. Once pending comments reach zero, it runs `scan` to check added or modified sources, creates or updates cards from studied concepts, checks format, sources, and eligibility with `audit`, and publishes the deck to your vault’s fixed private webpage URL with `daily --publish` (optionally adding `--discovery <study-note>` to include one new-concept card).
3. Open your private bookmark to flip cards and rate your recall. Tap a key term for its definition. Beside each source, you can copy its path, open it in Obsidian, or read an excerpt when one is available. To ask a question, type it or start with a shortcut such as **Example unclear**, then click **Save**. Ratings update the schedule. Your assistant handles comments on its next run, or when you ask. **My comments and replies** shows the original question, your comment, the reply, and any revised or linked card. It shows the card author if the issue recorded one and renders formulas in questions and replies offline. Interactive `--chat-output` cards in a supported chat use the same database.

[Daily task prompt and resolution schema](../Prompts/daily-review.md)

By default each daily deck includes up to 10 review cards, at most 6 first-time (`new`) cards, and at most 2 per concept, plus one optional new-concept card. When no review cards are due or eligible, the tool skips saving a review snapshot. Re-running on the same day reuses the existing deck.

The three ratings—**Again** (`1` day), **Shaky** (`3` days), and **Familiar** (`14` days)—re-enter the candidate pool after those configurable fixed intervals (stored in `.secondbrain.json`; FSRS is not implemented yet, and learning gains under these intervals have not been empirically validated). Daily caps can push back when a due card actually appears. Without explicit feedback, cards only rotate and personal mastery stays unknown.

## Past issues and editing today’s rating

The private webpage shows **Past ▾** once it has archived decks from two different dates. Choose a date to see the cards in the order and wording last delivered that day. Source links open the current notes. You can leave comments on past cards and use **Back to today** to return to the current deck.

On an active review card in today’s issue, you can save a comment and rate it later. To revise a saved rating, select **Change rating**, choose a rating and save. If another tab saved a rating after you started, the page shows the latest rating and clears your conflicting choice. Your comment and drafts on other cards remain available to submit.

Past issues accept comments only (`past_issue`). Ratings also lock when the current card differs from the snapshot (`superseded`), when the card is unavailable, paused, retired or awaiting a source check (`inactive`), or when the same version already has a rating from a newer issue (`rated_newer_issue`) or a different issue rated today (`rated_other_today`).

## New-concept cards

To include a study note in today’s deck, save the section below as `Study-Queue/Correlated Sampling.md` in a new vault. You can write prose in English, Chinese, or both, using English headings (`## Study Card` / `### Front` / `### Short Answer`) or Chinese headings (`## 知识卡` / `### 正面` / `### 简答`):

```markdown
## Study Card

### Front

If every row in a dataset is duplicated once, how does the standard error of the sample mean change?

### Short Answer

Both the sum and the row count double on every draw, so the sampling distribution of the mean is unchanged and the standard error stays the same.
```

For a study or review card, you can add two or three prerequisite terms under `### Key Terms` or `### 相关概念`. Write one bullet like `- Term: short definition` per term. Readers can open the definitions on the question side.

Run `python3 .flashcards/review.py daily --publish --discovery 'Study-Queue/Correlated Sampling.md'` (the bundled example uses `待学概念/数理基础/Correlated Sampling.md`). Open your private bookmark to view the card, expand its explanation and leave a comment, even on days with no due review cards. A new-concept card accepts written comments only. Viewing or commenting on it leaves familiarity scores unchanged.

## Card format and versioning

*(When you use a daily schedule or ask your assistant to create cards from notes you studied, your assistant writes and verifies this format for you.)*

Each flashcard file uses `type: flashcard_set`. Separate cards with H2 (`##`) headings, followed immediately by a `<!-- card: {...} -->` comment with `id`, `version`, `status`, `concept`, `topic` and `sources`. You can also include an `author`. To supply a `glossary`, use either the metadata or the key terms section. Use English headings (`### Front`, `### Short Answer`, optional `### Details`, `### Sources`, and `### Key Terms`) or Chinese headings (`### 正面`, `### 简答`, `### 展开`, `### 来源`, and `### 相关概念`), without mixing structural heading languages on the same card.

IDs take the form `sb-fc-0001` and stay stable across revisions. `status` is `active`, `paused`, or `retired`. Each source entry stores a vault-relative `path`, an exact `heading`, and that section’s `sha256`.

The bundled example includes a note on standard error. From the downloaded repository or a full example copy, you can hash its “定义与条件” (definition and conditions) section with this command.

```sh
python3 .flashcards/review.py source-hash 'Concepts/数理基础/Standard Error.md' '定义与条件'
```

To try the card below in an empty personal vault, first save the following source note as `Concepts/Correlated Sampling.md`.

```markdown
---
type: concept
status: active
---

# Correlated Sampling

## Duplicate-record calculation

Suppose the original observations are independent and each has variance σ².
With m observations, the sample mean has variance σ²/m. If every row appears
three times, the sum and the count both triple. The mean stays the same on
every draw, so its sampling variance is still σ²/m.
```

Read the section and check that it supports your card. Run this command from the personal vault to get the hash for the card’s `sha256` field.

```sh
python3 .flashcards/review.py source-hash 'Concepts/Correlated Sampling.md' 'Duplicate-record calculation'
```

If a source section changes, disappears or loses its unique heading, the card drops out of future decks until reviewed. Check the section, update the citation and revise the card as needed. Bump `version` when changing a registered card’s question, short answer, details, concept, topic or sources. Edits limited to the glossary or `author` preserve the card hash and review schedule. `audit` checks format, source hashes and eligibility. Registration (for example, during `session` or `daily --publish`) checks the version. Source hashes detect local text changes. Confirm the underlying claim against the source itself.

Save the card in `Flashcards/Correlated Sampling.md` with the hash you just computed. Your assistant can do both steps for you.

```markdown
---
type: flashcard_set
status: active
---

# Correlated Sampling Review

## Duplicate observations

<!-- card: {"id":"sb-fc-0001","version":1,"status":"active","concept":"Correlated Sampling","topic":"Statistical Estimation","sources":[{"path":"Concepts/Correlated Sampling.md","heading":"Duplicate-record calculation","sha256":"replace-with-output-from-source-hash"}]} -->

### Front

If each independent observation appears three times, does the variance of the sample mean drop to one third?

### Short Answer

Let each of the $m$ original independent observations have variance $\sigma^2$. Duplicating every row multiplies both numerator and denominator by three, leaving the sample mean identical—so its variance remains $\sigma^2/m$. The extra rows are perfectly correlated with the originals; treating $3m$ rows as independent is what wrongly gives $\sigma^2/(3m)$.

### Details

$\bar X=3\sum_iY_i/(3m)=\sum_iY_i/m$. The count of independent draws is still $m$; duplication only adds repeated records.

### Sources

[Duplicate-record calculation](../Concepts/Correlated%20Sampling.md)
```

Run `python3 .flashcards/review.py audit` after writing a card to inspect `total`, `eligible`, `errors`, and `needs_review`. If a newly written card shows `total: 0`, verify it lives under `Flashcards/` with `type: flashcard_set` and valid metadata. Never overwrite hashes to bypass review when a source needs checking.

Historical decks keep the original wording and version, flagging if the source changed since. Feedback on an older version stays in history without directly rescheduling the newer version; retired cards keep their history. Revision previews do not create new decks or accept ratings.

## Feedback and saving

Feedback identifies the deck and card by `workspace_id`, `session_date`, `card_id` and `version`. The tool checks `position` when supplied and deduplicates retries by `batch_id` and card ID. On the private webpage, a rating also carries `expected_rating_sequence`, the sequence shown when you started editing, or `null` for a first rating. If that value is stale, the server returns `409 Conflict` and rejects the whole batch. An invalid card ID or version also rolls back the batch. Feedback belongs to the vault that issued the deck.

The private webpage keeps drafts in your browser for the same vault, issue, card and version as you flip or switch tabs, while saved ratings and notes live in the vault’s SQLite store. If you ever need a standalone offline HTML deck, run `session` and later import an exported JSON file with `feedback --input <file>`. Written questions are stored separately and never converted into ratings automatically. When correcting an error, verify the primary source first and update related guides or cards if a pattern recurs.

`daily` returns unresolved comments in pages of up to 20 (passing `--after <next_after>` to continue if more remain), including questions left on older card versions or past issues. A direct reply, a card revision, or a linked follow-up card counts as a resolution, and related or revised cards can be expanded under the comment thread. Use `notes` to inspect the latest 20 written comments.

`.flashcards/local/review.sqlite3` holds card versions, published decks, feedback, and processed source hashes—treat it as personal data worth backing up. Generated HTML can always be rebuilt. Never copy `.flashcards/local/` when templating a new vault; back up and restore your database whole rather than mixing imports across vaults.
