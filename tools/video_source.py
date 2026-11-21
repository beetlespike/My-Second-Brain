"""Read one video with yt-dlp, optionally transcribing its audio with a local model."""

import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

from source_text import Material, NetworkUnavailable, ReadError, caption_material, stamp


def shared_runtimes():
    if os.environ.get("VIDEO_NOTE_CACHE_DIR"):
        return (Path(os.environ["VIDEO_NOTE_CACHE_DIR"]).expanduser(),)
    cache = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
    return (cache / "my-second-brain/video-note", cache / "codex/video-note")


def runtime_bin(root):
    return root / ("Scripts" if os.name == "nt" else "bin")


def available_model():
    """Find installed small-model weights for local transcription."""
    if os.environ.get("MSB_ASR_MODEL"):
        return Path(os.environ["MSB_ASR_MODEL"]).expanduser()
    hf_home = Path(
        os.environ.get("HF_HOME")
        or Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "huggingface"
    )
    hubs = [
        Path(os.environ.get("HF_HUB_CACHE") or hf_home / "hub"),
        *(runtime / "hf/hub" for runtime in shared_runtimes()),
    ]
    for hub in hubs:
        snapshots = hub / "models--Systran--faster-whisper-small/snapshots"
        for model in sorted(snapshots.glob("*")):
            if all((model / n).is_file() for n in ("model.bin", "config.json", "tokenizer.json")):
                return model
    return None


def asr_python():
    if importlib.util.find_spec("faster_whisper"):
        return sys.executable
    name = "python.exe" if os.name == "nt" else "python"
    candidates = [
        os.environ.get("MSB_VIDEO_PYTHON"),
        runtime_bin(Path(__file__).resolve().parents[1] / ".venv") / name,
        *(runtime_bin(runtime / "venv") / name for runtime in shared_runtimes()),
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            check = subprocess.run(
                [
                    str(candidate),
                    "-c",
                    "import importlib.util,sys;sys.exit(importlib.util.find_spec('faster_whisper') is None)",
                ],
                capture_output=True,
                timeout=10,
            )
            if check.returncode == 0:
                return str(candidate)
    return None


def yt_dlp():
    name = os.environ.get("MSB_YTDLP", "yt-dlp")
    exe = shutil.which(name)
    if not exe and name == "yt-dlp":
        binary = "yt-dlp.exe" if os.name == "nt" else "yt-dlp"
        folders = [
            Path(os.environ.get("MSB_VIDEO_PYTHON") or sys.executable).expanduser().parent,
            Path(sys.executable).parent,
            runtime_bin(Path(__file__).resolve().parents[1] / ".venv"),
            *(runtime_bin(runtime / "venv") for runtime in shared_runtimes()),
        ]
        for folder in folders:
            exe = shutil.which(str(folder / binary))
            if exe:
                break
    if not exe:
        raise ReadError("视频字幕需要 yt-dlp。也可从发布方或已授权的浏览器取得字幕，再用 --from 交给读取器。")
    return exe


def run_ytdlp(exe, args, work, timeout):
    result = subprocess.run(
        [
            exe,
            "--ignore-config",
            "--no-cache-dir",
            "--no-playlist",
            "--quiet",
            "--no-warnings",
            "--socket-timeout",
            "12",
            "--retries",
            "1",
            "--extractor-retries",
            "1",
            "--fragment-retries",
            "1",
            *args,
        ],
        cwd=work,
        capture_output=True,
        text=True,
        errors="replace",
        timeout=timeout,
    )
    if result.returncode:
        if re.search(
            r"could not resolve|failed to resolve|name resolution|nodename nor servname|"
            r"name or service not known|getaddrinfo failed|network is unreachable|"
            r"failed to establish a new connection.*operation not permitted",
            result.stderr,
            re.I | re.S,
        ):
            raise NetworkUnavailable("视频读取工具无法联网或解析原站。请通过宿主的联网审批重试同一读取命令。")
        status = re.search(r"HTTP Error \d+", result.stderr)
        raise ReadError("yt-dlp 读取失败" + (f"（{status[0]}）" if status else "。"))
    return result.stdout


def tracks(info, platform, language):
    preferred = [language] if language else [info.get("language"), "zh" if platform == "bilibili" else "en"]
    preferred = [p.lower() for p in preferred if p]
    for field in ("subtitles", "automatic_captions"):
        langs = []
        for lang, formats in (info.get(field) or {}).items():
            if lang in ("danmaku", "live_chat") or not formats:
                continue
            if field == "automatic_captions" and all("tlang=" in f.get("url", "") for f in formats):
                continue
            if language and not (
                lang.lower() == language.lower() or lang.lower().startswith(language.lower() + "-")
            ):
                continue
            langs.append(lang)

        def priority(lang):
            key = lang.lower()
            for index, p in enumerate(preferred):
                if key == p:
                    return index, 0
                if key.startswith(p + "-"):
                    return index, 1
            return len(preferred), 0

        for lang in sorted(langs, key=priority)[:2]:
            yield field, lang


def transcribe(audio, model):
    if not model or not all(
        (model / name).is_file() for name in ("model.bin", "config.json", "tokenizer.json")
    ):
        raise ReadError("语音转写需要已有的本地 faster-whisper 模型目录，可设置 MSB_ASR_MODEL 或提供字幕。")
    python = asr_python()
    if not python:
        raise ReadError("当前 Python 没有 faster-whisper，请用已有的转写环境运行，或提供字幕。")
    if python != sys.executable:
        worker = subprocess.run(
            [python, "-B", __file__, str(audio), str(model)], capture_output=True, text=True
        )
        if worker.returncode:
            raise ReadError("现有本地语音转写环境运行失败。")
        return Material(**json.loads(worker.stdout))
    from faster_whisper import WhisperModel

    try:
        recognizer = WhisperModel(str(model), device="cpu", compute_type="int8", local_files_only=True)
        segments, info = recognizer.transcribe(str(audio), beam_size=3)
        cues = [(stamp(s.start), stamp(s.end), s.text.strip()) for s in segments if s.text.strip()]
    except (RuntimeError, OSError, ValueError) as exc:
        raise ReadError("本地模型无法转写此音频。") from exc
    if not cues:
        raise ReadError("音频中没有取得可读的语音段。")
    return Material(
        "\n".join(f"[{a} – {b}] {t}" for a, b, t in cues),
        "local_asr",
        details={
            "language": info.language,
            "duration_seconds": round(info.duration, 2),
            "cues": len(cues),
            "first": cues[0][0],
            "last": cues[-1][1],
        },
    )


def video(url, platform, work, model=None, language=None):
    exe = yt_dlp()
    raw = run_ytdlp(
        exe, ["--skip-download", "--ignore-no-formats-error", "--dump-single-json", "--", url], work, 90
    )
    info = json.loads(raw)
    if info.get("_type") in ("playlist", "multi_video"):
        raise ReadError("请选择一集视频或指定分 P。")
    metadata = work / "video.json"
    metadata.write_text(raw, encoding="utf-8")
    base = ["--load-info-json", str(metadata)]
    title = info.get("title", "")
    problems = []
    for index, (field, lang) in enumerate(tracks(info, platform, language)):
        prefix = f"track{index}."
        option = "--write-subs" if field == "subtitles" else "--write-auto-subs"
        try:
            run_ytdlp(
                exe,
                [
                    *base,
                    option,
                    "--skip-download",
                    "--sub-langs",
                    re.escape(lang),
                    "--sub-format",
                    "vtt/srt/json3/best",
                    "-o",
                    prefix + "%(ext)s",
                ],
                work,
                90,
            )
            for path in work.glob(prefix + "*"):
                if path.suffix not in (".vtt", ".srt", ".json3", ".json"):
                    continue
                mat = caption_material(
                    path.read_bytes(),
                    path.suffix,
                    "platform_captions" if field == "subtitles" else "automatic_captions",
                )
                mat.title = title
                mat.details.update(language=lang, duration_seconds=info.get("duration"))
                return mat
        except (ReadError, subprocess.TimeoutExpired) as err:
            problems.append(str(err) if isinstance(err, ReadError) else "字幕请求超时")
    if model:
        if not model.is_dir() or not asr_python():
            raise ReadError("请先准备好本地转写环境和模型目录，或提供字幕。")
        run_ytdlp(
            exe,
            [
                *base,
                "--format",
                "worstaudio/best",
                "--http-chunk-size",
                "1M",
                "--no-simulate",
                "-o",
                "audio.%(ext)s",
            ],
            work,
            600,
        )
        audio = next((p for p in work.glob("audio.*") if p.suffix not in (".part", ".ytdl")), None)
        if audio and audio.is_file():
            mat = transcribe(audio, model)
            mat.title = title
            return mat
    detail = " / ".join(dict.fromkeys(problems))
    raise ReadError(f"{title or '视频'}：没有取得可读字幕。{detail} 可尝试发布方字幕或使用已有本地模型转写。")


if __name__ == "__main__":
    from dataclasses import asdict

    print(json.dumps(asdict(transcribe(Path(sys.argv[1]), Path(sys.argv[2])))))
