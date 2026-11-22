"""Open one on-demand, loopback-only review page per vault and feedback store."""

from contextlib import closing
from datetime import date
import errno
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import sqlite3
import subprocess
import sys
import time
from urllib.parse import parse_qs, urlsplit
import webbrowser

import feedback_inbox as inbox
import issue_archive
import review

HOST = '127.0.0.1'
RECORD = 'today_listener'
PROTOCOL = 6
MAX_BODY = 256 * 1024


def checked_cards(root):
    cards, errors, _ = review.catalog(root)
    if errors:
        raise ValueError('\n'.join(errors))
    return cards


def prepare(db, root, cfg, day, cards, *, note=None, preferred=(), deliver=False):
    discovery = review.read_discovery_card(root, note) if note else None
    discard = None
    if deliver and discovery is None:
        stored = review.selected_discovery(db, day)
        if stored:
            try:
                refreshed = review.read_discovery_card(root, stored['path'])
                discovery = refreshed if review.study_id(day, refreshed) == review.study_id(day, stored) else stored
            except (FileNotFoundError, ValueError):
                discard = stored
    session, _ = review.select_session(db, cards, day, preferred, settings=cfg, allow_empty=True,
                                       deliver=deliver, discovery=discovery, portal=not deliver,
                                       discard_discovery=discard)
    shown = session['date']
    if discovery is None:
        discovery = review.selected_discovery(db, shown)
    if discovery is not None:
        review.register_study(db, shown, discovery)
    if not session.get('workspace_id'):
        session['workspace_id'] = db.execute("SELECT value FROM metadata WHERE key='workspace_id'").fetchone()[0]
    return session, discovery


def visible_snapshot(deck, current, cfg):
    cards = review.visible_cards(deck, current, cfg)
    new_count = sum(c['presentation'] == 'new' for c in cards)
    return dict(deck, cards=cards, new_count=new_count, review_count=len(cards) - new_count)


def render_portal(db, root, cfg, today, deck, discovery, bank, *, archived=False, archive_open=False):
    day = deck['date']
    current = {c['id']: c for c in bank}
    issue = dict(deck, **issue_archive.navigation(db, day))
    issue.update(is_past_issue=day != today, past_issues_open=archive_open, interval_days=cfg['interval_days'])
    issue['cards'] = [dict(card, **review.rating_state(db, card, current.get(card['id']), day, today))
                      for card in deck['cards']]
    saved = [r[0] for r in db.execute('SELECT DISTINCT card_id FROM feedback WHERE day=? ORDER BY card_id', (day,))]
    page, _ = review.page_html(root, issue, discovery=discovery, saved_ids=saved, current_cards=bank, archived=archived)
    return page


def portal_page(root, folder, *, issue_day=None, archive_open=False):
    with closing(review.connect(root, folder)) as db, db:
        db.execute('BEGIN' if issue_day is not None else 'BEGIN IMMEDIATE')
        cfg = review.settings(root)
        today = review.today(cfg['timezone'])
        if issue_day is not None:
            pair = issue_archive.get(db, issue_day)
            if pair is None:
                return None
            return render_portal(db, root, cfg, today, *pair, review.cards_for_feedback(root),
                                 archived=True, archive_open=archive_open)
        bank = review.cards_for_feedback(root) if inbox.published_day(db) is not None else checked_cards(root)
        deck, discovery = prepare(db, root, cfg, today, bank)
        if deck['date'] == today:
            snapshot = visible_snapshot(deck, {c['id']: c for c in bank}, cfg)
            issue_archive.record(db, snapshot, discovery, 'today')
        else:
            archived = issue_archive.get(db, deck['date'])
            if archived:
                saved_deck, discovery = archived
                deck = dict(saved_deck, awaiting_publication=today)
            else:
                # An upgraded agent-managed vault may still be serving an unarchived legacy issue.
                deck = visible_snapshot(deck, {c['id']: c for c in bank}, cfg)
        return render_portal(db, root, cfg, today, deck, discovery, bank)


class TodayHandler(BaseHTTPRequestHandler):
    timeout = 10

    def log_message(self, format, *args):
        # The URL grants access to this vault. Keep it out of request logs.
        pass

    def reply(self, status, value, mime='application/json'):
        content = (json.dumps(value, ensure_ascii=False) if mime == 'application/json' else value).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', mime + '; charset=utf-8')
        self.send_header('Content-Length', str(len(content)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Content-Security-Policy', "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
        self.end_headers()
        try:
            self.wfile.write(content)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def route(self, method):
        if self.headers.get('Host') != self.server.authority:
            self.reply(403, {'error': '请从当前学习库的今日知识卡入口打开。'})
            return None
        if method == 'GET' and self.path.startswith(self.server.prefix + 'today?'):
            params = parse_qs(urlsplit(self.path).query, keep_blank_values=True)
            if any(len(values) != 1 for values in params.values()):
                self.reply(400, {'error': 'Duplicate query parameter', 'code': 'invalid_query'})
                return None
            query = {k: v[0] for k, v in params.items()}
            self.language = query.pop('lang', None)
            if self.language is not None and self.language not in ('en', 'zh'):
                self.reply(400, {'error': '请选择 en 或 zh。', 'code': 'invalid_language'})
                return None
            if not query:
                return 'today'
            if 'day' in query and query.keys() <= {'day', 'archive'}:
                self.issue_day = query['day']
                try:
                    valid = date.fromisoformat(self.issue_day).isoformat() == self.issue_day
                except ValueError:
                    valid = False
                if not valid or ('archive' in query and query['archive'] != '1'):
                    self.reply(400, {'error': 'Invalid issue date or archive flag', 'code': 'invalid_issue'})
                    return None
                self.archive_open = 'archive' in query
                return 'issue'
            if 'feedback' in query and query.keys() <= {'feedback', 'before'}:
                try:
                    if query['feedback'] != '1':
                        raise ValueError
                    cursor = query.get('before')
                    self.before = int(cursor) if cursor is not None else None
                    if cursor is not None and not (cursor.isascii() and cursor.isdecimal() and 0 < self.before < 2**63):
                        raise ValueError
                except ValueError:
                    self.reply(400, {'error': '无效的留言页。', 'code': 'invalid_feedback_page'})
                    return None
                return 'history'
        routes = {'GET': ('today',), 'POST': ('feedback', 'stop')}
        for name in routes[method]:
            if self.path == self.server.prefix + name:
                return name
        if method == 'GET' and self.path == '/health':
            return 'health'
        self.reply(404, {'error': '找不到这个入口。'})
        return None

    def do_GET(self):
        route = self.route('GET')
        if route == 'health':
            self.reply(200, {'instance': self.server.instance})
        elif route == 'history':
            try:
                with closing(review.connect(self.server.root, self.server.folder)) as db:
                    history = inbox.history_html(db, self.before, language=self.language)
            except (OSError, sqlite3.Error) as exc:
                self.reply(503, {'error': str(exc)})
                return
            self.reply(200, history, 'text/html')
        elif route in ('today', 'issue'):
            try:
                page = portal_page(self.server.root, self.server.folder,
                                   issue_day=self.issue_day if route == 'issue' else None,
                                   archive_open=route == 'issue' and self.archive_open)
                if page is None:
                    self.reply(404, {'error': 'No published issue for this date', 'code': 'issue_not_found'})
                    return
            except (ValueError, KeyError, OSError, sqlite3.Error) as exc:
                self.reply(503, {'error': str(exc)})
                return
            self.reply(200, page, 'text/html')

    def do_POST(self):
        route = self.route('POST')
        if route is None:
            return
        if self.headers.get('Origin') != 'http://' + self.server.authority:
            self.reply(403, {'error': '请从当前学习库的页面保存。'})
            return
        if self.headers.get_content_type() != 'application/json':
            self.reply(415, {'error': '需要 JSON 反馈。'})
            return
        if route == 'stop':
            self.reply(200, {'stopped': True})
            self.server.shutdown()
            return
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= MAX_BODY:
                self.reply(413, {'error': '反馈为空或过长。'})
                return
            payload = json.loads(self.rfile.read(size).decode('utf-8'))
            if not isinstance(payload, dict) or not isinstance(payload.get('entries'), list) or not all(isinstance(e, dict) for e in payload['entries']):
                raise ValueError('反馈格式不完整。')
            root = self.server.root
            with closing(review.connect(root, self.server.folder)) as db:
                receipt = review.save_portal_feedback(db, root, payload)
        except review.RatingConflict as exc:
            self.reply(409, exc.payload)
            return
        except (ValueError, TypeError, KeyError) as exc:
            self.reply(400, {'error': str(exc)})
            return
        except (OSError, sqlite3.Error) as exc:
            self.reply(503, {'error': str(exc)})
            return
        self.reply(200, receipt)


def listener_record(db, root, folder):
    row = db.execute('SELECT value FROM metadata WHERE key=?', (RECORD,)).fetchone()
    if row:
        record = json.loads(row[0])
        if record['scope'] == scope(root, folder):
            return record
    return {}


def scope(root, folder):
    if root == review.BUNDLED_VAULT and folder == review.TOOL_ROOT / '.flashcards/local':
        # This database and its bookmark were issued when the sample lived at the checkout root.
        root = review.TOOL_ROOT
    return review.digest(str(root) + '\0' + str(folder))


def contact(port, path, method='GET'):
    authority = f'{HOST}:{port}'
    headers = {'Origin': 'http://' + authority, 'Content-Type': 'application/json'}
    with closing(http.client.HTTPConnection(HOST, port, timeout=1)) as conn:
        conn.request(method, path, body=b'{}' if method == 'POST' else None, headers=headers)
        response = conn.getresponse()
        if response.status != 200:
            return {}
        value = json.loads(response.read(2048))
        return value if isinstance(value, dict) else {}


def running(record):
    if not record:
        return False
    try:
        return contact(record['port'], '/health').get('instance') == record['instance']
    except (OSError, ValueError, http.client.HTTPException):
        return False


def address(record):
    return f"http://{HOST}:{record['port']}/{record['key']}/today"


def serve(root, folder):
    # Serialize the short listen/reuse decision, including simultaneous Agent launches.
    with closing(review.connect(root, folder)) as db, db:
        db.execute('BEGIN IMMEDIATE')
        old = listener_record(db, root, folder)
        if running(old):
            if old.get('protocol') == PROTOCOL:
                print(json.dumps({'url': address(old), 'server': 'reused'}), flush=True)
                return
            stop_listener(old)
        port = old.get('port', 0)
        try:
            server = ThreadingHTTPServer((HOST, port), TodayHandler)
        except OSError as exc:
            if not port or exc.errno not in (errno.EADDRINUSE, errno.EACCES):
                raise
            raise OSError('私人网址原来的端口被其他程序占用。端口可用后，再打开今日知识卡即可沿用原书签。') from exc
        record = {'scope': scope(root, folder), 'port': server.server_port, 'protocol': PROTOCOL,
                  'key': old.get('key') or secrets.token_urlsafe(24), 'instance': secrets.token_hex(16)}
        server.root, server.folder = root, folder
        server.authority = f'{HOST}:{server.server_port}'
        server.prefix, server.instance = '/' + record['key'] + '/', record['instance']
        db.execute('INSERT OR REPLACE INTO metadata VALUES (?, ?)', (RECORD, json.dumps(record)))
    with server:
        print(json.dumps({'url': address(record), 'server': 'started'}), flush=True)
        server.serve_forever(poll_interval=0.1)


def stop(root, folder):
    path = folder / 'review.sqlite3'
    if not path.is_file():
        return {'stopped': False}
    with closing(sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)) as db:
        record = listener_record(db, root, folder)
    if not running(record):
        return {'stopped': False}
    return stop_listener(record)


def stop_listener(record):
    result = contact(record['port'], '/' + record['key'] + '/stop', 'POST')
    for _ in range(30):
        if not running(record):
            return result
        time.sleep(0.05)
    raise OSError('今日知识卡仍在关闭，请稍后重试。')


def start_listener(root, folder):
    options = {'creationflags': subprocess.CREATE_NO_WINDOW} if os.name == 'nt' else {'start_new_session': True}
    worker = subprocess.Popen([sys.executable, '-B', str(Path(__file__).resolve()), str(root), str(folder)],
                              stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, **options)
    with worker.stdout:
        line = worker.stdout.readline()
    if not line:
        raise OSError('今日知识卡启动失败，请重新运行入口。')
    result = json.loads(line)
    if 'error' in result:
        raise OSError(result['error'])
    return result


def run(root, args, *, publish=False):
    folder = (args.state_dir or root / '.flashcards/local').resolve()
    if args.stop:
        return stop(root, folder)
    result = start_listener(root, folder)
    deliver = bool(publish or args.discovery or args.prefer_new or args.chat_output)
    with closing(review.connect(root, folder)) as db, db:
        db.execute('BEGIN IMMEDIATE')
        cfg = review.settings(root)
        day = review.today(cfg['timezone'])
        bank = review.cards_for_feedback(root) if not deliver and inbox.published_day(db) is not None else checked_cards(root)
        deck, discovery = prepare(db, root, cfg, day, bank, note=args.discovery, preferred=args.prefer_new,
                                  deliver=deliver)
        snapshot = visible_snapshot(deck, {c['id']: c for c in bank}, cfg)
        count = len(snapshot['cards'])
        if publish:
            issue_archive.record(db, snapshot, discovery, 'daily --publish')
            render_portal(db, root, cfg, day, deck, discovery, bank)
    fragment = None
    if args.chat_output and (count or discovery):
        review.render(root, deck, args.chat_output, standalone=False, discovery=discovery)
        fragment = str(args.chat_output.resolve())
    result.update(date=deck['date'], workspace_id=deck['workspace_id'], count=count,
                  discovery=discovery['path'] if discovery else None)
    if publish:
        result['status'] = 'published'
    if deck.get('awaiting_publication'):
        result['awaiting_publication'] = deck['awaiting_publication']
    if args.chat_output:
        result['fragment'] = fragment
    if not args.no_open:
        result['opened'] = webbrowser.open(result['url'])
    return result


if __name__ == '__main__':
    try:
        serve(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
    except (OSError, ValueError, sqlite3.Error) as error:
        print(json.dumps({'error': str(error)}), flush=True)
        sys.exit(1)
