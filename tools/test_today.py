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

    def test_archive_starts_empty_and_only_web_delivery_records_an_issue(self):
        self.run_cli('session')
        self.run_cli('daily')
        db_path = self.vault / '.flashcards/local/review.sqlite3'
        with closing(sqlite3.connect(db_path)) as db, db:
            ws = db.execute("SELECT value FROM metadata WHERE key='workspace_id'").fetchone()
            self.assertTrue(db.execute("SELECT value FROM metadata WHERE key='agent_published_day'").fetchone()[0])
            db.execute('DROP TABLE published_issues')
        url = self.run_cli('today', '--no-open')['url']
        with closing(sqlite3.connect(db_path)) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM published_issues').fetchone()[0], 0)
            self.assertEqual(db.execute("SELECT value FROM metadata WHERE key='workspace_id'").fetchone(), ws)
        with ThreadPoolExecutor(max_workers=2) as pool:
            first, repeated = pool.map(lambda _: self.deck(url)[0], range(2))
        self.assertEqual(first, repeated)
        self.assertFalse(first['has_archive'])
        with closing(sqlite3.connect(db_path)) as db:
            rows = db.execute('SELECT day,session,discovery,card_count,evidence FROM published_issues').fetchall()
        self.assertEqual(len(rows), 1)
        day, session, study, count, evidence = rows[0]
        self.assertEqual((day, study, count, evidence), (first['date'], None, len(first['cards']), 'today'))
        self.assertNotIn('excerpt', json.loads(session)['cards'][0]['sources'][0])
        self.assertNotIn('rating_lock', json.loads(session)['cards'][0])

    def test_concurrent_discovery_selection_and_same_day_archive(self):
        url = self.run_cli('today', '--no-open')['url']
        regular = self.deck(url)[0]
        other = self.vault / '待学概念/Another.md'
        other.write_text('# Another study\n\n## Study Card\n\n### Front\nWhy?\n\n### Short Answer\nBecause.\n')
        notes = [DISCOVERY, other.relative_to(self.vault).as_posix()]
        with ThreadPoolExecutor(max_workers=2) as pool:
            result = list(pool.map(lambda note: self.command(self.vault, 'daily', '--publish', '--discovery', note,
                                                             check=False), notes))
        self.assertEqual(sorted(p.returncode for p in result), [0, 1])
        winner = notes[next(i for i, p in enumerate(result) if p.returncode == 0)]
        with closing(sqlite3.connect(self.vault / '.flashcards/local/review.sqlite3')) as db:
            study, evidence = db.execute('SELECT discovery,evidence FROM published_issues WHERE day=?',
                                         (regular['date'],)).fetchone()
        self.assertEqual((json.loads(study)['path'], evidence), (winner, 'daily --publish'))
        live = self.deck(url)[0]
        self.assertEqual(live['discovery']['path'], winner)
        self.assertEqual(regular['cards'], live['cards'])
        self.assertEqual(self.deck(url + '?day=' + regular['date'])[0]['discovery'], live['discovery'])

    def test_unrenderable_page_does_not_publish_an_issue(self):
        url = self.run_cli('today', '--no-open')['url']
        renderer = self.vault / '.flashcards/vendor/katex-0.19.1.min.js'
        renderer.rename(renderer.with_suffix('.unavailable'))
        self.assertEqual(self.http(url)[0], 503)
        failed = self.command(self.vault, 'daily', '--publish', check=False)
        self.assertNotEqual(failed.returncode, 0)
        with closing(sqlite3.connect(self.vault / '.flashcards/local/review.sqlite3')) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM published_issues').fetchone()[0], 0)

    def test_archive_routes_keep_original_positions_and_language(self):
        url = self.run_cli('today', '--no-open')['url']
        deck = self.deck(url)[0]
        day = date.fromisoformat(deck['date'])
        db_path = self.vault / '.flashcards/local/review.sqlite3'
        with closing(sqlite3.connect(db_path)) as db, db:
            raw = json.loads(db.execute('SELECT session FROM published_issues').fetchone()[0])
            for ago in range(1, 9):
                raw['date'] = (day - timedelta(days=ago)).isoformat()
                raw['cards'][0]['position'] = 22
                db.execute('INSERT INTO published_issues VALUES (?,?,NULL,?,?)',
                           (raw['date'], json.dumps(raw), len(raw['cards']), 'test'))
        card = deck['cards'][0]
        path = self.vault / card['card_file']
        def retire(match):
            meta = json.loads(match[1])
            if meta['id'] != card['id']:
                return match[0]
            return '<!-- card: ' + json.dumps(dict(meta, status='retired'), ensure_ascii=False) + ' -->'
        original = path.read_text()
        changed = re.sub(r'<!-- card: (\{[^\n]+\}) -->', retire, original)
        self.assertNotEqual(original, changed)
        path.write_text(changed)
        target = (day - timedelta(days=1)).isoformat()
        archive, _ = self.deck(url + '?day=' + target + '&archive=1&lang=en')
        self.assertTrue(archive['is_past_issue'] and archive['past_issues_open'] and archive['has_archive'])
        self.assertEqual(len(archive['past_issues']), 7)
        more = archive['past_issues_more_url']
        self.assertTrue(more.endswith('&archive=1'))
        self.assertEqual(archive['today_url'], 'today')
        self.assertEqual(archive['feedback_url'], 'today?feedback=1')
        older, _ = self.deck(url + more.removeprefix('today') + '&lang=en')
        self.assertEqual(len(older['past_issues']), 2)
        self.assertEqual(self.deck(url + '?day=' + target + '&archive=1&lang=zh')[0], archive)
        self.assertEqual([entry['day'] for entry in archive['past_issues'] if entry['is_current']], [target])
        self.assertEqual(archive['cards'][0]['position'], 22)
        self.assertEqual(archive['cards'][0]['rating_lock']['code'], 'inactive')
        self.assertEqual(self.http(url, self.feedback(archive))[0], 409)
        message = self.feedback(archive)
        message['entries'][0]['rating'] = None
        self.assertEqual(self.http(url, message)[0], 200)
        for query in ('?day=2026-02-30','?day=bad','?day=' + target + '&archive=0','?day=' + target + '&day=' + target,
                      '?feedback=1&before=0','?feedback=1&before=1&before=2'):
            self.assertEqual(self.http(url + query)[0], 400, query)
        for query in ('?day=1998-01-01','?archive=1','?lang=en&before=7','?day=' + target + '&feedback=1'):
            self.assertEqual(self.http(url + query)[0], 404, query)

    def test_stale_web_rating_rolls_back_other_cards_and_comment(self):
        url = self.run_cli('today', '--no-open')['url']
        deck = self.deck(url)[0]
        packet = self.feedback(deck)
        entry = packet['entries'][0]
        entry.update(note='', expected_rating_sequence=None)
        _, body = self.http(url, packet)
        saved = json.loads(body)['rating_states'][entry['card_id']]
        self.assertEqual(saved['saved_rating'], 'uncertain')
        self.assertIsNone(saved['rating_lock'])
        second = deck['cards'][1]
        stale = dict(packet, batch_id='stale-tab', entries=[
            dict(card_id=second['id'], version=second['version'], rating=None, note='Keep this draft.'),
            dict(entry, rating='again', note='Also keep this draft.')])
        status, body = self.http(url, stale)
        self.assertEqual(status, 409)
        conflict = json.loads(body)
        self.assertEqual((conflict['card_id'], conflict['code'], conflict['rating_sequence']),
                         (entry['card_id'], 'rating_changed', saved['rating_sequence']))
        self.assertEqual(self.run_cli('notes'), [])
        correction = dict(packet, batch_id='my-correction', entries=[
            dict(entry, expected_rating_sequence=saved['rating_sequence'], rating='familiar')])
        status, body = self.http(url, correction)
        self.assertEqual(status, 200)
        corrected = json.loads(body)['rating_states'][entry['card_id']]
        self.assertGreater(corrected['rating_sequence'], saved['rating_sequence'])
        self.assertEqual(self.deck(url)[0]['cards'][0]['saved_rating'], 'familiar')
        retry = json.loads(self.http(url, packet)[1])
        self.assertEqual((retry['duplicates'], retry['rating_states'][entry['card_id']]), (1, corrected))

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

    def test_existing_bookmark_and_feedback_survive_sample_directory_move(self):
        old_url = self.run_cli('today', '--no-open')['url']
        old_deck, _ = self.deck(old_url)
        self.assertEqual(self.http(old_url, self.feedback(old_deck))[0], 200)
        self.stop(self.vault)

        example = self.vault / 'examples/demo-vault'
        example.mkdir(parents=True)
        for folder in workflow.NOTE_DIRS + ('assets',):
            source = self.vault / folder
            if source.exists():
                source.rename(example / folder)
        (example / '.secondbrain.json').write_bytes((self.vault / '.secondbrain.json').read_bytes())
        self.assertFalse((example / '.flashcards').exists())
        self.assertEqual(self.run_cli('--root', str(self.vault), 'audit')['eligible'], 15)
        self.assertEqual(self.run_cli('today', '--no-open')['url'], old_url)
        self.assertEqual(self.run_cli('--root', str(example), 'today', '--no-open')['url'], old_url)
        self.assertEqual(self.deck(old_url)[0]['workspace_id'], old_deck['workspace_id'])
        self.assertEqual(self.run_cli('daily')['pending_count'], 1)
        self.assertFalse((example / '.flashcards/local/review.sqlite3').exists())

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
        note.parent.mkdir(exist_ok=True)
        note.write_text('# Bridge\n\n## 知识卡\n\n### 正面\nQuestion\n\n### 简答\nAnswer\n', encoding='utf-8')
        yesterday = date.fromisoformat(result['date']) - timedelta(days=1)
        cmd('session', '--date', yesterday.isoformat(), '--discovery', '待学概念/Bridge.md')
        self.assertFalse(self.deck(result['url'])[0].get('discovery'))
        prepared = cmd('today', '--no-open', '--discovery', '待学概念/Bridge.md')
        self.assertEqual(prepared['url'], result['url'])
        self.assertEqual(self.deck(result['url'])[0]['discovery']['front'], 'Question')
        with closing(sqlite3.connect(empty / '.flashcards/local/review.sqlite3')) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM sessions').fetchone()[0], 0)
            rows = list(db.execute('SELECT day,card_count,discovery FROM published_issues'))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0][:2], (result['date'], 0))
            self.assertEqual(json.loads(rows[0][2])['front'], 'Question')
        for name in ('Today.command', 'Today.cmd'):
            self.assertTrue((empty / name).is_file())
        self.assertNotEqual(self.run_cli('today', '--no-open')['url'], prepared['url'])
