"""Web feedback uses the published snapshot and the rating a reader saw."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

import feedback_inbox
import issue_archive
import review
from test_review import sample_cards


class RatingStateTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.db = review.connect(self.root)
        self.addCleanup(self.db.close)
        self.cards = sample_cards(2)
        self.day = '2026-02-12'
        self.tomorrow = '2026-02-13'
        self.deck = self.publish(self.day)
        self.first, self.second = self.deck['cards']

    def publish(self, day):
        deck, _ = review.make_session(self.db, self.cards, day)
        issue_archive.record(self.db, deck, None, 'portal')
        self.db.commit()
        return deck

    def entry(self, card, **changes):
        return dict(card_id=card['id'], position=card['position'], version=card['version'], **changes)

    def payload(self, batch, entries, day=None):
        return dict(batch_id=batch, workspace_id=self.deck['workspace_id'],
                    session_date=day or self.day, entries=list(entries))

    def save(self, batch, *entries, day=None, received=None, portal=True):
        return review.save_feedback(self.db, self.cards, self.payload(batch, entries, day),
                                    received or self.day, portal=portal)

    def test_lost_receipt_after_correction_returns_current_rating(self):
        cid = self.first['id']
        comment = self.entry(self.first, note='What happens next?', expected_rating_sequence=None)
        self.assertEqual(self.save('note-first', comment)['rating_states'][cid],
                         {'saved_rating': None, 'rating_sequence': None, 'rating_lock': None})
        rated = self.entry(self.first, rating='again', expected_rating_sequence=None)
        first = self.save('initial', rated)['rating_states'][cid]
        changed = dict(rated, rating='familiar', expected_rating_sequence=first['rating_sequence'])
        last = self.save('corrected', changed)['rating_states'][cid]
        self.assertGreater(last['rating_sequence'], first['rating_sequence'])
        self.assertEqual((last['saved_rating'], last['rating_lock']), ('familiar', None))
        retried = self.save('initial', rated)
        self.assertEqual((retried['saved'], retried['duplicates'], retried['rating_states'][cid]), (0, 1, last))
        with self.assertRaisesRegex(ValueError, '同一反馈编号'):
            self.save('initial', dict(rated, rating='uncertain'))
        for expected in (None, first['rating_sequence']):
            with self.assertRaises(review.RatingConflict) as conflict:
                self.save('stale', dict(changed, expected_rating_sequence=expected))
            self.assertEqual(conflict.exception.payload, dict(
                card_id=cid, error=str(conflict.exception), code='rating_changed', **last))
        with self.assertRaises(review.RatingConflict):
            self.save('old-client', self.entry(self.first, rating='again'))
        self.assertEqual(self.save('initial', rated, received=self.tomorrow)['duplicates'], 1)
        self.assertEqual(self.db.execute('SELECT count(*) FROM feedback').fetchone()[0], 3)

    def test_two_connections_cannot_overwrite_the_same_observed_rating(self):
        cid = self.first['id']
        rated = self.entry(self.first, rating='again', expected_rating_sequence=None)
        seq = self.save('initial', rated)['rating_states'][cid]['rating_sequence']
        ready = threading.Barrier(2)

        def write(rating):
            with closing(review.connect(self.root)) as db:
                entry = dict(rated, expected_rating_sequence=seq, rating=rating)
                ready.wait(timeout=8)
                try:
                    result = review.save_feedback(db, self.cards, self.payload(rating, [entry]), self.day, portal=True)
                except review.RatingConflict as conflict:
                    return conflict.payload
                return result['rating_states'][cid]

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(write, ['familiar', 'uncertain']))
        winner, = [result for result in results if 'code' not in result]
        loser, = [result for result in results if 'code' in result]
        self.assertEqual(loser['code'], 'rating_changed')
        self.assertEqual((loser['saved_rating'], loser['rating_sequence']),
                         (winner['saved_rating'], winner['rating_sequence']))
        self.assertEqual(self.db.execute('SELECT count(*) FROM feedback').fetchone()[0], 2)

    def test_waiting_portal_rechecks_the_time_and_card_after_acquiring_write_lock(self):
        for code in ('past_issue', 'inactive'):
            ready, go, writing = threading.Event(), threading.Event(), threading.Event()
            latest = {'day': self.day, 'cards': self.cards}

            def write():
                with closing(review.connect(self.root)) as db:
                    def observe(statement):
                        if statement == 'BEGIN IMMEDIATE':
                            writing.set()
                    db.set_trace_callback(observe)
                    ready.set()
                    self.assertTrue(go.wait(timeout=5))
                    payload = self.payload('waiting', [self.entry(self.first, rating='uncertain')])
                    return review.save_portal_feedback(db, self.root, payload)

            with self.subTest(code=code), patch.object(review, 'today', lambda _: latest['day']), \
                    patch.object(review, 'cards_for_feedback', lambda _: latest['cards']), \
                    ThreadPoolExecutor(max_workers=1) as pool:
                result = pool.submit(write)
                self.assertTrue(ready.wait(timeout=5))
                self.db.execute('BEGIN IMMEDIATE')
                try:
                    go.set()
                    self.assertTrue(writing.wait(timeout=5))
                    if code == 'past_issue':
                        latest['day'] = self.tomorrow
                    else:
                        latest['cards'] = [dict(c, status='paused', eligible=False) for c in self.cards]
                finally:
                    self.db.commit()
                with self.assertRaises(review.RatingConflict) as conflict:
                    result.result(timeout=5)
                self.assertEqual(conflict.exception.payload['code'], code)
        self.assertEqual(self.db.execute('SELECT count(*) FROM feedback').fetchone()[0], 0)

    def test_one_conflict_rolls_back_the_other_rating_and_both_comments(self):
        first = self.entry(self.first, rating='uncertain', expected_rating_sequence=None)
        second = self.entry(self.second, rating='again', expected_rating_sequence=None)
        self.save('other-tab', second)
        first['note'] = 'Explain the first example.'
        second['note'] = 'Explain the second example.'
        with self.assertRaises(review.RatingConflict) as conflict:
            self.save('batch', first, second)
        self.assertEqual(conflict.exception.payload['card_id'], self.second['id'])
        self.assertEqual(feedback_inbox.report(self.db, self.day)['pending_count'], 0)
        self.assertEqual(self.db.execute('SELECT count(*) FROM feedback').fetchone()[0], 1)
        kept = self.save('after-conflict', first, dict(second, rating=None))
        self.assertEqual((kept['saved'], kept['rating_states'][self.second['id']]['saved_rating']), (2, 'again'))
        notes = feedback_inbox.report(self.db, self.day)['items']
        self.assertEqual([item['note'] for item in notes], [first['note'], second['note']])

    def test_snapshot_changes_and_inactive_cards_lock_ratings_but_allow_notes(self):
        original = next(c for c in self.cards if c['id'] == self.first['id'])
        card_index = self.cards.index(original)
        for changes, code in (({'version': 2}, 'superseded'), ({'front': 'New'}, 'superseded'),
                              ({'eligible': False}, 'inactive'), ({'status': 'retired'}, 'inactive')):
            self.cards[card_index] = dict(original, **changes)
            with self.subTest(changes=changes), self.assertRaises(review.RatingConflict) as conflict:
                self.save('locked', self.entry(self.first, rating='again'))
            self.assertEqual(conflict.exception.payload['rating_lock'], {'code': code})
        self.assertEqual(self.save('note', self.entry(self.first, note='About this version'))['historical_only'], 1)
        self.assertEqual(self.save('import', self.entry(self.first, rating='again'), portal=False)['historical_only'], 1)
        self.cards[card_index] = original
        state = review.rating_state(self.db, self.first, original, self.day, self.day)
        self.assertEqual(state, dict(saved_rating=None, rating_sequence=None, rating_lock=None))

    def test_locks_use_issue_day_received_day_and_publication_pointer(self):
        next_deck = self.publish(self.tomorrow)
        next_card = next(c for c in next_deck['cards'] if c['id'] == self.first['id'])
        rated = self.entry(self.first, rating='again')
        for pointer in ('', self.tomorrow):
            self.db.execute('INSERT OR REPLACE INTO metadata VALUES (?,?)', (feedback_inbox.PUBLICATION, pointer))
            self.db.commit()
            with self.assertRaises(review.RatingConflict) as conflict:
                self.save('wrong-issue', rated)
            self.assertEqual(conflict.exception.payload['code'], 'past_issue')
        self.db.execute('DELETE FROM metadata WHERE key=?', (feedback_inbox.PUBLICATION,))
        self.db.commit()
        with self.assertRaises(review.RatingConflict) as conflict:
            self.save('after-midnight', rated, received=self.tomorrow)
        self.assertEqual(conflict.exception.payload['code'], 'past_issue')
        self.save('historical-import', rated, received=self.tomorrow, portal=False)
        with self.assertRaises(review.RatingConflict) as conflict:
            self.save('same-calendar-day', self.entry(next_card, rating='familiar'),
                      day=self.tomorrow, received=self.tomorrow)
        self.assertEqual(conflict.exception.payload['rating_lock'], {'code': 'rated_other_today', 'day': self.day})
        self.save('new-issue-import', self.entry(next_card, rating='familiar'),
                  day=self.tomorrow, received=self.tomorrow, portal=False)
        with self.assertRaises(review.RatingConflict) as conflict:
            self.save('older-issue', rated, received=self.tomorrow)
        self.assertEqual(conflict.exception.payload['rating_lock'], {'code': 'rated_newer_issue', 'day': self.tomorrow})
        self.assertEqual(self.save('historical-question', self.entry(self.first, note='Why?'),
                                   received=self.tomorrow)['saved'], 1)

    def test_portal_accepts_only_cards_and_discovery_in_delivered_snapshot(self):
        discovery = dict(title='One', front='Q', back='A', path='Study-Queue/One.md')
        selected = review.register_study(self.db, self.day, discovery)
        other = review.register_study(self.db, self.day, dict(discovery, title='Two'))
        self.db.execute('DELETE FROM published_issues')
        issue_archive.record(self.db, dict(self.deck, cards=[self.second]), discovery, 'portal')
        self.db.commit()
        for entry in (self.entry(self.first, note='Hidden'), dict(card_id=other, version=1, note='Unused'),
                      dict(self.entry(self.second, note='Wrong position'), position=1)):
            with self.subTest(entry=entry), self.assertRaises(ValueError):
                self.save('outside-issue', entry)
        with self.assertRaisesRegex(ValueError, '待学卡只接收文字'):
            self.save('study-rated', dict(card_id=selected, version=1, rating='again'))
        self.assertEqual(self.save('study', dict(card_id=selected, version=1, note='Question'))['saved'], 1)
        self.assertEqual(self.save('offline', self.entry(self.first, rating='again'), portal=False)['saved'], 1)

    def test_withdrawn_card_accepts_exact_retry_and_old_page_comments(self):
        cid = self.first['id']
        sent = self.entry(self.first, rating='again', note='Original', expected_rating_sequence=None)
        saved = self.save('initial', sent)['rating_states'][cid]
        issue_archive.record(self.db, dict(self.deck, cards=[self.second]), None, 'today')
        self.db.commit()
        receipt = self.save('initial', sent)
        self.assertEqual((receipt['duplicates'], receipt['saved']), (1, 0))
        state = receipt['rating_states'][cid]
        self.assertEqual(state, dict(saved, rating_lock={'code': 'past_issue', 'day': self.day}))
        with self.assertRaisesRegex(ValueError, '同一反馈编号'):
            self.save('initial', dict(sent, note='Changed'))
        with self.assertRaisesRegex(ValueError, '序号'):
            self.save('initial', dict(sent, position=self.second['position']))
        live = next(c for c in self.cards if c['id'] == cid)
        for changed, code in (({}, 'past_issue'), ({'version': 2}, 'superseded'),
                              ({'eligible': False, 'status': 'paused'}, 'inactive')):
            live.update(changed)
            with self.subTest(code=code), self.assertRaises(review.RatingConflict) as conflict:
                self.save('adjust', self.entry(self.second, note='Keep in draft'),
                          dict(sent, rating='familiar', expected_rating_sequence=saved['rating_sequence']))
            self.assertEqual(conflict.exception.payload['code'], code)
        receipt = self.save('late-note', self.entry(self.first, note='On this original version'))
        self.assertEqual((receipt['saved'], receipt['historical_only']), (1, 1))
        notes = feedback_inbox.report(self.db, self.day)['items']
        self.assertEqual([item['note'] for item in notes], ['Original', 'On this original version'])

    def test_withdrawn_discovery_still_accepts_its_readers_comments(self):
        study = dict(title='One', front='Question', back='Explanation', path='Study-Queue/One.md')
        cid = review.register_study(self.db, self.day, study)
        issue_archive.record(self.db, self.deck, study, 'today')
        self.db.commit()
        entry = dict(card_id=cid, version=1, note='First question')
        self.save('first', entry)
        issue_archive.record(self.db, self.deck, None, 'today')
        self.db.commit()
        self.assertEqual(self.save('first', entry)['duplicates'], 1)
        self.assertEqual(self.save('another', dict(entry, note='Follow-up'))['saved'], 1)
        with self.assertRaisesRegex(ValueError, '待学卡只接收文字'):
            self.save('bad', dict(entry, rating='familiar'))

    def test_upgraded_waiting_page_can_save_old_comments_without_creating_an_archive(self):
        self.db.execute('DELETE FROM published_issues')
        self.db.commit()
        comment = self.entry(self.first, note='Old question')
        with self.assertRaisesRegex(ValueError, '找不到对应日期已发布'):
            self.save('never-delivered', comment)
        self.db.execute('INSERT INTO metadata VALUES (?,?)', (feedback_inbox.PUBLICATION, self.day))
        self.db.commit()
        self.assertEqual(self.save('waiting', comment, received=self.tomorrow)['saved'], 1)
        with self.assertRaises(review.RatingConflict) as conflict:
            self.save('waiting-rating', self.entry(self.first, rating='again'), received=self.tomorrow)
        self.assertEqual(conflict.exception.payload['code'], 'past_issue')
        self.assertIsNone(issue_archive.get(self.db, self.day))

    def test_invalid_tokens_and_workspace_never_write_feedback(self):
        for invalid in (0, -1, False, 1.0, '1'):
            with self.subTest(token=invalid), self.assertRaisesRegex(ValueError, '正整数'):
                self.save('bad-token', self.entry(self.first, rating='again', expected_rating_sequence=invalid))
        payload = self.payload('wrong-vault', [self.entry(self.first, note='Wrong vault')])
        with self.assertRaisesRegex(ValueError, '当前学习目录'):
            review.save_feedback(self.db, self.cards, dict(payload, workspace_id='other'), self.day, portal=True)
        self.assertEqual(self.db.execute('SELECT count(*) FROM feedback').fetchone()[0], 0)
