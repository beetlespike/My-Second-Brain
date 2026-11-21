"""Read public X posts and X Articles from X HTML without executing page scripts."""

from html.parser import HTMLParser
import json
import re
from urllib.parse import urljoin, urlsplit

from source_text import Material, Page, ReadError


X_HOSTS = {
    "x.com",
    "www.x.com",
    "mobile.x.com",
    "twitter.com",
    "www.twitter.com",
    "mobile.twitter.com",
}
STATUS_PATH = re.compile(
    r"^/(?P<user>[A-Za-z0-9_]+|i/web|i)/(?P<kind>status|statuses|article)/(?P<id>\d+)(?:/.*)?$"
)
ARTICLE_MEDIA_HREF = re.compile(r"^https://(?:www\.)?(?:x|twitter)\.com/[^/]+/article/\d+/media/\d+(?:[/?#]|$)")


def is_x_url(url):
    try:
        host = (urlsplit(url).hostname or "").lower().rstrip(".")
    except ValueError:
        return False
    return host in X_HOSTS


def status_id(url):
    try:
        match = STATUS_PATH.fullmatch(urlsplit(url).path)
    except ValueError:
        return None
    return match.group("id") if match else None


def canonical_url(url):
    u = urlsplit(url)
    match = STATUS_PATH.fullmatch(u.path)
    if match:
        user = "i" if match.group("user") in ("i", "i/web") else match.group("user")
        kind = "article" if match.group("kind") == "article" else "status"
        return f"https://x.com/{user}/{kind}/{match.group('id')}"
    return u._replace(scheme="https", netloc="x.com", fragment="").geturl()


def _scan_js_string(text, quote_index):
    """Scan a double-quoted JS string literal in O(N) without regex backtracking."""
    if quote_index >= len(text) or text[quote_index] != '"':
        raise ValueError("Expected opening quote for JS string literal")
    i = quote_index + 1
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == "\\":
            i += 2
        elif ch == '"':
            return text[quote_index + 1 : i], i + 1
        else:
            i += 1
    raise ValueError("Unterminated JS string literal")


def _unescape_js_string(raw_inner):
    simple = {
        '\\"': '"',
        "\\'": "'",
        "\\\\": "\\",
        "\\/": "/",
        "\\n": "\n",
        "\\r": "\r",
        "\\t": "\t",
        "\\b": "\b",
        "\\f": "\f",
    }

    def repl(match):
        tok = match.group(0)
        if tok in simple:
            return simple[tok]
        if tok.startswith(("\\x", "\\u")):
            return chr(int(tok[2:], 16))
        return tok[1:]

    decoded = re.sub(r"\\(?:x[0-9a-fA-F]{2}|u[0-9a-fA-F]{4}|.)", repl, raw_inner)
    # Normalize any JS UTF-16 surrogate pairs safely to valid Unicode text.
    try:
        return decoded.encode("utf-16", "surrogatepass").decode("utf-16", "replace")
    except UnicodeError:
        return decoded


def _extract_js_string_field(text, field_name):
    match = re.search(rf'\b{re.escape(field_name)}\s*:\s*"', text)
    if not match:
        return ""
    raw, _ = _scan_js_string(text, match.end() - 1)
    return _unescape_js_string(raw)


class _ArticleHTMLParser(HTMLParser):
    """Convert X Article SSR or rendered DOM HTML into clean Markdown."""

    skip_tags = {"script", "style", "template", "noscript", "svg"}
    void_tags = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self, html, *, container_testids=()):
        super().__init__(convert_charrefs=True)
        self.container_testids = set(container_testids)
        self.active = not self.container_testids
        self.container_depths = []
        self.tag_stack = []
        self.skip_depth = 0
        self.blocks = []
        self.block_kind = None
        self.block_buf = []
        self.list_stack = []
        self.ordered_counts = []
        self.blockquote_depth = 0
        self.pre_depth = 0
        self.link_href = None
        self.link_buf = None
        self.link_has_image = False
        self.images_listed = 0
        self.image_urls = []
        self.referenced_urls = []
        self.feed(html)
        self.close()
        self._flush_block()

    def _current_target(self):
        return self.link_buf if self.link_buf is not None else self.block_buf

    def _start_block(self, kind):
        self._flush_block()
        self.block_kind = kind
        self.block_buf = []

    def _flush_block(self):
        text = "".join(self.block_buf).replace("\xa0", " ").strip()
        self.block_buf = []
        kind = self.block_kind
        self.block_kind = None
        if not text:
            return
        if kind and kind.startswith("h") and len(kind) == 2 and kind[1].isdigit():
            level = int(kind[1])
            clean = " ".join(line.strip() for line in text.splitlines() if line.strip())
            self.blocks.append(f"{'#' * level} {clean}")
        elif kind == "pre":
            self.blocks.append(f"```\n{text.rstrip()}\n```")
        elif kind == "blockquote" or self.blockquote_depth > 0:
            lines = [line.strip() for line in text.splitlines()]
            quoted = "\n".join(f"> {line}" if line else ">" for line in lines)
            self.blocks.append(quoted)
        elif kind == "li":
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            if not lines:
                return
            if self.list_stack and self.list_stack[-1] == "ol":
                self.ordered_counts[-1] += 1
                prefix = f"{self.ordered_counts[-1]}. "
            else:
                prefix = "- "
            body = f"\n{' ' * len(prefix)}".join(lines)
            self.blocks.append(f"{prefix}{body}")
        else:
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            if lines:
                self.blocks.append("\n".join(lines))

    def _record_ref(self, href):
        if href.startswith(("http://", "https://")) and not ARTICLE_MEDIA_HREF.match(href):
            if href not in self.referenced_urls:
                self.referenced_urls.append(href)

    def handle_starttag(self, tag, attrs):
        attr_map = {k: v or "" for k, v in attrs}
        if tag not in self.void_tags:
            self.tag_stack.append(tag)
        if not self.active:
            if attr_map.get("data-testid") in self.container_testids:
                self.active = True
                self.container_depths.append(len(self.tag_stack))
            return
        if tag in self.skip_tags or self.skip_depth:
            if tag not in self.void_tags:
                self.skip_depth += 1
            return
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._start_block(tag)
        elif tag == "blockquote":
            self._flush_block()
            self.blockquote_depth += 1
        elif tag == "ul":
            self._flush_block()
            self.list_stack.append("ul")
        elif tag == "ol":
            self._flush_block()
            self.list_stack.append("ol")
            self.ordered_counts.append(0)
        elif tag == "li":
            self._start_block("li")
        elif tag == "pre":
            self._start_block("pre")
            self.pre_depth += 1
        elif tag == "p":
            if self.block_kind != "li":
                self._start_block("p")
        elif tag == "div":
            if self.block_kind is None and self.block_buf:
                self._flush_block()
        elif tag == "figure":
            self._start_block("p")
        elif tag == "br":
            self._current_target().append("\n")
        elif tag == "code" and self.pre_depth == 0:
            self._current_target().append("`")
        elif tag == "a":
            href = attr_map.get("href", "").strip()
            if href:
                href = urljoin("https://x.com", href)
            self.link_href = href
            self.link_buf = []
            self.link_has_image = False
        elif tag == "img":
            src = (attr_map.get("src") or attr_map.get("data-src") or "").strip()
            alt = " ".join((attr_map.get("alt") or "").split())
            self.images_listed += 1
            if src:
                self.image_urls.append(src)
            marker = f"[Image {self.images_listed}: {alt}]" if alt else f"[Image {self.images_listed}]"
            if self.link_buf is not None:
                self.link_has_image = True
            self.block_buf.append(marker)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.void_tags:
            self.handle_endtag(tag)

    def handle_data(self, data):
        if not self.active or self.skip_depth:
            return
        if self.pre_depth == 0:
            data = re.sub(r"[ \t\r\n]+", " ", data)
        if not self.block_kind and not data.strip():
            return
        self._current_target().append(data)

    def handle_endtag(self, tag):
        if tag in self.void_tags:
            return
        if self.active and self.skip_depth:
            self.skip_depth -= 1
        elif self.active:
            if tag == "a" and self.link_buf is not None:
                label = " ".join("".join(self.link_buf).split())
                href = self.link_href or ""
                self.link_buf = None
                self.link_href = None
                if label and not self.link_has_image:
                    if href and not ARTICLE_MEDIA_HREF.match(href):
                        self._record_ref(href)
                        self.block_buf.append(href if label == href else f"[{label}]({href})")
                    else:
                        self.block_buf.append(label)
                elif label:
                    self.block_buf.append(label)
            elif tag == "code" and self.pre_depth == 0:
                self._current_target().append("`")
            elif tag in ("h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "figure"):
                self._flush_block()
            elif tag == "div":
                if self.block_kind is None:
                    self._flush_block()
                elif self.block_buf and not "".join(self.block_buf).endswith("\n"):
                    self.block_buf.append("\n")
            elif tag == "pre":
                self._flush_block()
                if self.pre_depth > 0:
                    self.pre_depth -= 1
            elif tag == "blockquote":
                self._flush_block()
                if self.blockquote_depth > 0:
                    self.blockquote_depth -= 1
            elif tag == "ul":
                self._flush_block()
                if self.list_stack and self.list_stack[-1] == "ul":
                    self.list_stack.pop()
            elif tag == "ol":
                self._flush_block()
                if self.list_stack and self.list_stack[-1] == "ol":
                    self.list_stack.pop()
                    self.ordered_counts.pop()
        while self.tag_stack:
            depth = len(self.tag_stack)
            popped = self.tag_stack.pop()
            if self.container_depths and depth == self.container_depths[-1]:
                self.container_depths.pop()
                if not self.container_depths:
                    self._flush_block()
                    self.active = False
            if popped == tag:
                break

    @property
    def markdown(self):
        return "\n\n".join(self.blocks).strip()


def _extract_ssr_article_parts(html):
    doc_match = re.search(r"articleDocument:(?:\$R\[\d+\]=)?\{", html)
    if not doc_match:
        return None
    parts_match = re.search(r"parts:(?:\$R\[\d+\]=)?\[", html[doc_match.end() :])
    if not parts_match:
        return None
    cursor = doc_match.end() + parts_match.end()
    fragments = []
    limit = len(html)
    while cursor < limit:
        if html[cursor] == "]":
            break
        part_match = re.match(
            r'\s*,?\s*(?:\$R\[\d+\]=)?\{\s*type\s*:\s*"html"\s*,\s*html\s*:\s*"',
            html[cursor : cursor + 120],
        )
        if not part_match:
            next_html = re.search(r'\{\s*type\s*:\s*"html"\s*,\s*html\s*:\s*"', html[cursor : cursor + 2000])
            if not next_html:
                break
            quote_pos = cursor + next_html.end() - 1
        else:
            quote_pos = cursor + part_match.end() - 1
        raw_inner, next_pos = _scan_js_string(html, quote_pos)
        fragments.append(_unescape_js_string(raw_inner))
        close_brace = html.find("}", next_pos)
        if close_brace < 0:
            break
        cursor = close_brace + 1
    if not fragments:
        return None
    parser = _ArticleHTMLParser("\n".join(fragments))
    if not parser.markdown:
        return None
    return parser


def _extract_ssr_content_key(html):
    doc_match = re.search(r'articleDocument:(?:\$R\[\d+\]=)?\{[^}]{0,200}?contentKey\s*:\s*"', html)
    if not doc_match:
        return None
    raw_inner, _ = _scan_js_string(html, doc_match.end() - 1)
    arr = json.loads(_unescape_js_string(raw_inner))
    if not isinstance(arr, list) or not arr:
        return None
    blocks = []
    image_count = 0
    for item in arr:
        if not isinstance(item, list) or len(item) < 3:
            continue
        kind, text = item[1], str(item[2]).strip()
        if kind == "atomic":
            image_count += 1
            blocks.append(f"[Image {image_count}]")
            continue
        if not text:
            continue
        if kind == "header-one":
            blocks.append(f"# {text}")
        elif kind == "header-two":
            blocks.append(f"## {text}")
        elif kind == "header-three":
            blocks.append(f"### {text}")
        elif kind == "blockquote":
            blocks.append("\n".join(f"> {line}" for line in text.splitlines()))
        elif kind == "unordered-list-item":
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            blocks.append("\n  ".join([f"- {lines[0]}", *lines[1:]]) if lines else "")
        elif kind == "ordered-list-item":
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            blocks.append("\n  ".join([f"1. {lines[0]}", *lines[1:]]) if lines else "")
        elif kind == "code-block":
            blocks.append(f"```\n{text}\n```")
        else:
            blocks.append(text)
    body = "\n\n".join(b for b in blocks if b).strip()
    if not body:
        return None
    return body, image_count


def _extract_ssr_metadata(html):
    info = {}
    meta_match = re.search(r"metadata:(?:\$R\[\d+\]=)?\{", html)
    if meta_match:
        window = html[meta_match.start() :]
        info["focal_tweet_id"] = _extract_js_string_field(window[:8000], "focalTweetId")
        info["author"] = _extract_js_string_field(window[:8000], "authorName")
        info["handle"] = _extract_js_string_field(window[:8000], "screenName")
        info["body_text"] = _extract_js_string_field(window[:8000], "bodyText")
        info["published_at"] = _extract_js_string_field(window[:10000], "publishedTime")
        info["canonical_url"] = _extract_js_string_field(window[:8000], "canonicalUrl")
        has_article_match = re.search(r"\bhasArticle\s*:\s*(!0|!1|true|false)", window[:8000])
        if has_article_match:
            info["has_article"] = has_article_match.group(1) in ("!0", "true")
    return info


def _find_tweet_result(node, target_id=None):
    if isinstance(node, dict):
        if node.get("__typename") == "Tweet" and isinstance(node.get("core"), dict):
            rest_id = node.get("rest_id") or ""
            if not target_id or rest_id == target_id:
                return node
        if "tweet_results" in node and isinstance(node["tweet_results"], dict):
            tr = node["tweet_results"]
            res = tr.get("result")
            if isinstance(res, dict) and (not target_id or tr.get("rest_id") == target_id or res.get("rest_id") == target_id):
                if res.get("__typename") == "Tweet":
                    return res
        for value in node.values():
            found = _find_tweet_result(value, target_id)
            if found is not None:
                return found
    elif isinstance(node, list):
        for item in node:
            found = _find_tweet_result(item, target_id)
            if found is not None:
                return found
    return None


def _extract_relay_tweet(html, target_id=None):
    for match in re.finditer(r'result:(?:\$R\[\d+\]=)?\{kind:"Result\.Ok",value:"', html):
        raw_inner, _ = _scan_js_string(html, match.end() - 1)
        payload_str = _unescape_js_string(raw_inner)
        if "threaded_conversation_with_injections_v2" not in payload_str:
            continue
        try:
            payload = json.loads(payload_str)
        except json.JSONDecodeError:
            continue
        tweet = _find_tweet_result(payload, target_id)
        if tweet is not None:
            return tweet
    return None


def _expand_tco_urls(text, url_entities):
    refs = []
    out = text
    for ent in url_entities or ():
        short = ent.get("url")
        expanded = ent.get("expanded_url")
        if short and expanded and short in out:
            out = out.replace(short, expanded)
            if expanded not in refs:
                refs.append(expanded)
        elif expanded and expanded not in refs:
            refs.append(expanded)
    return out, refs


def _clean_title(raw_title, handle="", author="", description="", fallback=""):
    title = (raw_title or "").strip()
    if title:
        title = re.sub(r"\s*/\s*X$", "", title).strip()
        quoted = re.match(r'^.+?\s+on\s+X:\s*"(.*)"$', title, re.S)
        if quoted:
            title = quoted.group(1).strip()
    if not title or re.fullmatch(r"https?://t\.co/\S+", title):
        title = (description or "").strip()
    if not title:
        title = fallback or (f"@{handle} on X" if handle else author or "X Post")
    return title.splitlines()[0].strip()


def _relay_article_meta(tweet):
    if not isinstance(tweet, dict):
        return {}
    user = tweet.get("core", {}).get("user_results", {}).get("result", {}).get("core", {})
    article_res = tweet.get("article", {}).get("article_results", {}).get("result", {})
    return {
        "author": user.get("name", ""),
        "handle": user.get("screen_name", ""),
        "article_title": article_res.get("title", ""),
    }


def _clean_details(meta, images_listed=None, referenced_urls=()):
    details = {}
    if meta.get("author"):
        details["author"] = meta["author"]
    if meta.get("handle"):
        details["handle"] = meta["handle"]
    if meta.get("published_at"):
        details["published_at"] = meta["published_at"]
    if images_listed:
        details["images_listed"] = images_listed
        details["images_read"] = False
    if referenced_urls:
        details["referenced_urls"] = list(referenced_urls)
    return details


def parse_x_html(html, url=""):
    """Extract an X Article or focal X post from X HTML without scraping replies."""
    page = Page(html)
    target_id = status_id(url) if url else None
    ssr = _extract_ssr_metadata(html)
    focal_id = target_id or ssr.get("focal_tweet_id") or None
    relay_tweet = _extract_relay_tweet(html, focal_id)
    relay_meta = _relay_article_meta(relay_tweet)

    meta = {
        "author": relay_meta.get("author") or ssr.get("author", ""),
        "handle": relay_meta.get("handle") or ssr.get("handle") or page.meta.get("twitter:creator", "").lstrip("@"),
        "published_at": ssr.get("published_at", ""),
    }
    article_title = relay_meta.get("article_title", "")

    # 1. X Article: SSR HTML parts -> SSR contentKey blocks -> browser-saved DOM
    parts_parser = _extract_ssr_article_parts(html)
    if parts_parser is not None:
        title = _clean_title(
            article_title or page.meta.get("og:title") or page.content("title"),
            meta["handle"],
            meta["author"],
            page.meta.get("og:description"),
        )
        return Material(
            parts_parser.markdown,
            "x_article",
            title,
            _clean_details(meta, parts_parser.images_listed, parts_parser.referenced_urls),
        )

    content_key = _extract_ssr_content_key(html)
    if content_key is not None:
        body, images = content_key
        title = _clean_title(
            article_title or page.meta.get("og:title") or page.content("title"),
            meta["handle"],
            meta["author"],
            page.meta.get("og:description"),
        )
        return Material(body, "x_article", title, _clean_details(meta, images))

    dom_parser = _ArticleHTMLParser(
        html, container_testids=("twitterArticleReadView", "longformRichTextComponent")
    )
    if dom_parser.markdown:
        title = _clean_title(
            article_title or page.meta.get("og:title") or page.content("title"),
            meta["handle"],
            meta["author"],
            page.meta.get("og:description"),
        )
        return Material(
            dom_parser.markdown,
            "x_article",
            title,
            _clean_details(meta, dom_parser.images_listed, dom_parser.referenced_urls),
        )

    # 2. Regular focal X post / Note Tweet (skip if page advertised an article whose body is missing)
    has_article = bool(ssr.get("has_article")) or page.meta.get("og:type") == "article"
    if not has_article and (not target_id or not ssr.get("focal_tweet_id") or target_id == ssr["focal_tweet_id"]):
        focal_text = ""
        refs = []
        if relay_tweet is not None:
            note_res = relay_tweet.get("note_tweet", {}).get("note_tweet_results", {}).get("result", {})
            if isinstance(note_res, dict) and note_res.get("text"):
                focal_text, refs = _expand_tco_urls(
                    note_res["text"],
                    note_res.get("entity_set", {}).get("urls"),
                )
            else:
                raw_text = (
                    relay_tweet.get("details", {}).get("full_text")
                    or relay_tweet.get("legacy", {}).get("full_text")
                    or ""
                )
                if raw_text:
                    focal_text, refs = _expand_tco_urls(
                        raw_text,
                        relay_tweet.get("legacy", {}).get("entities", {}).get("urls"),
                    )
        if not focal_text:
            focal_text = ssr.get("body_text", "").strip()
        if focal_text and not re.fullmatch(r"https?://(?:t\.co/\S+|(?:x|twitter)\.com/i/article/\d+)", focal_text.strip()):
            title = _clean_title(
                page.meta.get("og:title") or page.content("title"),
                meta["handle"],
                meta["author"],
                page.meta.get("og:description"),
                fallback=f"@{meta['handle']} on X" if meta["handle"] else "",
            )
            return Material(focal_text.strip(), "x_post", title, _clean_details(meta, referenced_urls=refs))

    raise ReadError(
        "X 原页未返回可读的文章或主贴正文（可能需要登录，或仅返回了页面框架/评论区）。"
        "可改用已授权的浏览器读取正文，再用 --from 交给读取器。"
    )
