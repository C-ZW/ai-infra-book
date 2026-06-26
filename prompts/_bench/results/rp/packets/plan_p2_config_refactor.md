# Judge packet — task `plan_p2_config_refactor` (medium/hard, tool)

## The task given to each candidate

> Produce an implementation plan — do NOT implement anything, output only the plan. Task to plan: replace the global CONFIG dict in app/config.py with an explicit Settings dataclass (timeout, retries, verbose) constructed once and passed into the functions that use it; update every call site and the tests; remove the global; keep behavior identical. Read the code to ground the plan. Cover: ordered steps, the exact call sites to migrate, how you would verify, and risks or clarifying questions.

## What to reward / penalize

PLAN QUALITY for a cross-cutting migration. A strong plan first IDENTIFIES ALL call sites (client.py, logger.py, runner.py, test_app.py) — completeness of discovery is the key test — then sequences: define Settings, thread it through each site, update tests, delete the global last, run tests. It should flag risks (a missed call site crashes; keeping defaults identical; whether to use a default factory). Must stay at plan altitude (no file edits in telemetry). Penalize missing call sites, wrong ordering (deleting the global before migrating), no verification, or starting to implement.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=11; wall=88.9s; answer_chars=7845; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
Read the whole surface. It's four tiny modules plus one test file; `CONFIG` is referenced in exactly three call sites across `client.py`, `logger.py`, `runner.py`, and the tests pass today (`python3 -m pytest -q` → 2 passed; note `python` is not on PATH, only `python3` / Python 3.13.7).

# Implementation Plan: replace global `CONFIG` with a `Settings` dataclass

## Current state (ground truth)
- `app/config.py:1` — global `CONFIG = {"timeout": 30, "retries": 3, "verbose": False}`.
- `app/client.py` — `connect(host)` reads `CONFIG["timeout"]`, `CONFIG["retries"]`.
- `app/logger.py` — `log(message)` reads `CONFIG["verbose"]` twice (one in the `if`, one in the `return`).
- `app/runner.py` — `run(host)` calls `connect(host)` and reads `CONFIG["timeout"]`.
- `test_app.py` — exercises `connect("h1")` and `run("h1")` against the default values 30 / 3.
- `app/__init__.py` is empty; there is **no** `__main__`/entry point that constructs config today (construction is implicit at import).

## Design decisions
- New `Settings` is a `@dataclass` with fields and defaults matching the dict exactly: `timeout: int = 30`, `retries: int = 3`, `verbose: bool = False`. Identical defaults are what keep behavior identical and let tests build `Settings()` with no args.
- `settings` becomes a **required positional parameter** on every function that used `CONFIG` (`connect`, `log`, `run`). This matches the task's "passed into the functions that use it" and forces every call site to be updated explicitly rather than silently falling back to a hidden default.
- `run` must **forward its received `settings` instance** to `connect` — do not construct a second `Settings()` inside `run` (that would still pass tests by luck but violates "constructed once").
- Recommend `@dataclass(frozen=True)` for immutability (nothing mutates `CONFIG` anywhere, so this is safe and prevents accidental shared-state mutation). Flagged as a judgment call below since it is the one observable difference from the old mutable dict.

## Ordered steps
1. **`app/config.py`** — remove the `CONFIG` dict; define `Settings` dataclass (`timeout/retries/verbose` with defaults 30/3/False). This is the only place the global disappears.
2. **`app/client.py`** — change signature to `connect(host, settings)`; replace `CONFIG["timeout"]`→`settings.timeout`, `CONFIG["retries"]`→`settings.retries`; drop `from app.config import CONFIG` (add `from app.config import Settings` only if you add a type annotation, otherwise no import needed).
3. **`app/logger.py`** — change signature to `log(message, settings)`; replace both `CONFIG["verbose"]` occurrences (the `if` guard and the `return`) with `settings.verbose`; remove the `CONFIG` import.
4. **`app/runner.py`** — change signature to `run(host, settings)`; pass through as `connect(host, settings)`; replace `CONFIG["timeout"]`→`settings.timeout`; swap the `CONFIG` import for `from app.config import Settings` (only if annotating).
5. **`test_app.py`** — `from app.config import Settings`; update calls to `connect("h1", Settings())` and `run("h1", Settings())`. Assertions stay unchanged (30 / 3) — they are the behavior-identical contract.
6. Sweep for stragglers and verify (below).

## Exact call sites to migrate
| File:line | Now | After |
|---|---|---|
| `app/config.py:1-5` | `CONFIG = {...}` | `Settings` dataclass; global removed |
| `app/client.py:1` | `from app.config import CONFIG` | removed (or `import Settings` for hint) |
| `app/client.py:4` | `def connect(host):` | `def connect(host, settings):` |
| `app/client.py:8` | `CONFIG["timeout"]` | `settings.timeout` |
| `app/client.py:9` | `CONFIG["retries"]` | `settings.retries` |
| `app/logger.py:1` | `from app.config import CONFIG` | removed |
| `app/logger.py:4` | `def log(message):` | `def log(message, settings):` |
| `app/logger.py:6` | `if CONFIG["verbose"]:` | `if settings.verbose:` |
| `app/logger.py:8` | `return CONFIG["verbose"]` | `return settings.verbose` |
| `app/runner.py:1` | `from app.config import CONFIG` | `from app.config import Settings` (or removed) |
| `app/runner.py:5` | `def run(host):` | `def run(host, settings):` |
| `app/runner.py:7` | `connect(host)` | `connect(host, settings)` |
| `app/runner.py:8` | `CONFIG["timeout"]` | `settings.timeout` |
| `test_app.py:6` | `connect("h1")` | `connect("h1", Settings())` |
| `test_app.py:11` | `run("h1")` | `run("h1", Settings())` |

Note: `logger.log` has no caller in the repo or tests — its signature still must change for consistency, but consider adding a test that constructs `Settings(verbose=True)` and asserts `log` prints + returns `True` (currently untested, see risks).

## How I'd verify
1. `python3 -m pytest -q` → expect **2 passed**, identical to baseline (use `python3`; `python` is absent).
2. `grep -rn "CONFIG" --include="*.py" .` → expect **zero matches** (proves the global is fully removed, no dangling reference).
3. Import smoke check: `python3 -c "import app.config, app.client, app.logger, app.runner"` → no `ImportError`/`NameError`.
4. Behavior-equivalence spot check: `python3 -c "from app.client import connect; from app.config import Settings; assert connect('h', Settings()) == {'host':'h','timeout':30,'retries':3}"`.
5. Confirm no unused `Settings` imports remain (e.g. `python3 -m pyflakes app test_app.py` if available; otherwise visual check).

## Risks / failure modes
- **Hidden external caller breaks.** Making `settings` required raises `TypeError` for any caller passing the old `connect(host)` arity. Grep shows only in-repo usage, but anything outside this repo (a script, notebook, downstream import of `app.config.CONFIG`) would break loudly — acceptable if this is the whole codebase, fatal if not. → clarifying question below.
- **Second-instance bug in `run`.** If `run` constructs its own `Settings()` instead of forwarding, "constructed once" is violated and a non-default `settings` passed to `run` would silently not reach `connect`. Tests use defaults so they'd pass anyway — this bug would be invisible to the current suite. Mitigate by forwarding explicitly and, ideally, adding a `run("h", Settings(timeout=5))` assertion.
- **Mutability change.** The old dict was mutable and module-global; `frozen=True` makes assignment raise `FrozenInstanceError`. No code mutates it today, so behavior is identical in practice — but if any out-of-repo code did `CONFIG["timeout"] = x`, that pattern is gone. Flagging as the one semantic difference.
- **Type drift.** Keep `timeout`/`retries` as `int` and `verbose` as `bool`; a stray default like `verbose: bool = 0` would technically alter the `return` type of `log`. Match 30/3/False exactly.
- **Untested `log`.** `log` is migrated blind (no test covers it). A typo (`settings.verbose` vs `settings.verose`) wouldn't be caught. Recommend adding a minimal `log` test as part of this change.

## Clarifying questions
1. **Required vs optional `settings`?** I plan to make it a required positional arg (explicit, forces call-site updates). Do you instead want `settings=None` → `Settings()` fallback for back-compat? That reintroduces an implicit default and partly defeats "constructed once."
2. **Is `app/` the entire surface?** Grep finds `CONFIG` only in these four files + tests. Can you confirm there's no external consumer of `app.config.CONFIG` (a `main`, CLI, or another package) that I can't see from this tree?
3. **Frozen dataclass acceptable?** I'd prefer `frozen=True` for safety; confirm nothing relies on mutating config at runtime.

The most dangerous unhandled case: if `run` quietly builds its own `Settings()` instead of forwarding the caller's, the change passes all current tests yet silently drops any non-default config on the floor in production — should I add a `run`-with-non-default-settings test to this plan so that failure mode can't ship invisibly?
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=10; wall=93.4s; answer_chars=6838; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
I've read all the code. The picture is small and fully mapped: one global dict, three consumer functions, one internal call chain (`run`→`connect`), and two tests. Here's the implementation plan.

---

# Plan: Replace global `CONFIG` dict with an explicit `Settings` dataclass

## Current state (grounded in the code)

| File | What it does with `CONFIG` |
|------|----------------------------|
| `app/config.py:1-5` | Defines the global `CONFIG = {"timeout": 30, "retries": 3, "verbose": False}` |
| `app/client.py:1,8,9` | Imports `CONFIG`; `connect(host)` reads `CONFIG["timeout"]`, `CONFIG["retries"]` |
| `app/runner.py:1,7,8` | Imports `CONFIG` + `connect`; `run(host)` calls `connect(host)` and reads `CONFIG["timeout"]` |
| `app/logger.py:1,6,8` | Imports `CONFIG`; `log(message)` reads `CONFIG["verbose"]` twice |
| `test_app.py:6,11` | Calls `connect("h1")` and `run("h1")` with no settings arg |
| `app/__init__.py` | Empty (no re-exports — nothing to update here) |

Dependency note: `run` is the only internal caller of `connect`, so `settings` must be **threaded through** `run → connect`. `log` has **no caller anywhere** in the repo (defined but never invoked).

## Design decision (recommended)

```python
# app/config.py
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    timeout: int = 30
    retries: int = 3
    verbose: bool = False
```

- **`frozen=True`** — the old dict was mutable but never mutated; freezing keeps observed behavior identical while preventing accidental in-place mutation (the failure mode that mutable shared state invites). 
- **Defaults matching the old values** — makes `Settings()` reproduce the exact old config, so `run("h1", Settings())` is behavior-identical and tests stay one-liners.
- **`settings` as a required positional parameter** on each function — this is the "explicit, passed-in" intent and is what forces the test/call-site updates the task asks for. (Trade-off flagged in Risks #1.)

## Ordered steps

1. **`app/config.py`** — replace the entire file: define the `Settings` dataclass above; **delete `CONFIG`**.
2. **`app/client.py`** — change signature `def connect(host)` → `def connect(host, settings)`; replace `CONFIG["timeout"]`/`CONFIG["retries"]` with `settings.timeout`/`settings.retries`; drop `from app.config import CONFIG` (add `from app.config import Settings` only if you choose to add a type annotation).
3. **`app/runner.py`** — change `def run(host)` → `def run(host, settings)`; change `conn = connect(host)` → `conn = connect(host, settings)`; replace `CONFIG["timeout"]` with `settings.timeout`; remove the `from app.config import CONFIG` import (keep `from app.client import connect`).
4. **`app/logger.py`** — change `def log(message)` → `def log(message, settings)`; replace both `CONFIG["verbose"]` reads with `settings.verbose`; drop the `CONFIG` import.
5. **`test_app.py`** — add `from app.config import Settings`; construct **one** `settings = Settings()` (per test, or a module-level/fixture instance); update `connect("h1", settings)` and `run("h1", settings)`. Assertions stay `== 30` / `retries == 3` (defaults unchanged).
6. **Verify** (below), then a final `grep` sweep to prove the global is gone.

## Exact call sites to migrate

**Signature changes (3):**
- `app/client.py:4` — `def connect(host)` → `def connect(host, settings)`
- `app/runner.py:5` — `def run(host)` → `def run(host, settings)`
- `app/logger.py:4` — `def log(message)` → `def log(message, settings)`

**Internal call site (1):**
- `app/runner.py:7` — `connect(host)` → `connect(host, settings)`

**`CONFIG` reads to convert (5):**
- `app/client.py:8` `CONFIG["timeout"]` → `settings.timeout`
- `app/client.py:9` `CONFIG["retries"]` → `settings.retries`
- `app/runner.py:8` `CONFIG["timeout"]` → `settings.timeout`
- `app/logger.py:6` `CONFIG["verbose"]` → `settings.verbose`
- `app/logger.py:8` `CONFIG["verbose"]` → `settings.verbose`

**Imports to change (3):** `app/client.py:1`, `app/runner.py:1`, `app/logger.py:1` (all `from app.config import CONFIG`).

**Test call sites (2):** `test_app.py:6`, `test_app.py:11`, plus the new import + `Settings()` construction.

## How to verify

1. **Static sweep — global is truly gone:** `grep -rn "CONFIG" . --include="*.py"` must return **nothing**.
2. **Imports clean (catches missed imports / signature typos):** `python -c "import app.config, app.client, app.runner, app.logger"`.
3. **Tests pass unchanged in intent:** `python -m pytest test_app.py -q` → both tests green (`timeout==30`, `retries==3`, `deadline==30`).
4. **Behavior-equivalence spot check:** in a REPL, `connect("h1", Settings()) == {"host":"h1","timeout":30,"retries":3}` and `run("h1", Settings())["deadline"] == 30`; `log("x", Settings(verbose=True))` prints and returns `True`, `log("x", Settings())` returns `False` and prints nothing.
5. **No stray callers outside repo scope:** confirm `grep -rn "from app.config"` shows only `Settings` imports (or none).

## Risks & clarifying questions

1. **Required vs. optional `settings` (API break).** A required param breaks any external caller using `connect(host)` / `run(host)` / `log(message)`. I recommend required (matches "update every call site and the tests"). **Q: is there any out-of-repo caller, or is backward compatibility required?** If yes, fall back to `settings: Settings = Settings()` (safe only because it's frozen) or `settings=None` → construct inside.
2. **`log` has zero callers.** Its signature change is unverifiable by the existing tests. **Q: should `log` change for consistency (recommended) — and is it part of a public API I should add a test for?** Otherwise a typo there ships silently.
3. **Loss of runtime monkeypatching.** A mutable global lets code/tests do `CONFIG["verbose"]=True` at runtime; a frozen dataclass passed by value removes that. No current test relies on it, but flag in case a downstream workflow does. **Q: is `frozen=True` acceptable, or is in-place override expected anywhere?**
4. **Defaults in the dataclass vs. fully explicit.** Keeping defaults preserves the "there is a default config" concept and keeps tests terse; dropping them forces every caller to specify all three. I recommend keeping defaults equal to the old values. **Q: OK to keep defaults?**
5. **Type drift on access.** `CONFIG["x"]` raised `KeyError`/`TypeError` on misuse; `settings.x` raises `AttributeError`. Irrelevant to the happy path (all internal callers pass a real `Settings`), but worth noting if any code catches the old exception type.

The most dangerous unhandled case here is the one with no test coverage: **if `log`'s signature changes but nothing calls it, a wrong attribute name (`settings.verbos`) passes the entire suite and detonates only in production — should I add a `log` test, or leave it as caller-trusted dead code?**
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=10; wall=86.3s; answer_chars=6395; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
Read all the code. The full surface is tiny and fully mapped: `CONFIG` is defined in `app/config.py` and read in exactly three modules (`client.py`, `runner.py`, `logger.py`); `test_app.py` exercises two of them. `app/__init__.py` is empty (no re-export), and there's no `__main__`/CLI entry point, no `conftest.py`, no build config.

# Plan: replace global `CONFIG` dict with a `Settings` dataclass

## Current state (grounded)
| File | Reads CONFIG | Functions |
|------|-------------|-----------|
| `app/config.py:1-5` | defines `CONFIG = {"timeout":30,"retries":3,"verbose":False}` | — |
| `app/client.py:1,8,9` | `CONFIG["timeout"]`, `CONFIG["retries"]` | `connect(host)` |
| `app/runner.py:1,8` | `CONFIG["timeout"]` | `run(host)` → calls `connect(host)` |
| `app/logger.py:1,6,8` | `CONFIG["verbose"]` (×2) | `log(message)` — *not called anywhere in repo* |
| `test_app.py:6,11` | — | calls `connect("h1")`, `run("h1")` |

## Design decisions (state assumptions, flag the open ones)
- **Dataclass**: `@dataclass(frozen=True)` in `app/config.py`, fields `timeout:int=30`, `retries:int=3`, `verbose:bool=False`. Defaults equal to today's dict values, so `Settings()` reproduces current behavior exactly → "behavior identical" holds. `frozen=True` makes a passed-around instance safe to share (no accidental mutation re-creating a hidden global).
- **Passing style**: add a **required positional** `settings` param to each function (`connect(host, settings)`, `run(host, settings)`, `log(message, settings)`). Required, *not* defaulted — a `settings=Settings()` default would evaluate once at def-time and become a de-facto shared global, defeating the task. Attribute access (`settings.timeout`) replaces subscript (`CONFIG["timeout"]`); types stay int/int/bool.
- **"Constructed once" site**: there is no application entry point in this repo, so the single construction lives at each top-level caller. Currently that's only the tests — I'll construct one `Settings()` (a `pytest` fixture, or a module-level constant) and thread it into both calls.

## Ordered steps
1. **`app/config.py`** — delete the `CONFIG` dict; add:
   ```python
   from dataclasses import dataclass

   @dataclass(frozen=True)
   class Settings:
       timeout: int = 30
       retries: int = 3
       verbose: bool = False
   ```
2. **`app/client.py`** — drop `from app.config import CONFIG`; change `def connect(host):` → `def connect(host, settings):`; body uses `settings.timeout`, `settings.retries`.
3. **`app/runner.py`** — drop `from app.config import CONFIG`; change `def run(host):` → `def run(host, settings):`; `conn = connect(host, settings)` (thread it through), `deadline = settings.timeout`. Keep `from app.client import connect`.
4. **`app/logger.py`** — drop `from app.config import CONFIG`; change `def log(message):` → `def log(message, settings):`; use `settings.verbose` in the `if` and the `return`. (Migrate it even though unused, so no `CONFIG` reference survives.)
5. **`test_app.py`** — import `Settings` from `app.config`, construct once, pass into both calls:
   ```python
   from app.config import Settings
   settings = Settings()
   ...
   c = connect("h1", settings)
   ...
   assert run("h1", settings)["deadline"] == 30
   ```
   Assertions stay unchanged (30 / 3 / 30).

## Exact call sites to migrate
- `app/client.py:4` definition + `:8-9` body.
- `app/runner.py:5` definition + `:7` (`connect(host)`→`connect(host, settings)`) + `:8` body.
- `app/logger.py:4` definition + `:6,:8` body.
- `test_app.py:6` (`connect("h1")`) and `:11` (`run("h1")`).
- Plus the three `from app.config import CONFIG` import lines (`client.py:1`, `runner.py:1`, `logger.py:1`).

## Verification
1. `grep -rn "CONFIG" . --include='*.py'` → must return **zero** matches (proves global removed and no orphan reference).
2. `python -m py_compile app/*.py test_app.py` → no syntax/parse errors.
3. `python -c "import app.config, app.client, app.runner, app.logger"` → import smoke test (no missing-name errors).
4. `python -m pytest test_app.py -q` → both tests pass; `test_connect_defaults` confirms timeout=30/retries=3, `test_run_deadline` confirms deadline=30 — i.e. behavior identical.
5. If a linter/type checker is present (none found in repo — no `pyproject.toml`/`setup.cfg`), run it; otherwise note it's unavailable.

## Risks / failure modes
- **Forgotten thread-through**: the one cross-function call is `run`→`connect`. If `run` doesn't forward `settings`, `connect` raises `TypeError` (missing arg) — caught immediately by step 4. This is the highest-value thing to get right.
- **API break for external consumers**: if anything *outside* this repo imports `app.config.CONFIG` or calls these functions with the old arity, removing the global / changing signatures is a breaking change. Repo-internally there are none, but I can't see external callers — see clarifying questions.
- **Misuse → AttributeError not KeyError**: a wrong field name now raises `AttributeError` instead of the old `KeyError`; passing `settings=None` raises `AttributeError`. Tests don't exercise misuse, so behavior on the happy path is identical. I will *not* add input validation (`__post_init__` range/type checks) because that would change behavior beyond the task — flagging it as optional hardening only.
- **Empty `app/__init__.py`**: confirmed 0 bytes, so no re-export of `CONFIG` to clean up.

## Clarifying questions
1. Is `app` an internal-only package, or a published/imported library where `CONFIG` or the current function signatures are part of a public API? (Decides whether the breaking change is acceptable or needs a shim/deprecation.)
2. Preferred construction site in the tests — a `pytest` fixture vs. a single module-level `Settings()` constant? Both satisfy "constructed once"; fixture is cleaner if more tests arrive.
3. Should `settings` be a plain required positional arg, or keyword-only (`def connect(host, *, settings)`) for call-site explicitness? Keyword-only is more robust but slightly more verbose at every call.
4. Want `Settings` frozen/immutable (my recommendation) or mutable so callers can tweak a field after construction?

The single most dangerous unhandled case: if this package is imported elsewhere I can't see, silently changing `connect`/`run`/`log` arity will break those callers at runtime, not at edit time — do you know of any consumer of `app` outside this repo?
````
