# From Study Chats to Knowledge

[简体中文](对话笔记.md)

Within user-selected or authorized learning conversations, organize only the parts the user actually worked through or confirmed reading. Keep necessary questions, answers, corrections, and images, and record the exact message range covered; note unreadable sections as gaps.

Store distilled chat notes under `Chats/` with `type: chat`, `source_platform`, `source_url` (or vault-relative `source_path`), `status`, and `evidence_status`. When no stable link exists, store the authorized excerpt in the vault’s private `.local/` directory and set `source_path` to its actual vault-relative path—never invent unreachable URLs.

Organize prose by learning progression: what prompted the question, what objects and conditions apply, how the explanation works, and which example or correction shifted understanding. Distill lengthy AI explanations while marking verification status clearly.

Keep conversation claims, external source checks, and synthesized understanding distinct. Attribute positions to the user only when they explicitly stated or confirmed them; AI explanations alone do not establish personal mastery. Where an external paper or implementation backs up a step, record what it verifies.

Deduplicate by concept meaning and aliases, updating `Concepts/` and relevant `MOCs/`, and review updated pages to ensure they clearly answer the motivating question.

Keep incremental read cursors and follow-ups inside `.local/`. When history tools are unavailable, use saved excerpts or exports provided by the user—never scan unrelated folders, accounts, or private messages by default.
