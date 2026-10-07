
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
