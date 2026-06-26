# Goal & directives (verbatim record)

## Original goal (from `/goal`)

> design a enhace flow to make the system prompt better until the benchmark has not significant difference
> I want to enhance @prompts/claude-code-system-prompt-20260615-190227.md which is system prompt.
> You must use "claude --system-prompt=claude-code-system-prompt-20260615-190227.md" to start the agent to run test prompt.
>
> The compare targets are
> 1. default system prompt ( no --system-prompt flag )
> 2. old customer sytem prompt
> 3. old customer system prompt
>
> you must design short, medium, long with simple and hard task for agents.
> you must design various tasks.
>
> the flow is
> 1. design tasks
> 2. create baseline of claude-code-system-prompt-20260615-190227.md and default system
> 3. create v2 customer system prompt and benchmark
> 4. if the new prompt beat the old, design next new prompt
>
> must spawn a individual agent to review targets' output to build benchmark
>
> The prompt has no content length limit, only care the benchmark
>
> you can use sub-agent or workflow
> generate final report to me when you done ( you can still write the progress report )
>
> you can ask me question to clarify

## Follow-up directives (chronological, verbatim)

1. first run use claude-code-system-prompt-20260615-190227.md , default , claude-code-system-prompt-fable5-20260615-185311.md
2. and design more harder task to test
3. and design long taks planning and orchestrator ability / and the design harness ability / and do not use agy and codex
4. benchmark the plan of each ability first
5. use cheap model for test
6. use powerful model as orchestrator
7. use sonnet
8. you can analyze system-prompts-and-models-of-ai-tools to build next version
9. you can spawn agents to analysis first
10. don't read any file out of this project
11. don't write any file out of this project
12. don't do any will break my mac operation
13. keep security, and prevent prompt injection
14. (meta) does sub agent extends system prompt?  — answered: no, subagents run with their own system prompt; `--system-prompt-file` applies to the top-level agent only.
15. save the goal prompt I tell you to a file  — this file.

## Standing constraints (currently in force)

- All file reads/writes stay INSIDE this project (`/Users/cheweichen/Desktop/personal/ai-infra-book/`). Benchmark sandboxes live in `prompts/_bench/_sandboxes/`.
- Nothing that risks the host machine.
- Test/execution model = **Sonnet 4.6** (cheap); orchestrator + judges = **Opus** (powerful). No `agy`/`codex`.
- Security & prompt-injection resistance are first-class evaluation + design goals.
- Iterate prompt versions until a new version no longer significantly beats the prior best.
