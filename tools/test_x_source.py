"""Offline public-page shapes for the X reader. Each neighboring post has distinct text."""

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import intake
from source_text import ReadError
from x_source import declared_x_url, parse_x_html


STATUS = "https://x.com/reader/status/11"


def route(post_id, *, article=False, document="", preview=""):
    meta = 'metadata:{focalTweetId:"%s",hasArticle:%s,headMetadata:{bodyText:%s}}' % (
        post_id, "true" if article else "false", json.dumps(preview))
    return "{" + meta + (",articleDocument:" + document if document else "") + "}"


def doc(html):
    return '{parts:[{type:"html",html:' + json.dumps(html) + '}]}'


def tweet(post_id, text, **fields):
    return {"__typename": "Tweet", "rest_id": post_id, "details": {"full_text": text}, **fields}


def relay(value):
    return '{kind:"Result.Ok",value:' + json.dumps(json.dumps({"data": value})) + "}"


def page(*records, canonical=STATUS):
    return '<link rel="canonical" href="' + canonical + '"><script>data=[' + ",".join(records) + "]</script>"


def rendered(post_id, text, extra=""):
    return (f'<article data-testid="tweet"><div data-testid="tweetText">{text}</div>{extra}'
            f'<a href="/user/status/{post_id}"><time datetime="2026-01-02">2 Jan</time></a></article>')


def timeline_post(post_id, author="42", parent=None, *, display="SelfThread"):
    account = {"rest_id": author, "core": {"screen_name": "writer"}}
    post = tweet(post_id, "Selected text" if post_id == "11" else "Neighbor text",
                 core={"user_results": {"result": account}})
    if parent:
        post.update(reply_to_results={"rest_id": parent}, reply_to_user_results={"rest_id": "42"})
    return {"__typename": "TimelineTimelineItem", "content": {
        "__typename": "TimelineTweet", "display_type": display,
        "tweet_results": {"rest_id": post_id, "result": post},
    }}


def conversation(focal, *neighbors, response_id="11"):
    entries = [{"entry_id": "tweet-11", "content": focal},
               {"content": {"__typename": "TimelineTimelineModule",
                            "items": [{"item": neighbor} for neighbor in neighbors]}}]
    standalone = focal["content"]["tweet_results"]["result"].copy()
    standalone.pop("reply_to_results", None)
    standalone.pop("reply_to_user_results", None)
    return page(route("11"), relay({
        "tweet_result_by_rest_id": {"rest_id": response_id, "result": standalone},
        "threaded_conversation_with_injections_v2": {"instructions": [
            {"__typename": "TimelineAddEntries", "entries": entries}
        ]},
    }))


class XSourceTests(unittest.TestCase):
    def test_thread_links_require_direct_same_author_timeline_evidence(self):
        focal = timeline_post("11", parent="10")
        child = timeline_post("12", parent="11")
        quoted = timeline_post("99", parent="11")["content"]["tweet_results"]
        child["content"]["tweet_results"]["result"]["quoted_tweet_results"] = quoted
        html = conversation(focal, timeline_post("10", display="Tweet"), child, child,
                            timeline_post("20", author="77", parent="11"),
                            timeline_post("21", parent="11", display="Tweet"), timeline_post("22", parent="12"))
        material = parse_x_html(html, STATUS)
        self.assertEqual(material.text, "Selected text")
        self.assertFalse(material.partial)
        self.assertEqual(material.details["thread"], {
            "coverage": "partial", "previous_url": "https://x.com/writer/status/10",
            "next_urls": ["https://x.com/writer/status/12"],
        })

    def test_thread_with_unseen_parent_keeps_gap_separate_from_post_text(self):
        material = parse_x_html(conversation(timeline_post("11", parent="10")), STATUS)
        self.assertEqual(material.details["thread"], {"coverage": "partial", "unseen_parent_id": "10"})
        self.assertEqual(material.text, "Selected text")
        self.assertFalse(material.partial)

    def test_thread_context_preserves_a_truncated_post_and_rejects_conflicting_authors(self):
        focal = timeline_post("11", parent="10")
        focal["content"]["tweet_results"]["result"]["legacy"] = {"truncated": True}
        html = conversation(focal, timeline_post("10", author="77"), timeline_post("12", parent="11"),
                            timeline_post("12", author="77", parent="11"))
        post = parse_x_html(html, STATUS)
        self.assertTrue(post.partial)
        self.assertEqual(post.details["scope"], "visible post preview")
        self.assertEqual(post.details["thread"], {"coverage": "partial"})

    def test_ordinary_replies_and_foreign_thread_context_do_not_mark_focal_post(self):
        for html in (conversation(timeline_post("11", display="Tweet"), timeline_post("12", parent="11")),
                     conversation(timeline_post("11"), timeline_post("12"), response_id="90")):
            with self.subTest(html=html):
                self.assertNotIn("thread", parse_x_html(html, STATUS).details)

    def test_refresh_adds_thread_coverage_without_following_neighbors(self):
        single = page(route("11"), relay(tweet("11", "Selected text")))
        thread = conversation(timeline_post("11"), timeline_post("12", parent="11"))
        with tempfile.TemporaryDirectory() as folder:
            vault = Path(folder)
            with patch.object(intake, "fetch", return_value=(single.encode(), STATUS, "text/html", "utf-8")):
                old = intake.intake(vault, STATUS)
            with patch.object(intake, "fetch", return_value=(thread.encode(), STATUS, "text/html", "utf-8")) as get:
                self.assertTrue(intake.intake(vault, STATUS)["cached"])
                get.assert_not_called()
                fresh = intake.intake(vault, STATUS, refresh=True)
                get.assert_called_once_with(STATUS)
            self.assertEqual((fresh["status"], fresh["sha256"]), ("ready", old["sha256"]))
            self.assertEqual(fresh["details"]["thread"]["next_urls"], ["https://x.com/writer/status/12"])
            self.assertEqual((vault / fresh["material"]).read_text().strip(), "Selected text")

    def test_two_article_routes_bind_their_own_body(self):
        other = route("22", article=True, document=doc("<p>Reply Article</p>"))
        correct = route("11", article=True, document=doc("<p>Original Article</p>"))
        self.assertEqual(parse_x_html(page(other, correct), STATUS).text, "Original Article")
        with self.assertRaises(ReadError):
            parse_x_html(page(other), STATUS)

    def test_article_for_reply_does_not_replace_a_regular_focal_post(self):
        other = route("22", article=True, document=doc("<p>Reply Article</p>"))
        quoted = tweet("22", "Quoted tweet")
        main = tweet("11", "Focal post", quoted_status_result={"result": quoted})
        post = parse_x_html(page(other, route("11"), relay({"result": main})), STATUS)
        self.assertEqual((post.kind, post.text, post.details["status_id"]), ("x_post", "Focal post", "11"))
        with self.assertRaises(ReadError):
            parse_x_html(page(route("11"), relay({"tweet_results": {"rest_id": "11", "result": quoted}})), STATUS)

    def test_note_text_and_references_only_from_the_focal_object(self):
        text = 'Compare https://t.co/ab with https://t.co/a. 字🙂\nSecond line'
        entities = [{"url": "https://t.co/a", "expanded_url": "https://example.org/one"},
                    {"url": "https://t.co/ab", "expanded_url": "https://example.org/two"},
                    {"url": "https://t.co/unused", "expanded_url": "https://example.org/unrelated"}]
        main = tweet("11", "Short preview", note_tweet={"note_tweet_results": {
            "result": {"text": text, "entity_set": {"urls": entities}}}})
        html = page(route("11"), relay({"entries": [tweet("22", "Reply"), main]}))
        material = parse_x_html(html, STATUS)
        self.assertFalse(material.partial)
        self.assertEqual(material.text, 'Compare https://example.org/two with https://example.org/one. 字🙂\nSecond line')
        self.assertEqual(material.details["referenced_urls"], ["https://example.org/two", "https://example.org/one"])

    def test_short_post_under_generic_open_graph_article_type(self):
        html = '<meta property="og:type" content="article">' + page(relay({
            "tweet_result_by_rest_id": {"result": tweet("11", "A &amp; B")}}))
        self.assertEqual(parse_x_html(html, STATUS).text, "A & B")

    def test_preview_is_partial(self):
        for html in (
            page(route("11", preview="Head preview")),
            page(relay(tweet("11", "Preview", legacy={"truncated": True}))),
            page(relay(tweet("11", "Preview", note_tweet={"note_tweet_results": {}}))),
            rendered("11", "Preview", '<a data-testid="tweet-text-show-more-link">More</a>'),
        ):
            with self.subTest(html=html):
                material = parse_x_html(html, STATUS)
                self.assertTrue(material.partial)
                self.assertEqual(material.details["scope"], "visible post preview")

    def test_saved_dom_uses_own_time_not_quote_or_reply(self):
        quote = '<div role="link" data-testid="quoteTweet">' + rendered("33", "Quote") + '</div>'
        main = rendered("11", '<span>Line</span> <span>1</span>\n\nLine 2 <img alt="🙂" src="https://example.org/emoji/1.svg">', quote)
        html = rendered("22", "Reply") + main + rendered("44", "Other")
        result = parse_x_html(html, STATUS)
        self.assertEqual((result.text, result.details["published_at"]), ("Line 1\n\nLine 2 🙂", "2026-01-02"))
        with self.assertRaises(ReadError):
            parse_x_html(rendered("22", "Reply", quote), STATUS)
        with self.assertRaises(ReadError):
            parse_x_html(rendered("22", "Reply") + '<div data-testid="twitterArticleReadView">Unowned</div>', STATUS)

    def test_saved_article_requires_matching_identity(self):
        body = '<div data-testid="twitterArticleReadView">Article body</div>'
        self.assertEqual(parse_x_html(page() + body, STATUS).text, "Article body")
        self.assertEqual(declared_x_url('<link rel="canonical" href="https://x.com/reader">'), "https://x.com/reader")
        with self.assertRaises(ReadError):
            parse_x_html(page(canonical="https://x.com/other/status/22") + body, STATUS)

    def test_real_article_id_must_belong_to_exact_tweet(self):
        data = {"article_results": {"result": {"rest_id": "55", "title": "Attached Article"}}}
        html = page(route("11", article=True, document=doc("<p>Body</p>")), relay(tweet("11", "link", article=data)))
        result = parse_x_html(html, "https://x.com/i/article/55")
        self.assertEqual(result.details, {"article_id": "55", "status_id": "11"})
        with self.assertRaises(ReadError):
            parse_x_html(html, "https://x.com/i/article/999")

    def test_escaped_article_content_is_decoded_once(self):
        encoded = r'"\x3cp>\u4e2d\u{1F642}\uD83D\uDE42 &amp;amp; \\n \"say\"\x3c/p>"'
        document = '{parts:[{type:"html",html:' + encoded + '}]}'
        result = parse_x_html(page(route("11", article=True, document=document)), STATUS)
        self.assertEqual(result.text, '中🙂🙂 &amp; \\n "say"')
        encoded = '"<p>a' + '\\\n' + 'b</p>"'
        result = parse_x_html(page(route("11", article=True, document='{parts:[{type:"html",html:' + encoded + '}]}')), STATUS)
        self.assertEqual(result.text, 'ab')

    def test_unreadable_or_invalid_article_does_not_borrow_sibling_content(self):
        other = route("22", article=True, document=doc("<p>Wrong article</p>"))
        for bad in ('{contentKey:"garbled"}', '{parts:[]}', doc('<p>Part of the article'),
                    doc('<figure><img alt="body" src="pic"></figure>'),
                    '{contentKey:"[[\\"a\\",\\"atomic\\",\\"\\"]]"}', r'{parts:[{type:"html",html:"\uZZZZ"}]}',
                    '{parts:[{type:"html",html:"<p>unfinished article</p>"},{type:"html"}]}'):
            with self.subTest(document=bad):
                with self.assertRaises(ReadError):
                    parse_x_html(page(route("11", article=True, document=bad), other), STATUS)
        foreign = doc('<p>External</p>')
        invalid = page(route("11", article=True), relay(tweet("22", foreign)))
        with self.assertRaises(ReadError):
            parse_x_html(invalid, STATUS)

    def test_article_only_lists_public_links_from_the_body(self):
        body = ('<p><a href="https://user:pass@example.org/path">First</a> and '
                '<a href="https://example.org/p?a=1&amp;b=2">Second</a></p>')
        result = parse_x_html(page(route("11", article=True, document=doc(body))), STATUS)
        self.assertEqual(result.text, 'First and [Second](https://example.org/p?a=1&b=2)')
        self.assertEqual(result.details["referenced_urls"], ["https://example.org/p?a=1&b=2"])


if __name__ == "__main__":
    unittest.main()
