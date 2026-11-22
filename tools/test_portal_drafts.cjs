// Run with Node, Playwright and Chromium installed.
const assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {chromium} = require('playwright');

const root = path.resolve(__dirname, '..');
const python = process.env.PYTHON || (process.platform === 'win32' ? 'py' : 'python3');
const flags = process.platform === 'win32' && !process.env.PYTHON ? ['-3', '-B'] : ['-B'];
const run = (cwd, args) => execFileSync(python, [...flags, ...args], {cwd, encoding: 'utf8'}).trim();
const field = (page, role) => page.locator('[data-role="' + role + '"]');
const rating = (page, code) => page.locator('[data-rating="' + code + '"]');
const pressed = (page, code) => rating(page, code).getAttribute('aria-pressed');

async function testPortalDrafts() {
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'msb-portal-drafts-'));
  const vault = path.join(temp, 'vault');
  const review = args => JSON.parse(run(vault, ['.flashcards/review.py', ...args]));
  let browser, started = false;
  try {
    run(root, ['tools/workflow.py', 'init', vault]);
    const [yesterday, studyDay] = run(vault, ['-c', `
import datetime, sys
from pathlib import Path
sys.path.insert(0, '.flashcards')
import issue_archive, review
vault = Path.cwd()
day = datetime.date.fromisoformat(review.today(review.settings(vault)['timezone'])) - datetime.timedelta(days=1)
with review.connect(vault) as db, db:
    issue, _ = review.make_session(db, review.catalog(vault)[0], day.isoformat())
    issue_archive.record(db, issue, None, 'test')
    older = (day - datetime.timedelta(days=1)).isoformat()
    study = review.read_discovery_card(vault, '待学概念/推理系统/Prefill-Decode Disaggregation.md')
    review.register_study(db, older, study)
    issue_archive.record(db, dict(issue, date=older, cards=[]), study, 'test')
print(day, older)
`]).split(' ');
    const {url} = review(['today', '--no-open']);
    started = true;
    browser = await chromium.launch({executablePath: process.env.CHROMIUM_PATH});
    const ctx = await browser.newContext({reducedMotion: 'reduce'});
    const page = await ctx.newPage(), sibling = await ctx.newPage();
    await Promise.all([page.goto(url + '?lang=en'), sibling.goto(url + '?lang=en')]);
    await field(page, 'flip').click();

    const requests = [];
    let loseReceipt = true, holdReceipt;
    await page.route('**/feedback', async route => {
      requests.push(route.request().postDataJSON());
      const response = await route.fetch();
      if (loseReceipt) {
        loseReceipt = false;
        await route.abort();
      } else {
        if (holdReceipt) await holdReceipt;
        await route.fulfill({response});
      }
    });
    await rating(page, 'again').click();
    await field(page, 'note').fill('Comment submitted once');
    await field(page, 'submit').click();
    await field(page, 'message').filter({hasText: 'unconfirmed'}).waitFor();
    await rating(page, 'familiar').click();

    // A different reader action lands between the original write and its duplicate receipt.
    const other = await browser.newPage({reducedMotion: 'reduce'});
    await other.goto(url + '?lang=en');
    await field(other, 'flip').click();
    await field(other, 'edit-rating-btn').click();
    await rating(other, 'uncertain').click();
    await field(other, 'submit').click();
    await field(other, 'edit-rating-btn').waitFor();
    await field(page, 'submit').click();
    await field(page, 'saved-rating-text').filter({hasText: 'Your choice: Familiar'}).waitFor();
    assert.equal(requests.length, 2);
    assert.deepEqual(requests[1], requests[0]);
    assert.match(await field(page, 'saved-rating-text').innerText(), /Saved rating: Shaky/);
    assert.equal(await field(page, 'note').inputValue(), '');
    await page.reload();
    assert.equal(await pressed(page, 'familiar'), 'true');
    await field(page, 'submit').click();
    await field(page, 'edit-rating-btn').waitFor();
    assert.equal(requests[2].entries[0].note, '');
    assert.ok(requests[2].entries[0].expected_rating_sequence > 0);
    assert.notEqual(requests[2].batch_id, requests[0].batch_id);

    // Preserve changes typed while a normal request is still in flight.
    await field(page, 'edit-rating-btn').click();
    await rating(page, 'again').click();
    await field(page, 'note').fill('Original note');
    let release;
    holdReceipt = new Promise(resolve => { release = resolve; });
    const sent = page.waitForRequest(req => req.url().endsWith('/feedback'));
    await field(page, 'submit').click();
    await sent;
    await rating(page, 'uncertain').click();
    await field(page, 'note').fill('Additional note');
    release();
    holdReceipt = null;
    await field(page, 'saved-rating-text').filter({hasText: 'Current saved: Again'}).waitFor();
    assert.equal(await pressed(page, 'uncertain'), 'true');
    assert.equal(await field(page, 'note').inputValue(), 'Additional note');
    await field(page, 'submit').click();
    await field(page, 'edit-rating-btn').waitFor();
    assert.equal(requests[4].entries[0].note, 'Additional note');
    assert.equal(requests[4].entries[0].rating, 'uncertain');

    // These two tabs share localStorage. Each retains its own draft when reloaded.
    for (const tab of [page, sibling]) {
      await field(tab, 'next').click();
      await field(tab, 'flip').click();
    }
    await rating(page, 'familiar').click();
    const longNote = 'x'.repeat(299);
    await field(page, 'note').fill(longNote);
    await field(page, 'review-quick-chips').getByText('Example unclear').click();
    assert.equal(await field(page, 'note').inputValue(), longNote);
    await rating(sibling, 'again').click();
    await field(sibling, 'submit').click();
    await field(sibling, 'edit-rating-btn').waitFor();
    await page.reload();
    assert.equal(await pressed(page, 'familiar'), 'true');
    assert.match(await field(page, 'saved-rating-text').innerText(), /Saved rating: Again/);
    await field(page, 'cancel-edit-rating-btn').click();
    assert.equal(await field(page, 'note').inputValue(), longNote);
    await field(page, 'submit').click();
    await field(page, 'message').filter({hasText: 'Comment saved'}).waitFor();
    assert.equal(requests[5].entries[0].rating, null);
    assert.equal(requests[5].entries[0].note, longNote);

    await field(page, 'note').fill('Lost receipt');
    loseReceipt = true;
    await field(page, 'submit').click();
    await field(page, 'message').filter({hasText: 'unconfirmed'}).waitFor();
    await field(page, 'note').fill('Draft when clicking Retry');
    holdReceipt = new Promise(resolve => { release = resolve; });
    const replay = page.waitForRequest(req => req.url().endsWith('/feedback'));
    await field(page, 'submit').click();
    await replay;
    await field(page, 'note').fill('Typed during retry');
    release();
    holdReceipt = null;
    await field(page, 'message').filter({hasText: 'later edits'}).waitFor();
    assert.equal(requests.length, 8);
    assert.equal(await field(page, 'note').inputValue(), 'Typed during retry');

    await page.goto(url + '?day=' + yesterday + '&lang=en');
    await field(page, 'flip').click();
    assert.equal(await rating(page, 'again').isDisabled(), true);
    await field(page, 'note').fill('Comment on archived issue');
    await field(page, 'submit').click();
    await field(page, 'draft-count').filter({hasText: 'Comment saved'}).waitFor();
    assert.doesNotMatch(await field(page, 'draft-count').innerText(), /rating still open/i);
    assert.doesNotMatch(await field(page, 'message').innerText(), /can still rate/i);

    await page.goto(url + '?day=' + studyDay + '&lang=en');
    assert.equal(await field(page, 'submit-row').isHidden(), true);
    await field(page, 'study-comment').locator('summary').click();
    await field(page, 'study-note').fill('Question for this study card');
    loseReceipt = true;
    await field(page, 'study-submit').click();
    await field(page, 'study-message').filter({hasText: 'unconfirmed'}).waitFor();
    await field(page, 'study-note').fill('');
    await field(page, 'study-submit').click();
    await field(page, 'study-message').filter({hasText: 'Comment saved'}).waitFor();
    assert.deepEqual(requests.at(-1), requests.at(-2));
    console.log('Portal drafts, rating confirmations, comment limits, archive receipts and study-only retries passed.');
  } finally {
    try {
      if (browser) await browser.close();
    } finally {
      try { if (started) review(['today', '--stop']); }
      finally { fs.rmSync(temp, {recursive: true, force: true}); }
    }
  }
}
testPortalDrafts().catch(error => { console.error(error); process.exitCode = 1; });
