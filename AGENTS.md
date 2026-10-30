# Project instructions

Read [CLAUDE.md](CLAUDE.md) for the shared project conventions, local toolchain,
and book maintenance requirements. They apply to every agent in this repository.

## Book authoring skill

Use [write-book](.agents/skills/write-book/SKILL.md) when asked to create,
update, or rescan a book. Its references, templates, and scripts live alongside
that file. Read the skill before executing its workflow.

The canonical skill directory is `.agents/skills/write-book/`.
`.claude/skills/write-book` is a relative directory symlink to it; edit the
canonical copy. Codex, Gemini CLI, Antigravity, and Cursor discover the shared
directory; Claude Code discovers the symlink in its own skill directory.

If an agent has no native skill command, ask it to read
`.agents/skills/write-book/SKILL.md` and follow it. Project configuration is
`write-book.config.json`; use its `tools_path` to locate the toolchain.
