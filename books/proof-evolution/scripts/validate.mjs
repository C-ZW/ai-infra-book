#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { hash, readBook, validateBook } from './book-lib.mjs';

const scriptsDir = path.dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
if (args.includes('--help')) {
  console.log('Usage: node scripts/validate.mjs [--json] [--config path]\nValidates chapter reconciliation, depth, placeholders, headings, citations, links, math register, baseline bytes, and unique reader id. No network requests.');
  process.exit(0);
}
const configIndex = args.indexOf('--config');
const config = configIndex >= 0 ? args[configIndex + 1] : path.join(scriptsDir, '../web/book.config.json');
let report;
try {
  report = validateBook(readBook(config));
  const parserHash = hash(fs.readFileSync(path.join(scriptsDir, 'vendor/marked-17.0.5.mjs')));
  if (parserHash !== '0b4487359ce6b85108708e7a532e1242a27f4718241e7b2de109ac6cd307d2dc') {
    report.errors.push('Vendored marked 17.0.5 differs from its recorded SHA-256.');
    report.pass = false;
  }
  report.parser = { name: 'marked', version: '17.0.5', sha256: parserHash };
} catch (error) { report = { pass: false, errors: [error.message] }; }
if (args.includes('--json')) console.log(JSON.stringify(report, null, 2));
else {
  console.log(`${report.pass ? 'PASS' : 'FAIL'}: ${report.actual_chapters ?? 0}/18 chapters; ${report.documents?.length ?? 0} documents.`);
  for (const issue of report.errors) console.error(`ERROR: ${issue}`);
  for (const warning of report.warnings || []) console.warn(`WARNING: ${warning}`);
  for (const document of report.documents || []) console.log(`${document.id}: ${document.han_characters} Han characters, ${document.footnotes} footnotes, ${document.links} links.`);
}
process.exitCode = report.pass ? 0 : 1;
