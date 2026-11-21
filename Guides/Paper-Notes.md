# From Papers to Knowledge

[简体中文](论文笔记.md)

When handed a paper link, inspect any existing local parse or read the accessible full text—focusing first on sections or derivations the user specified. Track separately what the abstract, body text, and figures actually cover. Markdown exports from MinerU, Docling, or similar tools work well when page numbers, section titles, and figure/table positions are preserved.

Save paper notes under `Papers/` using `type: paper`, `paper_note_kind: full` or `card`, `source_url` (or vault-relative `source_path`), `status`, and `evidence_status`. Ensure title, authors, publication date, and official link stay verifiable.

Explain each method’s inputs, operations, outputs, and boundary conditions around a concrete problem. Anchor key claims to exact Section, Figure, Table, Equation, or page references. Cross-check equations, experimental numbers, and plots against the original; mark unresolved parse questions explicitly rather than guessing (a clean PDF conversion does not prove mathematical correctness).

If only an abstract or secondary overview was read, record what was actually covered and list verification questions to revisit once the full paper is available.

Place general mechanisms in `Concepts/`, reserving paper-specific assumptions, experimental setups, and caveats inside the paper note. Cross-paper comparisons around one question belong in `MOCs/`.

Synthetic practice reports included for offline testing must remain clearly labeled as synthetic samples with zero real publication claims. Never promote private manuscripts or unpublished research into public examples automatically.
