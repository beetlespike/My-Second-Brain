# Books, Courses, and Practice Logs

[简体中文](其他来源.md)

Start from the book chapters you read, courses you studied, and experiments you ran. Keep provenance in source notes, merge reusable mechanisms into `Concepts/`, and connect them to concrete questions.

## Books

When first organizing books, create a `Books/` folder using `type: book`. Record title, author, edition, and exact chapters or section headings (page numbers vary across printings). State reading scope if only selected sections were covered. Keep necessary citations, personal explanations, and verifiable locations; store full authorized source texts in `.local/`.

Include `source_url` or vault-relative `source_path`, `status`, and `evidence_status`, and register `"Books"` under `source_dirs` in `.secondbrain.json` so link checks and initialization include it. Concept explanations go in `Concepts/` linking back to the book note.

## Courses

Video courses can live in `Videos/` with course name, lecture number, and timestamps—or in a dedicated `Courses/` directory added to `source_dirs` alongside companion slides (`Videos/` keeps `type: video`). Make each lecture note readable on its own, using topic maps when multiple lectures answer one question.

## Practice Logs

For code experiments, benchmarks, or project retrospectives, create `Practice/` using `type: practice` and register it in `source_dirs`. Record the question, setup, inputs/conditions, observed outcomes, and explanation, pointing `source_path` to authorized local artifacts where helpful.

Keep plans, synthetic calculations, AI suggestions, and actual execution outputs clearly distinguished, preserving reproducible inputs for key numbers. Personal work records and third-party files remain private unless explicitly shared.

## Adding Other Source Types

Follow the same pattern—add a directory only when needed, choose a consistent `type`, maintain provenance and evidence status, and consolidate shared mechanisms in `Concepts/` to avoid duplication.

See [Tools and extensions](Tools-and-Extensions.md) for commands and `.secondbrain.json` settings.
