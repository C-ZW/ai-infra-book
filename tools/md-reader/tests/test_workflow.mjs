// Exercise the actual Workflow script without dispatching agents or model calls.
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

const source = await readFile(new URL('../../../.agents/skills/write-book/scripts/p4-adjudicate.js', import.meta.url), 'utf8')
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor
const execute = new AsyncFunction('args', 'pipeline', 'agent', 'log', source.replace('export const meta', 'const meta'))
const families = ['openai', 'google', 'anthropic']

async function run(writer, flagger, wrongFamily = false) {
  let chosen
  const agent = async (prompt, options) => {
    if (options.label.startsWith('arbiter:')) {
      return { agrees_with_verifier: false, correct_value: '4', confidence: 'high', reasoning: 'Direct addition' }
    }
    chosen = prompt.match(/family \((\w+)\)/)[1]
    return { ran: true, family: wrongFamily ? writer : chosen, verdict: 'book_correct', detail: 'Independent addition' }
  }
  const pipeline = async (items, first, second) => Promise.all(items.map(async item => second(await first(item), item)))
  const result = await execute({ skillDir: '/skill', bookSrc: '/book', arbiterTemplate: '/arbiter', writerFamily: writer, findings: [{ file: 'ch01.md', claim: '2+2=4', verifier_value: '5', families: [flagger] }] }, pipeline, agent, () => {})
  assert.notEqual(chosen, writer)
  assert.notEqual(chosen, flagger)
  assert.equal(result.records[0].outcome, wrongFamily ? 'quarantined' : 'dismissed')
}

for (const writer of families) {
  for (const flagger of families) await run(writer, flagger)
}
await run('openai', 'google', true)
console.log('PASS: 9 family selections; mismatched tiebreak family quarantined')
