# Tools and Extensions

[简体中文](工具与扩展.md)

Any AI assistant able to run local commands can execute these steps for you. Offline card review runs with Python 3.9+ and the bundled KaTeX library. Run commands from your vault root (in Windows PowerShell, replace `python3` with `py -3`).

## Common Commands

Create a clean empty learning vault beside the downloaded template:

```sh
python3 tools/workflow.py init ../My-Learning --empty
```

*(When initializing from the full template, `--demo` copies only raw demo sources, while omitting both flags copies the full showcase vault—keeping personal caches, review databases, `.obsidian`, and Git history excluded.)*

Check integrity and manage daily cards:

```sh
python3 tools/workflow.py check
python3 .flashcards/review.py audit
python3 .flashcards/review.py scan
python3 .flashcards/review.py today --no-open
python3 .flashcards/review.py daily
```

Opening `Today.command` (macOS), `sh Today.command` (Linux), or `Today.cmd` (Windows) starts the vault’s loopback (`127.0.0.1`) server and opens its fixed private webpage URL in your browser (only needed on your first visit or after a reboot if you aren’t opening cards through an assistant chat). `today --no-open` returns that same bookmark URL, and `today --stop` stops the background listener.

Daily card automation runs `daily` first to check unresolved comments, resolves each via `resolve --input -`, runs `scan` and `audit` after updating notes/cards, and publishes to the fixed URL with `daily --publish` (add `--discovery <study-note>` to include a study card; optionally add `--chat-output <html-path>` if a host chat supports embedded interactive widgets). See [Flashcard format](Flashcard-Review.en.md) and [Automation](Automation.md).

Browser saves write directly to SQLite. Use `session` to generate a standalone HTML deck. To save feedback from it, import the exported JSON with `feedback --input <file>`. Inspect the last 20 notes with `notes`, view past decks with `show --date YYYY-MM-DD`, or pass `--root <dir>` and `--state-dir <dir>` before subcommands.

`check` validates local Markdown links, wiki-link headings, frontmatter types, and source properties (verify remote pages and factual accuracy separately). `audit` checks card formatting, source hashes, and eligibility (`needs_review` flags changed sources until reviewed and version-bumped).

The downloaded framework keeps its sample in `examples/demo-vault/`. From the framework root you can check any standalone vault with `python3 tools/workflow.py --root <vault> check`, or audit its cards with `python3 .flashcards/review.py --root <vault> audit`. A newly initialized personal vault carries its own tools and stores its records locally. If an existing checkout already has review records for the sample, run the launcher once after updating to reuse that database and bookmark.

## Configuration (`.secondbrain.json`)

New vaults default to the machine’s local timezone (`"local"`). Set `"timezone": "Asia/Shanghai"` (or any IANA timezone) in `.secondbrain.json` to keep a fixed schedule while traveling (`tzdata` may be required in minimal Python setups).

`.secondbrain.json` also configures `daily_limit` (1–25), `new_limit` (0 to `daily_limit`), `concept_limit` (>= 1), `interval_days` (`again`, `uncertain`, `familiar`), and `source_dirs` (top-level studied knowledge directories checked recursively; never add `Study-Queue`, `待学概念`, or `Flashcards` to `source_dirs`). Use standard relative Markdown links such as `[Standard Error](../Concepts/Standard%20Error.md)` across all editors.

## Extending Sources & Connecting Existing Vaults

Use `tools/intake.py` ([Sources and tools](Sources-and-tools.md)) or bring your own reading scripts. To connect an existing Markdown vault, copy the program files from `.flashcards/` (leave its `local/` directory behind), plus the tools and prompts, register your top-level knowledge folders in `.secondbrain.json` (`source_dirs`), place cards in `Flashcards/` and discovery notes in `Study-Queue/` (or `待学概念/`), and keep `.local/` and `.flashcards/local/` ignored in Git. See [Other sources](Other-Sources.md) for books, courses, and practice logs.

*(Review uses fixed intervals; future FSRS experiments must preserve card IDs, versions, explicit feedback, and past deck snapshots.)*

## Running Tests

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s .flashcards -p 'test_*.py'
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tools -p 'test_*.py'
```

With Node.js, Playwright, and Chromium installed, run `node tools/test_chat_feedback.cjs` to test multi-draft saving, offline export, and deduplicated chat retries against an isolated temporary vault.
