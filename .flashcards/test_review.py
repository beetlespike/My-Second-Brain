"""用隔离状态验证选卡、版本保护和反馈写入。"""

from collections import Counter
from copy import deepcopy
from datetime import date, timedelta
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import review


def sample_cards(n=100):
    return [{"id": f"sb-fc-{i:04d}", "version": 1, "status": "active",
             "concept": f"概念 {i // 3}", "topic": f"主题 {i % 7}",
             "front": f"问题 {i}", "back": "解释", "details": "例子", "sources": [],
             "eligible": True, "review_reasons": [], "card_file": "Flashcards/示例 卡片.md"}
            for i in range(1, n + 1)]


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="flashcard-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.db = review.connect(self.root)
        self.addCleanup(self.db.close)
        self.cards = sample_cards(300)
        self.day = "2026-10-28"

    def session(self, offset=0):
        day = (date.fromisoformat(self.day) + timedelta(days=offset)).isoformat()
        return review.make_session(self.db, self.cards, day)[0]

    def historical_session(self, review_count=0):
        """保存一组旧配额下的快照，供迁移和反馈兼容检查。"""
        chosen, concepts = [], Counter()
        for card in self.cards:
            if concepts[card['concept']] == 2:
                continue
            chosen.append(dict(deepcopy(card), position=len(chosen) + 1,
                               presentation='review' if len(chosen) < review_count else 'new'))
            concepts[card['concept']] += 1
            if len(chosen) == 25:
                break
        session = dict(schema_version=1, date=self.day, timezone='Asia/Shanghai', cards=chosen,
                       review_count=review_count, new_count=len(chosen) - review_count)
        review.register(self.db, self.cards)
        self.db.execute('INSERT INTO sessions VALUES (?, ?)', (self.day, review.dump(session)))
        self.db.commit()
        return session

    def feedback(self, session, ratings, batch="test-1", received=None):
        return review.save_feedback(self.db, self.cards, {
            "session_date": session["date"], "batch_id": batch, "workspace_id": session.get('workspace_id'),
            "entries": [{"card_id": c["id"], "version": c["version"], "position": c["position"],
                         "rating": rating} for c, rating in zip(session["cards"], ratings)]
        }, received or session["date"])

    def test_cold_start_and_next_day_mix(self):
        first = self.session()
        self.assertEqual((first["new_count"], first["review_count"]), (6, 0))
        second = self.session(1)
        self.assertEqual((second["new_count"], second["review_count"]), (6, 4))
        for session in (first, second):
            self.assertLessEqual(len({c["id"] for c in session["cards"]}), 10)
            self.assertLessEqual(max(Counter(c["concept"] for c in session["cards"]).values()), 2)

    def test_existing_bank_uses_six_new_cards_and_four_reviews(self):
        self.historical_session()
        result = self.session(1)
        self.assertEqual((result['review_count'], result['new_count']), (4, 6))
        self.assertEqual(len(result['cards']), 10)
        self.assertTrue(all(c['presentation'] == 'new' for c in result['cards'][:6]))

    def test_preferred_new_cards_respect_topic_rotation_and_history(self):
        self.cards = sample_cards(18)
        for index, card in enumerate(self.cards):
            card["concept"] = card["id"]
            card["topic"] = "甲" if index < 9 else "乙"
        preferred = [card["id"] for card in self.cards[4:9]]
        first, _ = review.make_session(self.db, self.cards, self.day, preferred)
        chosen = first["cards"]
        self.assertEqual(Counter(c["topic"] for c in chosen), {"甲": 3, "乙": 3})
        self.assertEqual([c["id"] for c in chosen if c["topic"] == "甲"], preferred[:3])
        other_ids = [card["id"] for card in self.cards[-3:]]
        same_day, reused = review.make_session(self.db, self.cards, self.day, other_ids)
        self.assertTrue(reused)
        self.assertEqual(same_day, first)

        self.feedback(first, ["again"])
        tomorrow = (date.fromisoformat(self.day) + timedelta(days=1)).isoformat()
        next_deck, _ = review.make_session(self.db, self.cards, tomorrow, [chosen[-1]["id"]])
        self.assertEqual((next_deck["new_count"], next_deck["review_count"]), (6, 4))
        self.assertEqual(next_deck["cards"][6]["id"], chosen[0]["id"])

    def test_due_reviews_stay_within_four_review_slots(self):
        prior = self.historical_session()
        self.feedback(prior, ['again'] * 9)
        result = self.session(1)
        self.assertEqual((result['review_count'], result['new_count']), (4, 6))
        selected = {c['id'] for c in result['cards'] if c['presentation'] == 'review'}
        self.assertTrue(selected.issubset(c['id'] for c in prior['cards'][:9]))

    def test_due_reviews_rotate_without_displacing_new_cards(self):
        prior = self.historical_session()
        self.feedback(prior, ['again'] * 12)
        due = {c['id'] for c in prior['cards'][:12]}
        reviewed = set()
        for offset in range(1, 4):
            result = self.session(offset)
            self.assertEqual((result['review_count'], result['new_count']), (4, 6))
            selected = {c['id'] for c in result['cards'] if c['presentation'] == 'review'}
            self.assertTrue(selected.issubset(due - reviewed))
            reviewed.update(selected)
        self.assertEqual(reviewed, due)

    def test_new_shortage_uses_remaining_slots_for_review(self):
        prior = self.historical_session()
        seen = {c['id'] for c in prior['cards']}
        unseen = [c for c in self.cards if c['id'] not in seen][:3]
        self.cards = [c for c in self.cards if c['id'] in seen] + unseen
        result = self.session(1)
        self.assertEqual((result['review_count'], result['new_count']), (7, 3))
        self.assertEqual(self.session(2)['review_count'], 10)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM sessions').fetchone()[0], 3)

    def test_same_day_is_immutable_even_after_catalog_change(self):
        first = self.session()
        self.cards[0]["version"] = 2
        self.cards[0]["back"] = "更新后的解释"
        second, reused = review.make_session(self.db, self.cards, self.day)
        self.assertTrue(reused)
        self.assertEqual(first, second)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM sessions").fetchone()[0], 1)

    def test_retired_cards_leave_view_but_keep_snapshot_and_feedback_positions(self):
        first = self.historical_session(review_count=12)
        original = deepcopy(first)
        self.feedback(first, ["uncertain"])
        prior_feedback = tuple(self.db.execute("SELECT * FROM feedback").fetchone())
        retired = {first["cards"][0]["id"], first["cards"][2]["id"]}
        for c in self.cards:
            if c["id"] in retired:
                c.update(status="retired", eligible=False)
        output = self.root / "view.html"
        with patch.object(review, "catalog", return_value=(self.cards, [], [])):
            display = review.render(self.root, first, output, standalone=False)
        embedded = output.read_text(encoding="utf-8").split('const deck = ', 1)[1]
        self.assertEqual(display, json.JSONDecoder().raw_decode(embedded)[0])
        self.assertEqual((len(display["cards"]), display["new_count"], display["omitted_count"]), (10, 6, 15))
        self.assertEqual([c["position"] for c in display["cards"]], [2, 4, 5, 6, 13, 14, 15, 16, 17, 18])
        self.assertEqual(first, original)
        self.assertEqual(self.session(), original)
        self.assertEqual(tuple(self.db.execute("SELECT * FROM feedback").fetchone()), prior_feedback)
        kept = display["cards"][0]
        result = review.save_feedback(self.db, self.cards, {
            "session_date": self.day, "batch_id": "filtered-view",
            "entries": [{"card_id": kept["id"], "version": kept["version"],
                         "position": kept["position"], "rating": "again"}]
        }, self.day)
        self.assertEqual(result["saved"], 1)
        self.assertTrue(retired.isdisjoint(c["id"] for c in self.session(1)["cards"]))

    def test_legacy_twenty_five_card_feedback_remains_valid(self):
        prior = self.historical_session()
        result = self.feedback(prior, ['uncertain'] * 25)
        self.assertEqual(result['saved'], 25)
        self.assertEqual(self.feedback(prior, ['uncertain'] * 25)['duplicates'], 25)
        self.assertEqual(self.session(), prior)

    def test_all_retired_snapshot_does_not_render_empty_view(self):
        first = self.session()
        for c in self.cards:
            c.update(status="retired", eligible=False)
        output = self.root / "view.html"
        with patch.object(review, "catalog", return_value=(self.cards, [], [])):
            with self.assertRaisesRegex(ValueError, "全部退出复习范围"):
                review.render(self.root, first, output)
        self.assertFalse(output.exists())

    def test_ninety_days_without_feedback_never_infers_mastery(self):
        self.cards = sample_cards(600)
        seen = set()
        for offset in range(90):
            session = self.session(offset)
            self.assertEqual(len(session["cards"]), 6 if offset == 0 else 10)
            self.assertEqual(session['new_count'], 6)
            self.assertGreater(session['new_count'], session['review_count'])
            seen.update(c["id"] for c in session["cards"])
            self.assertTrue(all("mastery" not in c and "rating" not in c for c in session["cards"]))
        self.assertEqual(len(seen), 540)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM feedback").fetchone()[0], 0)

    def test_missed_days_do_not_create_backlog(self):
        self.historical_session()
        later = self.session(10)
        self.assertEqual(len(later["cards"]), 10)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM sessions").fetchone()[0], 2)

    def test_small_bank_and_concept_cap(self):
        self.cards = sample_cards(7)
        result = self.session()
        self.assertEqual(len(result["cards"]), 6)
        self.assertLessEqual(max(Counter(c["concept"] for c in result["cards"]).values()), 2)
        later = self.session(1)
        self.assertEqual((later['new_count'], later['review_count']), (1, 5))

    def test_historical_eight_two_session_keeps_its_cards_when_rendered(self):
        first = self.historical_session(review_count=8)
        first['cards'] = first['cards'][:10]
        first['new_count'] = 2
        original = deepcopy(first)
        with patch.object(review, 'catalog', return_value=(self.cards, [], [])):
            display = review.render(self.root, first, self.root / 'view.html')
        self.assertEqual(display['cards'], first['cards'])
        self.assertEqual((display['new_count'], display['review_count']), (2, 8))
        self.assertEqual(first, original)

    def test_historical_question_can_open_its_moved_source(self):
        card = self.cards[0]
        card["sources"] = [{"path": "Concepts/缓存.md", "heading": "缓存"}]
        original = self.historical_session()
        snapshot = deepcopy(original)
        new_path = self.root / "Concepts/推理系统/缓存.md"
        new_path.parent.mkdir(parents=True)
        new_path.write_text("# 缓存\n")
        card.update(version=2, back="新的答案", sources=[
            {"path": str(new_path.relative_to(self.root)), "heading": "缓存"}
        ])
        with patch.object(review, "catalog", return_value=(self.cards, [], [])):
            display = review.render(self.root, original, self.root / "view.html")
        first = display["cards"][0]
        self.assertEqual(first["sources"], card["sources"])
        self.assertEqual(first["back"], snapshot["cards"][0]["back"])
        self.assertEqual(first["version"], snapshot["cards"][0]["version"])
        self.assertEqual(original, snapshot)

    def test_explicit_feedback_due_dates_and_priority(self):
        first = self.historical_session()
        self.feedback(first, ["again", "uncertain", "familiar"])
        ids = [c["id"] for c in first["cards"][:3]]
        next_day = self.session(1)
        included = {c["id"] for c in next_day["cards"]}
        self.assertIn(ids[0], included)
        self.assertNotIn(ids[1], included)
        self.assertNotIn(ids[2], included)
        self.session(2)
        self.assertIn(ids[1], {c["id"] for c in self.session(3)["cards"]})
        for offset in range(4, 14):
            self.assertNotIn(ids[2], {c["id"] for c in self.session(offset)["cards"]})
        self.assertIn(ids[2], {c["id"] for c in self.session(14)["cards"]})

    def test_feedback_interval_uses_receipt_day(self):
        first = self.session()
        self.feedback(first, ["again"], received="2026-11-02")
        cid = first["cards"][0]["id"]
        self.assertNotIn(cid, {c["id"] for c in self.session(5)["cards"]})
        self.assertIn(cid, {c["id"] for c in self.session(6)["cards"]})

    def test_duplicate_feedback_is_idempotent(self):
        first = self.session()
        self.assertEqual(self.feedback(first, ["again"])["saved"], 1)
        self.assertEqual(self.feedback(first, ["again"])["duplicates"], 1)
        with self.assertRaises(ValueError):
            self.feedback(first, ["familiar"])
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM feedback").fetchone()[0], 1)

    def test_invalid_batch_rolls_back_every_entry(self):
        first = self.session()
        with self.assertRaises(ValueError):
            self.feedback(first, ["again", "invented-rating"])
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM feedback").fetchone()[0], 0)

    def test_historical_version_feedback_is_saved_without_rescheduling(self):
        first = self.session()
        cid = first["cards"][0]["id"]
        c = next(c for c in self.cards if c["id"] == cid)
        c.update(version=2, back="修订的解释")
        result = self.feedback(first, ["familiar"])
        self.assertEqual(result["historical_only"], 1)
        self.assertEqual(self.db.execute("SELECT applied FROM feedback").fetchone()[0], 0)

    def test_edit_requires_version_increment(self):
        self.session()
        self.cards[0]["back"] = "修改正文"
        with self.assertRaisesRegex(ValueError, "递增 version"):
            self.session(1)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM sessions").fetchone()[0], 1)

    def test_paused_or_changed_sources_are_excluded(self):
        for c in self.cards[:30]:
            c["eligible"] = False
        self.assertTrue(all(c["id"] not in {x["id"] for x in self.cards[:30]} for c in self.session()["cards"]))

    def test_markdown_source_change_and_missing_heading(self):
        (self.root / "Concepts").mkdir(); (self.root / "Flashcards").mkdir()
        source = self.root / "Concepts/测试.md"
        source.write_text("# 测试\n\n## 机制\n\n有依据的解释。\n\n## 其他\n\n其他内容。\n")
        src = {"path": "Concepts/测试.md", "heading": "机制"}
        src["sha256"] = review.digest(review.source_text(self.root, src))
        c = deepcopy(self.cards[0]); c["sources"] = [src]
        text = "---\ntype: flashcard_set\n---\n## 测试卡片\n<!-- card: " + json.dumps(c, ensure_ascii=False) + " -->\n\n### 正面\n\n问题\n\n### 简答\n\n解释\n\n### 展开\n\n细节\n"
        (self.root / "Flashcards/测试 卡片.md").write_text(text)
        self.assertTrue(review.catalog(self.root)[0][0]["eligible"])
        source.write_text(source.read_text(encoding="utf-8").replace("其他内容", "更新无关章节"))
        self.assertTrue(review.catalog(self.root)[0][0]["eligible"])
        source.write_text(source.read_text(encoding="utf-8").replace("有依据的解释", "来源已修订"))
        self.assertFalse(review.catalog(self.root)[0][0]["eligible"])
        source.write_text("# 测试\n\n原章节已经移除。\n")
        self.assertFalse(review.catalog(self.root)[0][0]["eligible"])

    def test_source_scan_keeps_unprocessed_work_pending(self):
        (self.root / "Concepts").mkdir()
        source = self.root / "Concepts/新概念.md"
        source.write_text("# 新概念\n解释\n")
        self.assertEqual(review.scan_sources(self.db, self.root)["new"], ["Concepts/新概念.md"])
        self.assertEqual(review.scan_sources(self.db, self.root)["new"], ["Concepts/新概念.md"])
        review.acknowledge_source(self.db, self.root, "Concepts/新概念.md")
        self.db.commit()
        self.assertEqual(review.scan_sources(self.db, self.root)["new"], [])
        source.write_text("# 新概念\n新解释\n")
        self.assertEqual(review.scan_sources(self.db, self.root)["changed"], ["Concepts/新概念.md"])


if __name__ == "__main__":
    unittest.main()
