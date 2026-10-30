export const meta = {
  name: 'write-book-p4_5-teach-test',
  description: 'write-book P4.5: per-chapter teach-test — weak solver reads only the chapter, judge grades whether the chapter taught',
  phases: [
    { title: 'Generate', detail: 'one near-transfer problem per chapter' },
    { title: 'Solve', detail: 'weak (haiku-class) solver, chapter-only', model: 'haiku' },
    { title: 'Judge', detail: 'grade the chapter, not the solver' },
  ],
}
// Normative spec: references/phases.md §P4.5; roles: templates/teach-test.md.
// args contract (paths absolute):
//   skillDir      string — write-book skill directory
//   bookSrc       string — book source directory
//   templatePath  string — references/templates/teach-test.md
//   chapters      array  — [{ id, file, goal }] ; `file` relative to bookSrc,
//                          `goal` = the chapter's outline goal line
//   solverModel   string? — default 'haiku' (weak BY DESIGN: a strong solver
//                           masks teaching gaps with its own knowledge)
// returns: { total, passed, results: [{ id, passed, gaps, reason,
//            stuck_points, problem }] }
// The MAIN LOOP records outcomes in state.json and routes failures to the
// rewrite queue per §P4.5; this script only measures.

const A = typeof args === 'string' ? JSON.parse(args) : args
if (!A || !A.skillDir || !A.bookSrc || !A.templatePath ||
    !Array.isArray(A.chapters) || A.chapters.length === 0) {
  throw new Error('args must include skillDir, bookSrc, templatePath, and a non-empty chapters array')
}
const SOLVER_MODEL = A.solverModel || 'haiku'

const GEN_SCHEMA = {
  type: 'object',
  required: ['problem', 'expected_approach', 'pass_criteria'],
  additionalProperties: false,
  properties: {
    problem: { type: 'string' },
    expected_approach: { type: 'string' },
    pass_criteria: { type: 'string' },
  },
}
const SOLVE_SCHEMA = {
  type: 'object',
  required: ['solution', 'used_chapter_method', 'stuck_points'],
  additionalProperties: false,
  properties: {
    solution: { type: 'string' },
    used_chapter_method: { type: 'boolean' },
    stuck_points: { type: 'array', items: { type: 'string' } },
  },
}
const JUDGE_SCHEMA = {
  type: 'object',
  required: ['passed', 'gaps', 'reason'],
  additionalProperties: false,
  properties: {
    passed: { type: 'boolean' },
    gaps: { type: 'array', items: { type: 'string' } },
    reason: { type: 'string' },
  },
}

function genPrompt(ch) {
  return [
    'You are the teach-test GENERATOR.',
    `Read ${A.templatePath} and follow its §Generator section exactly.`,
    'Parameters:',
    `- chapter_path: ${A.bookSrc}/${ch.file}`,
    `- chapter_goal: ${ch.goal}`,
    `- baseline_path: ${A.bookSrc}/_meta/running-examples.md`,
    `- skill_dir: ${A.skillDir}`,
  ].join('\n')
}
function solvePrompt(ch, gen) {
  return [
    'You are the teach-test SOLVER (a learner).',
    `Read ${A.templatePath} and follow its §Solver section exactly.`,
    'Parameters:',
    `- chapter_path: ${A.bookSrc}/${ch.file}`,
    `- problem: ${gen.problem}`,
  ].join('\n')
}
function judgePrompt(ch, gen, sol) {
  return [
    'You are the teach-test JUDGE.',
    `Read ${A.templatePath} and follow its §Judge section exactly.`,
    'Parameters:',
    `- chapter_path: ${A.bookSrc}/${ch.file}`,
    `- problem: ${gen.problem}`,
    `- expected_approach: ${gen.expected_approach}`,
    `- pass_criteria: ${gen.pass_criteria}`,
    `- solver_output: ${JSON.stringify(sol)}`,
  ].join('\n')
}

const results = await pipeline(
  A.chapters,
  (ch) => agent(genPrompt(ch), {
    label: `gen:${ch.id}`, phase: 'Generate', schema: GEN_SCHEMA,
  }),
  async (gen, ch) => {
    if (!gen) return { id: ch.id, passed: false, gaps: [], reason: 'generator errored', stuck_points: [], problem: null }
    const sol = await agent(solvePrompt(ch, gen), {
      label: `solve:${ch.id}`, phase: 'Solve', schema: SOLVE_SCHEMA, model: SOLVER_MODEL,
    })
    if (!sol) return { id: ch.id, passed: false, gaps: [], reason: 'solver errored', stuck_points: [], problem: gen.problem }
    const verdict = await agent(judgePrompt(ch, gen, sol), {
      label: `judge:${ch.id}`, phase: 'Judge', schema: JUDGE_SCHEMA,
    })
    if (!verdict) return { id: ch.id, passed: false, gaps: [], reason: 'judge errored', stuck_points: sol.stuck_points, problem: gen.problem }
    return { id: ch.id, passed: verdict.passed, gaps: verdict.gaps, reason: verdict.reason, stuck_points: sol.stuck_points, problem: gen.problem }
  },
)

const clean = results.filter(Boolean)
const passed = clean.filter((r) => r.passed).length
log(`teach-test: ${passed}/${A.chapters.length} chapters passed`)
return { total: A.chapters.length, passed, results: clean }
