"""Snapshots of decks delivered through a vault's local review page."""

import json
from urllib.parse import urlencode


PAGE_SIZE = 7


def get(db, day):
    row = db.execute('SELECT session, discovery FROM published_issues WHERE day=?', (day,)).fetchone()
    if row is None:
        return None
    return json.loads(row[0]), json.loads(row[1]) if row[1] is not None else None


def former_card(db, day, cid):
    row = db.execute("SELECT value FROM metadata WHERE key=?", (f'former-issue-card:{day}:{cid}',)).fetchone()
    return json.loads(row[0]) if row else None


def record(db, deck, discovery, evidence):
    """Record the visible cards and their original positions in the delivery transaction."""
    if not deck['cards'] and discovery is None:
        return
    day = deck['date']
    previous = get(db, day)
    if previous is not None:
        original, study = previous
        if original == deck and study == discovery:
            return
        visible = {c['id'] for c in deck['cards']}
        removed = [c for c in original['cards'] if c['id'] not in visible]
        if study and discovery is None:
            from review import study_id
            removed.append(dict(study, id=study_id(day, study), version=1, kind='study'))
        for card in removed:
            db.execute('INSERT OR IGNORE INTO metadata VALUES (?, ?)',
                       (f"former-issue-card:{day}:{card['id']}", json.dumps(card, ensure_ascii=False)))
    session = json.dumps(deck, ensure_ascii=False, sort_keys=True)
    study = json.dumps(discovery, ensure_ascii=False, sort_keys=True) if discovery is not None else None
    db.execute("""
        INSERT INTO published_issues(day,session,discovery,card_count,evidence) VALUES (?,?,?,?,?)
        ON CONFLICT(day) DO UPDATE SET session=excluded.session, discovery=excluded.discovery,
            card_count=excluded.card_count, evidence=excluded.evidence
    """, (day, session, study, len(deck['cards']), evidence))


def navigation(db, day):
    def url(**params):
        return 'today' + ('?' + urlencode(params) if params else '')

    newer, total = db.execute('SELECT count(CASE WHEN day>? THEN 1 END), count(*) FROM published_issues',
                              (day,)).fetchone()
    offset = newer // PAGE_SIZE * PAGE_SIZE
    rows = list(db.execute('SELECT day, card_count, discovery IS NOT NULL FROM published_issues '
                           'ORDER BY day DESC LIMIT ? OFFSET ?', (PAGE_SIZE + 1, offset)))
    issues = [dict(day=d, card_count=n, has_discovery=bool(study), is_latest=offset == 0 and i == 0,
                   is_current=d == day, url=url(day=d))
              for i, (d, n, study) in enumerate(rows[:PAGE_SIZE])]
    more = url(day=rows[-1][0], archive=1) if len(rows) > PAGE_SIZE else None
    return dict(past_issues=issues, has_archive=total > 1, past_issues_more_url=more,
                today_url=url(), feedback_url=url(feedback=1))
