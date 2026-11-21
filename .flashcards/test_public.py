"""用合成材料验证独立使用时的配置、记录隔离和来源边界。"""

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import feedback_inbox
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

    def test_text_feedback_keeps_the_original_question_and_source(self):
        card = self.cards[0]
        source = {'path': 'Concepts/均值.md', 'heading': '定义'}
        card['sources'] = [source]
        deck, _ = review.make_session(self.db, [card], '2026-01-01')
        revised = dict(card, front='修订后的题目', version=2, sources=[])
        context = {'session_date': deck['date'], 'workspace_id': deck['workspace_id']}
        entry = {'card_id': card['id'], 'version': 1}
        note = '为什么要先求和？'
        review.save_feedback(self.db, [revised], dict(
            context, batch_id='rating', entries=[dict(entry, rating='again')]), '2026-01-02')
        saved = review.save_feedback(self.db, [revised], dict(
            context, batch_id='question', entries=[dict(entry, note=note)]), '2026-01-02')
        self.assertEqual(saved['historical_only'], 1)
        self.assertEqual(review.feedback_notes(self.root), [
            {'session_date': deck['date'], 'received': '2026-01-02',
             'card_id': card['id'], 'version': 1, 'note': note,
             'question': card['front'], 'sources': [source]}
        ])
        unused = self.root / 'unused'
        self.assertEqual(review.feedback_notes(self.root, unused), [])
        self.assertFalse(unused.exists())

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
        with patch.object(review, 'catalog', return_value=(self.cards, [], [])):
            display = review.render(self.root, deck, self.root / 'old.html')
        self.assertEqual(len(display['cards']), 6)

    def test_pending_pages_are_not_card_sources(self):
        for folder in ('待学概念', 'Study-Queue'):
            with self.subTest(folder=folder):
                p = self.root / folder / '例子.md'
                p.parent.mkdir()
                p.write_text('# 例子\n\n## 定义\n解释。')
                with self.assertRaises(ValueError):
                    review.source_text(self.root, {'path': str(p.relative_to(self.root)), 'heading': '定义'})
                config = self.root / '.secondbrain.json'
                config.write_text(json.dumps({'source_dirs': [folder]}))
                with self.assertRaises(ValueError):
                    review.settings(self.root)
                config.unlink()

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

    def test_heading_aliases_preserve_registered_version_and_snapshot(self):
        note = self.write_card_file()
        chinese = note.read_text(encoding='utf-8') + '\n### 来源\n[均值](../Concepts/均值.md)\n'
        note.write_text(chinese, encoding='utf-8')
        original, errors, _ = review.catalog(self.root)
        self.assertEqual(errors, [])
        day = '2026-01-12'
        snapshot, _ = review.make_session(self.db, original, day)
        english = chinese.replace('## 均值\n', '## 正面\n')
        for before, after in zip(('正面', '简答', '展开', '来源'), ('Front', 'Short Answer', 'Details', 'Sources')):
            english = english.replace('### ' + before, '### ' + after)
        note.write_text(english, encoding='utf-8')
        parsed, errors, _ = review.catalog(self.root)
        self.assertEqual(errors, [])
        self.assertEqual(parsed, original)
        self.assertEqual(review.make_session(self.db, parsed, day), (snapshot, True))

        extra = english[english.index('## 正面'):]
        extra = extra.replace(original[0]['id'], 'sb-fc-9999').replace('怎样计算均值？', '另一个问题？')
        extra = extra.replace('先求和。', '~~~md\n## 知识卡\n<!-- card: {} -->\n### 简答\n~~~\nUse the sum.')
        note.write_text(chinese + '\n' + extra, encoding='utf-8')
        cards, errors, _ = review.catalog(self.root)
        self.assertEqual(errors, [])
        self.assertEqual([c['id'] for c in cards], [original[0]['id'], 'sb-fc-9999'])
        self.assertIn('### 简答', cards[1]['details'])

    def test_mixed_or_duplicate_card_fields_are_rejected(self):
        note = self.write_card_file()
        chinese = note.read_text(encoding='utf-8') + '\n### 来源\n出处\n'
        for name, invalid in (
            ('front', chinese.replace('### 正面', '### Front')),
            ('details', chinese.replace('### 展开', '### Details')),
            ('sources', chinese.replace('### 来源', '### Sources')),
            ('duplicate answer', chinese + '\n### 简答\n另一段答案'),
            ('duplicate sources', chinese + '\n### 来源\n第二组来源'),
        ):
            with self.subTest(name=name):
                note.write_text(invalid, encoding='utf-8')
                cards, errors, _ = review.catalog(self.root)
                self.assertEqual(cards, [])
                self.assertEqual(len(errors), 1)
                self.assertRegex(errors[0], '混用|重复')

    def test_study_heading_selects_one_language_in_either_queue(self):
        english = '## Study Card\n### Front\nQuestion?\n### Short Answer\n答案。\n'
        chinese = '## 知识卡\n### 正面\nQuestion?\n### 简答\n答案。\n'
        for folder in ('Study-Queue', '待学概念'):
            note = self.root / folder / 'Example.md'
            note.parent.mkdir()
            for heading, body in [('Study Card', english), ('知识卡', chinese)]:
                with self.subTest(folder=folder, heading=heading):
                    note.write_text('# Title\n\n' + body + '\n## Next section\n### Sources\nOther note prose.')
                    card = review.read_discovery_card(self.root, note.relative_to(self.root))
                    self.assertEqual((card['title'], card['front'], card['back']), ('Title', 'Question?', '答案。'))
                    self.assertEqual(card.get('heading', '知识卡'), heading)
            for invalid in (english + chinese, english + english,
                            english + '\n### 来源\n备注', english.replace('## Study Card', '## 知识卡')):
                with self.subTest(folder=folder, invalid=invalid):
                    note.write_text(invalid)
                    with self.assertRaises(ValueError):
                        review.read_discovery_card(self.root, note.relative_to(self.root))

    def test_english_study_comment_and_revised_note_round_trip(self):
        path = 'Study-Queue/Example.md'
        note = self.root / path
        note.parent.mkdir()
        body = '# Example\n## Study Card\n### Front\nHow many?\n### Short Answer\nTwo.\n'
        note.write_text(body)
        card = review.read_discovery_card(self.root, path)
        day = '2026-01-12'
        deck, _ = review.make_session(self.db, [], day, discovery=card, allow_empty=True)
        self.assertEqual(review.selected_discovery(self.db, day), card)
        cid = review.study_id(day, card)
        feedback = {'session_date': day, 'workspace_id': deck['workspace_id'], 'batch_id': 'study-test',
                    'entries': [{'card_id': cid, 'version': 1, 'note': 'Why?'}]}
        self.assertEqual(review.save_feedback(self.db, [], feedback, day)['saved'], 1)
        pending = feedback_inbox.report(self.db, day)['items'][0]
        self.assertEqual(pending['sources'], [{'path': path, 'heading': 'Study Card'}])
        result = {'workspace_id': deck['workspace_id'], 'items': [
            {'id': pending['id'], 'outcome': 'revised', 'reply': 'The answer now explains the count.'}]}
        with self.assertRaisesRegex(ValueError, '尚未修订'):
            feedback_inbox.resolve(self.db, self.root, result, day)
        note.write_text(body.replace('Two.', 'One pair contains two items.'))
        self.assertEqual(feedback_inbox.resolve(self.db, self.root, result, day)['handled'], 1)
        self.assertEqual(feedback_inbox.resolve(self.db, self.root, result, day)['duplicates'], 1)
        self.assertIn('One pair contains two items.', feedback_inbox.history_html(self.db, language='en'))
        self.assertEqual(review.selected_discovery(self.db, day)['back'], 'Two.')


if __name__ == '__main__':
    unittest.main()
