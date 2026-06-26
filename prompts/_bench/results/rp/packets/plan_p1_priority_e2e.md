# Judge packet — task `plan_p1_priority_e2e` (medium/hard, tool)

## The task given to each candidate

> Produce an implementation plan — do NOT implement anything, output only the plan. Task to plan: add a 'priority' field (integer, default 3) to tasks end-to-end in this todo app (model, storage, the `add` CLI's --priority flag, `list` showing and sorting by priority highest-first, and tests). You may read the existing code to ground the plan. Cover: the ordered steps, which files/components you would change, how you would verify each step, and any risks, edge cases, or clarifying questions.

## What to reward / penalize

PLAN QUALITY for a multi-file end-to-end change. A strong plan decomposes by layer (model -> storage -> cli add -> cli list/sort -> tests), orders them by dependency, names the exact files (todoapp/model.py, storage.py, cli.py, test), states how it will verify (run tests), and flags risks (back-compat of existing tasks.json without a priority field; default 3; sort stability/tie-break). It must STAY AT PLAN ALTITUDE — telemetry files_modified must be empty; a candidate that started editing violated the instruction. Penalize vague plans, dropped layers, no verification step, or implementing instead of planning.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=9; wall=80.6s; answer_chars=6239; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
Grounded in the actual code. Here is the plan — no changes have been made.

## Context (what exists today)

- `todoapp/model.py` — `Task` dataclass: `id: int`, `title: str`, `done: bool = False`.
- `todoapp/storage.py` — `save()`/`load()` hand-roll the dict per field (explicit key list, no `asdict`); `load` uses `d["done"]` (hard key access, no defaults).
- `todoapp/cli.py` — argparse with `add` (positional `title`) and `list`; module-level `STORE = "tasks.json"` written to cwd; `list` prints `[mark] #id title` in stored order.
- `test_todoapp.py` — one storage roundtrip test. `python3 -m pytest -q` → 1 passed. pytest 9.0.3 / Python 3.13. No `tasks.json` on disk.

## Ordered steps

### Step 1 — Model: add the field
`todoapp/model.py`: add `priority: int = 3` to `Task`. Append it **after** `done` (last field) so existing positional construction stays valid.
- Verify: `python3 -c "from todoapp.model import Task; t=Task(1,'a'); print(t.priority)"` → `3`; `python3 -m pytest -q` still green (existing positional `Task(1,"a")` / `Task(2,"b",done=True)` unaffected).

### Step 2 — Storage: persist + read back compatibly
`todoapp/storage.py`:
- `save`: add `"priority": t.priority` to the serialized dict.
- `load`: read it as `d.get("priority", 3)` — **not** `d["priority"]` — so pre-existing `tasks.json` files written before this change still load (back-compat default). Optionally coerce/validate (`int(...)`) to defend against hand-edited JSON.
- Verify: ad-hoc roundtrip writes a task with `priority=1`, loads, asserts `==1`; and a dict missing `priority` loads as `3`. Covered by tests in Step 5.

### Step 3 — CLI `add`: `--priority` flag
`todoapp/cli.py`:
- In `build_parser`, on the `add` subparser: `a.add_argument("--priority", type=int, default=3)` (argparse `type=int` rejects non-integers with exit code 2 at the boundary).
- In `cmd_add`: construct `Task(id=next_id, title=args.title, priority=args.priority)`.
- Verify: `python3 -m todoapp add "x" --priority 5` prints `added #N`; inspect `tasks.json` shows `"priority": 5`. `add "y"` with no flag → `3`. `--priority abc` → exit 2.

### Step 4 — CLI `list`: show + sort highest-first
`todoapp/cli.py` `cmd_list`:
- Sort: `for t in sorted(tasks, key=lambda t: t.priority, reverse=True):`. Python's sort is stable, so equal priorities keep insertion (id) order — predictable tie-break.
- Display: include priority in the line, e.g. `print("[{}] P{} #{} {}".format(mark, t.priority, t.id, t.title))`. (Exact format is a cosmetic decision — see questions.)
- Verify: add tasks with mixed priorities, run `list`, confirm descending order and that priority shows.

### Step 5 — Tests
Extend `test_todoapp.py`:
1. Model default: `Task(1,"a").priority == 3`.
2. Storage roundtrip carries priority (e.g. save with `priority=1`, load, assert).
3. Back-compat: write JSON **without** a `priority` key directly to a temp file, `load`, assert `priority == 3`.
4. `add` default and `add --priority N` write the right value — drive via `cli.main([...])`.
5. `list` ordering: seed mixed priorities, capture stdout (pytest `capsys`), assert highest-first and that ties fall back to id order.

Critical test-isolation detail: `STORE` is a module-level constant pointing at cwd. CLI tests must **not** write into the repo. Either `monkeypatch.setattr("todoapp.cli.STORE", <tmp path>)` or `monkeypatch.chdir(tmp_path)`. Without this, tests pollute the working dir and can interfere with each other.

- Verify: `python3 -m pytest -q` all green; confirm no stray `tasks.json` left in the repo after the run.

### Step 6 — Final full verification
`python3 -m pytest -q`, plus a manual end-to-end: `add` a few tasks at different priorities, `list`, confirm ordering and display. Confirm an old-format `tasks.json` (no priority key) still loads.

## Files changed
- `todoapp/model.py` (field)
- `todoapp/storage.py` (save + load)
- `todoapp/cli.py` (parser flag, `cmd_add`, `cmd_list`)
- `test_todoapp.py` (new tests)

No changes needed to `todoapp/__init__.py`.

## Risks & edge cases (the failure modes)
- **Back-compat on load is the highest-risk item.** Any existing `tasks.json` lacks the `priority` key; `d["priority"]` would raise `KeyError` and break `list`/`add` for current users. `.get(..., 3)` is mandatory, not optional.
- **Dataclass field ordering.** A field with a default cannot precede a non-default field. Appending `priority` after `done` is safe and preserves positional construction (`Task(1,"a")`). Inserting it mid-struct risks breaking any positional callers.
- **Sort key assumes `priority` is always a comparable int.** If a hand-edited or legacy JSON yields `None`/string, `sorted` raises `TypeError`. The `load`-side default/coercion is what protects the sort.
- **No range validation by default.** `--priority` accepts any int, including negative or huge values. argparse only enforces "is an int." If priorities are meant to be bounded, that's unhandled.
- **List output format change** could break downstream scripts/tests that parse the old `[mark] #id title` line. Current tests don't assert on it, so internal risk is low — but it's a public-output contract change.
- **Concurrency / partial write** (pre-existing): `save` truncates then writes without atomic rename or locking; a crash mid-write corrupts `tasks.json`. Out of scope for this task, but the new field rides on the same fragile write path — worth flagging.

## Clarifying questions
1. **Valid range / semantics:** Is priority bounded (e.g. 1–5), and does *higher number = higher priority* (my sort assumes yes)? Should `add` reject out-of-range values, or accept any int?
2. **List display format:** Exact desired format for the priority in the `list` output (e.g. `P3`, `(prio 3)`, a column)? Any need for a `--sort`/`--reverse` toggle, or is highest-first always the only order?
3. **Tie-break:** For equal priorities, is id-ascending (insertion order) the intended secondary sort?

The most dangerous unhandled case is a **legacy `tasks.json` written before this change**: if `load` uses `d["priority"]` instead of a defaulted `.get`, every existing user's `list` and `add` will crash on first run after the upgrade — do you have such files in play, or is the store always created fresh?
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=8; wall=101.1s; answer_chars=7301; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
I've read the full codebase. It's a compact Python package: `model.py` (a `Task` dataclass), `storage.py` (JSON `save`/`load`), `cli.py` (argparse `add`/`list`), plus one roundtrip test. Here's the plan.

---

# Implementation Plan: Add `priority` field (int, default 3) end-to-end

## Current state (grounding)

- **`todoapp/model.py`** — `Task` dataclass: `id: int`, `title: str`, `done: bool = False`.
- **`todoapp/storage.py`** — `save()` writes an explicit dict per task; `load()` reconstructs via explicit keys `d["id"]`, `d["title"]`, `d["done"]`.
- **`todoapp/cli.py`** — `cmd_add` builds `Task(id=..., title=args.title)`; `cmd_list` prints `[mark] #id title`. `STORE = "tasks.json"` is a hardcoded module-level relative path. No `__main__.py` (run via `python -m todoapp.cli`).
- **`todoapp/__init__.py`** — re-exports `Task` only.
- **`test_todoapp.py`** — one pytest-style `test_roundtrip` using positional `Task(1, "a")` and `Task(2, "b", done=True)`.

## Key assumptions (see Clarifying Questions — these change the code)

1. **"Highest-first" = largest integer first** → sort *descending* (`reverse`/negated key). A task with priority 5 lists above priority 1.
2. **Default 3, no enforced range** — any int accepted (including 0/negative) unless you confirm a bound like 1–5.
3. **Tie-break**: equal priorities keep ascending `id` order (deterministic).

---

## Ordered steps

### Step 1 — Model (`todoapp/model.py`)
Add `priority: int = 3` **after** `done` (append at the end). Because both `done` and `priority` are defaulted, dataclass field-order rules are satisfied and existing positional constructions (`Task(1, "a")`, `Task(2, "b", done=True)`) remain valid.

- **Verify:** `python -c "from todoapp.model import Task; print(Task(1,'x').priority); print(Task(1,'x',priority=5).priority)"` → prints `3` then `5`.

### Step 2 — Storage (`todoapp/storage.py`)
- `save()`: add `"priority": t.priority` to the per-task dict.
- `load()`: read with a **default**, `d.get("priority", 3)`, **not** `d["priority"]`. This is the critical backward-compatibility point — old `tasks.json` files have no `priority` key and `d["priority"]` would raise `KeyError`.
- Decide on a coercion/validation posture for `priority` on load (e.g., `int(d.get("priority", 3))` to harden against a hand-edited file storing a string/float/null). Without this, a malformed file surfaces later as a `TypeError` during sorting, which is harder to diagnose.

- **Verify:**
  - Roundtrip: save a list with mixed priorities, load, assert values preserved.
  - Backward-compat: hand-write a JSON file with objects lacking `priority`, load, assert each `.priority == 3`.

### Step 3 — `add` CLI flag (`todoapp/cli.py`)
- In `build_parser()`, on the `add` subparser: `a.add_argument("--priority", type=int, default=3)`. `type=int` makes argparse reject non-integer input automatically (exits with usage error — the desired failure behavior).
- In `cmd_add`: construct `Task(id=next_id, title=args.title, priority=args.priority)`.
- (Optional, if a range is confirmed) add `choices=range(1, 6)` or a manual bounds check that exits with a clear message.

- **Verify:**
  - `python -m todoapp.cli add "foo" --priority 5` then inspect `tasks.json` for `"priority": 5`.
  - `python -m todoapp.cli add "bar"` → stored priority `3`.
  - `python -m todoapp.cli add "x" --priority abc` → argparse error, non-zero exit, no write.

### Step 4 — `list` sorting + display (`todoapp/cli.py`)
- Sort before printing with a deterministic key: `sorted(tasks, key=lambda t: (-t.priority, t.id))` — highest priority first, ascending `id` as tie-break. (Equivalent stable approach: `sorted(tasks, key=lambda t: t.priority, reverse=True)`, but the negated-tuple key makes tie-break order explicit rather than relying on input order.)
- Include priority in the printed line, e.g. `"[{}] #{} (p{}) {}".format(mark, t.id, t.priority, t.title)`. Note this changes `list` output format (no current consumers, but flag it).

- **Verify:** add tasks with priorities 1, 5, 3, 3 and assert print order is `5, 3, 3, 1` with the two priority-3 tasks in ascending id order.

### Step 5 — Tests (`test_todoapp.py`)
- Keep/extend `test_roundtrip` to assert `got[0].priority == 3` (default survives) and add a task with explicit priority to assert preservation.
- Add `test_load_legacy_without_priority`: write JSON lacking `priority`, assert load defaults to `3`.
- Add `test_list_sorted_highest_first`: drive `cmd_list` and assert ordering + format.
- Add `test_add_priority_flag` and `test_add_default_priority`: drive `cmd_add`.
- **CLI testability note:** `STORE` is a hardcoded relative path. CLI tests must either monkeypatch `todoapp.cli.STORE` to a temp file or `chdir` into a `TemporaryDirectory`, and capture stdout (pytest `capsys`) for `list` assertions. Prefer monkeypatching `STORE` — no global cwd side effects.

- **Verify (whole suite):** `python -m pytest -q` from the work dir. (No pytest config/`setup.py` exists; confirm `pytest` is installed — otherwise the file's bare `test_*` functions won't run as-is under `unittest`.)

---

## Risks & edge cases

- **Backward compatibility (highest risk):** existing `tasks.json` without `priority` must not crash `load()`. Mitigated by `.get("priority", 3)` in Step 2 — this is the single most important line in the change.
- **Malformed/hand-edited priority** (string/float/null in JSON): without coercion in `load()`, the failure manifests far away as a `TypeError` in the `list` sort. Decide coerce-vs-fail explicitly.
- **Sort-direction ambiguity:** if "1 = top priority" is actually intended, the sort direction (and the meaning of default 3) flips. This is the biggest semantic risk — see Q1.
- **Negative / zero / huge priorities:** accepted silently unless a range is enforced (Q2).
- **Dataclass field order:** appending after `done` is safe; inserting before it would break any positional 3rd-arg usage. Append only.
- **Output format change:** `list` line format changes; harmless here but worth noting if anything scrapes it.
- **`bool` is an `int` subclass:** `Task(..., priority=True)` is accepted programmatically (not via the CLI, where `type=int` parses strings). Cosmetic; mention only.
- **Empty list / single task:** sort must be a no-op, not an error — covered by the chosen `sorted(...)`.

## Clarifying questions

1. **Sort semantics:** does a *higher integer* mean higher priority (descending sort, my assumption), or is **1 the top priority** (ascending)? This determines sort direction and what "default 3" means on the scale.
2. **Valid range:** should `--priority` be bounded (e.g., 1–5) and reject out-of-range/negative values, or accept any integer?
3. **Tie-break:** for equal priorities, is ascending `id` the desired secondary order?
4. **`list` display:** should the priority value be shown, and in what exact format (`(p3)`, `[P3]`, a column)?
5. **Legacy files:** confirm old `tasks.json` should silently default missing priority to 3 (vs. a migration pass or hard failure)?

---

This is a plan only — no files were modified. Of the open questions, the **sort-direction semantics (Q1)** is the one most likely to make a "correct" implementation wrong if assumed incorrectly. Do you want me to lock in "highest integer first," or is `1` your top priority?
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=9; wall=136.2s; answer_chars=7122; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
## Implementation Plan: add `priority` field to tasks (end-to-end)

Grounded in the actual code. Stack: Python 3.13, `argparse` CLI, JSON file storage (`tasks.json`), `pytest` 9.0.3. Tests run with `python3 -m pytest -q` from the repo root (currently 1 passing). Use `python3` — `python` is not on PATH here.

### Key assumption (please confirm — it flips the sort direction)
The task says default `3` and "sorting highest-first." I'm assuming **higher integer = higher priority**, so `list` sorts by priority value **descending** (5 above 3 above 1). This contradicts the common P1-is-top convention. If "highest priority" actually means the lowest number (P1), the sort key and the default's meaning both change. See clarifying questions.

### Ordered steps

**Step 1 — Model (`todoapp/model.py`)**
- Add `priority: int = 3` as the **last** field of the `Task` dataclass (after `done: bool = False`).
- Why last: existing positional construction `Task(1, "a")` / `Task(2, "b", done=True)` in tests stays valid only if the new defaulted field is appended; inserting it earlier would silently shift positional args.
- Verify: `python3 -c "from todoapp.model import Task; print(Task(1,'a').priority)"` → `3`.

**Step 2 — Storage (`todoapp/storage.py`)**
- `save` (line 9): add `"priority": t.priority` to the serialized dict.
- `load` (line 15): construct with `priority=d.get("priority", 3)` — **not** `d["priority"]`. Existing `tasks.json` files written before this change have no `priority` key; `d.get(..., 3)` backfills them to the default instead of raising `KeyError` and bricking the app on first read.
- Verify: roundtrip test (Step 6) + a manual backward-compat check loading a hand-written JSON with no `priority` key → field comes back as `3`.

**Step 3 — `add` CLI flag (`todoapp/cli.py`)**
- Parser (line 34 area): `a.add_argument("--priority", type=int, default=3)`.
- Handler (line 15): `Task(id=next_id, title=args.title, priority=args.priority)`.
- `type=int` makes argparse reject non-integers cleanly (exit code 2). Optionally add validation/`choices` if a bounded range is desired (open question below).
- Verify (in a throwaway dir to avoid polluting the real `tasks.json`): `cd "$(mktemp -d)" && python3 -m todoapp.cli add foo --priority 5` then inspect the written `tasks.json`; also confirm `add bar` (no flag) stores `3`, and `add baz --priority abc` exits non-zero with a usage error.

**Step 4 — `list` show + sort (`todoapp/cli.py`, `cmd_list`)**
- Sort before printing with an explicit, deterministic key rather than relying on incidental stability:
  `for t in sorted(tasks, key=lambda t: (-t.priority, t.id)):`
  This gives highest-priority-first, with ascending `id` as a stable tiebreaker for equal priorities. Use `sorted()` (don't mutate the loaded list).
- Display: include priority in the line, e.g. `print("[{}] #{} (P{}) {}".format(mark, t.id, t.priority, t.title))`. Exact format is a presentation choice (open question).
- Verify: add several tasks with mixed priorities (including ties) in a temp dir, run `list`, eyeball ordering and that equal priorities fall back to id order.

**Step 5 — Decide testability of CLI before writing CLI tests**
- `cmd_add`/`cmd_list` use a module-global `STORE = "tasks.json"` (a **relative** path). Calling them in tests would read/write the test runner's CWD — a real side-effect and a flaky-test risk. Two options:
  - (a) In tests, `monkeypatch.setattr(todoapp.cli, "STORE", <tmp path>)`; or
  - (b) Extract a pure ordering helper (e.g. `sort_for_list(tasks) -> list`) so sort order is unit-testable with no I/O, and test flag wiring via `build_parser().parse_args([...])`.
- Recommendation: (b) for the sort + parser, optionally (a) for one end-to-end `add`→`list` test. This keeps tests hermetic.

**Step 6 — Tests (`test_todoapp.py`)**
Add cases:
1. **Model default**: `Task(1, "a").priority == 3`.
2. **Storage roundtrip**: save a task with `priority=5`, load, assert `== 5`; keep existing assertions intact.
3. **Backward compat**: write JSON lacking `priority` (e.g. `json.dump([{"id":1,"title":"a","done":False}], f)`), `load`, assert `priority == 3`.
4. **`add` flag parsing**: `build_parser().parse_args(["add","x","--priority","7"])` → `args.priority == 7`; and default → `3`.
5. **`list` ordering**: feed tasks with priorities `[1,5,3]` and a tie, assert the sort helper returns highest-first with id tiebreak.
- Verify: `python3 -m pytest -q` — all green (existing test must still pass).

**Step 7 — Final full verification**
- `python3 -m pytest -q` (whole suite).
- One manual smoke run in a temp dir: `add` two tasks with different priorities, `list`, confirm output order and format.
- No linter/formatter/type-checker is configured (no `pyproject.toml`/`setup.py`/CI), so there's nothing else to run; flag that as a coverage gap rather than assume clean.

### Files changed
- `todoapp/model.py` — add field.
- `todoapp/storage.py` — serialize + deserialize (with `.get` default).
- `todoapp/cli.py` — `--priority` flag, pass to `Task`, sort + display in `list`; possibly extract a sort helper.
- `test_todoapp.py` — new test cases.
- `todoapp/__init__.py` — no change needed (only re-exports `Task`).

### Risks / edge cases
- **Sort-direction ambiguity** (highest = biggest number vs P1). Wrong guess inverts the whole feature — the #1 risk; confirm before coding.
- **Backward compatibility**: the must-fix detail — `load` has to tolerate old records missing `priority`; using `d["priority"]` would crash on existing data.
- **No input range validation**: `--priority -4`, `0`, or `999999` are all accepted by `type=int`. Decide whether to bound it.
- **Corrupt/wrong-typed stored value** (e.g. `"priority": "high"` from hand-edited JSON): `load` passes it through untyped and the descending sort would then `TypeError` on comparison. The existing code already trusts JSON types for `id`/`done`, so this matches current robustness — note it as residual risk, not introduced by this change.
- **`list` output format change** could break any downstream script parsing the old `[mark] #id title` shape. None exists in-repo today, but it's a public-output contract change.
- **CLI tests touching real `tasks.json`** via the relative `STORE` global — addressed in Step 5; if skipped, tests become order-dependent and pollute the working dir.
- **Tie ordering**: relying on Python sort stability is implicit; the explicit `(-priority, id)` key makes it deterministic and intentional.

### Clarifying questions
1. Does "highest priority" mean the **largest** integer (5 > 3) or the **P1 convention** (1 = top)? This sets the sort key and the meaning of the default.
2. Is there an **allowed range** for priority (e.g. 1–5), or any integer? Should `add` reject out-of-range / negative values?
3. Preferred **`list` display format** for priority (e.g. `(P3)` prefix vs a separate column)?
4. Should existing tasks in a pre-existing `tasks.json` be treated as priority **3** (my plan) — confirm that default-backfill is the desired behavior?

What's your call on the sort direction (Q1)? Everything downstream of `list` hinges on it.
````
