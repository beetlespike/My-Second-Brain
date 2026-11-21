"""验证初始化、示例知识和来源修订后的完整复习过程。"""

from contextlib import closing
from fractions import Fraction
import importlib.util
import json
from math import comb
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import unquote, urlsplit

import workflow

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / 'examples/demo-vault'
GUIDE_PAIRS = {
    'Article-Notes.md': '文章笔记.md', 'Automation.md': '自动整理与维护.md', 'Chat-Notes.md': '对话笔记.md',
    'First-Run.md': '第一次使用.md', 'Flashcard-Review.en.md': 'Flashcard-Review.md', 'Graph-View.md': '关系图谱.md',
    'Network-Notes.md': '网络与主题地图.md', 'Other-Sources.md': '其他来源.md', 'Paper-Notes.md': '论文笔记.md',
    'Sources-and-tools.md': '来源与工具.md', 'Tools-and-Extensions.md': '工具与扩展.md', 'Video-Notes.md': '视频笔记.md',
}
PROMPT_PAIRS = {
    'intake.md': '整理材料.md', 'daily-review.md': '每日复习.md',
    'discover-concepts.md': '回顾与补学.md', 'study-concept.md': '带学新概念.md',
}
spec = importlib.util.spec_from_file_location('review', ROOT / '.flashcards/review.py')
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)


def markdown_targets(path):
    return list(workflow.inline_targets(workflow.prose(path.read_text(encoding='utf-8'))))


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve() / 'learning'
        workflow.initialize(ROOT, self.root)

    def test_example_links_and_card_sources_are_valid(self):
        self.assert_vault_navigation(self.root)
        source = EXAMPLE if EXAMPLE.is_dir() else ROOT
        for name in ('MOCs/Knowledge-Index.md', 'MOCs/知识库入口.md'):
            self.assertEqual((self.root / name).read_bytes(), (source / name).read_bytes(), name)
        self.assertEqual((self.root / 'LICENSE').read_bytes(), (ROOT / 'LICENSE').read_bytes())
        self.assertFalse((self.root / 'examples').exists())
        if EXAMPLE.is_dir():
            self.assertFalse((self.root / 'assets/demo/today-cards.en.png').exists())
            self.assertTrue((self.root / 'assets/demo/obsidian-graph.json').is_file())
        cards, errors, warnings = review.catalog(self.root)
        self.assertEqual((len(cards), len(errors), len(warnings)), (15, 0, 0))
        self.assertTrue(all(c['eligible'] for c in cards))
        self.assertEqual(workflow.check(self.root)['errors'], [])

    def test_empty_start_has_guides_and_no_example_or_feedback(self):
        dest = Path(self.tmp.name) / 'empty'
        workflow.initialize(ROOT, dest, empty=True)
        self.assertEqual(workflow.check(dest)['errors'], [])
        self.assertFalse((dest / 'assets').exists())
        self.assertFalse((dest / '.flashcards/local').exists())
        self.assertEqual(review.catalog(dest)[0], [])
        self.assertTrue((dest / 'Prompts/整理材料.md').is_file())
        self.assertTrue((dest / 'Study-Queue').is_dir())
        self.assertTrue((dest / '待学概念').is_dir())
        self.assertEqual((dest / 'LICENSE').read_bytes(), (ROOT / 'LICENSE').read_bytes())
        self.assert_vault_navigation(dest)
        self.assertEqual({p.name for p in (dest / 'MOCs').glob('*.md')}, {'Knowledge-Index.md', '知识库入口.md'})
        for name in ('README.md', 'README.zh.md'):
            self.assertFalse(any(url.startswith('assets/') for _, url in markdown_targets(dest / name)))

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

    def assert_vault_navigation(self, vault):
        required_links = {
            'README.md': ('README.zh.md', 'MOCs/Knowledge-Index.md'),
            'README.zh.md': ('README.md', 'MOCs/知识库入口.md'),
            'MOCs/Knowledge-Index.md': ('知识库入口.md',),
            'MOCs/知识库入口.md': ('Knowledge-Index.md',),
        }
        for page, required in required_links.items():
            targets = markdown_targets(vault / page)
            for url in required:
                self.assertIn(('', url), targets, page)
            for _, url in targets:
                link = urlsplit(url)
                if link.fragment and not link.scheme and not link.netloc:
                    target = (vault / page).parent / unquote(link.path) if link.path else vault / page
                    anchors = workflow.heading_anchors(review, target.read_text(encoding='utf-8'))
                    self.assertIn(unquote(link.fragment), anchors, (page, url))
        for name in ('AGENTS.md', 'CLAUDE.md', '.secondbrain.json'):
            self.assertEqual((vault / name).read_bytes(), (ROOT / name).read_bytes(), name)
        for folder, pairs in (('Guides', GUIDE_PAIRS), ('Prompts', PROMPT_PAIRS), ('', {'AGENTS.md': 'AGENTS.zh.md'})):
            for english, chinese in pairs.items():
                self.assertIn(('', chinese), markdown_targets(vault / folder / english), english)
                self.assertIn(('', english), markdown_targets(vault / folder / chinese), chinese)
        self.assertEqual((vault / 'CLAUDE.md').read_text(encoding='utf-8').splitlines(), ['@AGENTS.md'])
        for name in ('README.en.md', 'GEMINI.md', 'AGENTS.override.md', '.cursor'):
            self.assertFalse((vault / name).exists(), name)
        self.assert_homepage_parity(vault)

    def assert_homepage_parity(self, vault):
        english_to_chinese = {
            'README.zh.md': 'README.md',
            '#start-in-5-minutes': '#5-分钟上手',
            'Guides/First-Run.md': 'Guides/第一次使用.md',
            'Guides/First-Run.md#todays-cards': 'Guides/第一次使用.md#今日知识卡',
            'Guides/First-Run.md#a-vault-of-your-own': 'Guides/第一次使用.md#自己的学习库',
            'Guides/First-Run.md#browsing-the-example-vault': 'Guides/第一次使用.md#逛逛成品示例库',
            'Guides/Flashcard-Review.en.md': 'Guides/Flashcard-Review.md',
            'Guides/Flashcard-Review.en.md#feedback-and-saving': 'Guides/Flashcard-Review.md#反馈与保存',
            'Guides/Automation.md': 'Guides/自动整理与维护.md',
            'Guides/Sources-and-tools.md': 'Guides/来源与工具.md',
            'Guides/Graph-View.md': 'Guides/关系图谱.md',
            'Prompts/intake.md': 'Prompts/整理材料.md',
            'MOCs/Knowledge-Index.md': 'MOCs/知识库入口.md',
            'examples/demo-vault/MOCs/Knowledge-Index.md': 'examples/demo-vault/MOCs/知识库入口.md',
            'assets/demo/human-ai-loop.en.png': 'assets/demo/human-ai-loop.zh.png',
            'assets/demo/today-cards.en.png': 'assets/demo/today-cards.zh.png',
        }
        english = markdown_targets(vault / 'README.md')
        expected = [(kind, english_to_chinese.get(url, url)) for kind, url in english]
        self.assertEqual(markdown_targets(vault / 'README.zh.md'), expected)

    @unittest.skipUnless(EXAMPLE.is_dir(), 'Checks the release repository with the bundled example')
    def test_release_homepages_include_examples_guides_and_figures(self):
        self.assert_homepage_parity(ROOT)
        targets = markdown_targets(ROOT / 'README.md')
        self.assertEqual(len(targets), 26)
        self.assertIn(('', 'Guides/First-Run.md#browsing-the-example-vault'), targets)
        for image in ('human-ai-loop.en.png', 'obsidian-serving.png', 'today-cards.en.png', 'obsidian-graph.png'):
            self.assertIn(('!', 'assets/demo/' + image), targets)
        for name, lang in [('README.md', 'en'), ('README.zh.md', 'zh')]:
            text = (ROOT / name).read_text(encoding='utf-8')
            tag = next(t for t in re.findall(r'<img\b[^>]*>', text, re.I) if 'today-cards.' + lang + '.png' in t)
            self.assertRegex(tag, r'''\bwidth=["']460["']''')
            for _, url in markdown_targets(ROOT / name):
                link = urlsplit(url)
                if link.fragment and not link.scheme and not link.netloc:
                    target = ROOT / (unquote(link.path) or name)
                    self.assertIn(unquote(link.fragment), workflow.heading_anchors(review, target.read_text(encoding='utf-8')), url)
        self.assertEqual(workflow.check(ROOT)['errors'], [])

    def test_portal_reports_broken_files_images_and_sections(self):
        en = self.root / 'README.md'
        zh = self.root / 'README.zh.md'
        en.write_text(en.read_text(encoding='utf-8') + '\n[Note](missing.md)\n[Section](#missing-section)\n'
                      '<a name="about-me"></a>\n[About me](#about-me)\n'
                      '[Personal note](MOCs/Personal.md#custom-id)\n', encoding='utf-8')
        zh.write_text(zh.read_text(encoding='utf-8') + '\n![图](missing.png)\n[章节](Guides/第一次使用.md#缺失章节)\n'
                      '<p><img width="460" src="missing-preview.png"></p>\n', encoding='utf-8')
        user_note = self.root / 'MOCs/Personal.md'
        user_note.write_text('---\ntype: moc\n---\n\n<a id="custom-id"></a>\n[My block](#^my-block)\n', encoding='utf-8')
        errors = workflow.check(self.root)['errors']
        for page, url in [(en, 'missing.md'), (en, '#missing-section'), (zh, 'missing.png'),
                          (zh, 'missing-preview.png'), (zh, '#缺失章节')]:
            self.assertTrue(any(page.name in msg and url in msg for msg in errors), (page.name, url))
        self.assertFalse(any('Personal.md' in msg for msg in errors))
        self.assertFalse(any('#about-me' in msg for msg in errors))

    def test_empty_vault_starts_with_framework_defaults(self):
        base = Path(self.tmp.name)
        release = base / 'release'
        sample = release / 'examples/demo-vault'
        sample.mkdir(parents=True)
        (release / '.secondbrain.json').write_text('{"daily_limit": 8, "timezone": "local"}', encoding='utf-8')
        (sample / '.secondbrain.json').write_text('{"daily_limit": 7, "timezone": "local"}', encoding='utf-8')
        for name, empty, limit in [('personal', True, 8), ('sample-copy', False, 7)]:
            destination = base / name
            workflow.initialize(release, destination, empty=empty)
            self.assertEqual(review.settings(destination)['daily_limit'], limit)

    def test_distribution_and_external_vault_resolve_sources_against_each_vault(self):
        release = Path(self.tmp.name) / 'release'
        vault = release / 'examples/demo-vault'
        (vault / 'Books').mkdir(parents=True)
        (vault / '.secondbrain.json').write_text('{"source_dirs":["Books"],"timezone":"local"}', encoding='utf-8')
        note = vault / 'Books/Payload.md'
        note.write_text('---\ntype: book\nsource_path: assets/original.txt\nevidence_status: anchored\n---\n', encoding='utf-8')
        (release / 'assets').mkdir()
        (release / 'assets/original.txt').write_text('Outside the vault', encoding='utf-8')
        (release / 'README.md').write_text('[Book](examples/demo-vault/Books/Payload.md)\n<img src="missing.png">\n',
                                            encoding='utf-8')
        errors = workflow.check(release)['errors']
        self.assertTrue(any('examples/demo-vault/Books/Payload.md' in msg and 'source_path' in msg for msg in errors), errors)
        self.assertTrue(any('README.md' in msg and 'missing.png' in msg for msg in errors), errors)
        (vault / 'assets').mkdir()
        (vault / 'assets/original.txt').write_text('Vault source', encoding='utf-8')
        (release / 'missing.png').write_bytes(b'image fixture')
        self.assertEqual(workflow.check(release), {'notes_checked': 2, 'errors': [], 'warnings': []})
        self.assertFalse((vault / 'tools').exists())
        self.assertFalse((vault / '.flashcards').exists())
        checked = subprocess.check_output([sys.executable, '-B', str(ROOT / 'tools/workflow.py'), '--root', str(vault), 'check'])
        self.assertEqual(json.loads(checked)['notes_checked'], 1)
        copied = Path(self.tmp.name) / 'standalone'
        workflow.initialize(vault, copied)
        self.assertEqual((copied / 'Books/Payload.md').read_bytes(), note.read_bytes())
        self.assertEqual((copied / 'assets/original.txt').read_text(encoding='utf-8'), 'Vault source')
        self.assertTrue((copied / '.flashcards/review.py').is_file())
        self.assertTrue((copied / 'tools/workflow.py').is_file())
        self.assertEqual(workflow.check(copied)['errors'], [])

    def test_full_copy_preserves_legacy_homepages(self):
        (self.root / 'README.zh.md').rename(self.root / 'README.en.md')
        nested = self.root / 'examples/demo-vault'
        nested.mkdir(parents=True)
        (nested / '.secondbrain.json').write_text('{"timezone":"local"}', encoding='utf-8')
        (nested / 'README.md').write_text('Nested example', encoding='utf-8')
        legacy = {
            'README.md': '[English](README.en.md#custom-id)\n',
            'README.en.md': '<a id="custom-id"></a>\n[简体中文](README.md)\n',
        }
        for name, content in legacy.items():
            (self.root / name).write_text(content, encoding='utf-8')
        dest = Path(self.tmp.name) / 'legacy-copy'
        workflow.initialize(self.root, dest)
        self.assertEqual(workflow.check(dest)['errors'], [])
        for name, content in legacy.items():
            self.assertEqual((dest / name).read_text(encoding='utf-8'), content)
        self.assertFalse((dest / 'README.zh.md').exists())
        (dest / 'README.en.md').write_text('[Missing](missing-legacy-note.md)\n', encoding='utf-8')
        self.assertTrue(any('README.en.md' in msg and 'missing-legacy-note.md' in msg for msg in workflow.check(dest)['errors']))
        for mode in ('empty', 'demo'):
            with self.subTest(mode=mode):
                starter = Path(self.tmp.name) / mode
                workflow.initialize(self.root, starter, **{mode: True})
                self.assert_vault_navigation(starter)

    def test_demo_starts_with_sources_but_no_concept_notes_or_cards(self):
        dest = Path(self.tmp.name) / 'demo'
        result = workflow.initialize(ROOT, dest, demo=True)
        self.assertFalse(result['example_notes'])
        files = {f.relative_to(dest).as_posix() for f in (dest / 'assets').rglob('*') if f.is_file()}
        self.assertEqual(files, {'assets/demo/serving-sources.md', 'assets/demo/streaming-dialogue.md',
                                 'assets/demo/retrieval.md', 'assets/demo/first-token.vtt'})
        for name in files:
            source = EXAMPLE if EXAMPLE.is_dir() else ROOT
            self.assertEqual((dest / name).read_bytes(), (source / name).read_bytes())
        self.assertEqual(list((dest / 'Concepts').rglob('*.md')), [])
        self.assertEqual(review.catalog(dest), ([], [], []))
        self.assertFalse((dest / '.flashcards/local').exists())
        self.assert_vault_navigation(dest)
        for name in ('README.md', 'README.zh.md'):
            self.assertIn(('', 'assets/demo/serving-sources.md'), markdown_targets(dest / name))
        self.assertEqual(workflow.check(dest)['errors'], [])

    def test_initialization_never_overwrites_user_content(self):
        dest = Path(self.tmp.name) / 'occupied'
        dest.mkdir()
        p = dest / 'my-note.md'
        p.write_text('手写内容', encoding='utf-8')
        with self.assertRaises(ValueError):
            workflow.initialize(ROOT, dest)
        self.assertEqual(p.read_text(encoding='utf-8'), '手写内容')

    def test_template_runs_without_zone_data_with_a_legacy_output_encoding(self):
        env = dict(os.environ, PYTHONTZPATH='', PYTHONIOENCODING='cp1252')
        python = [sys.executable, '-S', '-B']
        def run(*args):
            result = subprocess.run([*python, *args], env=env, capture_output=True, check=True)
            return json.loads(result.stdout.decode('cp1252'))

        dest = Path(self.tmp.name).resolve() / '学习 vault 🐛'
        init = run(ROOT / 'tools/workflow.py', 'init', str(dest), '--empty')
        self.assertEqual(init['created'], str(dest))
        self.assertEqual(review.settings(dest)['timezone'], 'local')
        self.assertFalse((dest / '.flashcards/local').exists())
        cmd = [self.root / '.flashcards/review.py', '--root', self.root]
        audit = run(*cmd, 'audit')
        self.assertEqual(audit['eligible'], audit['total'])
        deck = run(*cmd, 'session')
        snapshot = run(*cmd, 'show', '--date', deck['date'])
        self.assertEqual(snapshot['timezone'], 'local')
        self.assertTrue(snapshot['cards'])
        self.assertEqual(deck['date'], review.today('local'))

    def test_copy_excludes_private_state_and_symlinks(self):
        private_source = self.root / '.local/imports/material.md'
        private_source.parent.mkdir(parents=True)
        private_source.write_text('local source text', encoding='utf-8')
        (self.root / '.local/source-files.json').write_text('{}', encoding='utf-8')
        (self.root / '.flashcards/local').mkdir(parents=True)
        (self.root / '.flashcards/local/private.txt').write_text('not for copying')
        (self.root / '.git').mkdir()
        (self.root / '.git/config').write_text('private history')
        (self.root / 'GEMINI.md').write_text('private assistant rules')
        (self.root / 'AGENTS.override.md').write_text('private workflow')
        (self.root / '.cursor/rules').mkdir(parents=True)
        (self.root / '.cursor/rules/private.mdc').write_text('private project')
        (self.root / 'Concepts/link.md').symlink_to(Path(self.tmp.name) / 'outside.md')
        for mode, options in [('full', {}), ('empty', {'empty': True}), ('demo', {'demo': True})]:
            with self.subTest(mode=mode):
                dest = Path(self.tmp.name) / mode
                workflow.initialize(self.root, dest, **options)
                for name in ('.local', '.flashcards/local', '.git', 'Concepts/link.md', 'GEMINI.md', 'AGENTS.override.md', '.cursor'):
                    self.assertFalse((dest / name).exists(), name)

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
        for mode in ('empty', 'demo'):
            with self.subTest(mode=mode):
                dest = Path(self.tmp.name) / mode
                workflow.initialize(self.root, dest, **{mode: True})
                self.assertIn('Books', review.settings(dest)['source_dirs'])
                self.assertTrue((dest / 'Books').is_dir())
                self.assertEqual(list((dest / 'Books').iterdir()), [])
                self.assertEqual(workflow.check(dest)['errors'], [])
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
