#!/usr/bin/env python3
"""Read one source into a private local cache for the vault's intake prompt."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import tempfile
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from source_text import (
    Material,
    NetworkUnavailable,
    Page,
    ReadError,
    caption_material,
    decode,
    pdf_material,
    supplied_parse,
)
from video_source import available_model, transcribe, video
from x_source import canonical_url, declared_x_url, is_x_url, parse_x_html, status_id


TOOL_ROOT = Path(__file__).resolve().parents[1]
LIMIT = 48 * 1024 * 1024
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"
CAPTION_EXTS = {".srt", ".vtt", ".json3"}
AUDIO_EXTS = {".mp3", ".m4a", ".mp4", ".wav", ".webm", ".flac", ".ogg", ".opus"}
ARXIV_ID = re.compile(
    r"^/(?:abs|pdf|html)/((?:\d{4}\.\d{4,5}|[a-z][a-z0-9.-]*/\d{7})(?:v\d+)?)(?:\.pdf)?/?$", re.I
)
NETWORK_ERRORS = (OSError, ValueError, subprocess.SubprocessError)
X_READER_VERSION = 2


def source_locator(value):
    """Accept a file, a URL, or a clipboard share containing one URL."""
    value = value.strip()
    matches = list(re.finditer(r"""https?://[^\s<>"“”「」【】《》（），。；！？、]+""", value, re.I))
    if not matches:
        return value
    if len(matches) > 1:
        raise ReadError("分享文字里有多个网址。请逐条提交，或指定要整理的那个链接。")
    match = matches[0]
    if "://" in value[:match.start()]:
        raise ReadError("请选择 HTTP(S) 链接或本地文件。")
    url = match[0]
    if match.span() != (0, len(value)):
        url = url.rstrip(".,;")
        for opening, closing in (("(", ")"), ("[", "]")):
            while url.endswith(closing) and url.count(closing) > url.count(opening):
                url = url[:-1]
    scheme, tail = url.split(":", 1)
    return scheme.lower() + ":" + tail


def web_url(value):
    u = urlsplit(value)
    if (
        u.scheme not in ("http", "https")
        or not u.hostname
        or u.username is not None
        or u.password is not None
    ):
        raise ReadError("Expected a public HTTP(S) URL without embedded credentials.")
    return u


class WebRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        web_url(newurl)
        if is_x_url(req.full_url) and status_id(req.full_url):
            check_x_location(req.full_url, newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def proxy_denied_request(text, url):
    match = re.fullmatch(r"Request to GET (\S+) on (\S+) not allowed by policy[.!]?", text.strip(), re.I)
    if not match:
        return False
    address = urlsplit(url)
    target = address.path or "/"
    if address.query:
        target += "?" + address.query
    return (match[1] in (target, address._replace(fragment="").geturl())
            and match[2].lower() == (address.hostname or "").lower())


def fetch(url):
    web_url(url)
    req = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        response = build_opener(WebRedirects()).open(req, timeout=20)
    except HTTPError as exc:
        if exc.code == 407:
            exc.close()
            raise NetworkUnavailable("当前网络代理要求身份验证（HTTP 407）。请使用宿主授权的网络连接读取同一来源。") from exc
        content_type = exc.headers.get("Content-Type", "") if exc.headers else ""
        if exc.code == 403 and content_type.partition(";")[0].strip().lower() in ("", "text/plain"):
            try:
                text = (exc.read(1024) or b"").decode("utf-8", "replace").strip()
            except OSError:
                text = ""
            if proxy_denied_request(text, exc.geturl()):
                exc.close()
                raise NetworkUnavailable("当前终端的网络代理限制了这次读取。请通过宿主的联网审批重试同一来源。") from exc
        raise
    except URLError as exc:
        message = str(exc.reason)
        tunnel = re.fullmatch(r"Tunnel connection failed:\s*(403|407)\b[^\n]*", message, re.I)
        if tunnel:
            raise NetworkUnavailable(f"当前代理拒绝了网络连接（HTTP {tunnel[1]}）。请使用宿主授权的网络连接读取同一来源。") from exc
        system_denial = re.fullmatch(r"(?:\[Errno (?:1|13)\]\s*)?(?:Operation not permitted|Permission denied)", message, re.I)
        if isinstance(exc.reason, (socket.gaierror, PermissionError)) or system_denial or proxy_denied_request(message, url):
            raise NetworkUnavailable(
                "当前终端的网络或 DNS 无法访问原站。请通过宿主的联网审批重试同一读取命令。"
            ) from exc
        raise
    with response:
        data = response.read(LIMIT + 1)
        if len(data) > LIMIT:
            raise ReadError("该文件超过单次 48 MiB 的读取限额，可交给本地解析器处理。")
        return (
            data,
            response.geturl(),
            response.headers.get_content_type(),
            response.headers.get_content_charset(),
        )


def platform(url):
    u = web_url(url)
    host = u.hostname.lower().rstrip(".")

    def domain(suffix):
        return host == suffix or host.endswith("." + suffix)

    if domain("bilibili.com") or host == "b23.tv":
        return "bilibili"
    if domain("youtube.com") or host == "youtu.be":
        return "youtube"
    if host == "mp.weixin.qq.com":
        return "wechat"
    if is_x_url(url):
        return "x"
    if (
        domain("arxiv.org")
        or domain("openreview.net")
        or domain("aclanthology.org")
        or domain("doi.org")
        or domain("usenix.org")
        and "/presentation/" in u.path
        or u.path.lower().endswith(".pdf")
    ):
        return "paper"
    return "web"


def x_source_url(url):
    u = web_url(url)
    if not is_x_url(url) or not status_id(url) or u.port not in (None, 80 if u.scheme == "http" else 443):
        raise ReadError("请提供具体的 X 帖子或长文章的公开链接。")
    return canonical_url(url)


def check_x_location(source, location):
    if not is_x_url(location) or not status_id(location):
        raise ReadError("X 返回了其他页面，无法核对所选帖子的正文。")
    src, dst = x_source_url(source), x_source_url(location)
    src_type, src_id = urlsplit(src).path.split("/")[-2:]
    dst_type, dst_id = urlsplit(dst).path.split("/")[-2:]
    if src_type == dst_type and src_id != dst_id:
        raise ReadError("返回页面的 X 编号与所选链接不符。")
    return dst


def x_response(data, encoding, source, final):
    address = check_x_location(source, final)
    mat = parse_x_html(decode(data, encoding), source)
    route, identifier = urlsplit(address).path.split("/")[-2:]
    if mat.details.get(route + "_id") != identifier:
        raise ReadError("无法从正文核对 X 返回地址对应的帖子或文章编号。")
    mat.details["source_url"] = address
    return mat


class SavedHTML(Page):
    """Keep the publisher's canonical URL separate from embedded posts."""

    def __init__(self, html):
        self.canonical = ""
        self.x_markup = False
        super().__init__(html)

    def handle_starttag(self, tag, attrs):
        if tag == "link" and any(name == "head" for name, _ in self.stack):
            link = dict(attrs)
            if "canonical" in (link.get("rel") or "").lower().split() and not self.canonical:
                self.canonical = link.get("href") or ""
        if any(key == "data-testid" and value in ("twitterArticleReadView", "longformRichTextComponent", "tweetText") for key, value in attrs):
            self.x_markup = True
        super().handle_starttag(tag, attrs)

    def is_x_page(self):
        address = self.canonical or self.meta.get("og:url")
        if address:
            return is_x_url(address)
        site = self.meta.get("og:site_name", "").strip().lower()
        return site in ("x", "twitter", "x (formerly twitter)") if site else self.x_markup


def read_file(data, suffix, source_type, source_url=None):
    if data.startswith(b"%PDF-") or suffix == ".pdf":
        return pdf_material(data)
    if suffix in CAPTION_EXTS or suffix == ".json" or data.lstrip(b"\xef\xbb\xbf").startswith(b"WEBVTT"):
        return caption_material(data, suffix)
    if suffix in (".html", ".htm") or data.lstrip()[:30].lower().startswith((b"<!doctype html", b"<html")):
        html = decode(data)
        page = SavedHTML(html)
        if source_type == "x" or (source_type in ("web", "file") and page.is_x_page()):
            declared = declared_x_url(html)
            mat = parse_x_html(html, source_url if source_type == "x" and source_url else declared)
            if declared:
                mat.details["source_url"] = x_source_url(declared)
            return mat
        if source_type in ("bilibili", "youtube") or page.meta.get("og:type", "").startswith("video"):
            raise ReadError("视频观看页本身不能作为字幕，请选择字幕文件或浏览器里读到的逐字稿。")
        if source_type == "paper":
            if page.section_prose:
                return paper_body(page)
            if page.content("abstract"):
                return Material(page.content("abstract"), "abstract", page.title, partial=True)
            raise ReadError("论文网页没有可识别的正文章节或摘要。")
        return page.article(wechat=source_type == "wechat" or bool(page.content("wechat")))
    if suffix not in (".md", ".txt", ".text", ".markdown"):
        raise ReadError("请选择 Markdown、正文、字幕、PDF 或本地音视频。")
    text = decode(data).strip()
    if "\x00" in text:
        raise ReadError("文件中含有二进制数据，请提供可读的文本文件。")
    if not text:
        raise ReadError("材料为空。")
    return Material(text, "supplied_text", details={"scope": "supplied file only"})


def file_material(path, source_type, model, source_url=None):
    path = supplied_parse(path.expanduser())
    if not path.is_file():
        raise ReadError("找不到指定的材料文件。")
    suffix = path.suffix.lower()
    if suffix in AUDIO_EXTS:
        return transcribe(path, model)
    if path.stat().st_size > LIMIT:
        raise ReadError("原文件超过 48 MiB，可提供本地解析后的文本。")
    return read_file(path.read_bytes(), suffix, source_type, source_url)


def paper_body(page):
    return Material(
        page.content("article"),
        "paper_html",
        page.title,
        {"sections": page.sections, "figures_read": False},
        partial="article" not in page.closed_regions,
    )


def arxiv(identifier, prefer_pdf=False):
    causes = []
    formats = ("pdf", "html", "abs") if prefer_pdf else ("html", "pdf", "abs")
    for fmt in formats:
        target = f"https://arxiv.org/{fmt}/{identifier}"
        try:
            data, final, mime, encoding = fetch(target)
            if fmt == "pdf":
                mat = pdf_material(data)
            else:
                page = Page(decode(data, encoding))
                if fmt == "abs":
                    body = page.content("abstract")
                    if not body:
                        continue
                    mat = Material(body, "abstract", page.title, partial=True)
                elif page.section_prose:
                    mat = paper_body(page)
                else:
                    continue
            mat.details["edition"] = identifier
            mat.details["retrieved_from"] = final
            return mat
        except NetworkUnavailable:
            raise
        except NETWORK_ERRORS as exc:
            causes.append(reason(exc))
    raise ReadError("arXiv 正文、PDF 和摘要均未取得。" + " / ".join(dict.fromkeys(causes)))


def online(url, kind, work, model, language):
    if kind in ("bilibili", "youtube"):
        return video(url, kind, work, model, language)
    u = web_url(url)
    if u.hostname in ("arxiv.org", "www.arxiv.org", "export.arxiv.org"):
        match = ARXIV_ID.fullmatch(u.path)
        if match:
            return arxiv(match[1], prefer_pdf=u.path.startswith("/pdf/"))
    data, final, mime, encoding = fetch(url)
    if kind == "x" or is_x_url(final):
        selected = url if kind == "x" else x_source_url(final)
        return x_response(data, encoding, selected, final)
    if data.startswith(b"%PDF-") or mime == "application/pdf":
        return pdf_material(data)
    suffix = Path(urlsplit(final).path).suffix.lower()
    if suffix in CAPTION_EXTS or mime in ("text/vtt", "text/plain", "text/markdown"):
        return read_file(data, suffix if suffix in CAPTION_EXTS else ".txt", kind)
    html = decode(data, encoding)
    page = Page(html)
    if kind == "paper" or page.meta.get("citation_pdf_url") or page.meta.get("citation_title"):
        if page.section_prose:
            return paper_body(page)
        pdf = page.paper_pdf(final)
        if not pdf and u.hostname in ("openreview.net", "www.openreview.net") and u.path == "/forum":
            identifier = parse_qs(u.query).get("id", [])
            if len(identifier) == 1:
                pdf = "https://openreview.net/pdf?" + urlencode({"id": identifier[0]})
        failure = ""
        if pdf:
            try:
                mat = pdf_material(fetch(pdf)[0])
                mat.title = page.title
                return mat
            except NETWORK_ERRORS as exc:
                failure = reason(exc)
        abstract = page.content("abstract") or page.meta.get("citation_abstract")
        if abstract:
            return Material(abstract, "abstract", page.title, {"full_text_issue": failure}, True)
        raise ReadError(f"论文入口未取得正文。{failure} 可用公开 PDF 或已有解析结果。")
    if page.meta.get("og:type", "").startswith("video"):
        raise ReadError("这是视频页面。请读取可用的字幕或音频转写。")
    return page.article(wechat=kind == "wechat")


def publisher_track(source, data, final, encoding, language):
    u = urlsplit(source)
    identifier = (parse_qs(u.query).get("v") or [u.path.rstrip("/").split("/")[-1]])[0]
    html = decode(data, encoding)
    page = Page(html)
    marker = re.compile(r"(?<![A-Za-z0-9_-])" + re.escape(identifier) + r"(?![A-Za-z0-9_-])")
    # Players often prefix their DOM id with 'video-player-' and append a display-instance suffix.
    matches = [
        player
        for player in page.players
        if any(
            marker.search(value) or value == identifier or ("video-player-" + identifier + "-") in value
            for value in player["identity"]
        )
    ]
    if not identifier or len(matches) != 1:
        raise ReadError("发布方页面不能唯一定位到同一集视频。可选择已核对的字幕文件。")
    choices = [
        track
        for track in matches[0]["tracks"]
        if not language or track[0].lower().split("-")[0] == language.lower().split("-")[0]
    ]
    for lang, href in choices:
        target = urljoin(final, href)
        try:
            body, link, mime, _ = fetch(target)
            ext = Path(urlsplit(link).path).suffix.lower()
            if mime == "text/vtt":
                ext = ".vtt"
            if ext not in CAPTION_EXTS:
                continue
            mat = caption_material(body, ext, "publisher_captions")
            mat.title = page.title
            mat.details["language"] = lang
            return mat
        except NETWORK_ERRORS:
            continue
    raise ReadError("发布方列出的字幕轨未返回可读语句。")


def supplement(locator, source, kind, model, language):
    if not locator.startswith(("http://", "https://")):
        return file_material(Path(locator), kind, model, source)
    if kind == "x" and is_x_url(locator):
        check_x_location(source, locator)
    data, final, mime, encoding = fetch(locator)
    if kind == "x" and (is_x_url(locator) or is_x_url(final)):
        return x_response(data, encoding, source, final)
    suffix = Path(urlsplit(final).path).suffix.lower()
    if kind in ("bilibili", "youtube") and (suffix in (".html", ".htm") or mime == "text/html"):
        return publisher_track(source, data, final, encoding, language)
    if mime == "text/vtt":
        suffix = ".vtt"
    if mime == "text/plain" and suffix not in CAPTION_EXTS:
        suffix = ".txt"
    if mime in ("text/html", "application/xhtml+xml"):
        suffix = ".html"
    return read_file(data, suffix, kind, source)


def reason(exc):
    if isinstance(exc, HTTPError):
        return f"HTTP {exc.code}"
    if isinstance(exc, URLError):
        return "网络连接失败：" + type(exc.reason).__name__
    if isinstance(exc, subprocess.TimeoutExpired):
        return "读取工具超时"
    if isinstance(exc, ReadError):
        return str(exc)
    return f"读取失败（{type(exc).__name__}）"


def atomic(path, data):
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as output:
            temp_path = Path(output.name)
            output.write(data)
        os.replace(temp_path, path)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def cached(folder, source, kind):
    try:
        record = json.loads((folder / "evidence.json").read_text(encoding="utf-8"))
        if not isinstance(record, dict):
            return None
        if kind == "x" or record.get("source_type") == "x":
            if record.get("x_reader_version") != X_READER_VERSION:
                return None
        file = folder / record["file"]
        if (
            record.get("source") == source
            and record.get("status") == "ready"
            and record.get("material") == ".local/imports/" + folder.name + "/" + file.name
            and file.is_file()
            and file.resolve().parent == folder
            and hashlib.sha256(file.read_bytes()).hexdigest() == record["sha256"]
        ):
            return record
    except (OSError, KeyError, ValueError, TypeError):
        pass
    return None


def configured_file(root, source, canonical=None):
    index = root / ".local/source-files.json"
    if not index.is_file():
        return None
    paths = json.loads(index.read_text(encoding="utf-8"))
    if not isinstance(paths, dict):
        raise ReadError(".local/source-files.json 应按原链接指定本地文件。")
    value = paths.get(source)
    if value is None and canonical:
        value = paths.get(canonical)
        if value is None:
            for other, candidate in paths.items():
                if not is_x_url(other):
                    continue
                try:
                    match = x_source_url(other) == canonical
                except ValueError:
                    continue
                if match:
                    if value is not None and value != candidate:
                        raise ReadError("同一 X 帖子的多个分享链接配置了不同文件。请按当前链接指定材料。")
                    value = candidate
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ReadError("该链接配置的本地材料路径无效。")
    return index.parent / Path(value).expanduser()


def intake(root, source, supplied=None, model=None, language=None, refresh=False, scope=None, *, auto_asr=False):
    root = root.resolve()
    if not root.is_dir():
        raise ReadError("请选择已有的学习目录。")
    raw_source = source_locator(source)
    is_web = raw_source.startswith(("http://", "https://"))
    if not is_web and "://" in raw_source:
        raise ReadError("请选择 HTTP(S) 链接或本地文件。")
    path = None if is_web else Path(raw_source).expanduser().resolve()
    kind = platform(raw_source) if is_web else "file"
    source = x_source_url(raw_source) if kind == "x" else raw_source
    source_label = source if is_web else path.name
    uses_video_reader = kind in ("bilibili", "youtube") and not supplied
    if auto_asr and model is None and (uses_video_reader or Path(supplied or source).suffix.lower() in AUDIO_EXTS):
        model = available_model()
    identity = source if is_web else str(path)
    folder = root / ".local/imports" / hashlib.sha256(identity.encode()).hexdigest()[:24]
    if folder.resolve() != folder:
        raise ReadError("导入缓存须使用学习目录内的实体目录。")
    folder.mkdir(parents=True, exist_ok=True)
    if scope and is_web and not supplied:
        raise ReadError("--scope 用于明确标记提供的文件或摘录。")
    mat = None
    local_issue = ""
    provided = supplied
    if is_web and not supplied:
        try:
            mapped = configured_file(root, raw_source, source if kind == "x" else None)
            if mapped is not None:
                mat = file_material(mapped, kind, model, source)
                provided = str(mapped)
                mat.details["origin"] = "configured local file"
        except NETWORK_ERRORS as exc:
            local_issue = reason(exc)
        prior = cached(folder, source_label, kind)
        if (
            mat is None
            and not refresh
            and prior
            and (
                not language
                or (prior.get("details", {}).get("language") or "").lower().split("-")[0]
                == language.lower().split("-")[0]
            )
        ):
            return dict(prior, cached=True, **({"local_file_issue": local_issue} if local_issue else {}))
    with tempfile.TemporaryDirectory(prefix="read-", dir=folder) as work:
        if supplied:
            mat = supplement(supplied, source, kind, model, language)
        elif is_web and mat is None:
            mat = online(source, kind, Path(work), model, language)
        elif not is_web:
            mat = file_material(path, kind, model)
    if local_issue:
        mat.details["local_file_issue"] = local_issue
    if mat.kind == "wechat_body":
        kind = "wechat"
    elif mat.kind in ("x_article", "x_post"):
        kind = "x"
    elif mat.kind in ("paper_html", "abstract"):
        kind = "paper"
    elif kind == "file" and mat.kind in ("captions", "local_asr"):
        kind = "video"
    elif kind == "file" and mat.kind == "pdf_text":
        kind = "pdf"
    if scope:
        mat.partial = True
        mat.details["scope"] = scope
        if scope == "abstract":
            mat.kind = "abstract"
    if kind in ("youtube", "bilibili") and mat.kind == "pdf_text":
        mat.partial = True
        mat.details["scope"] = "supplied PDF with unverified speech coverage"
    raw = (mat.text.strip() + "\n").encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()
    body = folder / ("text-" + digest[:16] + ".md")
    atomic(body, raw)
    record = {
        "status": "partial" if mat.partial else "ready",
        "source": source_label,
        "source_type": kind,
        "evidence": mat.kind,
        "title": mat.title,
        "characters": len(mat.text.strip()),
        "details": mat.details,
        "file": body.name,
        "material": body.relative_to(root).as_posix(),
        "sha256": digest,
        "next": "Prompts/整理材料.md",
    }
    if kind == "x":
        record["x_reader_version"] = X_READER_VERSION
    if provided:
        if provided.startswith(("https://", "http://")):
            u = urlsplit(provided)
            record["evidence_source"] = u._replace(query="", fragment="").geturl()
        else:
            record["evidence_source"] = Path(provided).name
    # A partial refresh can be read separately while the last complete source stays usable.
    manifest = "partial.json" if mat.partial else "evidence.json"
    atomic(folder / manifest, (json.dumps(record, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    return record


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source", help="public URL, share text with one URL, or local material")
    p.add_argument(
        "--from",
        dest="supplied",
        metavar="FILE_OR_URL",
        help="local text, PDF, parser output or a publisher caption URL",
    )
    example = TOOL_ROOT / 'examples' / 'demo-vault'
    default_root = TOOL_ROOT
    if example.resolve() == example and (example / '.secondbrain.json').is_file() and not (TOOL_ROOT / 'Flashcards').is_dir():
        default_root = example
    p.add_argument("--root", type=Path, default=default_root)
    p.add_argument("--refresh", action="store_true")
    p.add_argument("--scope", choices=("excerpt", "abstract"), help="label a supplied excerpt or abstract")
    p.add_argument("--language", help="preferred caption language, e.g. en or zh")
    speech = p.add_mutually_exclusive_group()
    speech.add_argument("--asr-model", type=Path, help="existing faster-whisper model directory")
    speech.add_argument("--no-asr", action="store_true", help="try captions without transcribing audio")
    args = p.parse_args()
    if args.root.resolve() == TOOL_ROOT:
        args.root = default_root
    ascii_output = not (sys.stdout.encoding or "utf-8").lower().startswith("utf")
    try:
        result = intake(args.root, args.source, args.supplied, args.asr_model, args.language,
                        args.refresh, args.scope, auto_asr=not args.no_asr)
    except NetworkUnavailable as exc:
        print(
            json.dumps(
                {
                    "status": "needs_network",
                    "reason": str(exc),
                    "next_action": "retry_same_command_with_host_network_permission",
                    "next": "Prompts/整理材料.md",
                },
                ensure_ascii=ascii_output,
            )
        )
        return 2
    except NETWORK_ERRORS as exc:
        print(
            json.dumps(
                {"status": "needs_material", "reason": reason(exc), "next": "Prompts/整理材料.md"},
                ensure_ascii=ascii_output,
            )
        )
        return 2
    print(json.dumps(result, ensure_ascii=ascii_output, indent=2))
    return 2 if result["status"] == "partial" else 0


if __name__ == "__main__":
    sys.exit(main())
