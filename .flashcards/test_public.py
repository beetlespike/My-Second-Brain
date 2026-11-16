"""用合成材料验证独立使用时的配置、记录隔离和来源边界。"""

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import review
from test_review import sample_cards


class PublicWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.db = review.connect(self.root)
        self.addCleanup(self.db.close)
        self.cards = sample_cards(6)
        for c in self.cards:
            c['concept'] = c['id']

    def test_review_continues_when_new_cards_run_out(self):
        review.make_session(self.db, self.cards, '2026-01-01')
        deck, _ = review.make_session(self.db, self.cards, '2026-01-02')
        self.assertEqual((deck['new_count'], deck['review_count']), (0, 6))

    def test_feedback_cannot_cross_learning_directories(self):
        deck, _ = review.make_session(self.db, self.cards, '2026-01-01')
        c = deck['cards'][0]
        payload = {'session_date': deck['date'], 'workspace_id': 'another-vault',
                   'batch_id': 'test', 'entries': [{'card_id': c['id'], 'version': c['version'], 'rating': 'again'}]}
        with self.assertRaisesRegex(ValueError, '学习目录'):
            review.save_feedback(self.db, self.cards, payload, deck['date'])
        self.assertEqual(self.db.execute('SELECT count(*) FROM feedback').fetchone()[0], 0)
        payload['workspace_id'] = deck['workspace_id']
        self.assertEqual(review.save_feedback(self.db, self.cards, payload, deck['date'])['saved'], 1)

    def test_custom_quota_and_review_only_mode(self):
        cfg = dict(daily_limit=3, new_limit=2, concept_limit=1, interval_days=review.INTERVALS)
        deck, _ = review.make_session(self.db, sample_cards(30), '2026-01-01', settings=cfg)
        self.assertEqual(deck['new_count'], 2)
        cfg['new_limit'] = 0
        deck, _ = review.make_session(self.db, sample_cards(30), '2026-01-02', settings=cfg)
        self.assertEqual((deck['new_count'], deck['review_count']), (0, 2))

    def test_only_explicit_valid_configuration_is_used(self):
        (self.root / '.secondbrain.json').write_text(json.dumps({'daily_limit': -1}))
        with self.assertRaises(ValueError):
            review.settings(self.root)

    def test_code_example_headings_do_not_change_source_resolution(self):
        text = '```markdown\n## 定义\n示例\n```\n## 定义\n真正的解释\n### 条件\n独立抽样\n## 后续\n其他'
        self.assertEqual(review.section(text, '定义'), '## 定义\n真正的解释\n### 条件\n独立抽样')

    def test_new_settings_do_not_hide_a_previous_daily_deck(self):
        deck, _ = review.make_session(self.db, self.cards, '2026-01-01')
        (self.root / '.secondbrain.json').write_text(json.dumps({'new_limit': 0}))
        (self.root / '.flashcards/viewer.html').write_text('__DECK_DATA__')
        with patch.object(review, 'catalog', return_value=(self.cards, [], [])):
            display = review.render(self.root, deck, self.root / 'old.html')
        self.assertEqual(len(display['cards']), 6)

    def test_pending_pages_are_not_card_sources(self):
        p = self.root / '待学概念' / '例子.md'
        p.parent.mkdir()
        p.write_text('# 例子\n\n## 定义\n解释。')
        with self.assertRaises(ValueError):
            review.source_text(self.root, {'path': str(p.relative_to(self.root)), 'heading': '定义'})

    def test_source_symlink_cannot_leave_the_learning_directory(self):
        folder = self.root / 'Concepts'
        folder.mkdir()
        with tempfile.TemporaryDirectory() as outside:
            target = Path(outside) / 'secret.md'
            target.write_text('## 外部\n不应读取。')
            (folder / 'link.md').symlink_to(target)
            with self.assertRaises(ValueError):
                review.source_text(self.root, {'path': 'Concepts/link.md', 'heading': '外部'})

    def write_card_file(self, marker='card: '):
        source = self.root / 'Concepts/均值.md'
        source.parent.mkdir()
        source.write_text('# 均值\n\n## 定义\n观测值相加再除以数量。\n', encoding='utf-8')
        src = {'path': 'Concepts/均值.md', 'heading': '定义'}
        src['sha256'] = review.digest(review.source_text(self.root, src))
        card = dict(self.cards[0], sources=[src])
        note = self.root / 'Flashcards/练习.md'
        note.parent.mkdir()
        note.write_text('---\ntype: flashcard_set\n---\n\n## 均值\n\n<!-- ' + marker
                        + json.dumps(card) + ' -->\n\n### 正面\n怎样计算均值？\n\n'
                        '### 简答\n观测值相加再除以数量。\n\n### 展开\n先求和。\n', encoding='utf-8')
        return note

    def test_hidden_json_without_card_marker_is_reported(self):
        self.write_card_file(marker='')
        cards, errors, _ = review.catalog(self.root)
        self.assertEqual(cards, [])
        self.assertTrue(any('card:' in e and '练习.md' in e for e in errors))

    def test_an_unmarked_card_cannot_hide_beside_a_valid_card(self):
        note = self.write_card_file()
        note.write_text(note.read_text() + '\n## 第二张\n\n### 正面\n另一个问题\n', encoding='utf-8')
        cards, errors, _ = review.catalog(self.root)
        self.assertEqual(len(cards), 1)
        self.assertTrue(any('第二张' in e and 'card:' in e for e in errors))

    def test_heading_in_code_example_does_not_split_a_card(self):
        note = self.write_card_file()
        note.write_text(note.read_text().replace('先求和。', '```markdown\n## 示例标题\n```\n先求和。'), encoding='utf-8')
        cards, errors, _ = review.catalog(self.root)
        self.assertEqual(errors, [])
        self.assertIn('先求和。', cards[0]['details'])


if __name__ == '__main__':
    unittest.main()
