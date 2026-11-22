"""Feedback receipts use the card and dates associated with each original comment."""

from pathlib import Path
import tempfile
import unittest

import feedback_inbox
import issue_archive
import review


class HistoryPageTests(unittest.TestCase):
    day = '2026-10-01'

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.db = review.connect(self.root, self.root / 'state')
        self.addCleanup(self.db.close)

    def comment(self, card_id, version=1):
        row = self.db.execute(
            'INSERT INTO feedback(event_id,day,card_id,version,note,received,applied,payload) '
            'VALUES (?,?,?,?,?,?,?,?)',
            (card_id, self.day, card_id, version, '<img src=x> $reader$', '2026-10-03', 1, '{}'))
        return row.lastrowid

    def version(self, card_id, version, **fields):
        self.db.execute('INSERT INTO versions VALUES (?,?,?,?)',
                        (card_id, version, 'hash', review.dump(fields)))

    def test_issued_review_metadata_dates_and_escaped_math(self):
        card = dict(id='first', version=1, position=14, author='Lin <editor>', front='Find $x$.')
        issue_archive.record(self.db, dict(date=self.day, cards=[card]), None, 'daily')
        self.version('first', 1, front='Old question', author='Registration author')
        self.version('first', 2, front='Use $x$', back='$x^2$ <img src=x>', details=r'$\sqrt{x}$')
        seq = self.comment('first')
        reply = dict(outcome='revised', reply='Use $$x=2$$ </script><img src=x>')
        self.db.execute('INSERT INTO feedback_resolutions VALUES (?,?,?,?,?)',
                        (seq, '2026-10-07', review.dump(reply), 'first', 2))
        for lang, issue, pos, ver, author, submitted, handled in [
            ('en', 'Issue', 'Card 14', 'Version 1', 'Author', 'Submitted', 'Replied'),
            ('zh', '期次', '第 14 张', '版本 1', '作者', '留言于', '回复于'),
        ]:
            with self.subTest(language=lang):
                page = feedback_inbox.history_html(self.db, language=lang)
                self.assertIn(f'{issue} <time>2026-10-01</time>', page)
                self.assertIn(f'{submitted} <time>2026-10-03</time>', page)
                self.assertIn(f'{handled} <time>2026-10-07</time>', page)
                self.assertIn(f'{pos} · {ver} · {author} Lin &lt;editor&gt;', page)
                self.assertNotIn('Registration author', page)
                self.assertIn('<h2 data-math-text>Find $x$.</h2>', page)
                self.assertIn('<p>&lt;img src=x&gt; $reader$</p>', page)
                self.assertIn('<span data-math-text>Use $$x=2$$ &lt;/script&gt;&lt;img', page)
                self.assertIn('<p data-math-text>$x^2$ &lt;img', page)
                self.assertIn(r'<span data-math-text>$\sqrt{x}$', page)
                self.assertIn('function renderMathText(', page)
                self.assertNotIn('<script src=', page)
                self.assertNotIn('<img src=x>', page)
                self.assertLess(len(page.encode('utf-8')), 1_000_000)
        self.assertFalse((self.root / '.flashcards').exists())

    def test_discovery_author_matches_only_the_original_study_id(self):
        study = dict(path='Study/Pool.md', title='Pool', front='Why pool?', back='Sharing.', author='Original author')
        cid = review.register_study(self.db, self.day, study)
        second = dict(study, back='A newer answer.', author='Different author')
        self.comment(review.register_study(self.db, self.day, second))
        issue_archive.record(self.db, dict(date=self.day, cards=[]), study, 'today')
        page = feedback_inbox.history_html(self.db, language='en')
        self.assertNotIn('Original author', page)
        self.assertNotIn('Different author', page)
        self.comment(cid)
        page = feedback_inbox.history_html(self.db, language='en')
        self.assertEqual(page.count('Author Original author'), 1)
        self.assertNotRegex(page, r'Card \d+ · Version')

    def test_legacy_session_provides_position_without_assigning_an_author(self):
        card = dict(id='old', version=1, front='Legacy question', position=9, author='Unconfirmed author')
        self.db.execute('INSERT INTO sessions VALUES (?,?)', (self.day, review.dump({'cards': [card]})))
        self.version('old', 1, front='Registered question', author='Registered author')
        self.comment('old')
        self.comment('unmatched')
        page = feedback_inbox.history_html(self.db, language='en')
        self.assertIn('Card 9 · Version 1', page)
        self.assertIn('Legacy question', page)
        self.assertNotIn('Unconfirmed author', page)
        self.assertNotIn('Registered author', page)
        self.assertIn('<h2 data-math-text>unmatched</h2>', page)
        self.assertEqual(self.db.execute('SELECT count(*) FROM published_issues').fetchone()[0], 0)
        issue_archive.record(self.db, dict(date=self.day, cards=[dict(card, version=2)]), None, 'today')
        page = feedback_inbox.history_html(self.db, language='en')
        self.assertNotIn('Card 9', page)
        self.assertNotIn('Unconfirmed author', page)
        self.assertIn('Registered question', page)


if __name__ == '__main__':
    unittest.main()
