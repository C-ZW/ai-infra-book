import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { Marked, Renderer } from './vendor/marked-17.0.5.mjs';

export const BOOK_ID = 'proof-evolution-2026';
export const CHAPTER_IDS = Array.from({ length: 18 }, (_, i) => `ch${String(i + 1).padStart(2, '0')}`);
export const APPENDIX_FILES = ['appendix-a-methods.md', 'appendix-b-timeline.md', 'appendix-c-worked-examples.md', 'appendix-d-sources.md'];
export const MIN_HAN = 4000;
export const BASE_START = '<!-- BEGIN BASELINE -->';
export const BASE_END = '<!-- END BASELINE -->';

export function escapeHTML(value) {
  return String(value).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
}

export function slug(value) {
  return String(value).normalize('NFKC').toLowerCase().replace(/[^\p{L}\p{N}_\s-]/gu, '').trim().replace(/\s+/g, '-').replace(/-+/g, '-') || 'section';
}

export function hash(value) {
  return crypto.createHash('sha256').update(value).digest('hex');
}

export function sourceID(file) {
  const basename = path.basename(file, '.md');
  return /^ch\d{2}(?:-|$)/.test(basename) ? basename.slice(0, 4) : slug(basename);
}

export function extractFootnotes(markdown) {
  const lines = markdown.replace(/\r\n?/g, '\n').split('\n');
  const definitions = new Map();
  const errors = [];
  const body = [];
  let fence = null;
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const fenceMatch = line.match(/^ {0,3}(`{3,}|~{3,})/);
    if (fenceMatch) {
      if (!fence) fence = { char: fenceMatch[1][0], length: fenceMatch[1].length };
      else if (fenceMatch[1][0] === fence.char && fenceMatch[1].length >= fence.length && /^ {0,3}(`{3,}|~{3,})\s*$/.test(line)) fence = null;
      body.push(line);
      continue;
    }
    if (fence) { body.push(line); continue; }
    const match = line.match(/^ {0,3}\[\^([A-Za-z0-9][A-Za-z0-9_.:-]*)\]:\s?(.*)$/);
    if (!match) { body.push(line); continue; }
    const id = match[1];
    const content = [match[2]];
    const definitionLine = i + 1;
    body.push('');
    while (i + 1 < lines.length) {
      const next = lines[i + 1];
      if (/^( {4}|\t)/.test(next)) {
        content.push(next.replace(/^( {4}|\t)/, ''));
        body.push('');
        i++;
      } else if (next.trim() === '' && /^( {4}|\t)/.test(lines[i + 2] || '')) {
        content.push(''); body.push(''); i++;
      } else break;
    }
    if (definitions.has(id)) errors.push(`Duplicate footnote definition [^${id}] at line ${definitionLine}.`);
    else definitions.set(id, { id, text: content.join('\n'), line: definitionLine });
  }
  return { body: body.join('\n'), definitions, errors };
}

function footnoteExtension(renderer) {
  return {
    name: 'footnoteRef', level: 'inline',
    start(src) { return src.indexOf('[^'); },
    tokenizer(src) {
      const match = /^\[\^([A-Za-z0-9][A-Za-z0-9_.:-]*)\]/.exec(src);
      if (match) return { type: 'footnoteRef', raw: match[0], id: match[1] };
    },
    renderer: renderer || (token => escapeHTML(token.raw))
  };
}

export function tokenParser(footnoteRenderer) {
  return new Marked({ gfm: true, breaks: false, pedantic: false, extensions: [footnoteExtension(footnoteRenderer)] });
}

function inlineText(tokens) {
  return (tokens || []).map(token => token.type === 'footnoteRef' ? '' : token.tokens ? inlineText(token.tokens) : token.text || token.raw || '').join('');
}

function proseText(tokens) {
  const pieces = [];
  const parser = tokenParser();
  parser.walkTokens(tokens, token => {
    if (['text', 'escape'].includes(token.type) && !token.tokens) pieces.push(token.text || '');
  });
  return pieces.join(' ');
}

export function parseDocument(markdown, file, group = '') {
  const extracted = extractFootnotes(markdown);
  const parser = tokenParser();
  const tokens = parser.lexer(extracted.body);
  const document = {
    file: path.resolve(file), id: sourceID(file), group, markdown,
    body: extracted.body, tokens, definitions: extracted.definitions,
    errors: [...extracted.errors], headings: [], links: [], references: [],
    rawHTML: [], images: [], unsupported: [], searchText: proseText(tokens)
  };
  const seenSlugs = new Map();
  const scan = (token, inFootnote = false) => {
    if (token.type === 'heading') {
      if (inFootnote) document.unsupported.push('Headings inside footnote definitions are unsupported.');
      const text = inlineText(token.tokens);
      const base = slug(text);
      const count = (seenSlugs.get(base) || 0) + 1;
      seenSlugs.set(base, count);
      document.headings.push({ depth: token.depth, text, slug: count === 1 ? base : `${base}-${count}` });
    }
    if (token.type === 'link') document.links.push(token.href);
    if (token.type === 'footnoteRef') {
      if (inFootnote) document.unsupported.push('Nested footnote references are unsupported.');
      else document.references.push(token.id);
    }
    if (token.type === 'html') document.rawHTML.push(token.raw);
    if (token.type === 'image') document.images.push(token.href);
    if (token.type === 'text' && !token.tokens && /\[\^/.test(token.raw)) document.unsupported.push('Malformed or unsupported footnote marker in prose.');
    if (token.type === 'code' && /^(mermaid|math|latex)$/i.test(token.lang || '')) document.unsupported.push(`Unsupported fenced language: ${token.lang}.`);
  };
  parser.walkTokens(tokens, token => scan(token));
  for (const definition of document.definitions.values()) {
    definition.tokens = parser.lexer(definition.text);
    parser.walkTokens(definition.tokens, token => scan(token, true));
  }
  document.title = document.headings.find(heading => heading.depth === 1)?.text || path.basename(file);
  document.hanCount = (document.searchText.match(/\p{Script=Han}/gu) || []).length;
  document.anchors = new Set(document.headings.map(heading => heading.slug));
  return document;
}

export function resolveLink(href, current, documents) {
  if (/^(?:https?:|mailto:)/i.test(href)) {
    try { const parsed = new URL(href); if (!['https:', 'http:', 'mailto:'].includes(parsed.protocol)) throw new Error(); }
    catch { return { error: `Malformed external URL: ${href}` }; }
    return { href, external: true };
  }
  if (/^[a-z][a-z0-9+.-]*:/i.test(href) || href.startsWith('//')) return { error: `Unsafe or unsupported URL scheme: ${href}` };
  const [rawFile, ...fragmentParts] = href.split('#');
  let relativeFile, fragment;
  try { relativeFile = decodeURIComponent(rawFile); fragment = decodeURIComponent(fragmentParts.join('#')); }
  catch { return { error: `Invalid URL encoding: ${href}` }; }
  if (relativeFile.includes('?') || path.isAbsolute(relativeFile)) return { error: `Unsupported local link: ${href}` };
  const destination = relativeFile ? path.resolve(path.dirname(current.file), relativeFile) : current.file;
  const target = documents.find(document => document.file === destination);
  if (!target) return { error: `Local link target is not in the reader manifest: ${href}` };
  if (fragment && !target.anchors.has(fragment)) return { error: `Missing heading anchor in ${path.basename(target.file)}: #${fragment}` };
  return { href: `#${target.id}${fragment ? `--${fragment}` : ''}`, external: false };
}


// Restrict figures to local, passive SVG. This deliberately small grammar is
// sufficient for our reproducible diagrams; it is not a general SVG sanitizer.
export function readFigure(href, document) {
  if (/^[a-z][a-z0-9+.-]*:/i.test(href) || href.startsWith('//') || /[?#]/.test(href)) throw new Error('Figure must be a local SVG path.');
  let decoded;
  try { decoded = decodeURIComponent(href); } catch { throw new Error('Invalid figure path encoding.'); }
  if (path.isAbsolute(decoded) || decoded.includes('\\')) throw new Error('Figure path must be relative.');
  const dir = path.dirname(document.file);
  const sourceRoot = path.basename(dir) === 'editorial' ? path.resolve(dir, '../book-src') : dir;
  const figureRoot = path.join(sourceRoot, 'figures');
  const file = path.resolve(dir, decoded);
  if (!file.startsWith(figureRoot + path.sep) || path.extname(file) !== '.svg') throw new Error('Figure must stay inside book-src/figures and use .svg.');
  if (!fs.existsSync(file) || !fs.statSync(file).isFile()) throw new Error(`Missing SVG figure: ${href}`);
  const realRoot = fs.realpathSync(figureRoot);
  if (realRoot !== figureRoot || !fs.realpathSync(file).startsWith(realRoot + path.sep)) throw new Error('Figure symlink escapes its source directory.');
  const bytes = fs.readFileSync(file);
  if (bytes.length > 100000) throw new Error('SVG figure exceeds the static size limit.');
  const xml = bytes.toString('utf8');
  if (/<!|<\?|url\s*\(/i.test(xml) || /&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9a-f]+;)/i.test(xml)) throw new Error('Active or unsupported SVG content.');
  const tags = new Set(['svg', 'title', 'desc', 'g', 'rect', 'line', 'polyline', 'polygon', 'circle', 'path', 'text']);
  const attrs = new Set(['xmlns', 'viewBox', 'role', 'aria-labelledby', 'id', 'x', 'y', 'x1', 'x2', 'y1', 'y2', 'cx', 'cy', 'r', 'width', 'height', 'd', 'points', 'fill', 'fill-opacity', 'stroke', 'stroke-width', 'stroke-opacity', 'stroke-dasharray', 'font-family', 'font-size', 'font-weight', 'text-anchor']);
  const stack = []; let cursor = 0; let roots = 0; let viewBox;
  for (const token of xml.matchAll(/<([^<>]+)>/g)) {
    const between = xml.slice(cursor, token.index);
    if (/[<>]/.test(between) || (!stack.length && between.trim())) throw new Error('Malformed SVG text.');
    cursor = token.index + token[0].length;
    const close = token[1].match(/^\/([A-Za-z]+)\s*$/);
    if (close) { if (stack.pop() !== close[1]) throw new Error('Unbalanced SVG elements.'); continue; }
    const open = token[1].match(/^([A-Za-z]+)([\s\S]*?)(\/?)$/);
    if (!open || !tags.has(open[1])) throw new Error('Unsupported SVG element.');
    const [, tag, rest, selfClose] = open;
    if (!stack.length) { if (tag !== 'svg' || ++roots !== 1) throw new Error('SVG must have one root.'); }
    else if (tag === 'svg') throw new Error('Nested SVG roots are unsupported.');
    const values = {}; let end = 0;
    for (const match of rest.matchAll(/\s+([A-Za-z][A-Za-z0-9-]*)\s*=\s*("[^"]*"|'[^']*')/g)) {
      if (rest.slice(end, match.index).trim()) throw new Error('Malformed SVG attributes.');
      if (!attrs.has(match[1]) || Object.hasOwn(values, match[1])) throw new Error('Unsupported or duplicate SVG attribute.');
      values[match[1]] = match[2].slice(1, -1); end = match.index + match[0].length;
    }
    if (rest.slice(end).trim()) throw new Error('Malformed SVG attributes.');
    if (tag === 'svg') {
      if (values.xmlns !== 'http://www.w3.org/2000/svg') throw new Error('SVG namespace is required.');
      viewBox = values.viewBox?.trim().split(/\s+/).map(Number);
      if (viewBox?.length !== 4 || viewBox.some(x => !Number.isFinite(x)) || viewBox[2] <= 0 || viewBox[3] <= 0) throw new Error('SVG needs a valid viewBox.');
    }
    if (!selfClose) stack.push(tag);
  }
  if (roots !== 1 || stack.length || xml.slice(cursor).trim()) throw new Error('Incomplete SVG.');
  return { file, bytes, sha256: hash(bytes), src: `data:image/svg+xml;base64,${bytes.toString('base64')}`, width: viewBox[2], height: viewBox[3] };
}

export function renderDocument(document, documents) {
  let headingIndex = 0;
  const noteOrder = [...new Set(document.references)];
  const referenceCounts = new Map();
  const noteID = id => `${document.id}--footnote-${id}`;
  const refID = (id, count) => `${document.id}--reference-${id}-${count}`;
  const parser = tokenParser(token => {
    const number = noteOrder.indexOf(token.id) + 1;
    const count = (referenceCounts.get(token.id) || 0) + 1;
    referenceCounts.set(token.id, count);
    return `<sup class="footnote-ref" id="${escapeHTML(refID(token.id, count))}"><a href="#${escapeHTML(noteID(token.id))}" role="doc-noteref" aria-label="註釋 ${number}">${number}</a></sup>`;
  });
  parser.use({ renderer: {
    heading(token) {
      const heading = document.headings[headingIndex++];
      const title = this.parser.parseInline(token.tokens);
      return `<h${token.depth} id="${escapeHTML(document.id)}--${escapeHTML(heading.slug)}"${token.depth === 1 ? ' tabindex="-1"' : ''}>${title}</h${token.depth}>\n`;
    },
    link(token) {
      const resolved = resolveLink(token.href, document, documents);
      if (resolved.error) throw new Error(resolved.error);
      return `<a href="${escapeHTML(resolved.href)}"${resolved.external ? ' target="_blank" rel="noopener noreferrer"' : ''}${token.title ? ` title="${escapeHTML(token.title)}"` : ''}>${this.parser.parseInline(token.tokens)}</a>`;
    },
    html(token) { return escapeHTML(token.text); },
    image(token) {
      const figure = readFigure(token.href, document);
      return `<img src="${figure.src}" alt="${escapeHTML(token.text)}" width="${figure.width}" height="${figure.height}">`;
    },
    paragraph(token) {
      const meaningful = (token.tokens || []).filter(t => t.type !== 'space' && !(t.type === 'text' && !t.raw.trim()));
      if (meaningful.length === 1 && meaningful[0].type === 'image') {
        return `<figure class="support-figure">${this.parser.parseInline(meaningful)}<figcaption>${escapeHTML(meaningful[0].text)}</figcaption></figure>\n`;
      }
      return Renderer.prototype.paragraph.call(this, token);
    },
    table(token) { return `<div class="table-scroll" role="region" tabindex="0" aria-label="表格，可水平捲動">${Renderer.prototype.table.call(this, token)}</div>\n`; }
  } });
  const content = parser.parser(document.tokens);
  const notes = noteOrder.map((id, index) => {
    const definition = document.definitions.get(id);
    if (!definition) throw new Error(`Missing footnote [^${id}] in ${document.file}.`);
    const rendered = parser.parser(definition.tokens);
    const returns = Array.from({ length: referenceCounts.get(id) }, (_, i) => `<a class="footnote-back" href="#${escapeHTML(refID(id, i + 1))}" role="doc-backlink" aria-label="返回註釋 ${index + 1} 的第 ${i + 1} 個引用">↩${referenceCounts.get(id) > 1 ? i + 1 : ''}</a>`).join(' ');
    return `<li id="${escapeHTML(noteID(id))}" role="doc-endnote">${rendered}<span class="footnote-returns">${returns}</span></li>`;
  }).join('\n');
  return content + (notes ? `\n<section class="footnotes" role="doc-endnotes" aria-label="本篇註釋"><h2>本篇註釋</h2><ol>${notes}</ol></section>\n` : '');
}

export function readBook(configFile) {
  const configPath = path.resolve(configFile);
  const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
  const configDir = path.dirname(configPath);
  const bookRoot = path.resolve(configDir, '..');
  const sourceRoot = path.resolve(configDir, config.source_dir || '../book-src');
  const documents = [];
  const readErrors = [];
  const entries = [];
  for (const group of config.groups || []) {
    for (const name of group.files || []) {
      const file = path.resolve(configDir, name);
      entries.push({ file, group: group.title, name });
      if (!file.startsWith(sourceRoot + path.sep) || path.extname(file) !== '.md') { readErrors.push(`Manifest path must be a Markdown file inside book-src: ${name}`); continue; }
      try { documents.push(parseDocument(fs.readFileSync(file, 'utf8'), file, group.title)); }
      catch (error) { readErrors.push(`Cannot read ${name}: ${error.message}`); }
    }
  }
  return { config, configPath, configDir, bookRoot, sourceRoot, documents, entries, readErrors };
}

export function extractBaseline(text) {
  const start = text.indexOf(BASE_START);
  const end = text.indexOf(BASE_END);
  if (start < 0 && end < 0) return null;
  if (start < 0 || end < 0 || end < start || text.indexOf(BASE_START, start + 1) >= 0 || text.indexOf(BASE_END, end + 1) >= 0) throw new Error('Baseline markers must occur exactly once and in order.');
  const content = text.slice(start + BASE_START.length, end);
  if (!content.startsWith('\n')) throw new Error('Baseline start marker must be followed by a single LF newline.');
  return content.slice(1);
}

function findConfigs(root) {
  const found = [];
  if (!fs.existsSync(root)) return found;
  for (const entry of fs.readdirSync(root, { withFileTypes: true })) {
    if (entry.name === '.git' || entry.name === 'node_modules' || entry.name.startsWith('.')) continue;
    const full = path.join(root, entry.name);
    if (entry.isDirectory()) found.push(...findConfigs(full));
    else if (entry.isFile() && /(?:book\.)?config\.json$/.test(entry.name) && path.basename(path.dirname(full)) === 'web') found.push(full);
  }
  return found;
}

export function validateBook(book, { checkRegistry = true } = {}) {
  const { config, documents, sourceRoot, entries } = book;
  const errors = [...book.readErrors];
  const warnings = [];
  const report = { id: config.id, expected_chapters: 18, actual_chapters: 0, documents: [], errors, warnings };
  if (config.id !== BOOK_ID) errors.push(`Reader id must be ${BOOK_ID}.`);
  if (config.ui_lang !== 'zh-TW') errors.push('Reader language must be zh-TW.');
  if (config.math_register !== 'unicode' || config.math === true) errors.push('Math register must be Unicode, with no KaTeX runtime.');
  if (config.expected_chapters !== 18) errors.push('Expected chapter count must be exactly 18.');
  if (config.chapter_min_han !== MIN_HAN) errors.push(`Chapter depth threshold must be exactly ${MIN_HAN} Han characters.`);
  if (config.output !== 'index.html') errors.push('Reader output must be index.html.');
  if (!config.title || !Array.isArray(config.groups) || !config.groups.length) errors.push('Reader title and ordered groups are required.');
  if (new Set((config.groups || []).map(group => group.title)).size !== (config.groups || []).length) errors.push('Reader group titles must be unique.');
  if (entries.length !== 23) errors.push(`Reader must contain 23 documents: introduction, 18 chapters, and four appendices; found ${entries.length}.`);
  const fileCounts = new Map();
  const idCounts = new Map();
  for (const entry of entries) fileCounts.set(entry.file, (fileCounts.get(entry.file) || 0) + 1);
  for (const document of documents) idCounts.set(document.id, (idCounts.get(document.id) || 0) + 1);
  for (const [file, count] of fileCounts) if (count > 1) errors.push(`Duplicate manifest file (${count} entries): ${path.basename(file)}`);
  for (const [id, count] of idCounts) if (count > 1) errors.push(`Duplicate document id (${count} entries): ${id}`);
  const manifestChapters = entries.filter(entry => /^ch\d{2}(?:-|\.)/.test(path.basename(entry.file))).map(entry => sourceID(entry.file));
  if (JSON.stringify(manifestChapters) !== JSON.stringify(CHAPTER_IDS)) errors.push(`Chapter manifest must contain ch01–ch18 exactly once and in order; found ${manifestChapters.join(', ')}.`);
  const diskChapters = fs.existsSync(sourceRoot) ? fs.readdirSync(sourceRoot).filter(name => /^ch\d.*\.md$/.test(name)) : [];
  const expectedFiles = new Set(entries.filter(entry => /^ch\d/.test(path.basename(entry.file))).map(entry => path.basename(entry.file)));
  for (const file of diskChapters) if (!expectedFiles.has(file)) errors.push(`Unlisted chapter file on disk: ${file}`);
  if (diskChapters.length !== 18) errors.push(`Exactly 18 chapter files must exist on disk; found ${diskChapters.length}.`);
  if (!entries.some(entry => path.basename(entry.file) === 'README.md')) errors.push('Source README.md must be included in the reader.');
  const listedAppendices = entries.filter(entry => /^appendix-/.test(path.basename(entry.file))).map(entry => path.basename(entry.file));
  if (JSON.stringify(listedAppendices) !== JSON.stringify(APPENDIX_FILES)) errors.push('All four planned appendices must appear exactly once and in order.');
  for (const document of documents) {
    const label = path.basename(document.file);
    const isChapter = CHAPTER_IDS.includes(document.id);
    if (isChapter) report.actual_chapters++;
    for (const issue of document.errors) errors.push(`${label}: ${issue}`);
    for (const issue of document.unsupported) errors.push(`${label}: ${issue}`);
    if (!document.body.trim()) errors.push(`${label}: Empty document.`);
    if (document.headings.filter(heading => heading.depth === 1).length !== 1 || document.headings[0]?.depth !== 1) errors.push(`${label}: Exactly one H1 must be the first heading.`);
    let previousDepth = 0;
    for (const heading of document.headings) {
      if (heading.depth > previousDepth + 1) errors.push(`${label}: Heading level jumps from H${previousDepth} to H${heading.depth}: ${heading.text}`);
      previousDepth = heading.depth;
    }
    if (isChapter && document.hanCount < MIN_HAN) errors.push(`${label}: Chapter has ${document.hanCount} Han characters; minimum is ${MIN_HAN} (code and footnotes excluded).`);
    if (/(?:\bTODO\b|\bTBD\b|\bFIXME\b|\blorem ipsum\b|待補(?:上|充|寫)?|待撰|占位文字|佔位文字|此處插入|尚待完成|內容略|待查證)/iu.test(document.markdown)) errors.push(`${label}: Placeholder text detected.`);
    if (/\\\(|\\\)|\\\[|\\\]|\$\$|\\(?:frac|sqrt|begin|end|sum|int)\b/u.test(document.markdown)) errors.push(`${label}: LaTeX delimiters or commands found in the Unicode math register.`);
    if (document.rawHTML.length) errors.push(`${label}: Raw HTML is unsupported; use authored Markdown.`);
    for (const href of document.images) {
      try { readFigure(href, document); } catch (error) { errors.push(`${label}: ${error.message}`); }
    }
    const referenced = new Set(document.references);
    for (const id of referenced) if (!document.definitions.has(id)) errors.push(`${label}: Missing footnote definition [^${id}].`);
    for (const [id, definition] of document.definitions) {
      if (!referenced.has(id)) errors.push(`${label}: Unused footnote definition [^${id}].`);
      if (!definition.text.trim()) errors.push(`${label}: Empty footnote definition [^${id}].`);
    }
    for (const href of document.links) {
      const resolved = resolveLink(href, document, documents);
      if (resolved.error) errors.push(`${label}: ${resolved.error}`);
    }
    if (isChapter && document.links.filter(href => /^https?:/i.test(href)).length < 2) errors.push(`${label}: At least two external source links are required, including footnote definitions.`);
    report.documents.push({ id: document.id, file: label, is_chapter: isChapter, han_characters: document.hanCount, headings: document.headings.length, footnotes: document.definitions.size, links: document.links.length });
  }
  const metaRoot = path.join(sourceRoot, '_meta');
  const outlinePath = path.join(metaRoot, 'outline.md');
  if (fs.existsSync(outlinePath)) {
    try {
      const outline = fs.readFileSync(outlinePath, 'utf8');
      const outlineIds = [...outline.matchAll(/^### (ch\d{2})\s/gm)].map(match => match[1]);
      if (JSON.stringify(outlineIds) !== JSON.stringify(CHAPTER_IDS)) errors.push('Outline chapter headings must declare ch01–ch18 exactly once and in order.');
      const baseline = extractBaseline(outline);
      if (baseline !== null) {
        const runningPath = path.join(metaRoot, 'running-examples.md');
        const maintenancePath = path.join(metaRoot, 'maintenance.md');
        if (!fs.existsSync(runningPath) || !fs.readFileSync(runningPath).equals(Buffer.from(baseline, 'utf8'))) errors.push('running-examples.md must be byte-identical to the marked baseline in outline.md.');
        if (!fs.existsSync(maintenancePath) || extractBaseline(fs.readFileSync(maintenancePath, 'utf8')) !== baseline) errors.push('maintenance.md baseline must be byte-identical to the marked baseline in outline.md.');
        report.baseline_sha256 = hash(baseline);
      } else warnings.push('Outline has no marked baseline; byte-identity check was not applicable.');
    } catch (error) { errors.push(`Baseline validation: ${error.message}`); }
  } else errors.push('The canonical outline is required.');
  const declaredManifestPath = path.join(metaRoot, 'chapter-manifest.json');
  if (fs.existsSync(declaredManifestPath)) {
    try {
      const declared = JSON.parse(fs.readFileSync(declaredManifestPath, 'utf8'));
      const list = Array.isArray(declared) ? declared : declared.chapters;
      const ids = list.map(entry => typeof entry === 'string' ? entry : entry.id);
      if (JSON.stringify(ids) !== JSON.stringify(CHAPTER_IDS)) errors.push('chapter-manifest.json IDs must be exactly ch01–ch18 in order.');
      const configuredPairs = entries.filter(entry => /^ch\d/.test(path.basename(entry.file))).map(entry => ({ id: sourceID(entry.file), file: path.basename(entry.file) }));
      const declaredPairs = list.map(item => typeof item === 'object' ? ({ id: item.id, file: path.basename(item.file || '') }) : ({ id: item, file: '' }));
      if (JSON.stringify(configuredPairs) !== JSON.stringify(declaredPairs)) errors.push('Reader chapter files and chapter-manifest.json must match as ordered id/file pairs.');
    } catch (error) { errors.push(`Cannot validate chapter-manifest.json: ${error.message}`); }
  } else errors.push('The independent chapter-manifest.json is required.');
  if (checkRegistry) {
    const repositoryRoot = path.resolve(book.bookRoot, '../..');
    for (const configFile of findConfigs(repositoryRoot)) {
      if (path.resolve(configFile) === book.configPath) continue;
      try { if (JSON.parse(fs.readFileSync(configFile, 'utf8')).id === config.id) errors.push(`Reader id collision with ${path.relative(repositoryRoot, configFile)}.`); }
      catch (error) { warnings.push(`Could not inspect reader config ${path.relative(repositoryRoot, configFile)}: ${error.message}`); }
    }
  }
  report.pass = errors.length === 0;
  return report;
}
