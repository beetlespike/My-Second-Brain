"""The daily agent's inbox and the receipts shown at the vault's private URL."""

import html
import json

PUBLICATION = 'agent_published_day'
PAGE_SIZE = 20
OUTCOMES = {'answered': '助手已回复', 'revised': '已修订卡片', 'linked': '已附相关卡片'}

_JOIN = '''
    FROM feedback f LEFT JOIN feedback_resolutions r ON r.sequence=f.sequence
'''
_SELECT = '''
    SELECT f.sequence AS id, f.day AS session_date, f.received, f.card_id, f.version,
           f.rating, f.note, v.payload AS original, r.decision, r.handled,
           updated.payload AS revision
''' + _JOIN + '''
    LEFT JOIN versions v ON v.card_id=f.card_id AND v.version=f.version
    LEFT JOIN versions updated ON updated.card_id=r.target_id AND updated.version=r.target_version
'''
_UNHANDLED = " WHERE has_note(f.note) AND r.sequence IS NULL"


class PendingFeedback(ValueError):
    def __init__(self, report):
        super().__init__('发布前还有留言待处理。')
        self.report = report


def published_day(db):
    row = db.execute('SELECT value FROM metadata WHERE key=?', (PUBLICATION,)).fetchone()
    return row[0] if row else None


def entry(db, row):
    result = dict(row)
    original = result.pop('original')
    card = json.loads(original) if original else {}
    if not card:
        old = db.execute('SELECT payload FROM sessions WHERE day=?', (row['session_date'],)).fetchone()
        if old:
            card = next((c for c in json.loads(old[0])['cards']
                         if (c['id'], c['version']) == (row['card_id'], row['version'])), {})
    result.update(kind=card.get('kind', 'review'), question=card.get('front'), answer=card.get('back'),
                  card_file=card.get('card_file'), sources=card.get('sources', []))
    decision = result.pop('decision')
    result['resolution'] = json.loads(decision) if decision else None
    revised = result.pop('revision')
    if revised:
        target = json.loads(revised)
        result['result_card'] = {key: target.get(key) for key in ('card_file', 'front', 'back', 'details')}
    return result


def report(db, day, after=0):
    count = db.execute('SELECT count(*) ' + _JOIN + _UNHANDLED).fetchone()[0]
    rows = list(db.execute(_SELECT + _UNHANDLED + ' AND f.sequence>? ORDER BY f.sequence LIMIT ?',
                           (after, PAGE_SIZE + 1)))
    return {'status': 'feedback_pending' if count else 'ready_to_prepare', 'date': day,
            'workspace_id': db.execute("SELECT value FROM metadata WHERE key='workspace_id'").fetchone()[0],
            'pending_count': count, 'items': [entry(db, row) for row in rows[:PAGE_SIZE]],
            'next_after': rows[PAGE_SIZE - 1]['id'] if len(rows) > PAGE_SIZE else None}


def require_clear(db, day):
    if db.execute('SELECT 1 ' + _JOIN + _UNHANDLED + ' LIMIT 1').fetchone():
        raise PendingFeedback(report(db, day))


def begin(db, day, after=0):
    """Keep the previous delivery available while an agent prepares a new one."""
    db.execute('BEGIN IMMEDIATE')
    try:
        if published_day(db) is None:
            previous = db.execute('SELECT max(day) FROM sessions WHERE day<=?', (day,)).fetchone()[0]
            study = db.execute("SELECT max(substr(key,11)) FROM metadata WHERE key LIKE 'discovery:%' "
                               "AND substr(key,11)<=?", (day,)).fetchone()[0]
            db.execute('INSERT INTO metadata VALUES (?, ?)', (PUBLICATION, max(previous or '', study or '')))
        result = report(db, day, after)
        db.commit()
        return result
    except Exception:
        db.rollback()
        raise


def resolve(db, root, payload, day):
    import review

    workspace = db.execute("SELECT value FROM metadata WHERE key='workspace_id'").fetchone()[0]
    if not isinstance(payload, dict) or payload.get('workspace_id') != workspace:
        raise ValueError('处理结果不属于这个知识库。')
    items = payload.get('items')
    if not isinstance(items, list) or not 1 <= len(items) <= 100:
        raise ValueError('每批可处理 1–100 条留言。')
    handled = duplicates = 0
    cards = None
    db.execute('BEGIN IMMEDIATE')
    try:
        for item in items:
            if not isinstance(item, dict) or type(item.get('id')) is not int:
                raise ValueError('需要留言编号。')
            row = db.execute(_SELECT + ' WHERE f.sequence=? AND has_note(f.note)', (item['id'],)).fetchone()
            if not row:
                raise ValueError('找不到这条文字留言。')
            outcome, reply = item.get('outcome'), item.get('reply')
            if not isinstance(outcome, str) or outcome not in OUTCOMES or not isinstance(reply, str) or not 1 <= len(reply.strip()) <= 2000:
                raise ValueError('需要处理方式和给读者的具体答复（最多 2000 字）。')
            decision = {'outcome': outcome, 'reply': reply.strip()}
            target_id, target_version = None, None
            if outcome == 'linked' or (outcome == 'revised' and not row['card_id'].startswith('study:')):
                target_id = item.get('card_id', row['card_id'] if outcome == 'revised' else None)
                target_version = item.get('version')
                if not isinstance(target_id, str) or type(target_version) is not int:
                    raise ValueError('请给出对应复习卡的编号和实际版本。')
                if (target_id == row['card_id']) != (outcome == 'revised'):
                    raise ValueError('revised 指原卡的修订，linked 指另一张相关卡。')
                decision.update(card_id=target_id, version=target_version)
            canonical = review.dump(decision)
            if row['decision'] is not None:
                if row['decision'] != canonical:
                    raise ValueError('这条留言已有不同的处理结果。')
                duplicates += 1
                continue
            original = entry(db, row)
            if target_id is not None:
                if cards is None:
                    bank, errors, _ = review.catalog(root)
                    if errors:
                        raise ValueError('\n'.join(errors))
                    cards = {c['id']: c for c in bank}
                target = cards.get(target_id)
                if not target or not target['eligible'] or target['version'] != target_version:
                    raise ValueError('对应卡片的版本或来源尚未通过核对。')
                if outcome == 'revised':
                    old = (original['question'], original['answer'], original['sources'])
                    previous = json.loads(row['original'] or '{}')
                    if target_version <= row['version'] or (
                            old == (target['front'], target['back'], target['sources'])
                            and all(previous.get(k) == target[k] for k in ('details', 'concept', 'topic'))):
                        raise ValueError('请先实际修订原卡并递增版本。')
                review.register(db, [target])
            elif outcome == 'revised':
                study = review.read_discovery_card(root, original['card_file'])
                if (study['front'], study['back']) == (original['question'], original['answer']):
                    raise ValueError('待学卡的题目或解释尚未修订。')
                target_id = review.register_study(db, row['session_date'], study)
                target_version = 1
            db.execute('INSERT INTO feedback_resolutions VALUES (?, ?, ?, ?, ?)',
                       (item['id'], day, canonical, target_id, target_version))
            handled += 1
        remaining = db.execute('SELECT count(*) ' + _JOIN + _UNHANDLED).fetchone()[0]
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {'handled': handled, 'duplicates': duplicates, 'pending_count': remaining}


_HISTORY_HEADER = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>我的留言与回复 · My Second Brain</title>
<style>
:root { color-scheme: light dark; font: 16px/1.65 system-ui, sans-serif; }
body { margin: 0; background: light-dark(#f3f6f8, #10161b); color: light-dark(#18252d, #e4eaf0); }
main { max-width: 43rem; margin: 2rem auto 4rem; padding: 0 1rem; }
h1 { margin: 1rem 0; font-size: clamp(1.6rem, 5vw, 2rem); }
article { margin: .85rem 0; padding: 1.2rem 1.4rem; border: 1px solid light-dark(#cfd9df, #394852);
          border-radius: .65rem; background: light-dark(#fff, #182128); }
h2 { margin: .45rem 0; font-size: 1.1rem; }
p { margin: .4rem 0; white-space: pre-wrap; overflow-wrap: anywhere; }
small { color: light-dark(#4e626f, #aabdc9); }
a, summary { color: light-dark(#285971, #a8d2e7); }
details, .reply { margin-top: .8rem; }
summary { cursor: pointer; }
details p { padding-left: .8rem; border-left: 2px solid light-dark(#cbdbe3, #52626d); }
</style></head>
<body><main><a href="today">返回今日知识卡</a><h1>我的留言与回复</h1>"""


def history_html(db, before=None):
    clauses = ' WHERE has_note(f.note)'
    args = []
    if before is not None:
        clauses += ' AND f.sequence<?'
        args.append(before)
    rows = list(db.execute(_SELECT + clauses + ' ORDER BY f.sequence DESC LIMIT ?', (*args, PAGE_SIZE + 1)))
    esc = html.escape
    parts = [_HISTORY_HEADER]
    if not rows:
        parts.append('<p>这里会显示你在卡片下留下的问题，以及助手的处理结果。</p>')
    for row in rows[:PAGE_SIZE]:
        item = entry(db, row)
        result = item['resolution']
        label = OUTCOMES[result['outcome']] if result else '待处理 · 助手下次制卡时处理'
        parts.extend(['<article>', '<small>' + esc(item['received']) + ' · ' + label + '</small>',
                      '<h2>' + esc(item['question'] or item['card_id']) + '</h2>',
                      '<p>' + esc(item['note']) + '</p>'])
        if result:
            parts.append('<p class="reply"><strong>助手回复</strong> <small>' + esc(item['handled']) +
                         '</small><br>' + esc(result['reply']) + '</p>')
        target = item.get('result_card')
        if target:
            parts.append('<details><summary>查看处理后的卡片</summary><p>' + esc(target['front']) +
                         '</p><p>' + esc(target['back']) + '</p>')
            if target['details']:
                parts.append('<p><strong>展开</strong><br>' + esc(target['details']) + '</p>')
            parts.append('</details>')
        parts.append('</article>')
    if len(rows) > PAGE_SIZE:
        parts.append(f'<a href="?feedback=1&amp;before={rows[PAGE_SIZE-1]["id"]}">更早的留言</a>')
    parts.append('</main></body></html>')
    return ''.join(parts)
