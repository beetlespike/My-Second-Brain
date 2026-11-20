# Reading materials and choosing tools

[简体中文](来源与工具.md)

When organizing something you've studied, use your own explanation or question to point the assistant to the relevant part. It can check the source with the tools you already have. You can also provide the text, a transcript, or an existing conversion.

| Source | A starting point | Optional tools | What to keep |
| --- | --- | --- | --- |
| Bilibili, YouTube, and other videos | Provide a transcript with timestamps, or ask the assistant to check for one | [yt-dlp](https://github.com/yt-dlp/yt-dlp) can retrieve available subtitles; [Whisper](https://github.com/openai/whisper) can transcribe audio you have obtained | Original URL, timestamps, and whether text, audio, or images were actually read |
| Web pages, X, and WeChat articles | Use an authorized browser reader, paste the text, or save HTML | [Trafilatura](https://trafilatura.readthedocs.io/en/latest/) can extract text from ordinary pages or saved HTML | URL, author, date, and relevant passages; check important images separately |
| Papers, PDFs, and scans | Read the PDF directly or provide an existing conversion | [Docling](https://docling-project.github.io/docling/) or [MinerU](https://github.com/opendatalab/MinerU); consider OCR for scanned pages | Page, section, equation, and figure references; check important details against the PDF |
| Codex, ChatGPT, and other conversations | Select a conversation and use the host's history tools, or supply an export | See [automation and maintenance](Automation.md). ChatGPT also offers [data export](https://help.openai.com/en/articles/7260999-exporting-your-chatgpt-history-and-data), subject to account and workspace availability | Questions, follow-ups, corrections, and the message range read; private chat links can stay in your own vault |
| Books, courses, and practical work | Supply chapters, lecture notes, experimental results, or your own records | Reuse the PDF, video, and text tools, or organize the material manually | Edition, location, experimental conditions, and original results |

The repository does not bundle these extraction tools. Install or connect them as needed. Subtitle availability, login state, and page restrictions can limit what they read. Check technical terms in transcripts and formulas and figures in PDF conversions.

## What the repository provides

The repository includes prompts and two local tools. `tools/workflow.py` creates learning folders and checks links. `.flashcards/review.py` makes the daily page for reviews and new concepts and saves review feedback. Your environment supplies browsers, parsers, and history access. You can extract and link concepts yourself or ask an AI assistant to help.

To choose a setup, ask:

> I mainly work with videos, web articles, and papers. Check my existing tools and use this list to suggest the fewest additions I need. Reuse working tools and use a project-local environment for installations. Tell me before any login, payment, or transfer of source material to an external service. Keep the option to provide text or subtitles myself.

## Bringing another tool into the workflow

Readable Markdown, plain text, or VTT with source URLs and page references or timestamps can be used with the [material intake prompt](../Prompts/整理材料.md). Temporary originals can go in `.local/imports/`. Give the ideas you've learned their own concept notes and explain how they relate to other nodes in the vault.

You can write your own extractor or connect another service. Try one source first and check for missing text, broken formulas, and lost references before processing a batch. Use each tool's official documentation for current commands and installation requirements.
