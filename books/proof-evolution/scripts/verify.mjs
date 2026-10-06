#!/usr/bin/env node
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const scriptsDir = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(scriptsDir, '..');
const args = process.argv.slice(2);
if (args.includes('--help')) {
  console.log('Usage: node scripts/verify.mjs [--json]\nRuns focused tooling tests, structural validation, exact arithmetic checks, reader freshness, and static offline HTML integrity. Node >=20 and Python >=3.9 are required. No network access. Browser interaction checks are separate: node scripts/browser-smoke.mjs.');
  process.exit(0);
}
const python = process.env.PROOF_BOOK_PYTHON || 'python3';
const commands = [
  { name: 'reader_javascript_syntax', command: process.execPath, args: ['--check', path.join(scriptsDir, 'reader.js')] },
  { name: 'tooling_regressions', command: process.execPath, args: ['--test', path.join(scriptsDir, 'tests/book-tools.test.mjs')] },
  { name: 'structural_contract', command: process.execPath, args: [path.join(scriptsDir, 'validate.mjs'), '--json'], json: true },
  { name: 'canonical_arithmetic', command: python, args: [path.join(scriptsDir, 'check-math.py'), '--json'], json: true },
  { name: 'reader_freshness', command: process.execPath, args: [path.join(scriptsDir, 'build-reader.mjs'), '--check'] },
  { name: 'reader_integrity', command: python, args: [path.join(scriptsDir, 'check-reader.py'), '--json'], json: true }
];
const steps = [];
for (const command of commands) {
  const result = spawnSync(command.command, command.args, { cwd: root, encoding: 'utf8', timeout: 30000, maxBuffer: 8 * 1024 * 1024 });
  const step = { name: command.name, pass: result.status === 0 && !result.error };
  if (command.json && result.stdout) {
    try { step.report = JSON.parse(result.stdout); } catch { step.output = result.stdout; step.pass = false; }
  } else step.output = result.stdout?.trim() || '';
  if (result.stderr?.trim()) step.stderr = result.stderr.trim();
  if (result.error) step.error = result.error.message;
  steps.push(step);
  if (!args.includes('--json')) {
    console.log(`${step.pass ? 'PASS' : 'FAIL'}: ${step.name}`);
    if (!step.pass) console.log(JSON.stringify(step.report || step, null, 2));
  }
}
const report = {
  pass: steps.every(step => step.pass),
  steps,
  limitations: [
    'External URLs are checked for syntax, not fetched by this offline command.',
    'Deterministic checks do not establish historical accuracy or replace editorial review.',
    'Arithmetic checks and same-model editorial review are not independent cross-model certification.',
    'Browser rendering and selected keyboard/interaction checks require the separate browser-smoke.mjs command.'
  ]
};
if (args.includes('--json')) console.log(JSON.stringify(report, null, 2));
else console.log(`${report.pass ? 'PASS' : 'FAIL'}: offline verification completed.`);
process.exitCode = report.pass ? 0 : 1;
