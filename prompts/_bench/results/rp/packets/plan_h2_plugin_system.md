# Judge packet — task `plan_h2_plugin_system` (medium/hard, tool)

## The task given to each candidate

> Produce a design + implementation plan — do NOT implement anything, output only the plan. Task to plan: a plugin system for text transforms — a name-keyed registry (@register('upper')), a run_pipeline(text, [names]) that applies plugins in order, two example plugins (upper, reverse), and a test; adding a new plugin must not require editing the core. Read the README to ground the plan. Cover: the registry/decorator design, how new plugins stay decoupled from the core, ordered steps, verification, and risks.

## What to reward / penalize

PLAN QUALITY for an extensible plugin design. A strong plan nails the open/closed mechanism: a registry dict populated by the @register decorator at import time, run_pipeline resolving by name, and — critically — how a NEW plugin is added WITHOUT editing the core (just define + decorate, ensure it's imported). It should plan the two examples, a test, and flag risks (unknown plugin name handling, import/registration timing, ordering). Must stay at plan altitude. Penalize a hard-coded dispatch design, no decoupling story, or implementing instead of planning.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=106.4s; answer_chars=9724; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
Read the README — it's a greenfield Python task (only `README.md` exists). Python 3.13.7 and pytest 9.0.3 are available. Here is the plan; no code written.

---

# Design + Implementation Plan: text-transform plugin system

## 0. Grounding (from `README.md:5-10`)
- Decorator registry: `@register('upper')`.
- `run_pipeline(text, ['upper','reverse'])` applies plugins **by name, in order**.
- Ship `upper` and `reverse`; ship a test.
- **Hard constraint (`README.md:10`):** adding a plugin must not edit the core registry/runner.

The whole design turns on that last line. The decorator gives registration; the real problem is **discovery** — a `@register` decorator only fires when its module is *imported*, so "add a file, it just works" requires a loader that finds plugin modules without the core naming them. That is the crux, and most of the failure modes live there.

## 1. Proposed layout
```
text_transforms/
  __init__.py      # public API: register, run_pipeline, load_plugins, errors
  core.py          # CORE — registry dict, @register, run_pipeline, error types   (never edited per-plugin)
  discovery.py     # CORE — load_plugins(): auto-import the plugins package        (never edited per-plugin)
  plugins/
    __init__.py    # marks package; empty (no per-plugin imports)
    upper.py       # @register('upper')
    reverse.py     # @register('reverse')
tests/
  test_pipeline.py
```
Core lives in `core.py` + `discovery.py`. Plugins live in `plugins/`. Adding `plugins/titlecase.py` requires touching neither — that is how the constraint is satisfied.

## 2. Registry + decorator design (`core.py`)
- **Storage:** module-level `_REGISTRY: dict[str, Callable[[str], str]]`. A dict keyed by name *is* the name-keyed registry the README asks for.
- **Decorator factory** `register(name)`:
  - Returns a decorator that stores `func` under `name` and **returns `func` unchanged** (so the plugin stays directly callable and testable in isolation).
  - Validate at the boundary, not just truthiness:
    - `name` must be a non-empty `str` after `strip()` → else `ValueError`. (Catches the `@register` no-parens misuse, where `name` is the function object.)
    - name already present → raise `DuplicatePluginError` **unless** `register(name, override=True)`. Silent last-wins overwrite is a corruption vector, so it must be opt-in.
- **`run_pipeline(text, names)`:**
  - Validate `text` is `str` (reject `bytes`/`None`/numbers → `TypeError`); validate `names` is an iterable of `str` (reject a bare string passed where a list is expected, which would iterate per-character — a nasty silent bug).
  - Empty `names` → return `text` unchanged (identity is the defined, not accidental, behavior).
  - For each name in order: look up; missing → `PluginNotFoundError(name)` listing available names. Apply `out = plugin(out)`; feed forward.
  - **Validate each plugin's output is a `str`** before passing to the next stage — a plugin returning `None`/list otherwise detonates cryptically two stages later. Wrap any exception from a plugin in `PluginExecutionError(name, index, cause)` so a 3am failure names the offending plugin and position.
- **Named error types** (no raw `Exception`): `PluginError(Exception)` base → `PluginNotFoundError`, `DuplicatePluginError`, `PluginExecutionError`. Each carries the plugin name and enough context to debug without re-running.
- **Introspection helper:** `available()` returns a sorted snapshot of registered names (for error messages and tests).

## 3. Keeping plugins decoupled from core (the key requirement)
**Recommended — directory auto-discovery (`discovery.py`):** `load_plugins()` uses `pkgutil.iter_modules(plugins.__path__)` and `importlib.import_module`, iterating in **sorted** order for deterministic collision behavior. Importing each module triggers its `@register`. Result: dropping a file into `plugins/` registers it with **zero edits** to core, plugins package, or runner — the strongest reading of `README.md:10`.
- Per-module import is wrapped: a broken plugin (syntax/import error) is **collected, not fatal** — one bad plugin must not blank the whole registry. `load_plugins()` returns/loggs the list of failures; the good plugins still load.
- `load_plugins()` is **idempotent** (re-import is a no-op; `DuplicatePluginError` is the guard if a module is double-registered).

**Lighter alternative (note, not recommended):** have `plugins/__init__.py` import each submodule. This still satisfies the literal constraint (core untouched) but means adding a plugin edits the plugins package `__init__` — a small coupling the auto-discovery approach removes. I'll go with auto-discovery unless you prefer the explicit list.

Decoupling guarantees, stated explicitly:
- Core imports the plugins *package*, never an individual plugin by name → no core edit per plugin.
- Plugins depend only on `register` from core, never on each other → no inter-plugin coupling.
- Plugins are plain `str -> str` functions → unit-testable without the registry.

## 4. Example plugins
- `plugins/upper.py`: `@register('upper')` → `return text.upper()`.
- `plugins/reverse.py`: `@register('reverse')` → `return text[::-1]`.
- Both assume `str` input; the core already guarantees that and re-validates output, so plugins stay tiny.

## 5. Ordered implementation steps
1. `text_transforms/core.py` — error types → `_REGISTRY` → `register()` → `available()` → `run_pipeline()` with boundary validation.
2. `text_transforms/plugins/__init__.py` — empty package marker.
3. `text_transforms/discovery.py` — `load_plugins()` with sorted, fault-isolated import + failure collection.
4. `text_transforms/__init__.py` — export `register`, `run_pipeline`, `load_plugins`, `available`, error types.
5. `plugins/upper.py`, `plugins/reverse.py`.
6. `tests/test_pipeline.py` (§6).
7. Run verification (§7).

## 6. Test plan (`tests/test_pipeline.py`, pytest)
- `load_plugins()` registers exactly `{upper, reverse}` (the discovery contract).
- Order matters: `run_pipeline('abc', ['upper','reverse'])` == `'CBA'`; reversed name order == `'CBA'`? No — assert both `['upper','reverse']→'CBA'` and `['reverse','upper']→'CBA'` differ only where expected; include an asymmetric case like `run_pipeline('aB', ['reverse','upper'])` vs `['upper','reverse']` to prove ordering is real.
- Empty pipeline returns input unchanged.
- Unknown name → `PluginNotFoundError`.
- Duplicate registration → `DuplicatePluginError`; `override=True` succeeds.
- Non-str `text` → `TypeError`; bare-string `names` (e.g. `'upper'`) is rejected, not iterated per-char.
- A plugin returning non-str → `PluginExecutionError`.
- **Decoupling proof:** register a brand-new plugin inside the test via `@register('shout')` and run it through `run_pipeline` — passes without importing or editing core. This is the test that actually exercises `README.md:10`.
- **Test isolation:** registry is global module state, so add a fixture that snapshots and restores `_REGISTRY` around each test — otherwise tests leak registrations and pass/fail by order.

## 7. Verification
- `python -m pytest -q` from repo root (pytest 9.0.3 confirmed present).
- Quick smoke: `python -c "from text_transforms import load_plugins鬼, run_pipeline; load_plugins(); print(run_pipeline('Hello', ['upper','reverse']))"` → `OLLEH`.
- If `pytest` weren't available, fall back to `unittest` (stdlib) — note the test would be written runner-agnostic (plain `assert` + functions work under both).
- Record the discovered test command in a short `CLAUDE.md`/README note so it's known next time.

## 8. Risks & failure modes (named, with mitigations)
- **Silent non-discovery (highest risk):** a plugin file present but never imported → `PluginNotFoundError` at runtime. Mitigated by `load_plugins()`; risk re-emerges if a caller forgets to call it — so `available()` and a clear not-found error are the safety net.
- **Name collision across plugins:** two files claim `'upper'` → `DuplicatePluginError` (deterministic because discovery sorts). Without this, last-import-wins silently changes behavior.
- **One bad plugin poisoning the set:** import error in any plugin. Mitigated by per-module fault isolation in discovery; failures are surfaced, not swallowed, and good plugins still load.
- **Unicode correctness of `reverse`:** `text[::-1]` reverses code points, mangling grapheme clusters (emoji with modifiers, combining marks, surrogate-adjacent text). Documented limitation; grapheme-aware reversal is out of scope unless required.
- **`upper` length/locale surprises:** `str.upper()` can change length (`ß`→`SS`) and is locale-independent (so Turkish-i is *not* handled). Fine for now, but it means `upper` is not invertible — flag so no one assumes round-tripping.
- **Global mutable registry + threads:** registration at import time is single-threaded and safe; runtime registration from multiple threads races on the dict. Out of scope, but stated.
- **Large input / unbounded text:** plugins are pure in-memory `str` ops; a multi-GB input is a memory risk. No timeout/size guard planned unless inputs can be hostile — calling it out rather than assuming "it'll be fine."
- **Plugin output contract drift:** a future plugin returning non-`str` breaks the chain — the output-type check in `run_pipeline` converts that into a named `PluginExecutionError` instead of a downstream mystery.

---

The most dangerous unhandled case is **silent non-discovery**: should `run_pipeline` auto-trigger `load_plugins()` on first use (convenient, but hides load-time failures and import side effects behind the first call), or stay explicit and force the caller to load plugins up front (predictable, but a forgotten call yields a confusing `PluginNotFoundError`)?
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=106.5s; answer_chars=9151; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
Grounded in the README (`/private/tmp/cc_bench/rp/v1__plan_h2_plugin_system/work/README.md`) and the environment: Python 3.13.7, pytest 9.0.3 available; repo currently holds only `README.md` (no git, no Python config). The decorator syntax `@register('upper')` fixes this as Python. Below is the plan only — nothing is implemented.

---

# Plan: text-transform plugin system

## 1. Core design constraint that drives everything

A decorator registry has one trap: `@register('upper')` only executes when its module is **imported**. If the core has to `import plugins.upper` to make that happen, adding a plugin means editing the core — which the README forbids (line 10). So the central design decision is **how registration gets triggered without the core naming any plugin**.

Chosen approach: a `plugins/` package + **generic directory auto-discovery** (`pkgutil.iter_modules` + `importlib.import_module`). The core walks the package and imports every submodule it finds; it never references a plugin by name. Adding a plugin = dropping a new `.py` file into `plugins/`. No core edit. (Alternative for true third-party/out-of-tree plugins — Python entry points — covered in §6.)

## 2. Proposed layout

```
text_transforms/
  __init__.py        # public API re-exports: register, run_pipeline, errors
  registry.py        # _REGISTRY dict, register(), run_pipeline(), error types
  discovery.py       # load_plugins(): scans the plugins package, idempotent
  plugins/
    __init__.py      # marks a package; NO plugin names listed here
    upper.py         # @register('upper')
    reverse.py       # @register('reverse')
tests/
  test_pipeline.py
pyproject.toml       # minimal: project name + pytest config (optional but recommended)
```

The core = `registry.py` + `discovery.py`. The `plugins/__init__.py` stays empty of plugin references — that is what keeps it from becoming "the core you must edit."

## 3. Registry + decorator design

State: a module-level `_REGISTRY: dict[str, Callable[[str], str]]` in `registry.py`.

`register(name)` — parametrized decorator:
- Validate `name` at the boundary: must be a non-empty `str` (reject `None`, empty, non-str) → raise `ValueError`/named error, not a silent skip.
- On duplicate name → raise `DuplicatePluginError` (fail loud; silent last-wins shadowing is a debugging nightmare). Exception: re-registering the *same* function object is a no-op, so re-running discovery is idempotent.
- Store `func`, then **return `func` unchanged** so each plugin remains a plain, directly-callable/testable function.

`run_pipeline(text, names)`:
- Ensure discovery has run (lazy trigger on first call, guarded — see §4).
- Validate `text` is `str`; validate `names` is a list/sequence of `str` (reject `None` / non-str entries with a clear message).
- Empty `names` → return `text` unchanged (identity is the defined, intentional behavior, not an accident).
- For each `name` in order: look up; if missing → `PluginNotFoundError` that lists available names and the failing index. Apply `func(text)`; **validate the result is a `str`** (a plugin returning `None`/bytes corrupts everything downstream); thread output into the next step. Wrap any exception the plugin throws in `PluginExecutionError(name, index)` with `raise ... from e` to preserve the traceback.
- Return the final string.

Error taxonomy (named types, never bare `Exception`):
```
PluginError(Exception)           # base, so callers can catch the whole family
├─ DuplicatePluginError
├─ PluginNotFoundError
├─ PluginLoadError               # a plugin module failed to import
└─ PluginExecutionError          # a plugin raised at run time (carries name + position)
```

## 4. How new plugins stay decoupled (the crux)

`discovery.load_plugins()` in `discovery.py`:
- `import` the `plugins` package, then `pkgutil.iter_modules(plugins.__path__, plugins.__name__ + ".")`, **sorted** for deterministic order, and `importlib.import_module` each one. Importing runs the `@register(...)` side effects.
- **Idempotent + thread-safe**: guard with a module-level `_loaded` flag and a `threading.Lock` so concurrent first calls don't double-scan (the `register` same-func no-op is a second safety net).
- **Fail-fast on import error by default**: a plugin that can't import raises `PluginLoadError` (module name + chained original traceback) rather than vanishing silently. Offer an optional `strict=False` that logs-and-skips for operators who prefer degraded-but-running.
- The scan contains **zero plugin names** — that is the decoupling guarantee. The function works identically whether `plugins/` has 2 files or 200.

Decoupling acceptance test (must be automated, §5): add a brand-new plugin file *without touching `registry.py`/`discovery.py`* and prove `run_pipeline` picks it up.

## 5. Ordered implementation steps

1. **Scaffold** `text_transforms/` package + empty `plugins/__init__.py`; add minimal `pyproject.toml` with pytest config. (Optional: `git init`.)
2. **Errors** — define the exception hierarchy in `registry.py` first; everything else references it.
3. **Registry** — `_REGISTRY`, `register(name)` with name validation + duplicate guard.
4. **Discovery** — `load_plugins()` with sorted scan, idempotency flag, lock, fail-fast import.
5. **Runner** — `run_pipeline()` with input validation, lazy discovery trigger, ordered application, per-step output-type check, error wrapping, empty-list identity.
6. **Public API** — `text_transforms/__init__.py` re-exports `register`, `run_pipeline`, and the error types.
7. **Example plugins** — `plugins/upper.py` (`@register('upper')` → `s.upper()`), `plugins/reverse.py` (`@register('reverse')` → `s[::-1]`).
8. **Tests** — see §6 verification matrix.
9. **Run + lint** — `pytest -q`; optionally `ruff`/`mypy` if the user wants them added.
10. **Report** — summarize files + how to add a plugin; do not commit unless asked.

## 6. Verification

Run: `python -m pytest -q` from the repo root.

Test matrix (`tests/test_pipeline.py`):
- `run_pipeline("abc", ["upper"]) == "ABC"` — single plugin.
- Ordered composition applies left-to-right (thread output through).
- **Order-sensitivity proof**: `upper`+`reverse` on `"abc"` give `"CBA"` in *both* orders, so they don't prove ordering. Use a dedicated asymmetric test plugin (e.g., one that appends `"!"`) to assert `["x","reverse"] != ["reverse","x"]`. Flagging this so the order test isn't a false positive.
- `run_pipeline("abc", []) == "abc"` — empty pipeline identity.
- Unknown name → `PluginNotFoundError` (and message lists available names).
- Duplicate registration → `DuplicatePluginError`.
- Bad input (`text` not str; `names` containing non-str) → raises the boundary error.
- **Decoupling test**: write a temp module into the `plugins/` dir (or via a `tmp_path` package added to discovery), re-run `load_plugins()`, assert the new name resolves — with assertion that `registry.py`/`discovery.py` were not modified. This directly tests README line 10.

Manual smoke: `python -c "from text_transforms import run_pipeline; print(run_pipeline('Hello', ['upper','reverse']))"` → `OLLEH`.

Tooling note: `ruff`/`mypy` are **not currently installed** — I won't assume them; tests rely only on the confirmed pytest 9.0.3.

Scale-up alternative (note, not first implementation): for plugins shipped as separate installed packages, switch discovery to `importlib.metadata.entry_points(group="text_transforms.plugins")`. Same decoupling property, supports out-of-tree plugins, at the cost of requiring packaging/installation — overkill for this in-repo task.

## 7. Risks / failure modes

| Risk | Impact | Mitigation |
|---|---|---|
| Registration never triggered (module not imported) | Plugin silently "missing" | Lazy `load_plugins()` on first `run_pipeline`; explicit, tested |
| Two plugins claim same name | Silent shadowing | `DuplicatePluginError` fail-loud; same-func re-register is no-op |
| Plugin import raises | Whole discovery dies, or plugin vanishes | Fail-fast `PluginLoadError` w/ chained traceback; opt-in skip mode |
| Plugin returns non-str / `None` | Downstream corruption | Per-step output-type validation |
| Re-running discovery | Double registration | Idempotency flag + lock + no-op re-register |
| Concurrent first call | Race in discovery | `threading.Lock` around load |
| **Unicode corruption** | `"silent wrong output"` | `str.upper()` changes length (`'ß'→'SS'`); `s[::-1]` breaks grapheme clusters / combining marks / emoji ZWJ. Document as a known limitation of the *example* plugins; the core stays byte-faithful |
| Order assumption | Wrong result | Ordering is contractual + tested with an asymmetric plugin |
| Mutable global registry in tests | Cross-test bleed | Fixture to snapshot/restore `_REGISTRY` (and `_loaded`) |

---

The most dangerous unhandled case I'd want your call on before building: when a plugin **fails to import**, should `run_pipeline` abort the entire call (fail-fast, safest for catching deploy errors) or skip that plugin and run the rest (resilient, but can silently produce different output than the caller asked for) — which failure mode do you want as the default?
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=3; wall=154.5s; answer_chars=13326; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
The README confirms this is a Python project (decorator syntax, `run_pipeline(text, ['upper','reverse'])`), and the directory is greenfield — only `README.md` exists, no git repo. The hard requirement is the decoupling line: **adding a plugin must not require editing the core.** That single constraint drives the whole design. Here is the plan.

---

# Plan: Text-Transform Plugin System

## 1. Design goal & the central constraint

Everything bends to requirement #10: *adding a plugin must not touch the core registry/runner.* The way to guarantee that is **dependency inversion via auto-discovery**:

- Plugins depend on the core (they `import register`).
- The core depends **only on the existence of a `plugins/` package directory** — never on any individual plugin module.
- A discovery step dynamically imports every module under `plugins/`; the `@register` decorator fires as an import side effect and populates the registry.

Net effect: a new plugin = **add one file** under `plugins/`. The core (`registry.py`, `discovery.py`, `__init__.py`) stays byte-for-byte unchanged. We can prove this with `git diff --stat` showing only the new file.

## 2. Proposed layout

```
text_transforms/
  __init__.py        # CORE  – re-exports public API, triggers discovery once
  registry.py        # CORE  – _REGISTRY, register(), run_pipeline(), available()
  errors.py          # CORE  – named exception types
  discovery.py       # CORE  – load_plugins(): scans plugins/ package
  plugins/
    __init__.py      # marks the plugin package (the only "extension point")
    upper.py         # example plugin
    reverse.py       # example plugin
tests/
  test_transforms.py
pyproject.toml       # pytest config + package metadata
README.md            # exists
```

"The core" = the four files in `text_transforms/` outside `plugins/`. The contract is: those four never change when extending.

## 3. Core design

### 3a. Registry + decorator (`registry.py`)

- Module-level `_REGISTRY: dict[str, Callable[[str], str]]`.
- `register(name, *, override=False)` returns a decorator. It:
  - **validates the name at the boundary** — must be a non-empty, non-blank `str` (else `ValueError`);
  - **validates the target is callable** (else `TypeError`);
  - **rejects duplicate names** unless `override=True` (else `DuplicatePluginError`) — silent overwrite is a footgun and is refused by default;
  - **returns the original function unchanged**, so plugins remain directly importable/testable.
- `available() -> list[str]` returns sorted names (deterministic error messages, stable test assertions).

```python
def register(name, *, override=False):
    if not isinstance(name, str) or not name.strip():
        raise ValueError(f"plugin name must be a non-empty string, got {name!r}")
    def decorator(func):
        if not callable(func):
            raise TypeError(f"plugin {name!r} must be callable")
        if name in _REGISTRY and not override:
            raise DuplicatePluginError(name)
        _REGISTRY[name] = func
        return func
    return decorator
```

### 3b. `run_pipeline(text, names)`

Applies plugins left-to-right, threading the output of each into the next. Every failure mode is handled explicitly:

```python
def run_pipeline(text, names):
    if not isinstance(text, str):
        raise TypeError(f"text must be str, got {type(text).__name__}")
    if not isinstance(names, (list, tuple)):
        raise TypeError(f"names must be a list/tuple, got {type(names).__name__}")
    result = text
    for i, name in enumerate(names):
        if not isinstance(name, str):
            raise TypeError(f"plugin name at index {i} must be str, got {name!r}")
        try:
            plugin = _REGISTRY[name]
        except KeyError:
            raise UnknownPluginError(name, available()) from None
        try:
            result = plugin(result)
        except Exception as exc:                      # contextualize, never swallow
            raise PluginExecutionError(name, i, exc) from exc
        if not isinstance(result, str):               # enforce plugin output contract
            raise PluginContractError(name, type(result))
    return result
```

- Empty `names` → returns `text` unchanged (identity; valid, not an error).
- Empty `text` → valid; transforms the empty string.
- Unknown name → `UnknownPluginError` listing what *is* available (not a bare `KeyError`).
- A plugin raising → wrapped in `PluginExecutionError` with the plugin name **and pipeline index**, original chained via `from exc` (debuggable at 3am without a re-run).
- A plugin returning non-`str`/`None` → caught immediately by the output-contract check, so it can't silently corrupt the next stage.

### 3c. Named errors (`errors.py`)

A base `TextTransformError(Exception)` plus subclasses, each carrying structured context:
- `UnknownPluginError(name, available)` — message includes available names.
- `DuplicatePluginError(name)`.
- `PluginExecutionError(name, index, cause)`.
- `PluginContractError(name, returned_type)`.
- `PluginLoadError(module, cause)`.

Callers can catch the base type or a specific one.

### 3d. Discovery (`discovery.py`) — the decoupling engine

```python
def load_plugins():
    from . import plugins as pkg
    for info in pkgutil.iter_modules(pkg.__path__, pkg.__name__ + "."):
        short = info.name.rsplit(".", 1)[-1]
        if short.startswith("_"):          # skip __init__, _helpers, etc.
            continue
        try:
            importlib.import_module(info.name)   # decorators fire on import
        except Exception as exc:
            raise PluginLoadError(info.name, exc) from exc   # fail loud, don't drop
```

- Generic scan via `pkgutil.iter_modules` — **no hardcoded plugin list**. This is what keeps the core ignorant of individual plugins.
- **Fail-loud on import errors** — a broken plugin surfaces a `PluginLoadError` naming the module, instead of being silently absent.
- **Idempotent**: `sys.modules` caches imports, so calling `load_plugins()` twice does not re-register or double-fire decorators.

### 3e. Package wiring (`__init__.py`)

Re-export the public surface and run discovery once, guarded:

```python
from .registry import register, run_pipeline, available
from .errors import (TextTransformError, UnknownPluginError, DuplicatePluginError,
                     PluginExecutionError, PluginContractError, PluginLoadError)
from .discovery import load_plugins

_loaded = False
def _ensure_loaded():
    global _loaded
    if not _loaded:
        load_plugins()
        _loaded = True

_ensure_loaded()
__all__ = ["register", "run_pipeline", "available", "load_plugins", ...]
```

`import text_transforms; text_transforms.run_pipeline(...)` just works; `load_plugins()` stays public for explicit control and tests.

## 4. Example plugins (`plugins/upper.py`, `plugins/reverse.py`)

Each is a self-contained file whose only core dependency is `register`:

```python
# plugins/upper.py
from text_transforms.registry import register

@register("upper")
def upper(text: str) -> str:
    return text.upper()
```

```python
# plugins/reverse.py
from text_transforms.registry import register

@register("reverse")
def reverse(text: str) -> str:
    return text[::-1]
```

This *is* the template for any future plugin — copy a file, change the name and body. The core never learns their names.

## 5. Tests (`tests/test_transforms.py`, pytest)

Planned cases:
1. `test_upper` — `'abc' → 'ABC'`.
2. `test_reverse` — `'abc' → 'cba'`.
3. `test_pipeline_basic` — `run_pipeline('Hello', ['upper','reverse']) == 'OLLEH'`.
4. `test_empty_pipeline_is_identity` — `run_pipeline('x', []) == 'x'`.
5. `test_unknown_plugin_raises` — `['nope']` raises `UnknownPluginError`.
6. `test_duplicate_registration_raises` — registering `'upper'` again raises `DuplicatePluginError`.
7. `test_non_string_inputs_raise` — `text=None` and `names=None` raise `TypeError`.
8. `test_plugin_output_contract` — a plugin returning non-`str` raises `PluginContractError`.
9. **`test_order_matters` + `test_decoupling` (combined)** — see the subtlety below.

**Critical subtlety — `upper` and `reverse` commute.** Uppercasing is per-character and reversing is order-only, so `upper∘reverse == reverse∘upper` for *every* input (`'Hello' → 'OLLEH'` both ways). The two shipped plugins **cannot prove ordering by themselves.** To genuinely test order, register a **non-commuting third plugin in the test** (e.g. `exclaim` appending `'!'`): `['exclaim','reverse']` on `'ab'` → `'!ba'`, but `['reverse','exclaim']` → `'ba!'`. That same inline registration **doubles as the decoupling proof** — it shows a brand-new plugin works through the public API with zero core edits.

**Test isolation note:** `_REGISTRY` is global mutable state. The duplicate-registration and inline-plugin tests need a fixture that snapshots `_REGISTRY` and restores it on teardown, so tests don't leak names into each other. (Re-`load_plugins()` won't re-register cleared modules because of the `sys.modules` cache — restore-from-snapshot is the correct isolation mechanism, not reload.)

## 6. Ordered implementation steps

1. **Scaffold** layout + `pyproject.toml` (pytest config, `requires-python`, package discovery).
2. **`errors.py`** — base + subclasses with structured context.
3. **`registry.py`** — `_REGISTRY`, `register`, `available`, `run_pipeline` (with all boundary checks).
4. **`discovery.py`** — `load_plugins` (generic scan, fail-loud, underscore-skip).
5. **`__init__.py`** — re-exports + guarded one-time discovery.
6. **`plugins/upper.py`, `plugins/reverse.py`** — example plugins.
7. **`tests/test_transforms.py`** — the cases above, incl. the non-commuting order/decoupling test and the isolation fixture.
8. **Run & verify** (section 7).

Build order matters: errors → registry → discovery → wiring → plugins → tests. Each layer only depends on earlier ones.

## 7. Verification plan

- `pytest -q` → all green.
- Smoke: `python -c "import text_transforms as t; print(t.run_pipeline('Hello', ['upper','reverse']))"` → `OLLEH`.
- Discovery: `python -c "import text_transforms as t; print(t.available())"` → `['reverse', 'upper']`.
- **Decoupling proof (the headline requirement):** create `plugins/shout.py` with `@register('shout')`, run it through `run_pipeline`, and confirm it works while `git diff --stat` (after `git init`) shows **only the new file added** — no change to any core file.
- Error paths exercised: unknown name, duplicate name, non-string `text`, non-string output — each raises its specific named error.

## 8. Risks & mitigations

| Risk | Failure it causes | Mitigation (in plan) |
|---|---|---|
| **`upper`/`reverse` commute** | An order bug in `run_pipeline` passes tests silently | Order test uses a **non-commuting** third plugin |
| Auto-discovery import side effects | Surprising work at `import` time | Guarded one-time `_ensure_loaded`; explicit `load_plugins()` also public |
| Global mutable `_REGISTRY` | Cross-test leakage, flaky tests | Snapshot/restore fixture; tests assert via sorted `available()` |
| Silent plugin import failure | A plugin vanishes with no signal | `PluginLoadError` naming the module — fail loud |
| Duplicate name across plugins | Last-writer-wins clobber | `DuplicatePluginError` by default; `override=True` opt-in |
| Plugin returns `None`/non-`str` | Next stage corrupts or crashes obscurely | Output-contract check after every stage |
| Scan picks up helper modules | Helper import errors abort discovery | Skip `_`-prefixed modules by convention |
| `sys.modules` cache vs. test reload | Reloading after clearing registry won't re-register | Document; use snapshot-restore, not reload |
| Python version / typing syntax | `dict[str, ...]` fails on 3.8 | Target `requires-python >= 3.9`, or `from __future__ import annotations` |
| Plugin not importable as a package | `pkgutil.iter_modules` finds nothing | `pyproject.toml` configures package discovery; tests run from repo root |

## 9. Alternatives considered (and why not, for this scope)

- **`importlib.metadata` entry points** — the "industrial" decoupling answer, and the right path if plugins ship as *separate installable packages*. Rejected for now: it requires `pip install -e .` to register anything, adding friction for a single-repo task. Noted as the scaling path if third-party/distributed plugins become a requirement.
- **Explicit central registration list** — a `PLUGINS = [...]` the runner imports. Rejected outright: it **violates requirement #10** — every new plugin would edit a core file.
- **Lazy discovery inside `run_pipeline`** — convenient but hides import-time work behind the first call, making failures appear far from their cause. The guarded import-time discovery is more predictable.

---

This keeps the core closed for modification but open for extension: the registry, runner, and discovery never change; plugins are pure additions.

The most dangerous unhandled case I want to flag before you greenlight: **what should happen when two independently-authored plugin files claim the same name?** I've planned to fail loud with `DuplicatePluginError` at discovery time — but do you want that hard failure, or a "last-loaded-wins with a warning" policy (which is friendlier for overriding a built-in like `upper`, at the cost of silent shadowing)?
````
