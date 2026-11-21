"""Offline regressions for source intake and evidence extraction."""

import codecs
from email.message import Message
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from urllib.error import HTTPError, URLError
from urllib.request import Request
from unittest.mock import patch

import intake
from source_text import Material, Page, ReadError, caption_material, pdf_material
from video_source import shared_runtimes, tracks

WECHAT = "https://mp.weixin.qq.com/s/fixture"
PAPER = "https://arxiv.org/abs/2309.06180v1"
VIDEO = "https://www.youtube.com/watch?v=abcdefghijk"
SRT = b"1\n00:00:01,000 --> 00:00:03,500\nA worked example.\n"


def saved_x_article(url, body="A saved article paragraph."):
    return ('<html><head><link rel="canonical" href="' + url + '"></head><body>'
            '<div data-testid="twitterArticleReadView"><p>' + body + '</p></div></body></html>')


class SourceIntakeTests(unittest.TestCase):
    def test_network_denial_has_a_different_next_action_from_missing_captions(self):
        import contextlib
        import io
        from video_source import run_ytdlp

        failure = subprocess.CompletedProcess(
            [], 1, stdout="", stderr="Could not resolve host: public.example"
        )
        with patch("video_source.subprocess.run", return_value=failure):
            with self.assertRaises(intake.NetworkUnavailable):
                run_ytdlp("yt-dlp", [], self.root, 10)
        output = io.StringIO()
        with (
            patch.object(sys, "argv", ["intake.py", PAPER, "--root", str(self.root)]),
            contextlib.redirect_stdout(output),
        ):
            with patch.object(intake, "fetch", side_effect=intake.NetworkUnavailable("DNS unavailable")):
                self.assertEqual(intake.main(), 2)
        self.assertEqual(json.loads(output.getvalue())["status"], "needs_network")

    def test_publisher_caption_url_and_multiple_players(self):
        caption = "https://course.example/right.srt"
        page = (
            b'<video id="other-player"><track kind="captions" src="/wrong.srt"></video>'
            b'<video id="abcdefghijk"><track kind="captions" src="/right.srt" srclang="en"></video>'
        )
        with patch.object(intake, "fetch", return_value=(SRT, caption, "text/plain", None)) as get:
            material = intake.publisher_track(VIDEO, page, "https://course.example/lesson", None, "en")
            get.assert_called_once_with(caption)
            self.assertEqual(material.kind, "publisher_captions")
            direct = intake.intake(self.root, VIDEO, caption)
            self.assertEqual((direct["details"]["cues"], direct["evidence_source"]), (1, caption))

    def test_explicit_arxiv_pdf_preserves_the_requested_version_and_format(self):
        url = "https://arxiv.org/pdf/2309.06180v1"
        with patch.object(
            intake, "fetch", return_value=(b"%PDF-example", url, "application/pdf", None)
        ) as get:
            with patch.object(intake, "pdf_material", return_value=Material("## Page 1\nSample", "pdf_text")):
                result = intake.intake(self.root, url)
        get.assert_called_once_with(url)
        self.assertEqual((result["evidence"], result["details"]["edition"]), ("pdf_text", "2309.06180v1"))

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()

    def test_wechat_uses_closed_article_body_and_ignores_scripts(self):
        p = Page(
            '<h1 id="activity-name">Title</h1><nav>menu</nav><div id="js_content"><p>First paragraph.</p>'
            '<script>ignore me</script><p>Second paragraph.</p><img data-src="sample.jpg"></div>footer'
        )
        m = p.article(wechat=True)
        self.assertEqual(
            (m.text, m.title, m.kind), ("First paragraph.\nSecond paragraph.", "Title", "wechat_body")
        )
        self.assertEqual(m.details["images_listed"], 1)
        self.assertFalse(m.partial)
        self.assertTrue(Page('<div id="js_content"><p>Part only.</p>').article(wechat=True).partial)
        with self.assertRaises(ReadError):
            Page("<main>Access verification</main>").article(wechat=True)

    def test_paper_landing_and_html_with_only_titles_are_not_a_full_text(self):
        abstract = b'<html><article><h1>Paper</h1><div class="ltx_abstract">An abstract.</div>'
        meta = b'<html><blockquote class="abstract">An abstract.</blockquote></html>'

        def fetch(url):
            if "/pdf/" in url:
                raise ReadError("PDF missing")
            return (
                meta
                if "/abs/" in url
                else abstract + b"<section><h2>Only a heading</h2></section></article></html>",
                url,
                "text/html",
                None,
            )

        with patch.object(intake, "fetch", side_effect=fetch) as requests:
            r = intake.intake(self.root, PAPER)
        self.assertEqual((r["status"], r["evidence"]), ("partial", "abstract"))
        self.assertEqual(
            [c.args[0] for c in requests.call_args_list],
            [f"https://arxiv.org/{f}/2309.06180v1" for f in ("html", "pdf", "abs")],
        )
        self.assertFalse(list((self.root / ".local").rglob("evidence.json")))

    def test_caption_text_and_coverage_require_spoken_cues(self):
        for body, ext in [
            (SRT, ".srt"),
            (b"WEBVTT\n\n00:01.000 --> 00:03.500 align:start\n<b>A worked example.</b>\n", ".vtt"),
            (b'{"body":[{"from":1,"to":3.5,"content":"A worked example."}]}', ".json"),
        ]:
            m = caption_material(body, ext)
            self.assertEqual(m.details["cues"], 1)
            self.assertIn("A worked example.", m.text)
        with self.assertRaises(ReadError):
            caption_material(b"WEBVTT\n\nNOTE placeholder\n", ".vtt")

    def test_official_companion_track_must_match_the_same_video(self):
        page = b'<html><video id="abcdefghijk"><track kind="captions" srclang="en" src="/captions.srt"></video></html>'
        with patch.object(
            intake, "fetch", return_value=(SRT, "https://course.example/captions.srt", "text/plain", None)
        ):
            m = intake.publisher_track(VIDEO, page, "https://course.example/video", "utf-8", "en")
        self.assertEqual((m.kind, m.details["language"]), ("publisher_captions", "en"))
        with self.assertRaises(ReadError):
            intake.publisher_track(
                VIDEO, page.replace(b"abcdefghijk", b"other"), "https://course.example/video", None, None
            )

    def test_video_page_and_slides_cannot_stand_in_for_its_transcript(self):
        path = self.root / "watch.html"
        path.write_text("<html><main>Description only</main></html>")
        with self.assertRaises(ReadError):
            intake.intake(self.root, VIDEO, str(path))
        pdf = self.root / "slides.pdf"
        pdf.write_bytes(b"%PDF-dummy")
        with patch.object(intake, "pdf_material", return_value=Material("Slide 1", "pdf_text")):
            result = intake.intake(self.root, VIDEO, str(pdf))
        self.assertEqual(result["status"], "partial")
        self.assertIn("unverified", result["details"]["scope"])

    def test_configured_parse_refreshes_locally_and_excerpt_preserves_complete_evidence(self):
        local = self.root / ".local"
        local.mkdir()
        bundle = local / "parsed"
        bundle.mkdir()
        p = bundle / "full.md"
        p.write_text("# Method\nThe full worked method.")
        (local / "source-files.json").write_text(json.dumps({PAPER: "parsed"}))
        with patch.object(intake, "fetch", side_effect=AssertionError("no network expected")):
            first = intake.intake(self.root, PAPER)
            p.write_text("# Method\nAn updated worked method.")
            second = intake.intake(self.root, PAPER)
            self.assertNotEqual(first["sha256"], second["sha256"])
            self.assertEqual(second["details"]["origin"], "configured local file")
            section = intake.intake(self.root, PAPER, str(p), scope="excerpt")
            self.assertEqual(section["status"], "partial")
            p.unlink()
            earlier = intake.intake(self.root, PAPER)
            self.assertEqual(earlier["sha256"], second["sha256"])
            self.assertTrue(earlier["cached"])
        self.assertTrue((self.root / first["material"]).is_file())

    def test_a_corrupt_cached_body_is_read_again(self):
        with patch.object(intake, "online", return_value=Material("first body", "wechat_body")):
            first = intake.intake(self.root, WECHAT)
        (self.root / first["material"]).write_text("stale edit")
        with patch.object(intake, "online", return_value=Material("actual source", "wechat_body")) as fetch:
            second = intake.intake(self.root, WECHAT)
        fetch.assert_called_once()
        self.assertNotEqual(first["sha256"], second["sha256"])

    def test_pdf_page_coverage_and_title_only_html(self):
        result = subprocess.CompletedProcess([], 0, stdout=b"Method on page 1\f\f", stderr=b"")
        with (
            patch("source_text.shutil.which", return_value="pdftotext"),
            patch("source_text.subprocess.run", return_value=result),
        ):
            m = pdf_material(b"%PDF-test")
        self.assertEqual(m.details, {"pages": 2, "pages_with_text": 1})
        self.assertTrue(m.partial)
        with self.assertRaises(ReadError):
            Page("<article><h1>Only a title</h1></article>").article()

    def test_video_track_selection_excludes_danmaku_and_translations_by_default(self):
        info = {
            "subtitles": {"danmaku": [{"url": "x"}], "en": [{"url": "cc"}]},
            "automatic_captions": {"fr": [{"url": "?tlang=fr"}], "en": [{"url": "original"}]},
        }
        self.assertEqual(
            list(tracks(info, "bilibili", None)), [("subtitles", "en"), ("automatic_captions", "en")]
        )

    def test_cli_accepts_a_local_file_without_a_url_and_reports_failures(self):
        p = self.root / "sample.vtt"
        p.write_bytes(b"WEBVTT\n\n00:01.000 --> 00:03.500\nAn example.\n")
        cli = [sys.executable, "-B", intake.__file__, "--root", str(self.root)]
        r = subprocess.run([*cli, str(p)], text=True, capture_output=True, check=True)
        data = json.loads(r.stdout)
        self.assertEqual(data["source"], p.name)
        self.assertTrue((self.root / data["material"]).is_file())
        failed = subprocess.run([*cli, str(self.root / "missing.vtt")], text=True, capture_output=True)
        self.assertEqual((failed.returncode, json.loads(failed.stdout)["status"]), (2, "needs_material"))

    def test_mobile_share_and_plain_url_reuse_the_same_episode(self):
        subtitle = self.root / "字幕 file.srt"
        subtitle.write_bytes(SRT)
        url = "https://www.bilibili.com/video/BV1jAZwBGEwi/?p=2"
        shared = intake.intake(self.root, "【视频标题】 " + url, str(subtitle))
        self.assertEqual((shared["source"], shared["source_type"]), (url, "bilibili"))
        with patch.object(intake, "online", side_effect=AssertionError("should reuse the episode")):
            self.assertTrue(intake.intake(self.root, url)["cached"])
        self.assertEqual(intake.source_locator("[Lesson](" + VIDEO + "&t=45s)"), VIDEO + "&t=45s")
        self.assertEqual(intake.source_locator("原文：" + PAPER + "。"), PAPER)
        with self.assertRaisesRegex(ReadError, "多个网址"):
            intake.intake(self.root, PAPER + "\n" + VIDEO, str(subtitle))

    def test_captions_and_plain_text_with_unicode_byte_order_marks(self):
        line = "第一个 token 是 🐛。"
        cue = "1\r\n00:00:01,000 --> 00:00:03,500\r\n" + line + "\r\n"
        encodings = ((codecs.BOM_UTF16_LE, "utf-16-le"), (codecs.BOM_UTF16_BE, "utf-16-be"),
                     (codecs.BOM_UTF8, "utf-8"), (codecs.BOM_UTF32_LE, "utf-32-le"))
        for bom, codec in encodings:
            with self.subTest(encoding=codec):
                captions = intake.read_file(bom + cue.encode(codec), ".srt", "video")
                self.assertIn(line, captions.text)
                self.assertIn("00:00:03.500", captions.text)
                self.assertEqual(intake.read_file(bom + line.encode(codec), ".txt", "file").text, line)
        with self.assertRaisesRegex(ReadError, "二进制"):
            intake.read_file(b"header\x00payload", ".txt", "file")

    def test_reader_json_preserves_unicode_on_a_legacy_console(self):
        note = self.root / "阅读 🐛.md"
        note.write_text("以前读过的一段。", encoding="utf-8")
        cmd = [sys.executable, "-B", intake.__file__, "--root", str(self.root)]
        env = dict(os.environ, PYTHONIOENCODING="cp1252")
        read = subprocess.run([*cmd, str(note)], env=env, capture_output=True, check=True)
        result = json.loads(read.stdout.decode("cp1252"))
        self.assertEqual(result["source"], note.name)
        self.assertEqual((self.root / result["material"]).read_text(encoding="utf-8").strip(),
                         note.read_text(encoding="utf-8"))
        missing = subprocess.run([*cmd, str(self.root / "缺少.txt")], env=env, capture_output=True)
        self.assertEqual((missing.returncode, json.loads(missing.stdout.decode("cp1252"))["status"]),
                         (2, "needs_material"))

    def test_shared_video_runtimes_prefer_neutral_cache_and_honor_override(self):
        base = self.root / "cache"
        with patch.dict(os.environ, {"XDG_CACHE_HOME": str(base)}, clear=False):
            os.environ.pop("VIDEO_NOTE_CACHE_DIR", None)
            self.assertEqual(
                shared_runtimes(),
                (base / "my-second-brain/video-note", base / "codex/video-note"),
            )
        override = self.root / "custom-video-cache"
        with patch.dict(os.environ, {"VIDEO_NOTE_CACHE_DIR": str(override)}, clear=False):
            self.assertEqual(shared_runtimes(), (override,))

    def test_x_article_ssr_parts_extracts_body_links_and_image_count(self):
        article_html = (
            '<h3 class="font-article"><span>Section One</span></h3>'
            '<p class="font-article"><span>Compare with </span>'
            '<a href="https://arxiv.org/abs/2406.17557"><span>The FineWeb Datasets</span></a>.</p>'
            '<blockquote><span>Loop summary here.</span></blockquote>'
            '<ul><li><span>Item one</span><br><span>Second line</span></li></ul>'
            '<figure><a href="/allen/article/100/media/901"><img src="https://pbs.twimg.com/media/ex.png" alt="Loop"></a></figure>'
        )
        ssr = (
            "<html><head>"
            '<meta property="og:site_name" content="X (formerly Twitter)">'
            '<meta property="og:title" content="Allen on X: &quot;Data Taste&quot; / X">'
            '<meta property="og:description" content="Data Taste">'
            "</head><body>"
            "<script>"
            "articleDocument:$R[7]={contentKey:\"[]\",parts:$R[9]=[$R[10]={type:\"html\",html:"
            + json.dumps(article_html).replace("<", "\\x3C")
            + "}]},"
            'metadata:$R[12]={authorName:"Allen",focalTweetId:"2123813175644782633",hasArticle:!0,'
            'headMetadata:{author:{screenName:"allen_datumwell"},bodyText:"https://t.co/abc",'
            'publishedTime:"2026-11-20T16:18:14.000Z"}}'
            "</script>"
            "<article><p>Reply comment that must not appear</p></article>"
            "</body></html>"
        ).encode("utf-8")
        url = "https://x.com/allen_datumwell/status/2123813175644782633?a=NonPRCM&s=20"
        with patch.object(intake, "fetch", return_value=(ssr, "https://x.com/allen_datumwell/status/2123813175644782633", "text/html", "utf-8")):
            res = intake.intake(self.root, url)
        self.assertEqual((res["status"], res["source_type"], res["evidence"]), ("ready", "x", "x_article"))
        self.assertEqual(res["source"], "https://x.com/allen_datumwell/status/2123813175644782633")
        self.assertEqual(res["title"], "Data Taste")
        self.assertEqual(res["details"]["author"], "Allen")
        self.assertEqual(res["details"]["handle"], "allen_datumwell")
        self.assertEqual(res["details"]["images_listed"], 1)
        self.assertFalse(res["details"]["images_read"])
        self.assertEqual(res["details"]["referenced_urls"], ["https://arxiv.org/abs/2406.17557"])
        text = (self.root / res["material"]).read_text(encoding="utf-8")
        self.assertIn("### Section One", text)
        self.assertIn("[The FineWeb Datasets](https://arxiv.org/abs/2406.17557)", text)
        self.assertIn("> Loop summary here.", text)
        self.assertIn("- Item one\n  Second line", text)
        self.assertIn("[Image 1: Loop]", text)
        self.assertNotIn("/media/901", text)
        self.assertNotIn("Reply comment that must not appear", text)

    def test_x_article_content_key_fallback_and_saved_dom_html(self):
        blocks = [
            ["a1", "header-two", "Intro"],
            ["a2", "unstyled", "First paragraph."],
            ["a3", "atomic", " "],
            ["a4", "blockquote", "Key point."],
        ]
        ssr = (
            "<html><head>"
            '<meta property="og:site_name" content="X (formerly Twitter)">'
            '<meta property="og:description" content="Fallback Article">'
            "</head><body><script>"
            "articleDocument:$R[1]={contentKey:"
            + json.dumps(json.dumps(blocks))
            + ",highlights:$R[2]={}},"
            'metadata:$R[3]={authorName:"Author",focalTweetId:"999",hasArticle:!0,'
            'headMetadata:{author:{screenName:"handle"},bodyText:"https://t.co/xyz"}}'
            "</script></body></html>"
        )
        from x_source import parse_x_html

        m = parse_x_html(ssr, "https://x.com/handle/status/999")
        self.assertEqual((m.kind, m.title, m.details["images_listed"]), ("x_article", "Fallback Article", 1))
        self.assertIn("## Intro", m.text)
        self.assertIn("[Image 1]", m.text)
        self.assertIn("> Key point.", m.text)

        dom_html = (
            "<html><head>"
            '<meta property="og:site_name" content="X (formerly Twitter)">'
            '<meta property="og:description" content="Saved DOM">'
            '<meta property="og:url" content="https://x.com/handle/status/888">'
            "</head><body>"
            '<nav>X navigation noise</nav>'
            '<div data-testid="twitterArticleReadView">'
            '<h2>Heading</h2><p>Saved body <a href="https://example.org/p">paper</a>.</p>'
            "</div>"
            '<article><p>Reply noise after article</p></article>'
            "</body></html>"
        )
        saved = self.root / "x_saved.html"
        saved.write_text(dom_html, encoding="utf-8")
        imported = intake.intake(self.root, "https://x.com/handle/status/888?s=20", str(saved))
        self.assertEqual((imported["status"], imported["source_type"], imported["evidence"]), ("ready", "x", "x_article"))
        body = (self.root / imported["material"]).read_text(encoding="utf-8")
        self.assertIn("[paper](https://example.org/p)", body)
        self.assertNotIn("Reply noise", body)

    def test_x_url_canonicalization_deduplicates_tracking_params_and_ignores_replies(self):
        ssr = (
            "<html><head>"
            '<meta property="og:site_name" content="X (formerly Twitter)">'
            '<meta property="og:description" content="Cached X">'
            "</head><body><script>"
            'articleDocument:$R[1]={contentKey:"[[\\"k1\\",\\"unstyled\\",\\"Body line.\\"]]"},'
            'metadata:$R[2]={authorName:"Allen",focalTweetId:"123",hasArticle:!0,'
            'headMetadata:{author:{screenName:"allen"},bodyText:"https://t.co/abc"}}'
            "</script></body></html>"
        ).encode("utf-8")
        first_url = "https://x.com/allen/status/123?a=tracking&s=20"
        second_url = "https://twitter.com/allen/status/123?s=46#fragment"
        with patch.object(intake, "fetch", return_value=(ssr, "https://x.com/allen/status/123", "text/html", "utf-8")) as get:
            first = intake.intake(self.root, first_url)
        get.assert_called_once_with("https://x.com/allen/status/123")
        with patch.object(intake, "online", side_effect=AssertionError("should reuse canonical cache")):
            second = intake.intake(self.root, second_url)
        self.assertEqual(first["source"], "https://x.com/allen/status/123")
        self.assertTrue(second["cached"])

        replies_only = (
            "<html><head>"
            '<meta property="og:site_name" content="X (formerly Twitter)">'
            '<meta property="og:title" content="Allen on X">'
            "</head><body>"
            "<article><p>@replyer Only a reply comment here.</p></article>"
            "</body></html>"
        ).encode("utf-8")
        with patch.object(intake, "fetch", return_value=(replies_only, "https://x.com/allen/status/456", "text/html", "utf-8")):
            with self.assertRaises(ReadError):
                intake.intake(self.root, "https://x.com/allen/status/456")

    def test_x_focal_post_extracts_main_post_without_replies(self):
        relay = {
            "data": {
                "threaded_conversation_with_injections_v2": {
                    "instructions": [{
                        "entries": [{
                            "content": {
                                "content": {
                                    "tweet_results": {
                                        "rest_id": "777",
                                        "result": {
                                            "__typename": "Tweet",
                                            "rest_id": "777",
                                            "core": {"user_results": {"result": {"core": {"name": "Sam", "screen_name": "sam_ai"}}}},
                                            "note_tweet": {
                                                "note_tweet_results": {
                                                    "result": {
                                                        "text": "Long note post with link https://t.co/xyz",
                                                        "entity_set": {"urls": [{"url": "https://t.co/xyz", "expanded_url": "https://arxiv.org/abs/2501.00001"}]},
                                                    }
                                                }
                                            },
                                        },
                                    }
                                }
                            }
                        }]
                    }]
                }
            }
        }
        post_html = (
            "<html><head>"
            '<meta property="og:site_name" content="X (formerly Twitter)">'
            '<meta property="og:title" content="Sam on X: &quot;Long note post&quot; / X">'
            "</head><body><script>"
            'metadata:$R[1]={authorName:"Sam",focalTweetId:"777",hasArticle:!1,'
            'headMetadata:{author:{screenName:"sam_ai"},bodyText:"Short fallback"}},'
            "result:$R[2]={kind:\"Result.Ok\",value:" + json.dumps(json.dumps(relay)) + "}"
            "</script><article><p>Unrelated reply text</p></article></body></html>"
        ).encode("utf-8")
        with patch.object(intake, "fetch", return_value=(post_html, "https://x.com/sam_ai/status/777", "text/html", "utf-8")):
            res = intake.intake(self.root, "https://x.com/sam_ai/status/777?s=20")
        self.assertEqual((res["status"], res["source_type"], res["evidence"]), ("ready", "x", "x_post"))
        body = (self.root / res["material"]).read_text(encoding="utf-8")
        self.assertIn("https://arxiv.org/abs/2501.00001", body)
        self.assertNotIn("Unrelated reply text", body)

        stub_article_html = (
            "<html><head>"
            '<meta property="og:site_name" content="X (formerly Twitter)">'
            '<meta property="og:type" content="article">'
            "</head><body><script>"
            'metadata:$R[1]={authorName:"Sam",focalTweetId:"778",hasArticle:!0,'
            'headMetadata:{author:{screenName:"sam_ai"},bodyText:"https://t.co/onlystub"}}'
            "</script></body></html>"
        ).encode("utf-8")
        with patch.object(intake, "fetch", return_value=(stub_article_html, "https://x.com/sam_ai/status/778", "text/html", "utf-8")):
            with self.assertRaises(ReadError):
                intake.intake(self.root, "https://x.com/sam_ai/status/778")

    def test_proxy_policy_403_maps_to_needs_network_while_remote_403_stays_needs_material(self):
        policy_headers = Message()
        policy_headers["Content-Type"] = "text/plain; charset=utf-8"
        policy_err = HTTPError(
            "https://x.com/allen/status/1",
            403,
            "Forbidden",
            policy_headers,
            BytesIO(b"Request to GET /allen/status/1 on x.com not allowed by policy"),
        )
        remote_headers = Message()
        remote_headers["Content-Type"] = "text/html; charset=utf-8"
        remote_err = HTTPError(
            "https://example.org/private",
            403,
            "Forbidden",
            remote_headers,
            BytesIO(b"<html><body><h1>Access Denied by Origin Server</h1>" + b"x" * 600 + b"</body></html>"),
        )
        try:
            with patch("intake.build_opener") as opener_cls:
                opener_cls.return_value.open.side_effect = policy_err
                with self.assertRaises(intake.NetworkUnavailable):
                    intake.fetch("https://x.com/allen/status/1")
                opener_cls.return_value.open.side_effect = remote_err
                with self.assertRaises(HTTPError):
                    intake.fetch("https://example.org/private")
        finally:
            policy_err.close()
            remote_err.close()

    def test_x_skips_legacy_comment_cache_and_reuses_revalidated_material(self):
        url = "https://x.com/reader/status/111"
        folder = self.root / ".local/imports" / hashlib.sha256(url.encode()).hexdigest()[:24]
        folder.mkdir(parents=True)
        old = folder / "text-comments.md"
        old.write_text("Only a comment.\n", encoding="utf-8")
        record = {"status": "ready", "file": old.name, "source": url, "material": old.relative_to(self.root).as_posix(),
                  "sha256": hashlib.sha256(old.read_bytes()).hexdigest()}
        manifest = folder / "evidence.json"
        for kind, evidence in [("web", "article_html"), ("x", "x_article")]:
            record.update(source_type=kind, evidence=evidence)
            manifest.write_text(json.dumps(record), encoding="utf-8")
            with patch.object(intake, "fetch", return_value=(b"<html><article>Just a reply.</article></html>", url, "text/html", "utf-8")) as get:
                with self.assertRaises(ReadError):
                    intake.intake(self.root, url + "?s=20")
                get.assert_called_once_with(url)
            self.assertEqual(json.loads(manifest.read_text(encoding="utf-8")), record)
        html = saved_x_article(url).encode()
        with patch.object(intake, "fetch", return_value=(html, url, "text/html", "utf-8")):
            result = intake.intake(self.root, url)
        with patch.object(intake, "fetch", side_effect=AssertionError("canonical cache should be used")):
            again = intake.intake(self.root, url.replace("x.com", "twitter.com") + "?s=46")
        self.assertTrue(again["cached"])
        self.assertEqual(again["sha256"], result["sha256"])
        self.assertTrue(old.is_file())

    def test_x_local_html_and_mapped_share_links_keep_the_selected_post(self):
        url = "https://x.com/reader/status/111"
        other = "https://x.com/writer/status/222"
        local = self.root / ".local"
        local.mkdir()
        saved = local / "reading.html"
        saved.write_text(saved_x_article(url), encoding="utf-8")
        archive = intake.intake(self.root, str(saved))
        self.assertEqual((archive["source_type"], archive["source"], archive["details"]["status_id"]), ("x", saved.name, "111"))
        self.assertEqual(archive["details"]["source_url"], url)
        (local / "source-files.json").write_text(json.dumps({url.replace("x.com", "twitter.com") + "?s=20": saved.name}))
        with patch.object(intake, "fetch", side_effect=AssertionError("mapped file should be used")):
            mapped = intake.intake(self.root, url + "?s=46")
        self.assertEqual((mapped["source"], mapped["evidence_source"], mapped["details"]["origin"]),
                         (url, saved.name, "configured local file"))
        saved.write_text(saved_x_article(other, "A different writer."), encoding="utf-8")
        with self.assertRaises(ReadError):
            intake.intake(self.root, url, str(saved))
        with patch.object(intake, "fetch", side_effect=AssertionError("cached verified article is available")):
            again = intake.intake(self.root, url)
        self.assertEqual(again["sha256"], mapped["sha256"])
        self.assertIn("local_file_issue", again)

    def test_x_checks_response_identity_and_rejects_status_pages_without_post_html(self):
        url = "https://x.com/sample/status/111"
        other = "https://x.com/other/status/222"
        for final, mime, body in [(other, "text/html", saved_x_article(other).encode()),
                                  ("https://x.com/i/flow/login", "text/html", saved_x_article(url).encode()),
                                  (url, "text/plain", b"Only the reply summary."),
                                  (url, "application/pdf", b"%PDF-not-a-post")]:
            with self.subTest(final=final, mime=mime):
                with patch.object(intake, "fetch", return_value=(body, final, mime, "utf-8")) as get:
                    with self.assertRaises(ReadError):
                        intake.intake(self.root, url)
                    get.assert_called_once_with(url)
        alias = "https://example.org/reading"
        with patch.object(intake, "fetch", return_value=(b"<html><article>Only replies</article></html>", url, "text/html", "utf-8")):
            with self.assertRaises(ReadError):
                intake.intake(self.root, alias)
        with patch.object(intake, "fetch", return_value=(saved_x_article(url).encode(), url, "text/html", "utf-8")):
            converted = intake.intake(self.root, alias)
        self.assertEqual((converted["source_type"], converted["source"], converted["details"]["source_url"]), ("x", alias, url))
        with patch.object(intake, "fetch", side_effect=AssertionError("unrelated source must not be fetched")):
            for target in ["https://x.com/reader", "https://twitter.com:10443/demo/status/111"]:
                with self.assertRaises(ReadError):
                    intake.intake(self.root, target)
            with self.assertRaises(ReadError):
                intake.intake(self.root, url, supplied=other)
        redirects = intake.WebRedirects()
        with self.assertRaises(ReadError):
            redirects.redirect_request(Request(url), None, 302, "Found", {}, other)
        same_post = url.replace("x.com", "twitter.com") + "?s=20"
        self.assertEqual(redirects.redirect_request(Request(url), None, 302, "Found", {}, same_post).full_url, same_post)

    def test_x_explicit_text_keeps_its_provenance_and_refresh_propagates_denial(self):
        url = "https://x.com/sample/status/111"
        text = self.root / "selected.txt"
        text.write_text("Text saved by the reader.", encoding="utf-8")
        with patch.object(intake, "fetch", side_effect=AssertionError("local file must be used")):
            result = intake.intake(self.root, url, str(text))
        self.assertEqual((result["evidence_source"], result["evidence"], result["details"]["scope"]),
                         (text.name, "supplied_text", "supplied file only"))
        error = HTTPError(url, 403, "Forbidden", Message(), BytesIO(b"Forbidden"))
        with error, patch.object(intake, "build_opener") as opener:
            opener.return_value.open.side_effect = error
            with self.assertRaises(HTTPError):
                intake.intake(self.root, url, refresh=True)
            self.assertEqual(opener.return_value.open.call_count, 1)

    def test_saved_publisher_article_with_an_embedded_post_uses_web_reader(self):
        publisher = self.root / "publisher.html"
        publisher.write_text(
            '<html><head><link rel="canonical" href="https://example.org/story"></head><body>'
            '<article><h1>Local reporting</h1><p>The publisher explains what happened.</p>'
            '<div data-testid="tweetText">An embedded quote.</div></article></body></html>', encoding="utf-8")
        with patch.object(intake, "declared_x_url", side_effect=AssertionError("ordinary publisher should use the web reader")):
            entry = intake.intake(self.root, str(publisher))
        self.assertNotEqual(entry["source_type"], "x")
        self.assertIn("The publisher explains what happened.", (self.root / entry["material"]).read_text(encoding="utf-8"))

    def test_proxy_auth_tunnel_and_ambiguous_origin_denials_are_distinguished(self):
        url = "https://x.com/sample/status/111"
        cases = [
            (403, "text/html", b"<h1>Not allowed by policy</h1>", HTTPError),
            (403, "text/plain", b"Blocked by our content policy", HTTPError),
            (403, "text/plain", b"Request to GET /thing on other.example not allowed by policy", HTTPError),
            (403, "text/plain", b"Request to GET /different on x.com not allowed by policy", HTTPError),
            (407, "text/html", b"<h1>Proxy Authentication Required</h1>", intake.NetworkUnavailable),
        ]
        for code, mime, text, expected in cases:
            headers = Message()
            headers["Content-Type"] = mime
            error = HTTPError(url, code, "Denied", headers, BytesIO(text))
            with self.subTest(code=code, body=text), error, patch.object(intake, "build_opener") as opener:
                opener.return_value.open.side_effect = error
                with self.assertRaises(expected):
                    intake.fetch(url)
                self.assertEqual(opener.return_value.open.call_count, 1)
        for message, expected in [("Tunnel connection failed: 403 Forbidden", intake.NetworkUnavailable),
                                  ("Tunnel connection failed: 407 Proxy Authentication Required", intake.NetworkUnavailable),
                                  ("origin said not allowed by policy", URLError)]:
            with self.subTest(message=message), patch.object(intake, "build_opener") as opener:
                opener.return_value.open.side_effect = URLError(OSError(message))
                with self.assertRaises(expected):
                    intake.fetch(url)
                self.assertEqual(opener.return_value.open.call_count, 1)
