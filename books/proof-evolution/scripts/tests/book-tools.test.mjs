import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { APPENDIX_FILES, BOOK_ID, CHAPTER_IDS, extractBaseline, extractFootnotes, parseDocument, readBook, readFigure, renderDocument, resolveLink, validateBook } from '../book-lib.mjs';
import { buildHTML } from '../build-reader.mjs';

const testDir = path.dirname(fileURLToPath(import.meta.url));

function fixture(t) {
  const root = fs.mkdtempSync(path.join(testDir, 'fixture-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  fs.mkdirSync(path.join(root, 'book-src/_meta'), { recursive: true });
  fs.mkdirSync(path.join(root, 'web'));
  const config = { id: BOOK_ID, title: '證明的理由', subtitle: '測試閱讀器', footer: '測試', ui_lang: 'zh-TW', expected_chapters: 18, chapter_min_han: 4000, math_register: 'unicode', output: 'index.html', groups: [
    { title: '開始', files: ['../book-src/README.md'] },
    { title: '正文', files: CHAPTER_IDS.map(id => `../book-src/${id}-chapter.md`) },
    { title: '附錄', files: APPENDIX_FILES.map(file => `../book-src/${file}`) }
  ] };
  fs.writeFileSync(path.join(root, 'web/book.config.json'), JSON.stringify(config));
  fs.writeFileSync(path.join(root, 'book-src/README.md'), '# 開始閱讀\n\n[第一章](ch01-chapter.md)。\n');
  for (const file of APPENDIX_FILES) fs.writeFileSync(path.join(root, 'book-src', file), '# 附錄\n\n方法與理由。\n');
  for (const id of CHAPTER_IDS) fs.writeFileSync(path.join(root, `book-src/${id}-chapter.md`), `# ${id} 可檢查的理由\n\n## 一個論證\n\n${'理由可以公開檢查。'.repeat(600)}\n\n論點。[^${id}-a]再次查證。[^${id}-b]\n\n[^${id}-a]: [第一個來源](https://example.com/a)。\n[^${id}-b]: [第二個來源](https://example.com/b)。\n`);
  const baseline = '| ID | Value |\n| --- | --- |\n| TEST | 25 |\n';
  fs.writeFileSync(path.join(root, 'book-src/_meta/outline.md'), `# Outline\n\n${CHAPTER_IDS.map(id => `### ${id} — Chapter`).join('\n\n')}\n\n<!-- BEGIN BASELINE -->\n${baseline}<!-- END BASELINE -->\n`);
  fs.writeFileSync(path.join(root, 'book-src/_meta/running-examples.md'), baseline);
  fs.writeFileSync(path.join(root, 'book-src/_meta/maintenance.md'), `# Maintenance\n\n<!-- BEGIN BASELINE -->\n${baseline}<!-- END BASELINE -->\n`);
  fs.writeFileSync(path.join(root, 'book-src/_meta/chapter-manifest.json'), JSON.stringify(CHAPTER_IDS.map(id => ({ id, file: `${id}-chapter.md` }))));
  return { root, configPath: path.join(root, 'web/book.config.json') };
}

test('a valid complete manifest passes; deleting a chapter cannot produce a vacuous pass', t => {
  const f = fixture(t);
  const valid = validateBook(readBook(f.configPath), { checkRegistry: false });
  assert.equal(valid.pass, true, JSON.stringify(valid.errors));
  assert.equal(valid.actual_chapters, 18);
  fs.unlinkSync(path.join(f.root, 'book-src/ch07-chapter.md'));
  const missing = validateBook(readBook(f.configPath), { checkRegistry: false });
  assert.equal(missing.pass, false);
  assert.equal(missing.actual_chapters, 17);
  assert.match(missing.errors.join('\n'), /Exactly 18 chapter files/);
});

test('a duplicate or reordered chapter manifest is rejected even when all files exist', t => {
  const f = fixture(t);
  const config = JSON.parse(fs.readFileSync(f.configPath));
  config.groups[1].files[1] = config.groups[1].files[0];
  fs.writeFileSync(f.configPath, JSON.stringify(config));
  const report = validateBook(readBook(f.configPath), { checkRegistry: false });
  assert.equal(report.pass, false);
  assert.match(report.errors.join('\n'), /Duplicate manifest file/);
  assert.match(report.errors.join('\n'), /exactly once and in order/);
});

test('depth counts substantive prose without fenced code or footnote padding', () => {
  const doc = parseDocument('# 理由\n\n正文。[^source]\n\n```text\n' + '字'.repeat(5000) + '\n```\n\n[^source]: ' + '字'.repeat(5000), '/book/ch01-test.md');
  assert.equal(doc.hanCount, 4);
});

test('footnote definitions inside fenced examples are not extracted as citations', () => {
  const parsed = extractFootnotes('```md\n[^inside]: not a note\n```\n\n[^real]: first paragraph\n\n    second paragraph');
  assert.deepEqual([...parsed.definitions.keys()], ['real']);
  assert.match(parsed.body, /\[\^inside\]/);
  assert.equal(parsed.definitions.get('real').text, 'first paragraph\n\nsecond paragraph');
});

test('duplicate footnote definitions and missing citation targets fail explicitly', t => {
  const f = fixture(t);
  const file = path.join(f.root, 'book-src/ch01-chapter.md');
  fs.appendFileSync(file, '\n[^ch01-a]: duplicate\n\nMissing.[^missing]\n');
  const report = validateBook(readBook(f.configPath), { checkRegistry: false });
  assert.match(report.errors.join('\n'), /Duplicate footnote definition/);
  assert.match(report.errors.join('\n'), /Missing footnote definition \[\^missing\]/);
});

test('same citation keys in different chapters get separate anchors and every repeated reference gets a return link', () => {
  const first = parseDocument('# 第一章\n\n甲。[^source]乙。[^source]\n\n[^source]: [來源](https://example.com)。', '/book/ch01-first.md');
  const second = parseDocument('# 第二章\n\n丙。[^source]\n\n[^source]: [來源](https://example.com)。', '/book/ch02-second.md');
  const html = renderDocument(first, [first, second]) + renderDocument(second, [first, second]);
  for (const id of ['ch01--footnote-source', 'ch02--footnote-source', 'ch01--reference-source-1', 'ch01--reference-source-2']) assert.match(html, new RegExp(`id="${id}"`));
  assert.match(html, /href="#ch01--reference-source-2"/);
});

test('relative heading links resolve with duplicate-heading suffixes; code-looking links are not navigable links', () => {
  const first = parseDocument('# 第一章\n\n[下一章](ch02-second.md#重複-2)\n\n`[not a link](missing.md)`', '/book/ch01-first.md');
  const second = parseDocument('# 第二章\n\n## 重複\n\n甲。\n\n## 重複\n\n乙。', '/book/ch02-second.md');
  assert.equal(first.links.length, 1);
  assert.equal(resolveLink(first.links[0], first, [first, second]).href, '#ch02--重複-2');
  assert.match(resolveLink('ch02-second.md#不存在', first, [first, second]).error, /Missing heading anchor/);
});

test('unsafe URLs and raw executable HTML never silently become executable reader content', t => {
  const f = fixture(t);
  const file = path.join(f.root, 'book-src/ch01-chapter.md');
  fs.appendFileSync(file, '\n<script>alert(1)</script>\n\n[bad](javascript:alert(1))\n');
  const report = validateBook(readBook(f.configPath), { checkRegistry: false });
  assert.match(report.errors.join('\n'), /Raw HTML is unsupported/);
  assert.match(report.errors.join('\n'), /Unsafe or unsupported URL scheme/);
  const escaped = parseDocument('# 安全\n\n<script>alert(1)</script>', '/book/ch01-test.md');
  const html = renderDocument(escaped, [escaped]);
  assert.doesNotMatch(html, /<script>/);
  assert.match(html, /&lt;script&gt;/);
});

test('the authored Markdown subset preserves emphasis, nested lists, tables, code and safe URLs', () => {
  const doc = parseDocument('# 形式\n\n**重點**與*強調*和`n²`。[來源](https://example.com?q=a&b=2)\n\n- 一\n  - 二\n\n| 甲 | 乙 |\n| --- | --- |\n| 1 | 2 |\n\n```text\nx < 3\n```', '/book/ch01-test.md');
  const html = renderDocument(doc, [doc]);
  for (const expected of ['<strong>重點</strong>', '<em>強調</em>', '<code>n²</code>', '<table>', 'x &lt; 3', 'q=a&amp;b=2']) assert.ok(html.includes(expected), expected);
  assert.equal((html.match(/<ul>/g) || []).length, 2);
});

test('baseline checks preserve trailing bytes and reject a stale maintenance copy', t => {
  const f = fixture(t);
  assert.equal(extractBaseline('x\n<!-- BEGIN BASELINE -->\n25\n<!-- END BASELINE -->'), '25\n');
  fs.appendFileSync(path.join(f.root, 'book-src/_meta/running-examples.md'), '\n');
  const report = validateBook(readBook(f.configPath), { checkRegistry: false });
  assert.equal(report.pass, false);
  assert.match(report.errors.join('\n'), /running-examples.md must be byte-identical/);
});

test('identical source inputs generate byte-identical self-contained HTML', t => {
  const f = fixture(t);
  const book = readBook(f.configPath);
  const first = buildHTML(book);
  assert.equal(first, buildHTML(readBook(f.configPath)));
  assert.equal((first.match(/<article class="chapter"/g) || []).length, 23);
  assert.doesNotMatch(first, /<script[^>]+src=|<link[^>]+href=/i);
  assert.match(first, /default-src &#39;none&#39;/);
  assert.match(first, /lang="zh-TW"/);
});


const STATIC_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><title>Circle</title><circle cx="50" cy="50" r="40" fill="none" stroke="black"/></svg>';
function figureFixture(t) {
  const f = fixture(t);
  const dir = path.join(f.root, 'book-src/figures'); fs.mkdirSync(dir);
  fs.writeFileSync(path.join(dir, 'circle.svg'), STATIC_SVG);
  const file = path.join(f.root, 'book-src/ch01-chapter.md');
  fs.appendFileSync(file, '\n![A circle & its radius](figures/circle.svg)\n');
  return { ...f, dir, file };
}

test('static SVG is embedded with alt text, caption, dimensions and no separate resource', t => {
  const f = figureFixture(t); const book = readBook(f.configPath);
  assert.equal(validateBook(book, {checkRegistry:false}).pass, true);
  const html = buildHTML(book);
  assert.match(html, /<figure class="support-figure"><img src="data:image\/svg\+xml;base64,/);
  assert.match(html, /alt="A circle &amp; its radius" width="100" height="100"/);
  assert.match(html, /<figcaption>A circle &amp; its radius<\/figcaption>/);
  assert.doesNotMatch(html, /<p><figure/);
  assert.match(html, /img-src data:/);
});

test('SVG rejects executable nodes, event handlers, external references and malformed XML', t => {
  const f = figureFixture(t); const doc = readBook(f.configPath).documents[1];
  for (const bad of [STATIC_SVG.replace('<title>', '<script>'), STATIC_SVG.replace('cx="50"', 'onload="alert(1)"'), STATIC_SVG.replace('fill="none"', 'fill="url(https://example.org/x)"'), STATIC_SVG.replace('cx="50"', 'href="x"'), STATIC_SVG.replace('</svg>', ''), '<!DOCTYPE svg>' + STATIC_SVG]) {
    fs.writeFileSync(path.join(f.dir, 'circle.svg'), bad);
    assert.throws(() => readFigure('figures/circle.svg', doc));
  }
});

test('figure paths cannot escape the dedicated directory or fetch network data', t => {
  const f = figureFixture(t); const doc = readBook(f.configPath).documents[1];
  for (const bad of ['https://example.org/x.svg', 'data:image/svg+xml,x', '/tmp/x.svg', '../outside.svg', 'figures/%2e%2e/outside.svg', 'figures/circle.svg?x=1']) assert.throws(() => readFigure(bad, doc));
  fs.writeFileSync(path.join(f.root,'outside.svg'),STATIC_SVG);
  fs.symlinkSync(path.join(f.root,'outside.svg'),path.join(f.dir,'escape.svg'));
  assert.throws(() => readFigure('figures/escape.svg',doc), /symlink/);
});

test('changing a figure invalidates generated reader bytes without changing Markdown', t => {
  const f = figureFixture(t); const first = buildHTML(readBook(f.configPath));
  fs.writeFileSync(path.join(f.dir,'circle.svg'),STATIC_SVG.replace('r="40"','r="35"'));
  assert.notEqual(first,buildHTML(readBook(f.configPath)));
});
