export const meta = {
  name: 'write-book-p2-chapters',
  description: 'write-book P2: one writer agent per planned chapter, bounded retries, structured status report',
  phases: [
    { title: 'Write', detail: 'one writer agent per planned chapter, <=3 attempts each' },
  ],
}
// args contract (all paths absolute unless noted):
//   skillDir      string  — write-book skill directory
//   bookSrc       string  — book source directory
//   lang          string  — book output language code (e.g. "zh-TW")
//   form          string  — "instructional" | "narrative" | "reference"
//   templatePath  string  — references/templates/chapter-writer.md
//   chapters      array   — [{ id, file, brief }] ; `file` is relative to bookSrc;
//                           `brief` = 1-3 line pointer to the chapter's outline entry
//                           (+ assigned bridge source / fade-out tier for instructional)
//   maxAttempts   number? — default 3
// returns: { total, written, results: [writer schema + attempts] }
// The MAIN LOOP owns _meta/state.json and the reconcile asserts; this script
// only dispatches writers and reports.

// Defensive: some harness paths deliver args as a JSON-encoded string.
const A = typeof args === 'string' ? JSON.parse(args) : args
if (!A || !A.skillDir || !A.bookSrc || !A.lang || !A.form || !A.templatePath ||
    !Array.isArray(A.chapters) || A.chapters.length === 0) {
  throw new Error('args must include skillDir, bookSrc, lang, form, templatePath, and a non-empty chapters array')
}
const MAX = A.maxAttempts || 3

const WRITER_SCHEMA = {
  type: 'object',
  required: ['chapter_id', 'status', 'depth_units', 'terms_defined', 'bridge_used', 'notes'],
  additionalProperties: false,
  properties: {
    chapter_id: { type: 'string' },
    status: { enum: ['written', 'failed'] },
    depth_units: { type: 'number' },
    terms_defined: { type: 'array', items: { type: 'string' } },
    bridge_used: { type: 'string' },
    notes: { type: 'string' },
  },
}

function writerPrompt(ch) {
  return [
    'You are a chapter-writer agent in the write-book pipeline.',
    `Read and follow EXACTLY this template: ${A.templatePath}`,
    'Parameters:',
    `- chapter_id: ${ch.id}`,
    `- output_file: ${A.bookSrc}/${ch.file}`,
    `- book_src: ${A.bookSrc}`,
    `- skill_dir: ${A.skillDir}`,
    `- form: ${A.form}`,
    `- lang: ${A.lang}`,
    `- brief: ${ch.brief || '(see the outline entry for this chapter id)'}`,
    'Then return the structured result the template specifies.',
  ].join('\n')
}

phase('Write')
const results = await pipeline(
  A.chapters,
  async (ch) => {
    let last = null
    for (let attempt = 1; attempt <= MAX; attempt++) {
      const r = await agent(writerPrompt(ch), {
        label: `write:${ch.id}#${attempt}`,
        phase: 'Write',
        schema: WRITER_SCHEMA,
      })
      if (r && r.status === 'written') return { ...r, attempts: attempt }
      last = r
      log(`${ch.id}: attempt ${attempt}/${MAX} ${r ? 'reported failed: ' + r.notes : 'errored (null result)'}`)
    }
    return {
      chapter_id: ch.id,
      status: 'failed',
      attempts: MAX,
      depth_units: 0,
      terms_defined: [],
      bridge_used: 'none',
      notes: (last && last.notes) || 'agent errored on every attempt',
    }
  },
)

const clean = results.filter(Boolean)
const written = clean.filter((r) => r.status === 'written').length
log(`chapters written: ${written}/${A.chapters.length}`)
return { total: A.chapters.length, written, results: clean }
