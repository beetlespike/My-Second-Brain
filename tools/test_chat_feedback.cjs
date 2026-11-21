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
    const studyPath = '待学概念/推理系统/Prefill-Decode Disaggregation.md';
    review(['session', '--fragment', '--discovery', studyPath, '--output', fragment]);
    const standalone = path.join(temp, 'standalone.html');
    review(['session', '--discovery', studyPath, '--output', standalone]);
    const html = fs.readFileSync(fragment, 'utf8');
    fs.writeFileSync(fragment, '<!doctype html><html lang="fr"><meta charset="utf-8"><title>Host</title>' + html, 'utf8');
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
    const hostURL = pathToFileURL(fragment).href + '?lang=en';
    await page.goto(hostURL);
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
    await field('study-comment').locator('summary').click();
    await field('study-note').fill('先保留这条待学留言。');
    await page.locator('[data-rating="uncertain"]').click();
    await field('sources').locator('summary').click();
    const sourcePath = await field('source-list').locator('.fc-note-path').first().innerText();
    assert.match(sourcePath, /\.md$/);
    await page.evaluate(() => {
      Object.defineProperty(navigator, 'clipboard', {configurable: true, value: {
        writeText: async path => {
          if (window.refuseCopy) throw new Error('Clipboard unavailable');
          window.copied = path;
        },
      }});
    });
    await field('discovery-source').getByRole('button', {name: 'Copy note path'}).click();
    assert.equal(await page.evaluate(() => window.copied), studyPath);
    await page.evaluate(() => { window.refuseCopy = true; });
    await field('source-list').getByRole('button', {name: 'Copy note path'}).first().click();
    assert.equal(await page.evaluate(() => getSelection().toString()), sourcePath);
    await page.getByRole('button', {name: '中文', exact: true}).click();
    assert.equal(await field('flip').textContent(), '翻回正面');
    assert.equal(await field('note').inputValue(), '第一张补一个算例。');
    assert.equal(await field('study-note').inputValue(), '先保留这条待学留言。');
    assert.equal(await page.locator('[data-rating="uncertain"]').getAttribute('aria-pressed'), 'true');
    assert(await field('sources').evaluate(node => node.open));
    assert(await field('note-details').evaluate(node => node.open));
    assert.equal(await field('discovery-source').getByRole('status').textContent(), '已复制路径。');
    assert.equal(await page.title(), 'Host');
    assert.equal(await page.locator('html').getAttribute('lang'), 'fr');
    assert.equal(page.url(), hostURL);
    await field('study-note').fill('');
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
    const batchId = await page.evaluate(() => window.openai.widgetState.privateContent.submission.id);
    await page.getByRole('button', {name: 'English', exact: true}).click();
    await field('message').filter({hasText: 'retry'}).waitFor();
    assert.equal(await page.evaluate(() => window.openai.widgetState.privateContent.submission.id), batchId);
    await page.reload();
    await field('next').click();
    await write('第四张的问题。');
    await submit(2);
    assert.deepEqual(sent.slice(2).map(item => item.notes), [['第三张的问题。'], ['第三张的问题。'], ['第四张的问题。']]);
    assert.equal(sent[2].id, sent[3].id);
    assert.equal(sent[3].receipt.duplicates, 1);
    assert.equal(review(['daily']).pending_count, 4);

    const context = await browser.newContext({locale: 'zh-TW'});
    const local = await context.newPage();
    const url = pathToFileURL(standalone).href;
    await local.goto(url);
    assert.equal(await local.locator('html').getAttribute('lang'), 'zh-CN');
    assert.match(await local.title(), /复习/);
    await local.getByRole('button', {name: 'English', exact: true}).click();
    assert.match(await local.title(), /Review/);
    await local.goto(url);
    assert.equal(await local.locator('html').getAttribute('lang'), 'en');
    await local.goto(url + '?lang=zh');
    assert.equal(await local.locator('html').getAttribute('lang'), 'zh-CN');
    await local.getByRole('button', {name: '翻到背面'}).click();
    await local.getByText('补充反馈或指出问题', {exact: true}).click();
    await local.locator('[data-role="note"]').fill('Keep this standalone note.');
    const downloading = local.waitForEvent('download');
    await local.getByRole('button', {name: '导出反馈文件'}).click();
    const download = await downloading;
    const payload = JSON.parse(fs.readFileSync(await download.path(), 'utf8'));
    assert.equal(payload.entries[0].note, 'Keep this standalone note.');
    await local.getByRole('button', {name: 'English', exact: true}).click();
    const fallback = await local.locator('[data-role="fallback-text"]').inputValue();
    assert.match(fallback, /^Save this feedback/);
    assert.deepEqual(JSON.parse(fallback.slice(fallback.indexOf('{'))), payload);
    assert.equal(await local.locator('[data-role="note"]').inputValue(), payload.entries[0].note);
    await context.close();
    console.log('Chat retries, language switching, source paths and standalone export passed.');
  } finally {
    if (browser) await browser.close();
    fs.rmSync(temp, {recursive: true, force: true});
  }
}
testChatFeedback().catch(error => { console.error(error); process.exitCode = 1; });
