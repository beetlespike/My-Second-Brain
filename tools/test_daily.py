"""Daily preparation and receipts use the same private site regardless of the agent."""

from contextlib import closing
from datetime import date, timedelta
import http.client
import json
from pathlib import Path
import re
import socket
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import urlsplit

import workflow


ROOT = Path(__file__).resolve().parents[1]
STUDY = '待学概念/推理系统/Prefill-Decode Disaggregation.md'


class DailyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.vault = Path(self.tmp.name) / 'My Vault'
        workflow.initialize(ROOT, self.vault)
        self.addCleanup(self.cli, 'today', '--stop', check=False)
        self.yesterday = (date.today() - timedelta(days=1)).isoformat()
        self.cli('session', '--date', self.yesterday)
        self.old = self.cli('show', '--date', self.yesterday)
        self.card = self.old['cards'][0]
        self.ws = self.old['workspace_id']

    def cli(self, *args, data=None, check=True):
        proc = subprocess.run([sys.executable, '-B', str(self.vault/'.flashcards/review.py'), *args],
                              input=json.dumps(data) if data is not None else None,
                              capture_output=True, text=True, encoding='utf-8', timeout=15)
        if check:
            self.assertEqual(proc.returncode, 0, proc.stderr)
            return json.loads(proc.stdout)
        return proc

    def post_note(self, batch, note, rating=None):
        entry = {'card_id': self.card['id'], 'version': self.card['version'], 'rating': rating, 'note': note}
        return self.cli('feedback', '--input', '-', '--received-date', self.yesterday,
                        data={'workspace_id': self.ws, 'session_date': self.yesterday, 'batch_id': batch, 'entries': [entry]})

    def resolve(self, items, check=True, workspace=None):
        return self.cli('resolve', '--input', '-', data={'workspace_id': workspace or self.ws, 'items': items}, check=check)

    def db(self):
        return sqlite3.connect(self.vault/'.flashcards/local/review.sqlite3')

    def http(self, url, payload=None):
        u = urlsplit(url)
        with closing(http.client.HTTPConnection(u.hostname, u.port, timeout=5)) as conn:
            if payload is None:
                conn.request('GET', u.path + ('?' + u.query if u.query else ''))
            else:
                conn.request('POST', u.path.rsplit('/', 1)[0] + '/feedback', json.dumps(payload),
                             {'Content-Type': 'application/json', 'Origin': 'http://' + u.netloc})
            response = conn.getresponse()
            body = response.read().decode()
            self.assertEqual(response.status, 200, body[:200])
            return json.loads(body) if payload is not None else body

    def deck(self, url):
        return json.loads(re.search(r'const deck = (.+);', self.http(url))[1])

    def test_existing_backlog_drains_oldest_first_without_skipping_arrivals(self):
        self.post_note('rating', '', 'again')
        for i in range(27):
            self.post_note('old-'+str(i), f'旧留言 {i}')
        with closing(self.db()) as db, db:
            db.execute('DROP TABLE IF EXISTS feedback_resolutions')
        first = self.cli('daily')
        self.assertEqual(first['pending_count'], 27)
        self.assertEqual(len(first['items']), 20)
        self.assertEqual([i['note'] for i in first['items']], [f'旧留言 {i}' for i in range(20)])
        self.assertEqual(first['items'][0]['question'], self.card['front'])
        self.assertEqual(first['items'][0]['card_file'], self.card['card_file'])
        self.assertEqual(self.cli('daily')['pending_count'], 27)
        next_page = self.cli('daily', '--after', str(first['next_after']))
        self.assertEqual([item['note'] for item in next_page['items']], [f'旧留言 {i}' for i in range(20, 27)])
        self.assertIsNone(next_page['next_after'])
        self.assertEqual(next_page['pending_count'], 27)
        url = self.cli('today', '--no-open')['url']
        recent = self.http(url + '?feedback=1')
        self.assertEqual(recent.count('<article>'), 20)
        cursor = re.search(r'feedback=1&amp;before=(\d+)', recent)[1]
        self.assertEqual(self.http(url + '?feedback=1&before=' + cursor).count('<article>'), 7)
        english = self.http(url + '?feedback=1&lang=en')
        self.assertIn(f'?feedback=1&amp;before={cursor}&amp;lang=en', english)
        older = self.http(url + '?feedback=1&before=' + cursor + '&lang=en')
        self.assertEqual(older.count('<article>'), 7)
        self.assertIn(f'?feedback=1&amp;before={cursor}&amp;lang=zh', older)
        self.post_note('during-work', '这一条在处理过程中到达')
        replies = [{'id': item['id'], 'outcome': 'answered', 'reply': '已对照来源，答案里的条件仍然成立。'}
                   for item in first['items']]
        self.assertNotEqual(self.resolve(replies, workspace='other', check=False).returncode, 0)
        self.assertNotEqual(self.resolve(replies + [{'id': -1, 'outcome': 'answered', 'reply': 'invalid'}],
                                         check=False).returncode, 0)
        self.assertEqual(self.cli('daily')['pending_count'], 28)
        self.assertEqual(self.resolve(replies)['handled'], 20)
        self.assertEqual(self.resolve(replies)['duplicates'], 20)
        self.assertNotEqual(self.resolve([dict(replies[0],reply='different')],check=False).returncode, 0)
        tail = self.cli('daily', '--publish')
        self.assertEqual((tail['status'], tail['pending_count']), ('feedback_pending', 8))
        self.assertNotIn('url', tail)
        self.assertEqual(tail['items'][-1]['note'], '这一条在处理过程中到达')
        with closing(self.db()) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM sessions').fetchone()[0], 1)
        self.assertEqual(len(self.cli('notes')),20)

    def test_browser_waits_for_agent_revision_then_publishes_at_same_url(self):
        self.post_note('revise', '换一个具体的数字例子。')
        item = self.cli('daily')['items'][0]
        url = self.cli('today','--no-open')['url']
        self.assertEqual(self.deck(url)['date'],self.yesterday)
        history = url + '?feedback=1'
        self.assertIn('待处理',self.http(history))
        self.assertEqual(self.cli('session','--fragment')['status'],'feedback_pending')
        version = self.card['version']
        decision = {'id':item['id'],'outcome':'revised','version':version+1,'reply':'卡背补上了一组数字。'}
        self.assertNotEqual(self.resolve([decision],check=False).returncode,0)
        note = self.vault/self.card['card_file']
        old = note.read_text(encoding='utf-8')
        meta = re.search(r'<!-- card: (\{[^\n]+\}) -->',old)
        self.assertEqual(json.loads(meta[1])['id'],self.card['id'])
        changed = dict(json.loads(meta[1]),version=version+1)
        body = old[:meta.start(1)]+json.dumps(changed,ensure_ascii=False)+old[meta.end(1):]
        note.write_text(body,encoding='utf-8')
        self.assertNotEqual(self.resolve([decision],check=False).returncode,0)
        note.write_text(body.replace(self.card['back'],self.card['back']+'\n\n例如，2 和 6 的均值为 4。',1),encoding='utf-8')
        self.assertEqual(self.resolve([decision])['handled'],1)
        self.assertIn('卡背补上了一组数字。',self.http(history))
        self.post_note('late','制卡以后、发布以前到达。')
        self.assertEqual(self.cli('daily','--publish')['status'],'feedback_pending')
        late=self.cli('daily')['items'][0]
        self.resolve([{'id':late['id'],'outcome':'answered','reply':'这个例子使用等权观测。'}])
        config=self.vault/'.secondbrain.json'
        cfg=json.loads(config.read_text()); cfg.update(new_limit=0,daily_limit=25,concept_limit=25)
        config.write_text(json.dumps(cfg),encoding='utf-8')
        published=self.cli('daily','--publish','--discovery',STUDY)
        self.assertEqual((published['status'],published['url']),('published',url))
        current=self.deck(url)
        self.assertEqual(current['date'],date.today().isoformat())
        new=next(c for c in current['cards'] if c['id']==self.card['id'])
        self.assertEqual(new['version'],version+1)
        self.assertIn('均值为 4',new['back'])
        self.assertEqual(self.cli('show','--date',self.yesterday),self.old)
        self.assertEqual(self.cli('daily','--publish')['url'],url)

    def test_reply_shows_the_expanded_example_from_the_handled_version(self):
        self.post_note('expanded-example', '展开里可以补一个算例吗？')
        item = self.cli('daily')['items'][0]
        url = self.cli('today', '--no-open')['url']
        card = self.card
        path = self.vault / card['card_file']
        original = path.read_text(encoding='utf-8')
        meta = re.search(r'<!-- card: (\{[^\n]+\}) -->', original)
        spec = json.loads(meta[1])
        self.assertEqual(spec['id'], card['id'])
        spec['version'] += 1
        changed = original[:meta.start(1)] + json.dumps(spec, ensure_ascii=False) + original[meta.end(1):]
        example = '三个观测值满足 2 < 4 < 6，等权均值是 4。'
        self.assertTrue(card['details'])
        self.assertEqual(changed.count(card['details']), 1)
        changed = changed.replace(card['details'], card['details'] + '\n\n' + example)
        path.write_text(changed, encoding='utf-8')

        receipt = self.resolve([{'id': item['id'], 'outcome': 'revised', 'version': spec['version'],
                                 'reply': '展开栏已补上计算过程。'}])
        self.assertEqual(receipt['handled'], 1)
        path.write_text(changed.replace(example, '后续编辑中的另一组数字。'), encoding='utf-8')
        history = self.http(url + '?feedback=1')
        self.assertIn('2 &lt; 4 &lt; 6，等权均值是 4。', history)
        self.assertNotIn('后续编辑中的另一组数字。', history)

    def test_study_card_comment_enters_inbox_and_does_not_schedule_a_review(self):
        cfg=self.vault/'.secondbrain.json'
        cfg.write_text(json.dumps({'timezone':'local','new_limit':0}),encoding='utf-8')
        old_entries=[{'card_id':c['id'],'version':c['version'],'rating':'familiar'} for c in self.old['cards']]
        self.cli('feedback','--input','-',data={'workspace_id':self.ws,'session_date':self.yesterday,
                 'batch_id':'rest','entries':old_entries})
        pub=self.cli('daily','--publish','--discovery',STUDY)
        self.assertEqual(pub['count'],0)
        url=pub['url']; deck=self.deck(url); card=deck['discovery']
        payload={'workspace_id':self.ws,'batch_id':'study-note','session_date':deck['date'],
                 'entries':[{'card_id':card['feedback_id'],'version':1,'note':'这张新卡为什么忽略重叠？'}]}
        self.assertEqual(self.http(url,payload)['saved'],1)
        self.assertEqual(self.http(url,payload)['duplicates'],1)
        item=self.cli('daily')['items'][0]
        self.assertEqual((item['kind'],item['card_file'],item['question']),('study',STUDY,card['front']))
        self.assertNotEqual(self.cli('feedback','--input','-',check=False,data=dict(payload,batch_id='bad',
                 entries=[dict(payload['entries'][0],rating='again')])).returncode,0)
        self.resolve([{'id':item['id'],'outcome':'answered','reply':'这里先看无法重叠时的传输成本。'}])
        self.assertIn('这里先看无法重叠时的传输成本。',self.http(url+'?feedback=1'))
        with closing(self.db()) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM sessions WHERE day=?',(deck['date'],)).fetchone()[0],0)

    def test_bookmark_survives_busy_port_and_stopped_listener(self):
        url = self.cli('today', '--no-open')['url']
        self.assertTrue(self.cli('today', '--stop')['stopped'])
        self.cli('daily')
        with socket.socket() as other:
            other.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            other.bind(('127.0.0.1', urlsplit(url).port))
            other.listen()
            failed = self.cli('daily', '--publish', check=False)
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn('端口', failed.stderr)
        self.assertEqual(self.cli('daily', '--publish')['url'], url)

    def test_retired_study_note_keeps_old_feedback_and_can_link_a_related_review(self):
        published = self.cli('daily', '--publish', '--discovery', STUDY)
        url = published['url']
        deck = self.deck(url)
        card = deck['discovery']
        payload = {
            'workspace_id': self.ws, 'batch_id': 'follow-up', 'session_date': deck['date'],
            'entries': [{'card_id': card['feedback_id'], 'version': 1, 'note': '能再附一道库里已有的复习题吗？'}],
        }
        self.assertEqual(self.http(url, payload)['saved'], 1)
        item = self.cli('daily')['items'][0]
        target = next(card for card in deck['cards'] if card['id'].startswith('sb-fc-'))
        decision = {'id': item['id'], 'outcome': 'linked', 'card_id': target['id'],
                    'version': target['version'], 'reply': '附上你题组里的相关练习，卡背给了计算步骤。'}
        self.assertNotEqual(self.resolve([dict(decision, version=1000)], check=False).returncode, 0)
        self.assertEqual(self.resolve([decision])['handled'], 1)
        (self.vault / STUDY).rename(self.vault / 'retired-study.md')
        self.assertEqual(self.cli('daily', '--publish')['url'], url)
        self.assertNotIn('discovery', self.deck(url))
        history = self.http(url + '?feedback=1')
        self.assertIn(target['front'], history)
        self.assertIn('已附相关卡片', history)
