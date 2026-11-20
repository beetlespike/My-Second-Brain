"""Offline regressions for the evidence handed to Codex."""

import codecs
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import intake
from source_text import Material, Page, ReadError, caption_material, pdf_material
from video_source import tracks

WECHAT = "https://mp.weixin.qq.com/s/fixture"
PAPER = "https://arxiv.org/abs/2309.06180v1"
VIDEO = "https://www.youtube.com/watch?v=abcdefghijk"
SRT = b"1\n00:00:01,000 --> 00:00:03,500\nA worked example.\n"


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
