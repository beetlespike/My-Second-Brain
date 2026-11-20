"""验证初始化、示例知识和来源修订后的完整复习过程。"""

from contextlib import closing
from fractions import Fraction
import importlib.util
import json
from math import comb
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import unquote

import workflow

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('review', ROOT / '.flashcards/review.py')
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve() / 'learning'
        workflow.initialize(ROOT, self.root)

    def test_example_links_and_card_sources_are_valid(self):
        self.assertEqual(workflow.check(self.root)['errors'], [])
        self.assertEqual((self.root / 'README.en.md').read_bytes(), (ROOT / 'README.en.md').read_bytes())
        self.assertEqual((self.root / 'LICENSE').read_bytes(), (ROOT / 'LICENSE').read_bytes())
        cards, errors, warnings = review.catalog(self.root)
        self.assertEqual((len(cards), len(errors), len(warnings)), (15, 0, 0))
        self.assertTrue(all(c['eligible'] for c in cards))

    def test_empty_start_has_guides_and_no_example_or_feedback(self):
        dest = Path(self.tmp.name) / 'empty'
        workflow.initialize(ROOT, dest, empty=True)
        self.assertEqual(workflow.check(dest)['errors'], [])
        self.assertFalse((dest / 'assets').exists())
        self.assertFalse((dest / '.flashcards/local').exists())
        self.assertEqual(review.catalog(dest)[0], [])
        self.assertTrue((dest / 'Prompts/整理材料.md').is_file())
        self.assertEqual((dest / 'LICENSE').read_bytes(), (ROOT / 'LICENSE').read_bytes())
        self.assertIn('[English](README.en.md)', (dest / 'README.md').read_text(encoding='utf-8'))
        self.assertIn('[简体中文](README.md)', (dest / 'README.en.md').read_text(encoding='utf-8'))

    def test_research_maps_cover_their_graphs_and_study_cards(self):
        def linked_notes(note):
            targets = re.findall(r'\]\(([^)#\n]+)(?:#[^)\n]*)?\)', note.read_text(encoding='utf-8'))
            return {(note.parent / unquote(t)).resolve() for t in targets if '://' not in t}

        existing = list((self.root / 'Concepts').rglob('*.md'))
        proposals = [p for p in (self.root / '待学概念').rglob('*.md') if 'ai-suggested' in workflow.fields(p.read_text()).get('tags', '')]
        self.assertTrue(all(p.stem.isascii() for p in existing + proposals))
        maps = {'case-serving': 'Streaming LLM Serving', 'case-tokenizers': 'Multilingual Tokenizers',
                'case-rlvr': 'RLVR and Coverage'}
        for tag, title in maps.items():
            with self.subTest(case=title):
                topic_map = self.root / 'MOCs' / (title + '.md')
                in_case = {p for p in existing if tag in workflow.fields(p.read_text()).get('tags', '')}
                pending = {p for p in proposals if tag in workflow.fields(p.read_text()).get('tags', '')}
                self.assertGreaterEqual(len(in_case), 10)
                self.assertEqual(len(pending), 3)
                self.assertTrue((in_case | pending).issubset(linked_notes(topic_map)))
                for note in pending:
                    self.assertGreaterEqual(len(linked_notes(note) & in_case), 2, note.name)
                    self.assertTrue(review.read_discovery_card(self.root, note.relative_to(self.root))['back'])
        serving_map = self.root / 'MOCs/Streaming LLM Serving.md'
        source_dirs = {p.relative_to(self.root).parts[0] for p in linked_notes(serving_map)}
        self.assertTrue({'Papers', 'Articles', 'Chats', 'Videos'}.issubset(source_dirs))

    def test_missing_link_in_english_readme_is_reported(self):
        note = self.root / 'README.en.md'
        note.write_text(note.read_text(encoding='utf-8') + '\n[Missing note](missing.md)\n', encoding='utf-8')
        self.assertTrue(any('README.en.md' in e and 'missing.md' in e for e in workflow.check(self.root)['errors']))

    def test_demo_starts_with_sources_but_no_concept_notes_or_cards(self):
        dest = Path(self.tmp.name) / 'demo'
        result = workflow.initialize(ROOT, dest, demo=True)
        self.assertFalse(result['example_notes'])
        files = {f.relative_to(dest).as_posix() for f in (dest / 'assets').rglob('*') if f.is_file()}
        self.assertEqual(files, {'assets/demo/serving-sources.md', 'assets/demo/streaming-dialogue.md',
                                 'assets/demo/retrieval.md', 'assets/demo/first-token.vtt'})
        for name in files:
            self.assertEqual((dest / name).read_bytes(), (ROOT / name).read_bytes())
        self.assertEqual(list((dest / 'Concepts').rglob('*.md')), [])
        self.assertEqual(review.catalog(dest), ([], [], []))
        self.assertFalse((dest / '.flashcards/local').exists())
        self.assertEqual(workflow.check(dest)['errors'], [])

    def test_initialization_never_overwrites_user_content(self):
        dest = Path(self.tmp.name) / 'occupied'
        dest.mkdir()
        p = dest / 'my-note.md'
        p.write_text('手写内容', encoding='utf-8')
        with self.assertRaises(ValueError):
            workflow.initialize(ROOT, dest)
        self.assertEqual(p.read_text(encoding='utf-8'), '手写内容')

    def test_copy_excludes_private_state_and_symlinks(self):
        (self.root / '.flashcards/local').mkdir(parents=True)
        (self.root / '.flashcards/local/private.txt').write_text('not for copying')
        (self.root / '.git').mkdir()
        (self.root / '.git/config').write_text('private history')
        (self.root / 'Concepts/link.md').symlink_to(Path(self.tmp.name) / 'outside.md')
        dest = Path(self.tmp.name) / 'copy'
        workflow.initialize(self.root, dest)
        self.assertFalse((dest / '.flashcards/local').exists())
        self.assertFalse((dest / '.git').exists())
        self.assertFalse((dest / 'Concepts/link.md').exists())

    def add_book(self, text):
        path = self.root / 'Books/读书笔记.md'
        path.parent.mkdir()
        path.write_text(text, encoding='utf-8')
        config_path = self.root / '.secondbrain.json'
        config = json.loads(config_path.read_text(encoding='utf-8'))
        config['source_dirs'].append('Books')
        config_path.write_text(json.dumps(config), encoding='utf-8')
        return path

    def test_custom_source_directory_survives_initialization(self):
        book = self.add_book('---\ntype: book\nsource_path: assets/demo/文章原文.md\nevidence_status: anchored\n---\n\n# 读书笔记\n')
        dest = Path(self.tmp.name) / 'with-books'
        workflow.initialize(self.root, dest)
        self.assertEqual((dest / 'Books/读书笔记.md').read_bytes(), book.read_bytes())
        self.assertEqual(workflow.check(dest)['errors'], [])

    def test_custom_material_requires_source_and_evidence(self):
        self.add_book('---\ntype: book\n---\n\n# 读书笔记\n')
        errors = workflow.check(self.root)['errors']
        self.assertTrue(any('Books/读书笔记.md' in e and 'source_url' in e for e in errors))
        self.assertTrue(any('Books/读书笔记.md' in e and 'evidence_status' in e for e in errors))

    def test_dashes_inside_source_url_keep_following_properties(self):
        self.add_book('---\ntype: book\nsource_url: https://example.org/a---b\nevidence_status: anchored\n---\n\n# 读书笔记\n')
        self.assertEqual(workflow.check(self.root)['errors'], [])

    def test_review_keeps_literal_template_tokens_in_card_text(self):
        cards, _, _ = review.catalog(self.root)
        question = '模板何时替换 __MATH_RENDERER__？'
        card = dict(cards[0], front=question)
        with closing(review.connect(self.root)) as db:
            session, _ = review.make_session(db, [card], '2026-01-01')
        output = self.root / 'view.html'
        review.render(self.root, session, output)
        self.assertTrue(question in output.read_text(encoding='utf-8'))

    def run_review(self, *args):
        return subprocess.run([sys.executable, '-B', '.flashcards/review.py', *args], cwd=self.root,
                              capture_output=True, text=True, encoding='utf-8')

    def test_review_card_can_omit_the_expanded_answer(self):
        path = self.root / 'Flashcards/抽样估计.md'
        text = path.read_text(encoding='utf-8')
        start = text.index('\n### 展开\n')
        end = text.index('\n### 来源\n', start)
        path.write_text(text[:start] + text[end:], encoding='utf-8')

        result = self.run_review('session', '--date', '2026-01-01')
        self.assertEqual(result.returncode, 0, result.stderr)
        cards, errors, _ = review.catalog(self.root)
        self.assertEqual(errors, [])
        card = next(c for c in cards if c['id'] == 'sb-fc-0001')
        self.assertTrue(card['eligible'])
        self.assertEqual(card['details'], '')
        self.assertTrue(card['sources'])

    def test_discovery_card_keeps_the_existing_review_deck(self):
        note = '待学概念/数理基础/Correlated Sampling.md'
        self.run_review('session', '--date', '2026-01-01').check_returncode()
        self.run_review('session', '--date', '2026-01-02').check_returncode()
        snapshot = self.run_review('show', '--date', '2026-01-02').stdout
        result = self.run_review('session', '--date', '2026-01-02', '--discovery', note)
        self.assertEqual(result.returncode, 0, result.stderr)
        displayed = json.loads(result.stdout)
        self.assertGreater(displayed['review'], 0)
        self.assertTrue(displayed['reused'])
        self.assertEqual(displayed['discovery'], note)
        self.assertEqual(self.run_review('show', '--date', '2026-01-02').stdout, snapshot)
        page = Path(displayed['output']).read_text(encoding='utf-8')
        self.assertIn('200 行记录', page)

    def test_discovery_card_can_be_opened_without_a_review_deck(self):
        with closing(review.connect(self.root)) as db:
            cards, _, _ = review.catalog(self.root)
            first, _ = review.make_session(db, cards, '2026-01-01')
            review.save_feedback(db, cards, {
                'session_date': first['date'], 'workspace_id': first['workspace_id'], 'batch_id': 'first',
                'entries': [{'card_id': c['id'], 'version': c['version'], 'rating': 'familiar'}
                            for c in first['cards']]
            }, '2026-01-01')
        (self.root / '.secondbrain.json').write_text('{"new_limit": 0}', encoding='utf-8')
        note = '待学概念/数理基础/Correlated Sampling.md'
        result = self.run_review('session', '--date', '2026-01-02', '--discovery', note)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['count'], 0)
        self.assertEqual(json.loads(result.stdout)['discovery'], note)
        self.assertNotEqual(self.run_review('show', '--date', '2026-01-02').returncode, 0)

    def test_discovery_card_must_be_in_the_pending_notes(self):
        result = self.run_review('session', '--discovery', 'Concepts/数理基础/Standard Error.md')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('待学概念', result.stderr)
        self.assertFalse((self.root / '.flashcards/local').exists())

    def test_missing_and_ambiguous_note_links_are_reported(self):
        p = self.root / 'Concepts/数理基础/Sample Mean.md'
        p.write_text(p.read_text(encoding='utf-8') + '\n[[不存在]]\n', encoding='utf-8')
        self.assertTrue(any('不存在' in e for e in workflow.check(self.root)['errors']))

    def test_full_review_feedback_and_source_revision_cycle(self):
        cards, _, _ = review.catalog(self.root)
        with closing(review.connect(self.root)) as db:
            first, reused = review.make_session(db, cards, '2026-01-01')
            self.assertFalse(reused)
            self.assertEqual(first['new_count'], 6)
            snapshot = db.execute('SELECT payload FROM sessions').fetchone()[0]
            c = first['cards'][0]
            feedback = {'workspace_id': first['workspace_id'], 'session_date': first['date'], 'batch_id': 'first',
                        'entries': [{'card_id': c['id'], 'version': c['version'], 'rating': 'uncertain'}]}
            self.assertEqual(review.save_feedback(db, cards, feedback, '2026-01-01')['saved'], 1)
            self.assertEqual(review.save_feedback(db, cards, feedback, '2026-01-01')['duplicates'], 1)
            source = c['sources'][0]
            note = self.root / source['path']
            text = note.read_text(encoding='utf-8')
            text = text.replace('## ' + source['heading'] + '\n', '## ' + source['heading'] + '\n\n新增一处需要复核的解释。\n')
            note.write_text(text, encoding='utf-8')
            changed, _, _ = review.catalog(self.root)
            self.assertFalse(next(x for x in changed if x['id'] == c['id'])['eligible'])
            later, _ = review.make_session(db, changed, '2026-01-02')
            self.assertNotIn(c['id'], [x['id'] for x in later['cards']])
            view = self.root / '.flashcards/local/views/old.html'
            display = review.render(self.root, first, view)
            self.assertTrue(next(x for x in display['cards'] if x['id'] == c['id'])['snapshot_warning'])
            card_file = self.root / c['card_file']
            content = card_file.read_text(encoding='utf-8')
            for match in review.META.finditer(content):
                meta = json.loads(match[1])
                if meta['id'] == c['id']:
                    meta['version'] += 1
                    meta['sources'][0]['sha256'] = review.digest(review.source_text(self.root, source))
                    content = content[:match.start(1)] + json.dumps(meta, ensure_ascii=False) + content[match.end(1):]
                    break
            card_file.write_text(content, encoding='utf-8')
            revised, _, _ = review.catalog(self.root)
            feedback['batch_id'] = 'late-feedback'
            self.assertEqual(review.save_feedback(db, revised, feedback, '2026-01-02')['historical_only'], 1)
            next_day, _ = review.make_session(db, revised, '2026-01-03')
            self.assertEqual(next(x for x in next_day['cards'] if x['id'] == c['id'])['version'], c['version'] + 1)
            self.assertEqual(db.execute('SELECT payload FROM sessions WHERE day=?', ('2026-01-01',)).fetchone()[0], snapshot)

    def test_teaching_table_matches_exact_binomial_variances(self):
        for n in (4, 16, 64):
            probabilities = [(k, Fraction(comb(n, k), 2 ** n)) for k in range(n + 1)]
            mean = sum(Fraction(k, n) * p for k, p in probabilities)
            variance = sum((Fraction(k, n) - mean) ** 2 * p for k, p in probabilities)
            self.assertEqual(mean, Fraction(1, 2))
            self.assertEqual(variance, Fraction(1, 4 * n))


if __name__ == '__main__':
    unittest.main()
