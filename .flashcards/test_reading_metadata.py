"""Check optional reading fields at the review and study card entry points."""

from contextlib import closing
import json
from pathlib import Path
import tempfile
import unittest

import review


EN = '### Front\nWhat is the mean?\n### Short Answer\nThe sum divided by the count.\n'
ZH = '### 正面\n均值是多少？\n### 简答\n总和除以个数。\n'


class ReadingMetadataTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        for name in ('Flashcards', 'Concepts', 'Study-Queue'):
            (self.root / name).mkdir()
        source = {'path': 'Concepts/Mean.md', 'heading': 'Mean'}
        (self.root / source['path']).write_text('# Mean\nSum divided by count.\n', encoding='utf-8')
        source['sha256'] = review.digest(review.source_text(self.root, source))
        self.metadata = {'id': 'sb-fc-0014', 'version': 1, 'status': 'active',
                         'concept': 'Mean', 'topic': 'Sampling', 'sources': [source]}

    def write_review(self, body, **metadata):
        comment = '<!-- card: ' + json.dumps(dict(self.metadata, **metadata)) + ' -->'
        (self.root / 'Flashcards/Means.md').write_text(
            '---\ntype: flashcard_set\n---\n## Sample mean\n' + comment + '\n' + body, encoding='utf-8')
        return review.catalog(self.root)

    def study(self, body, heading='Study Card'):
        relative = 'Study-Queue/Means.md'
        (self.root / relative).write_text('# Sampling\n## ' + heading + '\n' + body, encoding='utf-8')
        return review.read_discovery_card(self.root, relative)

    def test_review_snapshots_preserve_their_reading_fields_at_the_same_version(self):
        cards, errors, _ = self.write_review(EN)
        self.assertEqual(errors, [])
        original = cards[0]
        self.assertNotIn('author', original)
        self.assertNotIn('glossary', original)
        with closing(review.connect(self.root)) as db:
            old, _ = review.make_session(db, cards, '2026-01-01')
            body = EN + '### Key Terms\n- Range: endpoints: $[a:b]$\n* 均值：总和除以个数\n'
            cards, errors, _ = self.write_review(body, author='Sam 李')
            self.assertEqual(errors, [])
            updated = cards[0]
            self.assertEqual(review.card_hash(original), review.card_hash(updated))
            self.assertEqual(updated['glossary'], [
                {'id': 'Range', 'term': 'Range', 'definition': 'endpoints: $[a:b]$'},
                {'id': '均值', 'term': '均值', 'definition': '总和除以个数'}])
            self.assertEqual(old, review.make_session(db, cards, '2026-01-01')[0])
            snapshot = review.make_session(db, cards, '2026-01-02')[0]['cards'][0]
            self.assertEqual((snapshot['author'], snapshot['glossary']), ('Sam 李', updated['glossary']))
            registered = json.loads(db.execute('SELECT payload FROM versions').fetchone()[0])
            self.assertNotIn('author', registered)
            self.assertNotIn('glossary', registered)

    def test_study_comment_and_section_keep_the_legacy_id_and_card_text(self):
        for language, body, label in (('Study Card', EN, 'Key Terms'), ('知识卡', ZH, '相关概念')):
            with self.subTest(language=language):
                old = self.study(body, language)
                comment = '<!-- reading: {"author":"Alice","glossary":[{"id":"n","term":"N","definition":"Count"}]} -->'
                from_comment = self.study(comment + '\n' + body, language)
                self.assertEqual(from_comment['author'], 'Alice')
                self.assertEqual(from_comment['glossary'], [{'id': 'n', 'term': 'N', 'definition': 'Count'}])
                from_section = self.study(body + '### ' + label + '\n* N：Count\n', language)
                for card in (from_comment, from_section):
                    self.assertEqual({key: card[key] for key in old}, old)
                    self.assertEqual(review.study_id('2026-01-02', card), review.study_id('2026-01-02', old))
                self.assertEqual(from_section['glossary'], [{'id': 'N', 'term': 'N', 'definition': 'Count'}])

    def test_review_metadata_preserves_explicit_term_ids_and_source_hashes(self):
        glossary = [{'id': 'n', 'term': 'N', 'definition': 'Count: the number of observations.'}]
        body = ZH + '### 来源\n[均值](../Concepts/Mean.md)\n'
        cards, errors, _ = self.write_review(body, author='Alice', glossary=glossary)
        self.assertEqual(errors, [])
        self.assertEqual(cards[0]['author'], 'Alice')
        self.assertEqual(cards[0]['glossary'], glossary)
        self.assertEqual(cards[0]['sources'], self.metadata['sources'])
        self.assertTrue(cards[0]['eligible'])

    def test_fenced_examples_are_ignored_by_both_parsers(self):
        example = '\n~~~~markdown\n<!-- reading: garbage -->\n### 相关概念\n- 错：例子\n~~~~\n'
        section = '\n### Key Terms\n```md\n- Example: hidden\n```\n- N: Count\n'
        study = self.study(example + EN + example + section)
        cards, errors, _ = self.write_review(EN + example + section)
        self.assertEqual(errors, [])
        self.assertEqual(study['glossary'], cards[0]['glossary'])
        self.assertEqual([x['term'] for x in study['glossary']], ['N'])
        self.assertIn('<!-- reading: garbage -->', study['back'])

    def test_duplicate_definitions_and_mixed_heading_languages_are_locatable(self):
        section = '### 相关概念\n- N：Count\n'
        cases = (
            (ZH + section, {'glossary': []}, 'glossary 重复'),
            (ZH + section + section, {}, '小节重复'),
            (EN + section, {}, '混用中英文'),
            (ZH + '### 相关概念\n', {}, '至少一个词条'),
            (ZH + '### 相关概念\n- N\n', {}, '第 1 行'),
            (ZH + '### 相关概念\n- N：\n', {}, 'definition'),
            (ZH + section + '- n: duplicate\n', {}, '重复'),
            (ZH, {'glossary': [{'term': '', 'definition': 'x'}]}, 'term'),
            (ZH, {'author': ['Alice']}, 'author'),
            (ZH, {'glossary': {}}, '列表'),
            (ZH, {'glossary': [{'term': 'x', 'definition': 'a', 'id': '1'},
                               {'term': 'y', 'definition': 'b', 'id': '1'}]}, '重复'),
        )
        for body, metadata, error in cases:
            with self.subTest(body=body, metadata=metadata):
                cards, errors, _ = self.write_review(body, **metadata)
                self.assertEqual(cards, [])
                self.assertEqual(len(errors), 1)
                self.assertIn('Means.md：Sample mean', errors[0])
                self.assertIn(error, errors[0])

    def test_study_comment_errors_and_section_exclusivity(self):
        comment = '<!-- reading: {"glossary":[]} -->\n'
        for body, error in (
            (comment + EN + '### Key Terms\n- N: Count', 'glossary 重复'),
            (comment + comment + EN, '注释重复'),
            (EN + comment, '第一个小节'),
            ('<!-- reading: [] -->\n' + EN, 'JSON 对象'),
            ('<!-- reading: { -->\n' + EN, 'JSON 无效'),
        ):
            with self.subTest(body=body):
                with self.assertRaisesRegex(ValueError, 'Means.md.*' + error):
                    self.study(body)


if __name__ == '__main__':
    unittest.main()
