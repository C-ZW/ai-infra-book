from pathlib import Path
R=Path('books/proof-evolution')
def patch(file,old,new):
 p=R/file;t=p.read_text();assert t.count(old)==1,(file,old[:80],t.count(old));p.write_text(t.replace(old,new))
helper=Path('.github/proof-svg-helper.mjs').read_text()
patch('scripts/book-lib.mjs','export function renderDocument(document, documents) {',helper+'\nexport function renderDocument(document, documents) {')
patch('scripts/book-lib.mjs',"    image() { throw new Error('Images are not supported by this text-only reader.'); },",r'''    image(token) {
      const figure = readFigure(token.href, document);
      return `<img src="${figure.src}" alt="${escapeHTML(token.text)}" width="${figure.width}" height="${figure.height}">`;
    },
    paragraph(token) {
      const meaningful = (token.tokens || []).filter(t => t.type !== 'space' && !(t.type === 'text' && !t.raw.trim()));
      if (meaningful.length === 1 && meaningful[0].type === 'image') {
        return `<figure class="support-figure">${this.parser.parseInline(meaningful)}<figcaption>${escapeHTML(meaningful[0].text)}</figcaption></figure>\n`;
      }
      return Renderer.prototype.paragraph.call(this, token);
    },''')
patch('scripts/book-lib.mjs',"    if (document.images.length) errors.push(`${label}: Images are unsupported in this text-only offline reader.`);",r'''    for (const href of document.images) {
      try { readFigure(href, document); } catch (error) { errors.push(`${label}: ${error.message}`); }
    }''')
patch('scripts/build-reader.mjs','escapeHTML, hash, readBook, renderDocument, validateBook','escapeHTML, hash, readBook, readFigure, renderDocument, validateBook')
patch('scripts/build-reader.mjs',"  const sourceDigest = hash(JSON.stringify({ config, sources:","  const figures = documents.flatMap(document => document.images.map(href => [href, readFigure(href, document).sha256]));\n  const sourceDigest = hash(JSON.stringify({ config, figures, sources:")
patch('scripts/build-reader.mjs',"; base-uri 'none'; form-action 'none'`", "; img-src data:; base-uri 'none'; form-action 'none'`")
p=R/'scripts/reader.css';p.write_text(p.read_text()+'''\n/* A support diagram stays with its prose and never becomes a page layout. */
.support-figure { margin: 1.6rem 0; break-inside: avoid; }
.support-figure img { display: block; width: 100%; max-width: 680px; height: auto; margin: 0 auto; background: white; }
.support-figure figcaption { max-width: 42rem; margin: .65rem auto 0; font-size: .9em; line-height: 1.65; }
''')
patch('scripts/verify.mjs',"const commands = [", "const commands = [\n  { name: 'generated_support_figures', command: python, args: [path.join(scriptsDir, 'build-figures.py'), '--check'] },")
patch('scripts/check-reader.py','from collections import Counter','from collections import Counter\nimport xml.etree.ElementTree as ET')
patch('scripts/check-reader.py','        self.resources = []','        self.resources = []\n        self.figures = []')
patch('scripts/check-reader.py','                    self.resources.append({"tag": tag, "attribute": key, "value": attributes[key]})','''                    if tag == "img" and key == "src" and attributes[key].startswith("data:image/svg+xml;base64,"):
                        self.figures.append(attributes)
                    else:
                        self.resources.append({"tag": tag, "attribute": key, "value": attributes[key]})''')
patch('scripts/check-reader.py','    if parsed.resources:\n', '''    for figure in parsed.figures:
        try:
            payload = base64.b64decode(figure["src"].split(",", 1)[1], validate=True)
            root = ET.fromstring(payload)
            if root.tag != "{http://www.w3.org/2000/svg}svg" or not figure.get("alt"):
                raise ValueError("Figure lacks SVG root or alt text.")
            for element in root.iter():
                if element.tag.split("}")[-1] not in {"svg", "g", "title", "desc", "line", "polyline", "polygon", "circle", "path", "rect", "text"}:
                    raise ValueError("Unsupported SVG element.")
                if any(key.lower().startswith("on") or key.split("}")[-1] in {"href", "style"} or "url(" in value.lower() for key, value in element.attrib.items()):
                    raise ValueError("Active SVG attribute.")
        except (ValueError, ET.ParseError) as error:
            errors.append(f"Invalid embedded SVG: {error}")
    if parsed.figures and "img-src data:" not in parsed.csp:
        errors.append("CSP must allow embedded data images.")
    if parsed.resources:
''')
patch('scripts/check-reader.py','"separate_resources": len(parsed.resources), "errors": errors,','"separate_resources": len(parsed.resources), "embedded_figures": len(parsed.figures), "errors": errors,')
p=R/'scripts/tests/book-tools.test.mjs';t=p.read_text().replace('parseDocument, readBook, renderDocument','parseDocument, readBook, readFigure, renderDocument');p.write_text(t+'\n'+Path('.github/proof-figure-tests.mjs').read_text())
patch('book-src/_meta/style-guide.md','Real figures, if necessary, must be generated reproducibly and include descriptive captions.','Support figures must clarify a specific spatial or procedural relationship, without replacing the continuous prose. The five static SVG figures are generated by `scripts/build-figures.py`; use standalone Markdown image paragraphs with descriptive captions. Only passive SVG in `book-src/figures/` is accepted and embedded in the offline reader. No decorative figures or font files are bundled.')
patch('book-src/_meta/style-guide.md',"Writers atomically replace their assigned files and never edit another writer's chapter or `_meta/state.json`. The root editor owns consistency, appendix compilation, evidence reconciliation, and honest gate statuses.","Use atomic replacement for source files. Keep revision decisions and actual checks in the single `verification-report.md`; do not recreate per-agent reports or state snapshots. The editor owns consistency, appendix compilation, evidence reconciliation, and honest gate statuses.")
p=R/'book-src/_meta/outline.md';t=p.read_text();t=t.replace('Briefly distinguish legal standards','Distinguish institutional decisions under finite resources from mathematical entailment; avoid a separate legal-standards digression. Do not conflate');p.write_text(t)
p=R/'README.md';t=p.read_text().replace('python3 scripts/check-math.py\n','python3 scripts/build-figures.py\npython3 scripts/check-math.py\n').replace('第一個指令重算','第二個指令重算');t=t.replace('歷史查核、這次零上下文審閱、未解問題與實際測試範圍','本輪已針對審稿修訂正文與樣章，加入五張必要的支援圖；樣章仍是獨立替代稿，不代表全書敘事已重寫。歷史查核、零上下文審閱、逐項處置與實際測試範圍');p.write_text(t)
p=R/'editorial/README.md';t=p.read_text();start=t.index('The new cold review');t=t[:start]+'''The 2026-10-07 revision clarifies the k-th layer, includes the exact multiplication by 30 in the tablet example, and adds the shared square-growth and circle-construction figures. The title mapping above remains explicit. The sample is still separate; historical sources retain their stated access limits. Actual review coverage and checks are recorded only in [the consolidated report](../book-src/_meta/verification-report.md).\n''';p.write_text(t)
p=R/'scripts/README.md';t=p.read_text().replace('node scripts/validate.mjs\n','python3 scripts/build-figures.py\nnode scripts/validate.mjs\n');t=t.replace('原始 HTML、圖片與需要額外渲染器的 Mermaid／LaTeX 區塊會被拒絕。這些限制對應本書實際使用的文稿格式。','原始 HTML 與需要額外渲染器的 Mermaid／LaTeX 區塊會被拒絕。獨立圖片段落可引用 `book-src/figures/` 裡的靜態 SVG；其檔案須通過受限標籤與屬性檢查，不允許事件、腳本、外部資源或逃出圖目錄的路徑。圖片與圖說會內嵌於閱讀器，圖片 bytes 也納入重建一致性檢查。五張支援圖由 `build-figures.py` 生成，`--check` 可核對產物。圖例不含字型檔，使用閱讀裝置提供的中文字型。');t=t.replace('依序執行工具的針對性回歸測試','核對五張生成圖，再依序執行工具的針對性回歸測試');p.write_text(t)
print('Applied scoped reader and documentation changes.')
