"""Exercise the browser launcher and the chat handoff against separate sample vaults."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from datetime import date, timedelta
import http.client
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import urlsplit

import workflow


ROOT = Path(__file__).resolve().parents[1]
DISCOVERY = '待学概念/推理系统/Prefill-Decode Disaggregation.md'


class TodayTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.vault = Path(self.tmp.name) / '学习 vault'
        workflow.initialize(ROOT, self.vault)
        self.addCleanup(self.stop, self.vault)

    def command(self, vault, *args, data=None, check=True):
        return subprocess.run([sys.executable, '-B', str(vault / '.flashcards/review.py'), *args],
                              input=data, text=True, encoding='utf-8', capture_output=True,
                              timeout=15, check=check)

    def run_cli(self, *args, data=None):
        return json.loads(self.command(self.vault, *args, data=data).stdout)

    def stop(self, vault):
        if (vault / '.flashcards/local/review.sqlite3').is_file():
            self.command(vault, 'today', '--stop', check=False)

    def http(self, url, payload=None, *, origin=None):
        u = urlsplit(url)
        connection = http.client.HTTPConnection(u.hostname, u.port, timeout=4)
        try:
            if payload is None:
                connection.request('GET', u.path + ('?' + u.query if u.query else ''))
            else:
                headers = {'Content-Type': 'application/json', 'Origin': origin or 'http://' + u.netloc}
                connection.request('POST', u.path.rsplit('/', 1)[0] + '/feedback',
                                     json.dumps(payload).encode(), headers)
            response = connection.getresponse()
            return response.status, response.read().decode('utf-8')
        finally:
            connection.close()

    def deck(self, url):
        status, html = self.http(url)
        self.assertEqual(status, 200, html[:120])
        deck = json.loads(re.search(r'const deck = ([^\n]+);', html)[1])
        return deck, html

    def feedback(self, session):
        card = session['cards'][0]
        return {'session_date': session['date'], 'workspace_id': session['workspace_id'], 'batch_id': 'test-today',
                'entries': [{'card_id': card['id'], 'version': card['version'], 'position': card['position'],
                             'rating': 'uncertain', 'note': '下次换一个例子。'}]}

    def test_browser_write_and_retry_use_the_existing_feedback_store(self):
        url = self.run_cli('today', '--no-open')['url']
        self.assertEqual(urlsplit(url).hostname, '127.0.0.1')
        session, html = self.deck(url)
        self.assertIn('保存反馈', html)
        self.assertIn("fetch('feedback'", html)
        self.assertEqual(session['saved_ids'], [])
        payload = self.feedback(session)
        status, body = self.http(url, payload)
        self.assertEqual(status, 200, body)
        self.assertEqual(json.loads(body), {'saved': 1, 'duplicates': 0, 'historical_only': 0})
        self.assertEqual(json.loads(self.http(url, payload)[1])['duplicates'], 1)
        self.assertEqual(self.run_cli('notes')[0]['note'], '下次换一个例子。')
        self.assertEqual(self.deck(url)[0]['saved_ids'], [payload['entries'][0]['card_id']])
        wrong_vault = dict(payload, workspace_id='other', batch_id='other')
        self.assertGreaterEqual(self.http(url, wrong_vault)[0], 400)
        self.assertEqual(self.http(url, payload, origin='https://example.org')[0], 403)
        self.assertEqual(len(self.run_cli('notes')), 1)

    def test_language_switch_preserves_deck_and_feedback(self):
        url = self.run_cli('today', '--no-open')['url']
        deck, _ = self.deck(url + '?lang=en')
        self.assertEqual(self.deck(url + '?lang=zh')[0], deck)
        self.assertEqual(self.http(url, self.feedback(deck))[0], 200)
        for lang, title in [('en', 'My comments and replies'), ('zh', '我的留言与回复')]:
            status, page = self.http(url + '?feedback=1&lang=' + lang)
            self.assertEqual(status, 200)
            self.assertIn(f'<h1>{title}</h1>', page)
            self.assertIn('下次换一个例子。', page)
            self.assertIn(f'href="today?lang={lang}"', page)
        for query in ('?lang=fr', '?lang=', '?lang=en&lang=zh', '?feedback=1&lang=fr'):
            self.assertEqual(self.http(url + query)[0], 400)
        self.assertEqual(self.http(url + '?lang=en&before=7')[0], 404)

    def test_launches_reuse_one_browser_and_the_chat_selected_concept(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            launched = list(pool.map(lambda _: self.run_cli('today', '--no-open'), range(2)))
        self.assertEqual(launched[0]['url'], launched[1]['url'])
        self.assertEqual({result['server'] for result in launched}, {'started', 'reused'})
        fragment = Path(self.tmp.name) / 'chat.html'
        self.run_cli('session', '--fragment', '--discovery', DISCOVERY, '--output', str(fragment))
        snippet = fragment.read_text(encoding='utf-8')
        self.assertNotIn('<!doctype', snippet.lower())
        self.assertIn('sendFollowUpMessage', snippet)
        self.assertNotIn("fetch('feedback'", snippet)
        session, _ = self.deck(launched[0]['url'])
        self.assertEqual(session['discovery']['path'], DISCOVERY)
        second_fragment = Path(self.tmp.name) / 'both.html'
        combined = self.run_cli('today', '--no-open', '--chat-output', str(second_fragment))
        self.assertEqual(combined['workspace_id'], session['workspace_id'])
        self.assertEqual(combined['url'], launched[0]['url'])
        self.assertEqual(Path(combined['fragment']).read_bytes(), fragment.read_bytes())
        payload = self.feedback(session)
        self.assertEqual(self.run_cli('feedback', '--input', '-', data=json.dumps(payload))['saved'], 1)
        self.assertEqual(json.loads(self.http(launched[0]['url'], payload)[1])['duplicates'], 1)
        self.assertTrue(self.run_cli('today', '--stop')['stopped'])
        reopened = self.run_cli('today', '--no-open')
        self.assertEqual(reopened['url'], launched[0]['url'])
        self.assertEqual(reopened['discovery'], DISCOVERY)

    def test_chat_fragment_can_reuse_or_omit_todays_prepared_study_card(self):
        self.run_cli('session', '--discovery', DISCOVERY)
        fragment = Path(self.tmp.name) / 'chat.html'
        reused = self.run_cli('session', '--fragment', '--output', str(fragment))
        self.assertEqual(reused.get('discovery'), DISCOVERY)
        review_only = self.run_cli('session', '--fragment', '--review-only', '--output', str(fragment))
        self.assertNotIn('discovery', review_only)

    def test_date_selection_is_scoped_and_empty_vault_can_receive_a_card_later(self):
        empty = Path(self.tmp.name) / 'empty'
        workflow.initialize(ROOT, empty, empty=True)
        self.addCleanup(self.stop, empty)
        def cmd(*args):
            return json.loads(self.command(empty, *args).stdout)
        result = cmd('today', '--no-open')
        self.assertEqual(result['count'], 0)
        session, _ = self.deck(result['url'])
        self.assertEqual(session['cards'], [])
        self.assertFalse(session.get('discovery'))
        no_cards = cmd('today', '--no-open', '--chat-output', str(empty / 'absent.html'))
        self.assertIsNone(no_cards['fragment'])
        self.assertFalse((empty / 'absent.html').exists())
        note = empty / '待学概念/Bridge.md'
        note.write_text('# Bridge\n\n## 知识卡\n\n### 正面\nQuestion\n\n### 简答\nAnswer\n', encoding='utf-8')
        yesterday = date.fromisoformat(result['date']) - timedelta(days=1)
        cmd('session', '--date', yesterday.isoformat(), '--discovery', '待学概念/Bridge.md')
        self.assertFalse(self.deck(result['url'])[0].get('discovery'))
        prepared = cmd('today', '--no-open', '--discovery', '待学概念/Bridge.md')
        self.assertEqual(prepared['url'], result['url'])
        self.assertEqual(self.deck(result['url'])[0]['discovery']['front'], 'Question')
        with closing(sqlite3.connect(empty / '.flashcards/local/review.sqlite3')) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM sessions').fetchone()[0], 0)
        for name in ('Today.command', 'Today.cmd'):
            self.assertTrue((empty / name).is_file())
        self.assertNotEqual(self.run_cli('today', '--no-open')['url'], prepared['url'])
