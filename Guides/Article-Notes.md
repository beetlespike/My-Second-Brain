# From Articles to Knowledge

[简体中文](文章笔记.md)

When handed an article link, start by reading the full available article text. Incorporate any sections or thoughts the user highlighted. Record title, publication date, author, and original URL in frontmatter or citation metadata. Store article notes under `Articles/` using `type: article`, `status`, `evidence_status`, and `source_url` (or vault-relative `source_path`).

Keep key claims, supporting excerpts or figures, underlying mechanisms, and applicability boundaries clearly separated from your own synthesis. Inspect essential figures directly—never cite unread images or truncated text as verified support.

Connect reusable mechanisms to `Concepts/`, stating why each link holds beside the link, and fold refinements into existing synonymous pages. Referenced papers can stay cited inline; spin up a dedicated paper note only when a paper carries primary explanatory responsibility and verify its original text.

Use `status` (`draft`, `reading`, `distilled`) to track note preparation and `evidence_status` (`unchecked`, `partial`, `anchored`, `verified`) for source verification. Completing distillation does not mark personal mastery.

Keep raw fetched pages in private `.local/`, storing only necessary, authorized excerpts inside vault notes.
