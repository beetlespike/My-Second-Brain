"""Read public X posts and X Articles from X HTML without executing page scripts."""

from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser
import json
import re
from urllib.parse import urljoin, urlsplit

from source_text import Material, ReadError


X_HOSTS = {
    "x.com",
    "www.x.com",
    "mobile.x.com",
    "twitter.com",
    "www.twitter.com",
    "mobile.twitter.com",
}
STATUS_PATH = re.compile(
    r"^/(?P<user>[A-Za-z0-9_]+|i/web|i)/(?P<kind>status|statuses|article)/(?P<id>[0-9]+)(?:/.*)?$"
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


def _text(value):
    if not isinstance(value, str):
        return ""
    if re.search(r"[\ud800-\udfff]", value):
        return value.encode("utf-16", "surrogatepass").decode("utf-16", "replace")
    return value


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
        if tok[1:] in ("\n", "\r", "\r\n"):
            return ""
        if tok[1] in ("x", "u"):
            digits = tok[2:].strip("{}")
            if not digits or int(digits, 16) > 0x10ffff:
                raise ValueError("Invalid code point in serialized X data")
            return chr(int(digits, 16))
        return tok[1:]

    decoded = re.sub(r"\\(?:u\{[0-9a-fA-F]{1,6}\}|u[0-9a-fA-F]{4}|x[0-9a-fA-F]{2}|\r\n|[\s\S])", repl, raw_inner)
    return _text(decoded)


class _ArticleHTMLParser(HTMLParser):
    """Convert X Article SSR or rendered DOM HTML into clean Markdown."""

    skip_tags = {"script", "style", "template", "noscript", "svg"}
    void_tags = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self, html, *, tweet_text=False):
        super().__init__(convert_charrefs=True)
        self.tweet_text = tweet_text
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
        self.readable = False
        self.images_listed = 0
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
        text = "".join(self.block_buf)
        self.block_buf = []
        kind = self.block_kind
        self.block_kind = None
        if not text.strip():
            return
        if kind == "pre":
            code = text.strip("\n")
            fence = "`" * max(3, 1 + max((len(m[0]) for m in re.finditer(r"`+", code)), default=0))
            self.blocks.append(f"{fence}\n{code}\n{fence}")
            return
        text = text.replace("\xa0", " ").strip()
        if self.tweet_text:
            self.blocks.append(text)
        elif kind and kind.startswith("h") and len(kind) == 2 and kind[1].isdigit():
            level = int(kind[1])
            clean = " ".join(line.strip() for line in text.splitlines() if line.strip())
            self.blocks.append(f"{'#' * level} {clean}")
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
        if _public_link(href) and not ARTICLE_MEDIA_HREF.match(href):
            if href not in self.referenced_urls:
                self.referenced_urls.append(href)

    def handle_starttag(self, tag, attrs):
        attr_map = {k: v or "" for k, v in attrs}
        if tag not in self.void_tags:
            self.tag_stack.append(tag)
        embedded = attr_map.get("data-testid") in ("tweet", "quoteTweet", "quotedTweet", "tweet-text-show-more-link")
        if tag in self.skip_tags or self.skip_depth or tag == "article" or embedded:
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
                href = _link_target(href)
            self.link_href = href
            self.link_buf = []
            self.link_has_image = False
        elif tag == "img":
            src = (attr_map.get("src") or attr_map.get("data-src") or "").strip()
            alt = " ".join((attr_map.get("alt") or "").split())
            if self.tweet_text and alt and "emoji" in src:
                self.readable = True
                self._current_target().append(alt)
                return
            self.images_listed += 1
            marker = f"[Image {self.images_listed}: {alt}]" if alt else f"[Image {self.images_listed}]"
            if self.link_buf is not None:
                self.link_has_image = True
            self.block_buf.append(marker)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.void_tags:
            self.handle_endtag(tag)

    def handle_data(self, data):
        if self.skip_depth:
            return
        if data.strip() and self.block_kind not in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.readable = True
        if self.pre_depth == 0 and not self.tweet_text:
            data = re.sub(r"[ \t\r\n]+", " ", data)
        if not self.block_kind and not data.strip() and not self.block_buf and self.link_buf is None and not self.tweet_text:
            return
        self._current_target().append(data)

    def handle_endtag(self, tag):
        if tag in self.void_tags or tag not in self.tag_stack:
            return
        if self.skip_depth:
            self.skip_depth -= 1
        else:
            if tag == "a" and self.link_buf is not None:
                label = " ".join("".join(self.link_buf).split())
                href = self.link_href or ""
                self.link_buf = None
                self.link_href = None
                if label and not self.link_has_image:
                    if _public_link(href) and not ARTICLE_MEDIA_HREF.match(href):
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
            popped = self.tag_stack.pop()
            if popped == tag:
                break

    @property
    def markdown(self):
        return "\n\n".join(self.blocks).strip()


def _article_body(document):
    if not isinstance(document, dict):
        return None
    parts = document.get("parts")
    if isinstance(parts, list) and parts and all(isinstance(part, dict) and part.get("type") == "html"
                                               and isinstance(part.get("html"), str) for part in parts):
        parser = _ArticleHTMLParser("".join(part["html"] for part in parts))
        if parser.readable and not parser.tag_stack:
            return parser.markdown, parser.images_listed, parser.referenced_urls
    try:
        arr = json.loads(document.get("contentKey") or "[]")
    except (TypeError, ValueError, RecursionError):
        return None
    if not isinstance(arr, list):
        return None
    readable = False
    blocks = []
    image_count = 0
    for item in arr:
        if not isinstance(item, list) or len(item) < 3 or not isinstance(item[1], str):
            return None
        kind = item[1]
        text = _text(item[2]).strip()
        if kind == "atomic":
            image_count += 1
            blocks.append(f"[Image {image_count}]")
            continue
        if not text:
            continue
        if kind not in ("header-one", "header-two", "header-three"):
            readable = True
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
    if not readable:
        return None
    return body, image_count, []


# The public router serializes data as JS object literals with optional $R[n] assignments.
# Keep object and array boundaries while reading its data. Other script expressions are inert.
_JS_TOKENS = re.compile(r"""
    (?P<string>"(?:\\[\s\S]|[^"\\])*"|'(?:\\[\s\S]|[^'\\])*'|`(?:\\[\s\S]|[^`\\])*`)
    |(?P<comment>//[^\r\n]*|/\*[\s\S]*?\*/)
    |(?P<assignment>\$R\[\d+\]\s*=)
    |(?P<field>[\w$]+)\s*:\s*
    |(?P<boolean>![01]|\btrue\b|\bfalse\b)
    |(?P<word>[\w$]+)
    |(?P<other>[^\s])
""", re.VERBOSE)


def _router_records(script):
    if not any(key in script for key in ("focalTweetId", "articleDocument", "Result.Ok")):
        return
    stack = [{}]
    key = None
    for token in _JS_TOKENS.finditer(script):
        kind = token.lastgroup
        if kind in ("assignment", "comment"):
            continue
        if kind == "field":
            key = token["field"]
            continue
        char = token[0]
        parent = stack[-1]
        if char in ("}", "]"):
            if len(stack) > 1:
                if (char == "}") != isinstance(parent, dict):
                    return
                stack.pop()
                if isinstance(parent, dict) and ("metadata" in parent or parent.get("kind") == "Result.Ok"):
                    yield parent
            key = None
            continue
        if char in ("{", "["):
            value = {} if char == "{" else []
            stack.append(value)
        elif kind == "string":
            try:
                value = _unescape_js_string(char[1:-1])
            except ValueError:
                value = None
        elif char in ('"', "'", "`"):
            return
        elif kind == "boolean":
            value = char in ("true", "!0")
        else:
            key = None
            continue
        if isinstance(parent, dict):
            if key is not None:
                parent[key] = value
        else:
            parent.append(value)
        key = None
    if len(stack) == 1 and "metadata" in stack[0]:
        yield stack[0]


def _public_link(href):
    if not isinstance(href, str):
        return False
    try:
        url = urlsplit(href)
        return url.scheme in ("https", "http") and bool(url.hostname) and url.username is None and url.password is None
    except ValueError:
        return False


def _link_target(href):
    try:
        return urljoin("https://x.com", href)
    except ValueError:
        return ""


def _identity(url):
    if not _public_link(url) or not is_x_url(url):
        return None
    match = STATUS_PATH.fullmatch(urlsplit(url).path)
    if match:
        return ("article" if match["kind"] == "article" else "status", match["id"])
    return None


class _SavedPage(HTMLParser):
    """Locate closed rendered regions, their owning tweet's time permalink, and router data."""

    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.html = html
        self.line_starts = [0] + [m.end() for m in re.finditer("\n", html)]
        self.stack = []
        self.urls = []
        self.meta = {}
        self.title = []
        self.scripts = []
        self.regions = []
        self.feed(html)
        self.close()

    def _offset(self):
        line, column = self.getpos()
        return self.line_starts[line - 1] + column

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        testid = attrs.get("data-testid")
        parent = self.stack[-1] if self.stack else {}
        owner = parent.get("owner")
        quoted = parent.get("quoted", False) or testid in ("quoteTweet", "quotedTweet") or (owner is not None and attrs.get("role") == "link" and tag != "a")
        if tag == "article" or testid == "tweet":
            owner = {"ids": set(), "time": ""}
        frame = {"tag": tag, "owner": owner, "quoted": quoted}
        if tag == "script" and owner is None and not quoted:
            frame["router_script"] = not any(f["tag"] in ("template", "noscript", "pre", "code") for f in self.stack)
        if all(f["tag"] in ("html", "head") for f in self.stack):
            if tag == "meta":
                name = (attrs.get("property") or attrs.get("name") or "").lower()
                content = attrs.get("content") or ""
                self.meta.setdefault(name, content)
                if name == "og:url":
                    self.urls.append(content)
            if tag == "link" and "canonical" in (attrs.get("rel") or "").lower().split():
                self.urls.append(attrs.get("href") or "")
            if tag == "title":
                frame["head_title"] = True
        if owner is not None and not quoted and testid == "tweet-text-show-more-link":
            owner["truncated"] = True
        if not quoted and tag == "a" and owner is not None:
            url = _link_target(attrs.get("href") or "")
            frame["permalink"] = _identity(url)
            if frame["permalink"]:
                frame["handle"] = STATUS_PATH.fullmatch(urlsplit(url).path)["user"]
        if not quoted and tag == "time" and owner is not None:
            anchor = next((f for f in reversed(self.stack) if f["tag"] == "a"), {})
            link = anchor.get("permalink")
            if link and link[0] == "status":
                if anchor["handle"] not in ("i", "i/web"):
                    owner["handle"] = anchor["handle"]
                owner["ids"].add(link[1])
                owner["time"] = attrs.get("datetime") or ""
        if not quoted and testid in ("twitterArticleReadView", "longformRichTextComponent", "tweetText"):
            frame["region"] = testid
            frame["start"] = self._offset() + len(self.get_starttag_text())
        if tag not in _ArticleHTMLParser.void_tags:
            self.stack.append(frame)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in _ArticleHTMLParser.void_tags:
            self.handle_endtag(tag)

    def handle_data(self, data):
        if self.stack and self.stack[-1].get("router_script"):
            self.scripts.append(data)
        elif self.stack and self.stack[-1].get("head_title"):
            self.title.append(data)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            frame = self.stack[i]
            if frame["tag"] != tag:
                continue
            del self.stack[i:]
            if "region" in frame:
                self.regions.append((frame["region"], frame["owner"], self.html[frame["start"]:self._offset()]))
            return


def declared_x_url(html):
    """Return the X permalink declared by a saved page, when present."""
    urls = [url for url in _SavedPage(html).urls if _public_link(url) and is_x_url(url)]
    return next((url for url in urls if _identity(url)), urls[0] if urls else "")


def _expand_tco_urls(text, entities):
    urls = {}
    for entity in entities if isinstance(entities, list) else ():
        if isinstance(entity, dict) and isinstance(entity.get("url"), str) and _public_link(entity.get("expanded_url") or ""):
            urls[entity["url"]] = entity["expanded_url"]
    refs = []

    def expand(match):
        short = match[0]
        href = urls.get(short)
        if not href:
            return short
        if href not in refs:
            refs.append(href)
        return href

    return re.sub(r"https?://t\.co/[A-Za-z0-9_]+", expand, text), refs


def _tweet_results(node, focal_id):
    pending = [node]
    while pending:
        value = pending.pop()
        if isinstance(value, dict):
            if value.get("__typename") == "Tweet" and value.get("rest_id") == focal_id:
                yield value
                continue
            pending.extend(reversed(list(value.values())))
        elif isinstance(value, list):
            pending.extend(reversed(value))


def _object(node, *keys):
    for key in keys:
        node = node.get(key) if isinstance(node, dict) else None
    return node if isinstance(node, dict) else {}


def _clean_title(raw_title, handle="", author="", description="", fallback=""):
    title = _text(raw_title).strip()
    if title:
        title = re.sub(r"\s*/\s*X$", "", title).strip()
        quoted = re.match(r'^.+?\s+on\s+X:\s*"(.*)"$', title, re.S)
        if quoted:
            title = quoted.group(1).strip()
    if not title or re.fullmatch(r"https?://t\.co/\S+", title):
        title = _text(description).strip()
    if not title:
        title = fallback or (f"@{handle} on X" if handle else author or "X Post")
    return title.splitlines()[0].strip()


def _clean_details(meta, images_listed=None, referenced_urls=()):
    details = {}
    for key in ("author", "handle", "published_at"):
        if value := _text(meta.get(key)):
            details[key] = value
    if images_listed:
        details["images_listed"] = images_listed
        details["images_read"] = False
    if referenced_urls:
        details["referenced_urls"] = list(referenced_urls)
    return details


def parse_x_html(html, url=""):
    """Read the requested post, or its own Article, from a public or saved X page."""
    error = "X 原页未返回能与目标链接核对的文章或主贴正文。可提供该帖的完整保存页或正文。"
    dom = _SavedPage(html)
    declared = {_identity(u) for u in dom.urls if _identity(u)}
    requested = _identity(url) if url else None
    if url and not requested:
        raise ReadError(error)
    records = [r for script in dom.scripts for r in _router_records(script)]
    routes = [r for r in records if isinstance(r.get("metadata"), dict)]
    status_ids = {value for kind, value in declared if kind == "status"}
    article_ids = {value for kind, value in declared if kind == "article"}
    if requested:
        (status_ids if requested[0] == "status" else article_ids).add(requested[1])
    if len(status_ids) > 1 or len(article_ids) > 1:
        raise ReadError(error)
    routes_by_id = {}
    for route in routes:
        identities = {value for value in (route.get("focalTweetId"), route["metadata"].get("focalTweetId"))
                      if isinstance(value, str) and value.isascii() and value.isdecimal()}
        canonical = _identity(_object(route["metadata"], "headMetadata").get("canonicalUrl") or "")
        if canonical and canonical[0] == "status":
            identities.add(canonical[1])
        if len(identities) == 1:
            routes_by_id.setdefault(identities.pop(), []).append(route)
        elif identities:
            raise ReadError(error)
    focal_id = next(iter(status_ids), None)
    if not focal_id and len(routes_by_id) == 1:
        focal_id = next(iter(routes_by_id))
    if focal_id and routes_by_id and focal_id not in routes_by_id:
        raise ReadError(error)
    article_id = next(iter(article_ids), None)
    if not (focal_id or article_id):
        raise ReadError(error)
    matching_routes = routes_by_id.get(focal_id, [])
    if len(matching_routes) > 1:
        raise ReadError(error)
    route = matching_routes[0] if matching_routes else {}
    page_identity = bool(declared or route)
    meta = _object(route, "metadata")
    head = _object(meta, "headMetadata")
    tweets = []
    if focal_id:
        for record in records:
            if record.get("kind") != "Result.Ok" or not isinstance(record.get("value"), str):
                continue
            try:
                data = json.loads(record["value"])
            except (ValueError, RecursionError):
                continue
            tweets.extend(_tweet_results(data, focal_id))

    attachment = next((result for tweet in tweets
                       if (result := _object(tweet, "article", "article_results", "result"))), {})
    attached_id = _text(attachment.get("rest_id"))
    if article_id and focal_id and attached_id != article_id:
        raise ReadError(error)
    if attached_id:
        article_id = attached_id
    user = next((result for tweet in tweets if (result := _object(tweet, "core", "user_results", "result"))), {})
    user_core = _object(user, "core") or _object(user, "legacy")
    details = _clean_details({
        "author": user_core.get("name") or meta.get("authorName"),
        "handle": user_core.get("screen_name") or _object(head, "author").get("screenName")
                  or dom.meta.get("twitter:creator", "").lstrip("@"),
        "published_at": head.get("publishedTime") or next((t["legacy"]["created_at"] for t in tweets
                                                         if _object(t, "legacy").get("created_at")), ""),
    })
    if "published_at" not in details:
        for tweet in tweets:
            stamp = _object(tweet, "details").get("created_at_ms")
            if type(stamp) is int and 0 <= stamp < 253402300799000:
                moment = datetime.fromtimestamp(stamp / 1000, timezone.utc)
                details["published_at"] = moment.isoformat(timespec="milliseconds").replace("+00:00", "Z")
                break
    if focal_id:
        details["status_id"] = focal_id
    if article_id:
        details["article_id"] = article_id
    title = _clean_title(attachment.get("title") or dom.meta.get("og:title") or "".join(dom.title),
                         details.get("handle"), details.get("author"), dom.meta.get("og:description"))
    expects_article = bool(attachment or article_ids or meta.get("hasArticle") is True)
    plain_post = (meta.get("hasArticle") is False or any(t.get("note_tweet") for t in tweets)) and not attachment
    if expects_article and not plain_post:
        result = _article_body(route.get("articleDocument"))
        if result:
            body, images, refs = result
            details.update(_clean_details({}, images, refs))
            return Material(body, "x_article", title, details)

    # A recorded time permalink ties the tweet container to one post. A standalone
    # Article view can also use the canonical page identity when it has no tweet wrapper.
    regions = [(name, owner, fragment) for name, owner, fragment in dom.regions
               if (owner is not None and owner["ids"] == {focal_id}) or (owner is None and page_identity)]
    for kind in ("longformRichTextComponent", "twitterArticleReadView"):
        candidates = [(owner, body) for name, owner, body in regions if name == kind]
        if len(candidates) == 1 and not plain_post:
            owner, fragment = candidates[0]
            parser = _ArticleHTMLParser(fragment)
            if parser.readable:
                details.update(_clean_details({}, parser.images_listed, parser.referenced_urls))
                if owner and owner["time"]:
                    details.setdefault("published_at", owner["time"])
                if owner and owner.get("handle"):
                    details.setdefault("handle", owner["handle"])
                return Material(parser.markdown, "x_article", title, details)
    if expects_article:
        raise ReadError(error)
    # Note Tweet text is complete. Its legacy counterpart may contain only the preview.
    for tweet in tweets:
        note = _object(tweet, "note_tweet", "note_tweet_results", "result")
        if isinstance(note.get("text"), str) and note["text"].strip():
            text, refs = _expand_tco_urls(_text(note["text"]), _object(note, "entity_set").get("urls"))
            details.update(_clean_details({}, referenced_urls=refs))
            return Material(text.strip(), "x_post", title, details)
    text, refs = "", []
    partial = any(tweet.get("note_tweet") or _object(tweet, "legacy").get("truncated") for tweet in tweets)
    for tweet in tweets:
        raw = _object(tweet, "details").get("full_text") or _object(tweet, "legacy").get("full_text")
        if isinstance(raw, str) and raw.strip():
            entities = tweet.get("url_entities") or _object(tweet, "legacy", "entities").get("urls")
            # X escapes markup characters in short-post text. Ordinary ampersands in
            # code or prose may resemble an HTML entity without the terminating semi-colon.
            raw = re.sub(r"&(amp|lt|gt|quot|#39);", lambda m: unescape(m[0]), _text(raw))
            text, refs = _expand_tco_urls(raw, entities)
            break
    if not text:
        candidates = [(owner, body) for name, owner, body in regions if name == "tweetText" and owner]
        if len(candidates) == 1:
            owner, fragment = candidates[0]
            parser = _ArticleHTMLParser(fragment, tweet_text=True)
            if parser.readable:
                if owner["time"]:
                    details.setdefault("published_at", owner["time"])
                if owner.get("handle"):
                    details.setdefault("handle", owner["handle"])
                details.update(_clean_details({}, referenced_urls=parser.referenced_urls))
                partial = partial or owner.get("truncated", False)
                if partial:
                    details["scope"] = "visible post preview"
                return Material(parser.markdown, "x_post", title, details, partial=partial)
        if not candidates:
            text = head.get("bodyText") or meta.get("bodyText") or ""
            partial = True
    if isinstance(text, str) and text.strip() and not re.fullmatch(r"https?://(?:t\.co/\S+|(?:x|twitter)\.com/i/article/\d+)", text.strip()):
        details.update(_clean_details({}, referenced_urls=refs))
        if partial:
            details["scope"] = "visible post preview"
        return Material(text.strip(), "x_post", title, details, partial=partial)
    raise ReadError(error)
