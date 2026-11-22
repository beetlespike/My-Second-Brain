"""验证离线公式资源与修订预览的隔离。"""

from copy import deepcopy
import base64
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import review


class MathRenderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="flashcard-math-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.card = dict(id="sb-fc-0001", version=2, status="active", eligible=True,
                         sources=[], position=1, presentation="new", topic="数学",
                         concept="示例", front="公式", back=r"$\sqrt{d}$", details="说明")
        self.session = dict(date="2026-11-14", cards=[self.card], new_count=1, review_count=0)

    def test_pinned_math_renderer_integrity(self):
        data = (review.ASSET_DIR / "vendor/katex-0.19.1.min.js").read_bytes()
        self.assertEqual(base64.b64encode(hashlib.sha384(data).digest()).decode(),
                         "a1WQdjRj162i159OYq041X6I4K8NenkrI09LlPmiHg0YOb7CR+wJOraXwK9abpnE")

    def test_preview_does_not_mutate_original_session(self):
        before = deepcopy(self.session)
        output = self.root / "preview.html"
        with patch.object(review, "catalog", return_value=([self.card], [], [])):
            result = review.render(self.root, self.session, output, preview=True)
        self.assertTrue(result["preview"])
        self.assertEqual(self.session, before)
        self.assertFalse((self.root / ".flashcards").exists())
        text = output.read_text(encoding="utf-8")
        self.assertIn("sb-flashcards-2026-11-14-revision", text)
        self.assertNotIn("__MATH_RENDERER__", text)
        self.assertLess(len(text.encode()), 1_000_000)

    def test_regular_session_keeps_feedback_identity(self):
        output = self.root / "daily.html"
        with patch.object(review, "catalog", return_value=([self.card], [], [])):
            result = review.render(self.root, self.session, output)
        self.assertNotIn("preview", result)
        self.assertEqual(result["cards"][0]["id"], self.card["id"])
        self.assertEqual(result["cards"][0]["version"], self.card["version"])
        self.assertEqual(result["cards"][0]["position"], 1)

    def test_long_math_on_a_legacy_25_card_issue_stays_self_contained(self):
        formula = r"$$\operatorname{Var}(\bar X)=\frac{1}{n^2}\sum_{i=1}^{n}\sum_{j=1}^{n}\operatorname{Cov}(X_i,X_j)$$"
        cards = [dict(self.card, id=f'sb-fc-{i:04d}', position=i, details='\n\n'.join([formula] * 12))
                 for i in range(1, 26)]
        issue = dict(self.session, cards=cards, is_past_issue=True)
        page, data = review.page_html(self.root, issue, current_cards=[], saved_ids=[])
        self.assertEqual([c['position'] for c in data['cards']], list(range(1, 26)))
        self.assertEqual(data['cards'][-1]['details'], cards[-1]['details'])
        self.assertIn('renderToString', page)
        self.assertNotIn('<script src=', page)
        self.assertLess(len(page.encode()), 1_000_000)

    def test_missing_renderer_leaves_previous_output(self):
        output = self.root / "daily.html"
        output.write_text("previous valid view")
        assets = self.root / 'incomplete-tool'
        assets.mkdir()
        (assets / 'viewer.html').write_text('__MATH_RENDERER__')
        with patch.object(review, "ASSET_DIR", assets), patch.object(review, "catalog", return_value=([self.card], [], [])):
            with self.assertRaises(FileNotFoundError):
                review.render(self.root, self.session, output)
        self.assertEqual(output.read_text(encoding="utf-8"), "previous valid view")


if __name__ == "__main__":
    unittest.main()
