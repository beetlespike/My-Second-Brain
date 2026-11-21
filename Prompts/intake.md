# Organize Studied Material

[简体中文](整理材料.md)

When a chat message in this vault contains only a URL, share text with a link, or a local file, organize it right away. Start by running `python3 tools/intake.py <url-or-file>` from the vault root and open the returned `material`. Extract concepts strictly from what was actually read, prioritizing any timestamp range, section, or thought the user gave.

If `intake.py` returns `needs_network`, request single-target read-only network access through your host environment’s approval mechanism, re-run the exact same command, and continue based on what loads. If it returns `partial`, note what part was covered and look for sources that complete it. If it returns `needs_material`, check accessible content from an authorized browser tab, publisher captions for the same episode, or an existing parser output using `--from`. Only ask the user for the minimum missing text when gaps remain, keeping captions, visuals, and handouts clearly distinguished.

Check existing concepts by meaning and aliases before creating new pages. When a synonymous concept already exists, add new explanations, examples, or applicability conditions to that page. Give each newly introduced concept a self-contained note in `Concepts/`. Keep a concise source note under `Papers/`, `Articles/`, `Videos/`, or `Chats/` linking to each extracted concept.

Read each new concept alongside existing concepts in the vault. Where does one step rely on a familiar method? Which earlier conclusion shifts under a new condition? Write that reasoning directly in prose and add a standard relative Markdown link (`[Concept Name](../Concepts/...md)`) right on that phrase—only link where you can state why the connection holds.

Standard relative Markdown links work directly across all editors and let graph views such as Obsidian draw edges between notes. Add backlinks on older pages where readers coming from that direction need the new example. When several concepts together answer one larger question, gather them in the relevant map of content under `MOCs/` (creating a new map only when no existing map covers that question; one concept can belong to multiple maps).

Preserve the user’s handwritten notes and corrections, check links, and audit any affected flashcards. If several existing nodes together reveal a missing bridging concept worth learning, assess it with [Discover missing nodes](discover-concepts.md) and place valid candidates in `Study-Queue/` (or `待学概念/`). Summarize what concepts were added or updated, how they connect to older notes, and any unreadable source gaps. Sending a link never marks a concept as mastered on its own.
