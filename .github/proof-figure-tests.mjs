
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
