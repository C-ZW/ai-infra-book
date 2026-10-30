#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';
import assert from 'node:assert/strict';

const scriptsDir = path.dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
if (args.includes('--help')) {
  console.log('Usage: node scripts/browser-smoke.mjs [--json] [--screenshots directory]\nRequires an existing Playwright installation and Chromium browser. Uses a local file in offline browser contexts; no package download or web access. An optional CODEX_PRIMARY_RUNTIME_NODE_MODULES can locate Playwright.');
  process.exit(0);
}
const require = createRequire(import.meta.url);
let playwright;
try { playwright = require('playwright'); }
catch {
  try {
    if (!process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES) throw new Error('No optional runtime module path.');
    playwright = require(path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES, 'playwright'));
  } catch {
    console.error('Optional browser check unavailable: install Playwright and Chromium in your normal development environment, or provide the existing runtime module path. No browser verification has run.');
    process.exit(2);
  }
}
const screenshotsIndex = args.indexOf('--screenshots');
const screenshotsDir = screenshotsIndex >= 0 ? path.resolve(args[screenshotsIndex + 1]) : null;
if (screenshotsDir) fs.mkdirSync(screenshotsDir, { recursive: true });
const source = path.resolve(scriptsDir, '../web/index.html');
const url = pathToFileURL(source).href;
const report = { pass: false, status: 'not_run', browser: 'Chromium', mode: 'file URL; network offline', checks: [], screenshots: [], errors: [], remote_requests: [] };
let browser;

async function record(name, operation) {
  await operation();
  report.checks.push({ name, pass: true });
}

async function pageFor(options = {}) {
  const context = await browser.newContext({ viewport: { width: 1360, height: 1000 }, deviceScaleFactor: 2, offline: true, ...options });
  const page = await context.newPage();
  page.setDefaultTimeout(8000);
  page.on('pageerror', error => report.errors.push(error.message));
  page.on('console', message => { if (message.type() === 'error') report.errors.push(message.text()); });
  page.on('request', request => { if (/^https?:/.test(request.url())) report.remote_requests.push(request.url()); });
  return { context, page };
}

async function noOverflow(page) {
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1), true, 'Unexpected horizontal page overflow.');
}

async function screenshot(page, name) {
  if (!screenshotsDir) return;
  const file = path.join(screenshotsDir, name);
  await page.screenshot({ path: file, fullPage: false });
  report.screenshots.push(file);
}

try {
  if (!fs.existsSync(source)) throw new Error('Build the reader before running its browser checks.');
  const executablePath = process.env.PROOF_BOOK_CHROMIUM || playwright.chromium.executablePath();
  if (!fs.existsSync(executablePath)) throw new Error('Chromium executable is unavailable. Browser interaction checks and screenshots were not run.');
  browser = await playwright.chromium.launch({ executablePath, headless: true, args: ['--force-device-scale-factor=2'] });
  report.status = 'running';
  report.browser_version = browser.version();
  const { page, context } = await pageFor();
  await page.goto(url);
  await record('desktop_initial_render', async () => {
    await page.waitForFunction(() => document.querySelectorAll('.chapter:not([hidden])').length === 1);
    assert.equal(await page.locator('.chapter').count(), 23);
    assert.equal(await page.locator('.nav-link[aria-current="page"]').count(), 1);
    await noOverflow(page);
    await screenshot(page, 'desktop-introduction.png');
  });
  await record('chapter_navigation_and_footnote_round_trip', async () => {
    await page.locator('.nav-link[data-document="ch03"]').click();
    await page.waitForFunction(() => !document.getElementById('ch03').hidden);
    const first = page.locator('#ch03 .footnote-ref a').first();
    const target = await first.getAttribute('href');
    await first.click();
    await page.waitForFunction(expected => decodeURIComponent(location.hash) === expected, target);
    assert.equal(await page.locator('[role="doc-endnote"]:target').count(), 1);
    await page.locator('[role="doc-endnote"]:target .footnote-back').first().click();
    await page.waitForFunction(() => location.hash.includes('--reference-'));
    assert.equal(await page.locator('.footnote-ref:target').count(), 1);
  });
  await record('full_text_search_and_keyboard', async () => {
    await page.keyboard.press('/');
    assert.equal(await page.locator('#book-search').evaluate(element => element === document.activeElement), true);
    await page.locator('#book-search').fill('反證');
    assert.ok((await page.locator('.nav-link:visible').count()) > 0);
    assert.match(await page.locator('#search-status').textContent(), /找到/);
    await page.keyboard.press('Escape');
    assert.equal(await page.locator('#book-search').inputValue(), '');
    assert.equal(await page.locator('.nav-link:visible').count(), 23);
  });
  await record('reading_progress_persists_in_unique_namespace', async () => {
    await page.locator('.nav-link[data-document="ch12"]').click();
    await page.waitForFunction(() => !document.getElementById('ch12').hidden);
    await page.evaluate(() => window.scrollTo(0, (document.documentElement.scrollHeight - innerHeight) * 0.45));
    await page.waitForFunction(() => {
      const saved = JSON.parse(localStorage.getItem('proof-evolution-2026:reading-progress'));
      return saved?.chapter === 'ch12' && saved.ratio > 0.4 && saved.ratio < 0.5;
    });
    await page.reload();
    await page.waitForFunction(() => {
      const ratio = scrollY / (document.documentElement.scrollHeight - innerHeight);
      return ratio > 0.4 && ratio < 0.5;
    });
    await noOverflow(page);
  });
  await record('table_render_and_print_visibility', async () => {
    const table = page.locator('#ch12 .table-scroll').first();
    if (await table.count()) { await table.scrollIntoViewIfNeeded(); await screenshot(page, 'desktop-worked-table.png'); }
    await page.emulateMedia({ media: 'print' });
    assert.equal(await page.locator('.chapter:visible').count(), 23);
    assert.equal(await page.locator('.sidebar:visible').count(), 0);
    await page.emulateMedia({ media: 'screen' });
  });
  await context.close();
  const mobile = await pageFor({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true });
  await mobile.page.goto(url + '#ch06');
  await record('mobile_navigation_search_and_layout', async () => {
    await mobile.page.waitForFunction(() => !document.getElementById('ch06').hidden);
    assert.equal(await mobile.page.locator('#book-navigation').isVisible(), false);
    await mobile.page.locator('#menu-toggle').click();
    assert.equal(await mobile.page.locator('#menu-toggle').getAttribute('aria-expanded'), 'true');
    assert.equal(await mobile.page.locator('#book-search').evaluate(element => element === document.activeElement), true);
    await mobile.page.locator('.nav-link[data-document="ch06"]').click();
    await mobile.page.waitForFunction(() => document.getElementById('menu-toggle').getAttribute('aria-expanded') === 'false');
    await noOverflow(mobile.page);
    await screenshot(mobile.page, 'mobile-limit-chapter.png');
  });
  await mobile.context.close();
  const restricted = await pageFor();
  await restricted.page.addInitScript(() => Object.defineProperty(window, 'localStorage', { configurable: true, get() { throw new Error('Storage intentionally unavailable in this test.'); } }));
  await restricted.page.goto(url);
  await record('blocked_storage_does_not_break_reading', async () => {
    await restricted.page.locator('.nav-link[data-document="ch01"]').click();
    await restricted.page.waitForFunction(() => !document.getElementById('ch01').hidden);
    assert.equal(await restricted.page.locator('.chapter:not([hidden])').count(), 1);
  });
  await restricted.context.close();
  const noScript = await pageFor({ javaScriptEnabled: false, viewport: { width: 390, height: 844 } });
  await noScript.page.goto(url);
  await record('no_javascript_reading_fallback', async () => {
    assert.equal(await noScript.page.locator('.chapter:visible').count(), 23);
    assert.equal(await noScript.page.locator('#book-navigation').isVisible(), true);
    await noOverflow(noScript.page);
  });
  await noScript.context.close();
  assert.equal(report.remote_requests.length, 0, 'Reader attempted a network resource request.');
  assert.equal(report.errors.length, 0, 'Browser emitted runtime or console errors.');
  report.pass = true;
  report.status = 'passed';
} catch (error) { report.errors.push(error.stack || error.message); }
finally { if (browser) await browser.close(); }
if (!report.pass && report.status === 'running') report.status = 'failed';
report.limitations = ['A focused Chromium regression check, not an accessibility certification or a cross-browser guarantee.', 'External source pages are not fetched or validated by this offline test.'];
if (args.includes('--json')) console.log(JSON.stringify(report, null, 2));
else {
  console.log(`${report.pass ? 'PASS' : 'FAIL'}: browser smoke checks (${report.checks.length} completed).`);
  for (const check of report.checks) console.log(`PASS: ${check.name}`);
  for (const error of report.errors) console.error(error);
  for (const file of report.screenshots) console.log(`Screenshot: ${file}`);
}
process.exitCode = report.pass ? 0 : 1;
