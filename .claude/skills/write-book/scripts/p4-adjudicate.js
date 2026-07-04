export const meta = {
  name: 'write-book-p4-adjudicate',
  description: 'write-book P4: per-finding arbiter recompute, cross-family tiebreak, fix or quarantine',
  phases: [
    { title: 'Arbitrate', detail: 'closed-book recompute of each verifier finding' },
    { title: 'Resolve', detail: 'fix / cross-family tiebreak / quarantine' },
  ],
}
// Normative rules: references/adjudication.md. Summary implemented here:
//   arbiter agrees the book is wrong           -> fix
//   arbiter disagrees, flagged by >=2 families -> quarantine (no vote)
//   arbiter disagrees, flagged by 1 family     -> tiebreak via a panel CLI whose
//     family is neither the flagging family nor the writer family;
//     book_wrong -> fix ; book_correct -> dismissed ; else -> quarantine
// A `dismissed` outcome always carries the tiebreak record.
//
// args contract (paths absolute):
//   skillDir         string — write-book skill directory
//   bookSrc          string — book source directory
//   arbiterTemplate  string — references/templates/arbiter.md
//   writerFamily     string — e.g. "anthropic"
//   findings         array  — [{ file, claim, book_value, verifier_value,
//                                verifier_explanation, families }]
//                              `file` relative to bookSrc; `families` = model
//                              families that flagged this claim
// returns: { records: [{ file, claim, outcome, arbiter, tiebreak, fix_summary }] }
// The MAIN LOOP writes _meta/verify-log.md from `records` and re-runs
// verify_book on fixed chapters; this script never writes logs or state.

// Defensive: some harness paths deliver args as a JSON-encoded string.
const A = typeof args === 'string' ? JSON.parse(args) : args
if (!A || !A.skillDir || !A.bookSrc || !A.arbiterTemplate || !A.writerFamily ||
    !Array.isArray(A.findings) || A.findings.length === 0) {
  throw new Error('args must include skillDir, bookSrc, arbiterTemplate, writerFamily, and a non-empty findings array')
}

const ARBITER_SCHEMA = {
  type: 'object',
  required: ['agrees_with_verifier', 'correct_value', 'confidence', 'reasoning'],
  additionalProperties: false,
  properties: {
    agrees_with_verifier: { type: 'boolean' },
    correct_value: { type: 'string' },
    confidence: { enum: ['high', 'medium', 'low'] },
    reasoning: { type: 'string' },
  },
}

const TIEBREAK_SCHEMA = {
  type: 'object',
  required: ['ran', 'family', 'verdict', 'detail'],
  additionalProperties: false,
  properties: {
    ran: { type: 'boolean' },
    family: { type: 'string' },
    verdict: { enum: ['book_correct', 'book_wrong', 'inconclusive'] },
    detail: { type: 'string' },
  },
}

const FIX_SCHEMA = {
  type: 'object',
  required: ['edited', 'summary'],
  additionalProperties: false,
  properties: {
    edited: { type: 'boolean' },
    summary: { type: 'string' },
  },
}

// Tiebreak CLI per excluded family (writer family is anthropic-class, so the
// tiebreaker is always one of the two non-writer panel CLIs).
function tiebreakCli(flaggingFamily) {
  if (flaggingFamily === 'openai') {
    return { family: 'google', how: 'agy --model "Gemini 3.5 Flash (Medium)" -p <prompt>' }
  }
  // flagged by google or (writer-family) anthropic -> openai
  return { family: 'openai', how: 'codex exec -m gpt-5.5 --skip-git-repo-check <prompt>' }
}

function arbiterPrompt(f) {
  return [
    'You are an adjudication arbiter in the write-book pipeline.',
    `Read and follow EXACTLY this template: ${A.arbiterTemplate}`,
    'Parameters:',
    `- chapter_path: ${A.bookSrc}/${f.file}`,
    `- baseline_path: ${A.bookSrc}/_meta/running-examples.md`,
    `- claim: ${f.claim}`,
    `- verifier_value: ${f.verifier_value}`,
    `- verifier_explanation: ${f.verifier_explanation || '(none given)'}`,
    `- skill_dir: ${A.skillDir}`,
    'Then return the structured result the template specifies.',
  ].join('\n')
}

function tiebreakPrompt(f, cli) {
  return [
    'You are a tiebreak runner in the write-book adjudication pipeline. An',
    'external verifier and an internal arbiter disagree about a claim in a',
    'book chapter. Your job is to obtain ONE independent verdict from a',
    `different model family (${cli.family}) by running its CLI via Bash, then`,
    'report that verdict faithfully. You do NOT judge the claim yourself.',
    '',
    `CLI to use: ${cli.how}`,
    '(Compose the prompt text yourself from the material below; mind shell',
    'quoting — writing the prompt to a temp file and using command',
    'substitution is fine. If the CLI errors, times out (give it ~240s), or',
    'returns no parseable verdict, report verdict "inconclusive" — a CLI',
    'failure is a tool limitation, never evidence about the claim.)',
    '',
    'The prompt you send it must: quote the claim, the book\'s stated value,',
    'and the challenger value; ask it to recompute closed-book from the',
    'quoted material only; and require a final line',
    '`VERDICT: book_correct` or `VERDICT: book_wrong`.',
    '',
    `claim: ${f.claim}`,
    `book value: ${f.book_value || '(as stated in the claim)'}`,
    `challenger (verifier) value: ${f.verifier_value}`,
    '',
    'Return the structured result: ran (did the CLI produce a verdict),',
    `family ("${cli.family}"), verdict, detail (the CLI's decisive reasoning,`,
    'or the failure reason).',
  ].join('\n')
}

function fixPrompt(f, arbiter) {
  return [
    'You are a fix agent in the write-book pipeline. An adjudicated verifier',
    'finding was CONFIRMED; apply the correction.',
    `Read ${A.skillDir}/references/pitfalls.md first — rules 4, 5 and 8 apply.`,
    '',
    `chapter: ${A.bookSrc}/${f.file}`,
    `claim (wrong in the book): ${f.claim}`,
    `confirmed correct value: ${arbiter.correct_value}`,
    `arbiter reasoning: ${arbiter.reasoning}`,
    '',
    'Rules:',
    '- Fix the chapter text (value AND any surrounding derivation steps that',
    '  depended on the wrong value).',
    `- FIRST check ${A.bookSrc}/_meta/running-examples.md: if the corrected`,
    '  value contradicts a base number in that baseline, DO NOT edit anything',
    '  — return edited=false with summary "contradicts base-numbers table"',
    '  (that escalation belongs to the main loop, per pitfalls rule 8).',
    '- Touch only this one chapter file. No other files.',
    'Return: edited (boolean), summary (what changed, one line).',
  ].join('\n')
}

const records = await pipeline(
  A.findings,
  (f) => agent(arbiterPrompt(f), {
    label: `arbiter:${f.file}`,
    phase: 'Arbitrate',
    schema: ARBITER_SCHEMA,
  }),
  async (arbiter, f) => {
    const base = { file: f.file, claim: f.claim, arbiter, tiebreak: null, fix_summary: null }
    if (!arbiter) {
      return { ...base, outcome: 'quarantined', reason: 'arbiter errored' }
    }
    if (arbiter.agrees_with_verifier) {
      const fix = await agent(fixPrompt(f, arbiter), {
        label: `fix:${f.file}`, phase: 'Resolve', schema: FIX_SCHEMA,
      })
      if (fix && fix.edited) return { ...base, outcome: 'fixed', fix_summary: fix.summary }
      return { ...base, outcome: 'quarantined', reason: (fix && fix.summary) || 'fix agent errored' }
    }
    // Arbiter thinks the book is right.
    const families = Array.isArray(f.families) ? f.families : []
    if (families.length >= 2) {
      return { ...base, outcome: 'quarantined', reason: 'arbiter disagrees with >=2 independent families — no mechanical vote' }
    }
    const cli = tiebreakCli(families[0] || A.writerFamily)
    const tb = await agent(tiebreakPrompt(f, cli), {
      label: `tiebreak:${f.file}`, phase: 'Resolve', schema: TIEBREAK_SCHEMA,
    })
    if (!tb || !tb.ran || tb.verdict === 'inconclusive') {
      return { ...base, tiebreak: tb, outcome: 'quarantined', reason: 'tiebreak inconclusive or CLI failure' }
    }
    if (tb.verdict === 'book_wrong') {
      // Two independent voices (verifier + tiebreaker) against the arbiter.
      const fix = await agent(fixPrompt(f, { correct_value: f.verifier_value, reasoning: tb.detail }), {
        label: `fix:${f.file}`, phase: 'Resolve', schema: FIX_SCHEMA,
      })
      if (fix && fix.edited) return { ...base, tiebreak: tb, outcome: 'fixed', fix_summary: fix.summary }
      return { ...base, tiebreak: tb, outcome: 'quarantined', reason: (fix && fix.summary) || 'fix agent errored' }
    }
    return { ...base, tiebreak: tb, outcome: 'dismissed', reason: 'arbiter + cross-family tiebreaker both find the book correct' }
  },
)

const clean = records.filter(Boolean)
const tally = {}
for (const r of clean) tally[r.outcome] = (tally[r.outcome] || 0) + 1
log(`adjudication outcomes: ${JSON.stringify(tally)}`)
return { records: clean }
