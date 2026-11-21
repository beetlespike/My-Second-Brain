# Reading a source

[简体中文](来源与工具.md)

Paste a link into your AI assistant chat inside the vault. A phone’s share text can include the title along with the URL. The reader takes one URL at a time. To see what it found and where it saved the text, run this from the vault folder:

```sh
python3 tools/intake.py 'https://arxiv.org/abs/2309.06180'
```

| Source | What the reader does | Other ways in |
| --- | --- | --- |
| Bilibili and YouTube | Uses yt-dlp to read timed captions for one video. Platform captions and automatic captions are identified separately. With an existing local transcription setup, it can transcribe the public audio when captions are unavailable. | Use the publisher’s captions for the same video, an installed video reader, a transcript from an authorized browser, or SRT/VTT. Slides, descriptions and viewer comments are separate evidence. |
| WeChat and other articles | Reads the original WeChat article body or the article/main region of an ordinary page. Images require separate inspection. | If the original returns a challenge or a shell, use an authorized browser and supply its saved HTML or text. |
| X and X Articles | Reads public X Articles and main posts directly (preserving inline references and stripping share tracking query parameters). Embedded images and uncaptured replies require separate inspection. | For login-gated posts or multi-reply threads, read the page in an authorized browser and pass its saved HTML or text via `--from`. |
| Papers | Uses a configured local parse first. An arXiv abstract link tries the HTML, then the PDF at the same version. A PDF link tries the PDF first. It can follow a designated paper PDF from a publisher page. An abstract is labelled separately. | Supply existing MinerU or Docling Markdown, a PDF, or OCR from scanned pages. Check figures and important equations against the original. |
| Chats, books and practice | Reads selected Markdown or text files. | History access comes from the host. Markdown and plain-text chat exports, excerpts and lab notes work too. [Automation](Automation.md) |

The template includes the [reader](../tools/intake.py), the [intake prompt](../Prompts/intake.md), link checks, and review tools (see [Tools and extensions](Tools-and-Extensions.md) for all commands and settings). Your assistant uses the returned evidence to write the source note, check existing concepts, and explain links. Learning progress is recorded separately.

### Bring your own reader

```sh
python3 tools/intake.py lesson.vtt
python3 tools/intake.py 'https://arxiv.org/abs/2309.06180' --from paper/full.md
```

`--from` keeps the original URL while reading a file. Captions and text can use UTF-8 or UTF-16 with a byte-order mark (BOM). A parser export folder containing one Markdown file works too. For video, supply a publisher caption URL or a public course page containing the same video ID and a caption track. Use `--scope excerpt` or `--scope abstract` when that is all the supplied text covers.

To reuse an existing local file automatically, map the exact source URL in `.local/source-files.json`. Relative paths start at that configuration file. The optional map can point to a paper parse, saved captions or an article export.

```json
{"https://arxiv.org/abs/2309.06180": "parses/pagedattention/full.md"}
```

### Optional tools

Web pages and text files need only the Python 3.9+ standard library. Reading a PDF’s text layer uses Poppler’s `pdftotext`. For online video captions, the reader uses [yt-dlp](https://github.com/yt-dlp/yt-dlp#dependencies). To install it with pip as shown below, use Python 3.11 or later.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install yt-dlp
```

On Windows use `.venv\Scripts\python.exe`. The reader checks PATH, the current Python environment, the vault’s `.venv`, and an existing local video-note runtime.

For audio transcription, install [faster-whisper](https://github.com/SYSTRAN/faster-whisper) in that environment and supply local model weights. An existing installation works too. Select a model directory with `--asr-model`, or use `--no-asr` to try captions only. A previously cached small model can be detected automatically. Use `MSB_YTDLP`, `MSB_VIDEO_PYTHON` or `MSB_ASR_MODEL` to point to another installation. An authorized browser handles pages that require login.

### Read the result

`ready` means usable text was found. Check `evidence` for the kind of text. `partial` returns the material available so far. `needs_network` means the shell could not reach the source. The assistant should retry using the host’s network approval. `needs_material` identifies missing evidence. These three statuses return exit code 2. Your assistant tries available alternatives before asking for missing material. Text and receipts stay in `.local/imports/`. Repeat links reuse a cached result, and `--refresh` reads again. New vaults exclude this cache and personal review records.
