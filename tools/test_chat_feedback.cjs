// Run with Node, Playwright and its Chromium browser installed.
const assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const {chromium} = require('playwright');

async function testChatFeedback() {
  const root = path.resolve(__dirname, '..');
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'msb-chat-feedback-'));
  const vault = path.join(temp, 'vault');
  const python = process.env.PYTHON || (process.platform === 'win32' ? 'py' : 'python3');
  const flags = process.platform === 'win32' && !process.env.PYTHON ? ['-3', '-B'] : ['-B'];
  const run = (cwd, args, data) => JSON.parse(execFileSync(python, [...flags, ...args], {
    cwd, encoding: 'utf8', input: data === undefined ? undefined : JSON.stringify(data),
    env: {...process.env, PYTHONIOENCODING: 'utf-8'},
  }));
  let browser;
  try {
    run(root, ['tools/workflow.py', 'init', vault]);
    const review = (args, data) => run(vault, ['.flashcards/review.py', ...args], data);
    const fragment = path.join(temp, 'cards.html');
    review(['session', '--fragment', '--output', fragment]);
    const html = fs.readFileSync(fragment, 'utf8');
    fs.writeFileSync(fragment, '<!doctype html><meta charset="utf-8">' + html, 'utf8');
    browser = await chromium.launch({executablePath: process.env.CHROMIUM_PATH});
    const page = await browser.newPage();
    const sent = [];
    await page.addInitScript(() => {
      window.testMessages = [];
      window.openai = {
        get widgetState() { return JSON.parse(sessionStorage.getItem('widget') || 'null'); },
        setWidgetState: value => sessionStorage.setItem('widget', JSON.stringify(value)),
        sendFollowUpMessage: async ({prompt}) => {
          window.testMessages.push(prompt);
          if (window.loseReceipt) {
            window.loseReceipt = false;
            throw new Error('The chat accepted the message before the connection closed.');
          }
        },
      };
    });
    await page.goto(pathToFileURL(fragment).href);
    const field = name => page.locator('[data-role="' + name + '"]');
    const write = async note => {
      await field('flip').click();
      if (!await field('note').isVisible()) await field('note-details').locator('summary').click();
      await field('note').fill(note);
    };
    const submit = async (expected = 1) => {
      await field('submit').click();
      await page.waitForFunction(count => window.testMessages.length >= count, expected, {timeout: 5000});
      const messages = await page.evaluate(() => window.testMessages.splice(0));
      for (const prompt of messages) {
        const batch = JSON.parse(prompt.slice(prompt.indexOf('{')));
        const receipt = review(['feedback', '--input', '-'], batch);
        sent.push({id: batch.batch_id, notes: batch.entries.map(entry => entry.note), receipt});
      }
    };

    await write('第一张补一个算例。');
    await submit();
    await field('next').click();
    await write('第二张需要说明条件。');
    await submit();
    assert.deepEqual(sent.map(item => item.notes), [['第一张补一个算例。'], ['第二张需要说明条件。']]);
    assert.equal(review(['daily']).pending_count, 2);

    await field('next').click();
    await write('第三张的问题。');
    await page.evaluate(() => { window.loseReceipt = true; });
    await submit();
    await field('message').filter({hasText: '重试'}).waitFor();
    await page.reload();
    await field('next').click();
    await write('第四张的问题。');
    await submit(2);
    assert.deepEqual(sent.slice(2).map(item => item.notes), [['第三张的问题。'], ['第三张的问题。'], ['第四张的问题。']]);
    assert.equal(sent[2].id, sent[3].id);
    assert.equal(sent[3].receipt.duplicates, 1);
    assert.equal(review(['daily']).pending_count, 4);
    console.log('Each comment was saved once, including the submission retried after reopening.');
  } finally {
    if (browser) await browser.close();
    fs.rmSync(temp, {recursive: true, force: true});
  }
}
testChatFeedback().catch(error => { console.error(error); process.exitCode = 1; });
