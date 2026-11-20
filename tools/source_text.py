"""Read text, page structure and timed captions without executing source content."""

import codecs
from dataclasses import dataclass, field
from html import unescape
from html.parser import HTMLParser
import json
import re
import shutil
import subprocess
from urllib.parse import urljoin


@dataclass
class Material:
    text: str
    kind: str
    title: str = ""
    details: dict = field(default_factory=dict)
    partial: bool = False


class ReadError(ValueError):
    """This source did not yield usable evidence."""


def clean(lines):
    text = "".join(lines).replace("\xa0", " ")
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())


class NetworkUnavailable(ReadError):
    """The current process could not reach a source over the network."""


class Page(HTMLParser):
    """Collect named text regions and candidate paper and caption links."""

    void = set("area base br col embed hr img input link meta param source track wbr".split())
    skip = set("script style template noscript svg nav footer form".split())
    blocks = set("p div section article h1 h2 h3 h4 h5 h6 li tr br blockquote figcaption pre".split())

    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.parts = {name: [] for name in ("article", "main", "wechat", "abstract", "title", "headline")}
        self.meta = {}
        self.pdf_links = []
        self.anchor = None
        self.players = []
        self.player = None
        self.sections = 0
        self.section_prose = False
        self.closed_regions = set()
        self.wechat_images = 0
        self.feed(html)
        self.close()

    def handle_starttag(self, tag, attrs):
        attrs = {k: v or "" for k, v in attrs}
        regions = set(self.stack[-1][1]) if self.stack else set()
        ident = attrs.get("id", "")
        classes = attrs.get("class", "").split()
        if tag in self.skip or "skip" in regions:
            regions = {"skip"}
        else:
            if tag == "meta":
                key = (attrs.get("property") or attrs.get("name", "")).lower()
                self.meta.setdefault(key, attrs.get("content", ""))
            if tag in ("title", "article", "main"):
                regions.add(tag)
            if tag == "h1" or ident == "activity-name":
                regions.add("headline")
            if ident == "js_content":
                regions.add("wechat")
            if "ltx_document" in classes:
                regions.add("article")
            if (
                ident == "abstract"
                or "abstract" in classes
                or "ltx_abstract" in classes
                or attrs.get("role") == "doc-abstract"
            ):
                regions.add("abstract")
            if (
                "article" in regions
                and (tag == "section" or "ltx_section" in classes)
                and "abstract" not in regions
            ):
                self.sections += 1
                regions.add("paper_section")
            if tag == "video":
                self.player = {"identity": list(attrs.values()), "tracks": []}
                self.players.append(self.player)
            if self.player is not None:
                if tag == "source" and attrs.get("src"):
                    self.player["identity"].append(attrs["src"])
                if tag == "track" and attrs.get("kind") in ("subtitles", "captions") and attrs.get("src"):
                    self.player["tracks"].append((attrs.get("srclang", ""), attrs["src"]))
            if tag == "img" and "wechat" in regions and (attrs.get("src") or attrs.get("data-src")):
                self.wechat_images += 1
            if tag == "a":
                self.anchor = (attrs.get("href", ""), [attrs.get("title", "")])
            if tag in self.blocks:
                self.append(regions, "\n")
            if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
                regions.add("heading")
                self.append(regions - {"headline"}, "#" * int(tag[1]) + " ")
            if tag == "math" and attrs.get("alttext"):
                self.append(regions, attrs["alttext"])
                regions = {"skip"}
        if tag not in self.void:
            self.stack.append((tag, regions))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.void:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag == "video":
            self.player = None
        if tag == "a" and self.anchor:
            href, parts = self.anchor
            label = " ".join(" ".join(parts).lower().split())
            if re.search(r"\.pdf(?:[?#]|$)", href, re.I) and re.fullmatch(
                r"(?:download\s+)?(?:paper|pdf|full.?text)(?:\s*\(?pdf\)?)?", label
            ):
                self.pdf_links.append(href)
            self.anchor = None
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                parent = self.stack[i - 1][1] if i else set()
                self.closed_regions.update(self.stack[i][1] - parent)
                if tag in self.blocks:
                    self.append(self.stack[i][1], "\n")
                del self.stack[i:]
                return

    def append(self, regions, text):
        for region in regions:
            if region in self.parts:
                self.parts[region].append(text)

    def handle_data(self, data):
        if self.stack:
            regions = self.stack[-1][1]
            self.append(regions, data)
            if (
                "paper_section" in regions
                and not regions.intersection({"heading", "abstract", "skip"})
                and any(c.isalnum() for c in data)
            ):
                self.section_prose = True
            if self.anchor and "skip" not in regions:
                self.anchor[1].append(data)

    def content(self, region):
        return clean(self.parts[region])

    @property
    def title(self):
        return (
            self.content("headline").split("\n")[0]
            or self.meta.get("og:title")
            or self.meta.get("citation_title")
            or self.content("title")
        )

    def article(self, wechat=False):
        if wechat:
            body = self.content("wechat")
            if (
                not body
                or not any(c.isalnum() for c in body)
                or body.strip("# ") == self.title
                or len(body) < 200
                and any(x in body for x in ("当前环境异常", "完成验证后即可继续访问", "此内容因违规无法查看"))
            ):
                raise ReadError("公众号原页没有返回可读的 js_content 正文。")
            return Material(
                body,
                "wechat_body",
                self.title,
                {"images_listed": self.wechat_images, "images_read": False},
                partial="wechat" not in self.closed_regions,
            )
        body = self.content("article") or self.content("main")
        if not any(line.strip() for line in body.splitlines() if not line.startswith("#")):
            raise ReadError("网页缺少可识别的正文。可改用浏览器读取或提供正文文件。")
        area = "article" if self.content("article") else "main"
        return Material(body, "article_body", self.title, partial=area not in self.closed_regions)

    def paper_pdf(self, base):
        href = self.meta.get("citation_pdf_url") or next(iter(self.pdf_links), None)
        return urljoin(base, href) if href else None


def decode(data, charset=None):
    if data.startswith((codecs.BOM_UTF32_LE, codecs.BOM_UTF32_BE)):
        encodings = ("utf-32",)
    elif data.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        encodings = ("utf-16",)
    elif data.startswith(codecs.BOM_UTF8):
        encodings = ("utf-8-sig",)
    else:
        encodings = dict.fromkeys((charset, "utf-8", "gb18030"))
    for encoding in encodings:
        if encoding:
            try:
                return data.decode(encoding)
            except (UnicodeDecodeError, LookupError):
                continue
    raise ReadError("无法识别文本编码，请提供 UTF-8 文本或带字节顺序标记的 Unicode 文件。")


def stamp(seconds):
    milliseconds = round(float(seconds) * 1000)
    mins, millis = divmod(milliseconds, 60000)
    hours, mins = divmod(mins, 60)
    sec, millis = divmod(millis, 1000)
    return f"{hours:02d}:{mins:02d}:{sec:02d}.{millis:03d}"


def caption_material(data, suffix, kind="captions"):
    text = decode(data)
    cues = []
    if suffix in (".json", ".json3"):
        obj = json.loads(text)
        if isinstance(obj, dict) and "events" in obj:
            for event in obj["events"]:
                if not event.get("segs"):
                    continue
                start = event.get("tStartMs", 0) / 1000
                end = start + event.get("dDurationMs", 0) / 1000
                cues.append((stamp(start), stamp(end), "".join(s.get("utf8", "") for s in event["segs"])))
        elif isinstance(obj, dict):
            for cue in obj.get("body", []):
                if (
                    isinstance(cue, dict)
                    and isinstance(cue.get("content"), str)
                    and "from" in cue
                    and "to" in cue
                ):
                    cues.append((stamp(cue["from"]), stamp(cue["to"]), cue["content"]))
    else:
        timestamp = r"(?:\d+:)?\d{2}:\d{2}[.,]\d{3}"
        for block in re.split(r"\n[ \t]*\n", text.replace("\r\n", "\n").replace("\r", "\n")):
            lines = block.strip().splitlines()
            if not lines or lines[0].startswith(("NOTE", "STYLE", "REGION")):
                continue
            for idx, line in enumerate(lines):
                times = re.match(rf"^({timestamp})\s*-->\s*({timestamp})(?:\s|$)", line.strip())
                if times:
                    cues.append((*times.groups(), " ".join(lines[idx + 1 :])))
                    break
    normalized = []
    for start, end, words in cues:
        words = " ".join(unescape(re.sub(r"<[^>]*>", "", words)).split())
        if words:
            normalized.append((start.replace(",", "."), end.replace(",", "."), words))
    if not normalized:
        raise ReadError("字幕文件没有可读的带时间戳语句。")
    body = "\n".join(f"[{start} – {end}] {words}" for start, end, words in normalized)
    return Material(
        body, kind, details={"cues": len(normalized), "first": normalized[0][0], "last": normalized[-1][1]}
    )


def pdf_material(data):
    if not data.startswith(b"%PDF-"):
        raise ReadError("返回的内容并非 PDF。")
    tool = shutil.which("pdftotext")
    if not tool:
        raise ReadError("读取 PDF 需要 pdftotext（Poppler），也可以提供已有的 MinerU / Docling Markdown。")
    result = subprocess.run([tool, "-enc", "UTF-8", "-", "-"], input=data, capture_output=True, timeout=120)
    if result.returncode:
        raise ReadError("PDF 文本提取失败，可改用已有解析结果。")
    pages = result.stdout.decode("utf-8").split("\f")
    if pages and not pages[-1].strip():
        pages.pop()
    present = [i for i, p in enumerate(pages, 1) if p.strip()]
    if not present:
        raise ReadError("PDF 没有文字层，请尝试已有 OCR 或解析结果。")
    body = "\n\n".join(f"## Page {i}\n\n{p.strip()}" for i, p in enumerate(pages, 1) if p.strip())
    return Material(
        body,
        "pdf_text",
        details={"pages": len(pages), "pages_with_text": len(present)},
        partial=len(present) != len(pages),
    )


def supplied_parse(path):
    if not path.is_dir():
        return path
    # Common single-document export layouts. A directory containing multiple documents is ambiguous.
    choices = [
        p
        for p in path.rglob("*.md")
        if p.is_file() and not p.is_symlink() and p.resolve().is_relative_to(path.resolve())
    ]
    if len(choices) != 1:
        raise ReadError("解析目录需要能唯一确定一份 Markdown，请直接选择目标 .md 文件。")
    return choices[0]
