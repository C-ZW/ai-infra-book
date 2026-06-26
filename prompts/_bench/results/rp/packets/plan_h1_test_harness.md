# Judge packet — task `plan_h1_test_harness` (medium/hard, tool)

## The task given to each candidate

> Produce a design + implementation plan — do NOT implement anything, output only the plan. Task to plan: design a small reusable test harness (no pytest/unittest) with test registration, a runner that isolates and catches per-test exceptions, per-test timeout enforcement, and a pass/fail summary; then tests for mathlib.py including a deliberate failure. Read mathlib.py to ground the plan. Cover: the harness API/design, ordered build steps, how you would verify it, and risks or edge cases.

## What to reward / penalize

PLAN QUALITY for harness design. A strong plan specifies the harness API (how tests register — decorator/list; how the runner isolates failures so one failing test doesn't abort; HOW timeouts are enforced — signal.alarm vs thread/process, with the trade-offs), the summary format, and a verification approach (run it, include a failing+timeout case). The failure-isolation and timeout MECHANISM is the discriminator. Must stay at plan altitude. Penalize hand-waving the timeout/isolation mechanism, no API design, or implementing instead of planning.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=3; wall=138.3s; answer_chars=12560; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
## Grounding: what `mathlib.py` actually exposes

Three pure functions, no state, no I/O (`mathlib.py:1-19`):

- `add(a, b)` → `a + b`. No validation; behavior depends entirely on operand types (`int+int`, `str+str` concat, mixed → `TypeError`).
- `divide(a, b)` → raises `ZeroDivisionError("division by zero")` when `b == 0`, else `a / b` (always **true division** → float).
- `is_prime(n)` → `False` for `n < 2`, otherwise trial division to `√n`. Correct, but unbounded `while` → cost grows with `n` (a large `n` is the natural way to exercise the timeout).

These give clean targets: a value-equality test, an exception-raising test, a boolean-predicate test, and an easy true/false boundary (`is_prime(1)` is `False`) for the deliberate failure.

---

## Failure modes first (the parts that will actually bite)

The hard problem in this harness is **timeout enforcement**, not registration. Naming the traps up front because they drive the design:

1. **You cannot kill a Python thread.** A thread-based timeout (`Thread.join(t)`) reports the timeout but the runaway test keeps running in the background, holding locks/files and skewing later timing. Threads also can't interrupt CPU-bound C calls.
2. **`signal.SIGALRM` is POSIX-only and main-thread-only.** It cleanly interrupts pure-Python loops (like `is_prime`), but doesn't exist on Windows and raises `ValueError` if armed off the main thread. A C extension in a tight loop won't yield to it until it returns to the interpreter.
3. **A broad `except Exception` inside a test will swallow the timeout signal** if the timeout is delivered as an `Exception` subclass. `is_prime` has no try/except, but a real test suite will — so the timeout must be raised as a **`BaseException` subclass** to survive `except Exception`.
4. **No true isolation without subprocesses.** Same-process tests share globals, `sys.modules`, cwd, monkeypatches. "Isolation" here means *exception isolation* (one test's crash doesn't abort the run), not *state isolation*. This limit must be stated, not implied.
5. **Catching too much aborts user intent.** If the runner catches `BaseException`, `KeyboardInterrupt` gets logged as a test error and Ctrl-C won't stop the run. The runner must catch `Exception` for failures, handle the timeout type explicitly, and let `KeyboardInterrupt`/`SystemExit` propagate.
6. **`assert` is stripped under `python -O`.** Tests relying on bare `assert` silently pass. Provide explicit check helpers that raise regardless of optimization flags.
7. **Alarm leakage.** If the previous SIGALRM handler and pending alarm aren't restored/cancelled in a `finally`, one test's timeout can fire during the next test or after the run.
8. **A test with no assertions passes vacuously** — false confidence. Worth a note in reporting, not enforcement.

**Chosen timeout strategy:** `signal.setitimer(ITIMER_REAL)` + `SIGALRM` as the primary mechanism (real, interrupting, simple, correct for pure-Python mathlib), the timeout delivered as a `TestTimeout(BaseException)`. Detect non-POSIX / non-main-thread at runtime and **degrade explicitly**: either fall back to a documented thread-watchdog (reports timeout, can't kill) or refuse to claim enforcement. Subprocess-per-test (`multiprocessing`, truly killable) is noted as the heavyweight upgrade path but is out of scope for a "small" harness. The degradation must be *logged*, never silent.

---

## Harness API / design

Two modules:

- `microtest.py` — the reusable harness.
- `test_mathlib.py` — tests for `mathlib`, run via the harness.

### Result model

```
class Status(enum):  PASS, FAIL, ERROR, TIMEOUT, SKIP
TestResult = dataclass(name, status, duration_s, message, traceback_str)
Summary    = dataclass(results: list, counts: dict, exit_code: int,
                       total_duration_s, degraded_timeout: bool)
```

- `FAIL` = a `TestFailure` (assertion didn't hold — an expected negative result).
- `ERROR` = any other `Exception` (a bug in code-under-test or in the test itself).
- Distinguishing the two is deliberate: a failed assertion and a `TypeError` mean different things to the reader.

### Named exceptions

```
class HarnessError(Exception)        # misconfiguration: bad decorator use, dup name, bad timeout
class TestFailure(AssertionError)    # raised by check_* helpers; → FAIL
class SkipTest(Exception)            # → SKIP
class TestTimeout(BaseException)     # raised by the alarm; → TIMEOUT; survives `except Exception`
```

### Registration

```
@test                                 # bare form
def test_add_basic(): ...

@test(name="...", timeout=2.0, tags=("slow",), skip=False)
def test_big_prime(): ...
```

- Decorator validates at decoration time: target is callable; `timeout` is `None` or a positive finite number; `name` (defaulting to `fn.__name__`) is **unique** → else raise `HarnessError` (reject collisions rather than silently overwrite).
- Registry is an **insertion-ordered list** of `TestCase(name, fn, timeout, tags, skip)`. Deterministic order = reproducible runs. Optional `seed`-based shuffle later, off by default.

### Assertion helpers (raise `TestFailure`, work under `-O`)

```
check(cond, msg="")            check_eq(actual, expected)      check_ne(...)
check_true(x)  check_false(x)  check_almost_eq(a, b, tol=1e-9)   # for float math
with assert_raises(ZeroDivisionError): divide(1, 0)             # context manager
```

`check_almost_eq` exists specifically because `divide` returns floats and `add` on floats is exact-equality-hostile.

### Runner

```
def run(tests=None, default_timeout=5.0, fail_fast=False,
        verbose=True, stream=sys.stdout) -> Summary
```

Per test, in order:
1. If `skip` → record `SKIP`, continue.
2. Start `perf_counter()`; arm timeout (`min(case.timeout or default_timeout)`).
3. Call the test inside `try/except`:
   - no exception → `PASS`
   - `SkipTest` → `SKIP`
   - `TestFailure`/`AssertionError` → `FAIL` (+ message)
   - `TestTimeout` → `TIMEOUT`
   - other `Exception` → `ERROR` (+ formatted traceback)
   - `KeyboardInterrupt`/`SystemExit` → **disarm alarm, re-raise** (abort run cleanly)
4. `finally`: disarm alarm, restore prior handler, record duration.
5. Stream one structured line: `STATUS  name  (12.3ms)`.
6. If `fail_fast` and status in {FAIL, ERROR, TIMEOUT} → stop.

### Summary + exit

- Print counts: `N passed, M failed, K errored, T timed out, S skipped` + total wall time.
- For each non-pass, print name, message, and traceback (errors only).
- `exit_code = 0` iff no FAIL/ERROR/TIMEOUT; else `1`. Empty registry → exit `0` **with a printed warning** ("0 tests registered") so an accidentally-empty run isn't mistaken for success.
- CLI: `if __name__ == "__main__": sys.exit(run().exit_code)`.
- **The runner never raises on a test failure** — failures are data in the `Summary`. It only raises `HarnessError` for its own misconfiguration.

---

## Ordered build steps

1. **Result model & enums** — `Status`, `TestResult`, `Summary`. Pure data, no logic.
2. **Named exceptions** — the four classes above; `TestTimeout` must subclass `BaseException`.
3. **Registry + `@test` decorator** — support bare and parameterized forms; full boundary validation; duplicate-name rejection.
4. **Assertion helpers** — `check*`, `assert_raises`, `check_almost_eq`.
5. **Timeout primitive** — a `timeout(seconds)` context manager: capability-detect POSIX + main thread; arm `setitimer`/`SIGALRM` with a handler that raises `TestTimeout`; `finally` disarms + restores. On unsupported platforms, set `Summary.degraded_timeout = True` and log it.
6. **Runner loop** — isolation, timing (`perf_counter`), exception classification, streaming output, `fail_fast`.
7. **Summary reporting + exit code** — counts, failure detail, empty-registry warning.
8. **CLI entry** in `microtest.py`.
9. **`test_mathlib.py`** — import `microtest` + `mathlib`, register the tests below.
10. **Harness self-tests** (meta) — a tiny separate module that registers known-passing, known-failing, known-erroring, and known-timing-out tests to prove the harness classifies each correctly.

---

## `test_mathlib.py` plan (incl. the deliberate failure)

| Test | Asserts | Purpose |
|---|---|---|
| `test_add_integers` | `check_eq(add(2,3), 5)` | happy path |
| `test_add_negatives` | `check_eq(add(-4,1), -3)` | sign handling |
| `test_add_floats` | `check_almost_eq(add(0.1,0.2), 0.3)` | float-equality trap, done right |
| `test_divide_exact` | `check_eq(divide(6,3), 2.0)` | true-division returns float |
| `test_divide_by_zero` | `assert_raises(ZeroDivisionError): divide(1,0)` | exception path |
| `test_is_prime_true` | `2,3,13,97` → True | positives |
| `test_is_prime_false` | `0,1,4,9,100` → False | composites + `n<2` boundary |
| `test_is_prime_negative` | `is_prime(-7)` is False | below-range |
| **`test_is_prime_one_is_prime`** | **`check_true(is_prime(1))`** | **DELIBERATE FAILURE** — `is_prime(1)` is `False`, so this raises `TestFailure`. Docstring marks it intentional. |
| `test_big_prime_timeout` *(optional, `tags=("slow",)`, `timeout=0.05`)* | `is_prime(<huge prime>)` | exercises the timeout path on demand; off by default to keep runs fast |

The deliberate failure is a `FAIL` (not an `ERROR`) — it proves the harness reports a *failed assertion* with a clear message and flips the exit code, while every other test still runs.

---

## How I'd verify the harness

1. **Classification correctness** (via the meta self-tests in step 10): one test of each kind → assert the `Summary` shows exactly `1 PASS, 1 FAIL, 1 ERROR, 1 TIMEOUT, 1 SKIP`, and that `passed+failed+errored+timedout+skipped == total`.
2. **Isolation**: place an `ERROR` test *before* a `PASS` test; confirm the later test still runs (crash didn't abort the loop).
3. **Timeout actually interrupts**: a test doing `while True: pass` with `timeout=0.1` returns `TIMEOUT` in ~0.1s, not hanging — and the *next* test still runs (alarm was disarmed, no leakage).
4. **Timeout survives `except Exception`**: a test wrapping a hang in `try/except Exception` still times out (proves `TestTimeout` is a `BaseException`).
5. **Exit code**: full `test_mathlib` run (with the deliberate failure) → exit `1`, summary names `test_is_prime_one_is_prime`. Remove/skip that test → exit `0`.
6. **Empty registry**: `run()` with nothing registered → exit `0` + the printed "0 tests" warning.
7. **`-O` robustness**: run `python -O test_mathlib.py`; the deliberate failure must *still* fail (proves no reliance on bare `assert`).
8. **Degradation visibility**: simulate non-POSIX (or run off main thread) → `degraded_timeout=True` is logged, not silently dropped.
9. **Ctrl-C**: interrupt mid-run → process exits promptly, no spurious `ERROR` entry, alarm disarmed.

---

## Risks & edge cases

- **Timeout portability** — POSIX/main-thread only; Windows unsupported under the chosen mechanism. Mitigation: capability-detect + explicit degraded mode; document subprocess as the robust upgrade.
- **Thread fallback leaks** — a timed-out watchdog thread keeps running. Mitigation: state it loudly; never claim the test was stopped.
- **C-bound loops ignore SIGALRM** until they return to the interpreter. `is_prime` is pure Python so it's fine, but the limitation is real for reused suites.
- **Same-process state pollution** — globals, cwd, monkeypatches bleed across tests. Out of scope; documented. Subprocess isolation is the fix if needed.
- **Alarm leakage / reentrancy** — must restore handler + cancel alarm in `finally`; no nested `timeout()` without save/restore.
- **`except Exception` swallowing timeouts** — addressed by `TestTimeout(BaseException)`.
- **Vacuous passes** — a test with no checks passes; harness can't detect intent. Note in docs.
- **Float equality** — `add`/`divide` return floats; tests must use `check_almost_eq`, not `check_eq`, for fractional results.
- **Duplicate test names** — rejected at registration to avoid ambiguous reports.
- **Timing precision** — use `perf_counter`, not `time.time` (monotonic, no wall-clock jumps).
- **Large traceback noise** — print full tracebacks only for `ERROR`; keep `FAIL` to the assertion message.

---

The one decision I'd want your call on before building: **should timeout enforcement be real-kill (subprocess-per-test, correct on every platform but ~10–50ms fork overhead per test and picklability constraints) or best-effort (SIGALRM on POSIX, degraded elsewhere) — i.e., do you need this harness to enforce timeouts reliably on Windows, or is a documented POSIX-only guarantee acceptable for the "small" version?**
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=3; wall=160.6s; answer_chars=12745; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
I have the grounding I need. `mathlib.py` exposes three pure functions:

- `add(a, b)` → `a + b` (polymorphic on `+`, no validation)
- `divide(a, b)` → raises `ZeroDivisionError` when `b == 0` (note: `b == 0` is also true for `0.0`), otherwise **true** division → returns a `float` (`divide(7, 2) == 3.5`)
- `is_prime(n)` → trial division up to `√n`; `n < 2` → `False`

Below is the design + implementation plan only. Nothing is implemented.

---

# Plan: A Small Reusable Test Harness + `mathlib` Tests

## 0. Failure modes I designed around first (Murphy's Law pass)

Before the API, the specific ways a naive harness silently lies or breaks — these drive every design decision below:

1. **A leftover timer fires during the *next* test or during result printing** → a passing test gets a spurious timeout/error. Mitigation: cancel the timer and restore the prior signal handler in a `finally`, every iteration.
2. **A test with a bare `except:` swallows the timeout signal** → infinite loop reported as PASS. Mitigation: documented limitation of the in-process backend; raise a dedicated exception type and note the process-isolation upgrade.
3. **`python -O` strips `assert`** → assertions vanish, everything goes green. Mitigation: ship explicit assertion *functions* (not bare `assert`) as the recommended path.
4. **Zero tests registered** → an empty suite reports "all passed," the classic CI false-green. Mitigation: empty registry is a soft failure (warn + non-zero exit).
5. **Float equality** (`divide` returns floats) → `divide(1, 3) == 0.3333…` is brittle. Mitigation: tolerance-based assert helper.
6. **Catching `BaseException`** would swallow `KeyboardInterrupt`/`SystemExit` and trap the user in a run. Mitigation: catch `Exception` (+ our timeout type); let `KeyboardInterrupt`/`SystemExit` propagate.
7. **`SIGALRM` is Unix-/main-thread-only** (fine on this Darwin host, breaks on Windows / worker threads). Mitigation: documented; pluggable timeout backend.

## 1. Harness API / Design

Two files, no third-party deps, standard library only:

- `harness.py` — registry, decorator, assertions, timeout primitive, runner, reporting, CLI.
- `test_mathlib.py` — imports `harness` + `mathlib`, registers tests, runs them.

### 1.1 Result model & statuses

```text
Status (enum-like constants): PASS, FAIL, ERROR, TIMEOUT, SKIP
TestResult (dataclass/namedtuple):
    name: str
    status: str
    duration_s: float
    exc_type: str | None
    message: str | None
    traceback: str | None   # truncated
```

Rationale for separating **FAIL vs ERROR**: `FAIL` = an `AssertionError` (the test's claim was false — expected, actionable). `ERROR` = any other unexpected exception (the test or code under test blew up). `TIMEOUT` = our timeout fired. The pass/fail summary collapses these (only `PASS` counts as good) but the breakdown tells you *why*.

### 1.2 Registration API

A decorator that supports both bare and parameterized forms and preserves **insertion order** (deterministic runs):

```text
@test                          # bare
def test_add_basic(): ...

@test(name="div by zero", timeout=0.5)   # parameterized
def test_divide_zero(): ...
```

- Registry is a module-level ordered list of `(name, fn, timeout_override)`.
- A test is a **zero-argument callable**. PASS = returns normally; non-PASS = raises.
- Duplicate names → warn and disambiguate (suffix `#2`) rather than silently clobber.
- Optional `skip=True` / `@skip(reason)` → recorded as `SKIP`, not run, not counted as failure.

### 1.3 Assertion helpers (because no unittest, and to survive `-O`)

A minimal, explicit set that raise `AssertionError` with a useful message:

```text
assert_true(cond, msg=None)
assert_equal(actual, expected, msg=None)
assert_almost_equal(a, b, tol=1e-9, msg=None)   # for divide's floats
assert_raises(exc_type, fn, *args, **kwargs)     # returns the caught exc; fails if none/wrong type
```

`assert_raises` is essential for pinning `divide(x, 0)` → `ZeroDivisionError` and `add("a", 1)` → `TypeError`. Bare `assert` is still *supported* (caught as `AssertionError`) but documented as discouraded under `-O`.

### 1.4 Timeout primitive

**Recommended default: in-process `signal.SIGALRM` via `signal.setitimer(ITIMER_REAL, seconds)`** — sub-second resolution, zero dependencies, and (the key point for this code) it *interrupts pure-Python loops* like `is_prime`'s `while i*i <= n`, which is exactly the shape of code under test.

```text
context manager: time_limit(seconds):
    install SIGALRM handler that raises TestTimeout
    setitimer(ITIMER_REAL, seconds)      # 0/None disables
    try: yield
    finally:
        setitimer(ITIMER_REAL, 0)        # cancel — ALWAYS
        restore previous handler
```

- `TestTimeout` subclasses `Exception` (not `BaseException`) so the runner catches it normally.
- Must run on the main thread (documented).

**Documented robustness upgrade (same registration API, swappable backend): `multiprocessing.Process` isolation** — each test runs in a child process, `join(timeout)` then `terminate()`. This is the only way to get *true* isolation (state leaks, segfaults, `os._exit`, bare-`except` timeout-swallowing all become survivable) and cross-platform timeouts. Cost: per-test process overhead and **picklability** (test fns must be top-level, no closures/lambdas). I recommend shipping the SIGALRM backend as default and noting the process backend as the drop-in for "hard isolation" needs.

### 1.5 Runner

```text
run_all(default_timeout=2.0, fail_fast=False, name_filter=None) -> Summary:
    results = []
    for (name, fn, t_override) in registry (in order, optionally filtered):
        if skipped: record SKIP; continue
        t0 = perf_counter()
        try:
            with time_limit(t_override or default_timeout):
                fn()
            status, exc, msg, tb = PASS, None, None, None
        except TestTimeout:        status = TIMEOUT ...
        except AssertionError as e: status = FAIL; capture msg + short tb
        except Exception as e:      status = ERROR; capture type + msg + short tb
        # KeyboardInterrupt / SystemExit deliberately NOT caught -> propagate
        finally:
            duration = perf_counter() - t0
        record TestResult; if fail_fast and not PASS: break
    return Summary(results)
```

Each test is fully wrapped → one failing test never aborts the others (**isolation of failures**). The `finally` guarantees the timer is dead before the next iteration.

### 1.6 Summary & reporting

```text
Summary:
    counts per status, total, total_duration
    exit_code property: 0 iff (total > 0 and FAIL==ERROR==TIMEOUT==0) else 1
    print_report(): one line per test, then a totals line
```

- Per-test line: `PASS  test_add_basic            (0.000s)` / `FAIL  test_divide_truediv     (0.000s)  expected 3, got 3.5`.
- Failures/errors print a **truncated** traceback (cap lines/chars) so output stays readable.
- **Empty registry → warn loudly and return exit code 1** (no false-green).
- `harness.main()` runs `run_all()`, prints the report, returns `summary.exit_code` for CI.

### 1.7 Test-module entry point

`test_mathlib.py` ends with:

```text
if __name__ == "__main__":
    import sys
    sys.exit(harness.main())   # registers-on-import, runs, exits with proper code
```

(Discovery-by-import-a-named-module is the obvious later extension; for a "small" harness, run-the-module is simpler and sufficient.)

## 2. Ordered build steps

1. ✅ **Read `mathlib.py`** (done) — pin exact behaviors, incl. true-division float return and `b == 0` covering `0.0`.
2. **Result model + status constants** in `harness.py`.
3. **Registry + `@test` decorator** (bare + parameterized, ordered, dup-name handling).
4. **Assertion helpers** (`assert_true/equal/almost_equal/raises`).
5. **Timeout primitive** (`time_limit` context manager) — build and unit-check *in isolation* first (steps 2–5 have no interdependencies and can be drafted together).
6. **Runner loop** (try/except taxonomy, `finally` timer-cancel, traceback capture, `fail_fast`).
7. **Summary aggregation + `print_report` + `exit_code`** (empty-registry guard).
8. **`main()` CLI** glue.
9. **`test_mathlib.py`**: passing tests for `add`, `divide`, `is_prime` + **one deliberate failure**.
10. **Run, read the report, confirm** the deliberate failure shows as `FAIL` and exit code is `1`.

## 3. Test cases for `mathlib` (incl. the deliberate failure)

**`add`** — `add(2,3)==5`; `add(-1,1)==0`; `add(2.5,0.5)==3.0`; `assert_raises(TypeError, add, "a", 1)` (pins the no-validation boundary).

**`divide`** — `divide(6,3)==2.0`; `assert_almost_equal(divide(1,3), 0.333333333, tol=1e-6)`; `assert_raises(ZeroDivisionError, divide, 1, 0)`; and a note-test that `divide(1, 0.0)` *also* raises.

**`is_prime`** — true: `2, 13, 7919`; false: `0, 1, -7, 9, 15`.

**Deliberate failure (one, clearly commented):** assert `assert_equal(divide(7, 2), 3)`. This both (a) reliably produces a `FAIL` to prove the harness reports failures, and (b) doubles as documentation of the true-division pitfall (actual `3.5`). The failure message will read `expected 3, got 3.5`, making the demonstration self-explanatory.

## 4. How I would verify the harness

**Meta-tests (harness testing itself)** — a tiny self-test module exercising each runner branch, since the deliberate failure only proves the `FAIL` path:

- Passing test → `PASS`.
- `raise ValueError` → `ERROR` (not FAIL).
- `assert_true(False)` → `FAIL`.
- `time.sleep(5)` with `timeout=0.2` → `TIMEOUT` in ~0.2s, **and the very next fast test still PASSes** (proves the timer was cancelled and isolation holds).
- `is_prime(10**18)`-style CPU loop with a small timeout → `TIMEOUT` (proves SIGALRM interrupts pure-Python loops, not just `sleep`).
- Run the suite **twice in one process** → identical results (proves handler restoration, no state bleed).
- Empty registry → warning + exit code `1`.

**Acceptance run:** execute `python test_mathlib.py`; expect all `mathlib` tests `PASS` except the one deliberate `FAIL`, a correct totals line, and **process exit code `1`**. Then flip the deliberate failure to the correct assertion and confirm exit code `0` — proving the pass path and that the harness isn't stuck-red.

**Observability check:** confirm each result carries a non-zero/zero-but-sane `duration_s`, the failing line's truncated traceback is present, and ordering matches registration order.

## 5. Risks & edge cases (and how the plan handles each)

| Risk / edge case | Handling |
|---|---|
| Leftover alarm fires during next test/printing | `setitimer(0)` + restore handler in `finally` every iteration |
| Test with bare `except:` swallows timeout → false PASS | Documented limit of in-process backend; process-isolation backend immune |
| `python -O` strips `assert` | Ship assert *functions*; document the `-O` caveat |
| Float equality on `divide` | `assert_almost_equal(tol=…)` |
| Catching `BaseException` traps Ctrl-C | Catch `Exception` + `TestTimeout` only; let `KeyboardInterrupt`/`SystemExit` propagate |
| `SIGALRM` is Unix/main-thread-only | Default works on this Darwin host; pluggable process backend for Windows/threads; documented |
| Empty suite reads as green | Empty registry → warn + exit `1` |
| Test mutates global/shared state → leaks to next test | In-process has no state isolation — documented "tests must be independent"; process backend gives true isolation |
| Segfault / `os._exit` / `sys.exit` inside a test | Kills in-process runner — only the process backend survives it; called out explicitly |
| Blocking C call holding the GIL | SIGALRM may not interrupt until a bytecode boundary; documented; process backend can `terminate()` |
| Duplicate test names | Warn + disambiguate, never silently overwrite |
| Picklability (only if process backend chosen) | Require top-level test fns; no lambdas/closures; documented |
| Huge traceback/message floods output | Truncate captured tracebacks to a line/char cap |
| Nested/concurrent runners share one `ITIMER_REAL` | Harness documented as single-threaded, one-runner-at-a-time |

---

The single most dangerous unhandled case I'd want your call on before building: **if a test under the default in-process backend catches our `TestTimeout` (e.g., a broad `except Exception:` inside the test) or hard-crashes the interpreter, the harness will either mis-report it as PASS or die entirely** — do you want the default backend to stay the lightweight SIGALRM one (small, fast, but trusts tests not to swallow signals or segfault), or should I make the **process-isolation backend the default** and accept the per-test overhead and picklability constraints in exchange for a harness that survives anything a test throws at it?
````

### Candidate C

Behavioral telemetry: exit=-9; timed_out=True; turns=None; wall=200.0s; answer_chars=0; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
(empty answer)
````
