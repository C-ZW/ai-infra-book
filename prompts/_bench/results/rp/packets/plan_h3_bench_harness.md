# Judge packet — task `plan_h3_bench_harness` (medium/hard, tool)

## The task given to each candidate

> Produce a design + implementation plan — do NOT implement anything, output only the plan. Task to plan: a benchmark harness that runs candidate functions against shared inputs, enforces a per-call timeout, captures exceptions as failures without crashing, times successful calls, and prints a comparison table; demonstrated on candidates.py (one candidate hangs on some inputs). Read candidates.py to ground the plan. Cover: the harness design, how timeouts and exception isolation work, ordered steps, verification, and risks.

## What to reward / penalize

PLAN QUALITY for a robust benchmark harness (anxious-engineer dimensions). A strong plan specifies the timeout MECHANISM (and why — slow_sum_to hangs for n<0, so a thread/process or signal-based hard timeout is required; a plain try/except will NOT catch a hang), exception isolation per call, timing of successes only, and the table format. It should note that slow_sum_to(-1) infinite-loops and must be timed out, and flag parallel-safety. Must stay at plan altitude. Penalize ignoring the hang/timeout problem, no isolation story, or implementing instead of planning.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=3; wall=192.0s; answer_chars=13439; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
I've read `candidates.py`. Here's the plan, grounded in what that file actually does.

---

# Benchmark Harness — Design & Implementation Plan

## 1. What `candidates.py` tells us (the facts that drive the design)

```
fast_sum_to(n) = n*(n+1)//2          # closed form, O(1), correct for all n incl. negatives
slow_sum_to(n) = while i != n: ...   # O(n) loop; CORRECT for n>=0, INFINITE LOOP for n<0
CANDIDATES  = [fast_sum_to, slow_sum_to]
TEST_INPUTS = [0, 1, 10, 100, -1]
```

Concrete per-cell expectation the harness must reproduce:

| input | `fast_sum_to` | `slow_sum_to` |
|---|---|---|
| 0 | `0` (OK) | `0` (OK) |
| 1 | `1` (OK) | `1` (OK) |
| 10 | `55` (OK) | `55` (OK) |
| 100 | `5050` (OK) | `5050` (OK) |
| **-1** | `0` (OK) | **HANG → must TIMEOUT** |

Three design-critical properties fall out of this:
- The hang is a **CPU-bound pure-Python infinite loop**, not an I/O wait or `sleep`. The timeout mechanism must be able to stop *that*.
- The hang also slowly **grows memory** — `i` and `total` are unbounded Python ints incrementing forever. A long timeout risks OOM, not just wasted time.
- Both candidates share one contract, so the harness can do a **cross-candidate output agreement check** for inputs where more than one succeeds (here they agree on 0/1/10/100; `-1` is undecidable because `slow` never produces a value).

Candidates are clean module-level functions with no import-time side effects — important for the process-based approach below.

## 2. Failure modes first: how do you actually stop an infinite loop?

This is the crux. The naive answers all have sharp edges:

| Mechanism | Stops a pure-Python infinite loop? | Critical failure mode |
|---|---|---|
| `signal.SIGALRM` / `setitimer` | Yes (signals checked between bytecodes) | **Main-thread + Unix only**; one timer at a time; a candidate with a bare `except:` around its loop *swallows the timeout exception and keeps hanging*; cannot contain a native segfault or `os._exit`; the interrupted candidate's partial state stays in-process. |
| `threading.Thread` + `join(timeout)` | "Returns" but **cannot kill the thread** | The hung thread **lives on, burning CPU and holding the GIL**, which *corrupts the timing of every subsequent measurement* — fatal for a benchmark specifically. |
| `ProcessPoolExecutor` + `future.result(timeout)` | Raises `TimeoutError` | Does **not** kill the worker; pool can starve/deadlock as workers get permanently stuck. |
| **`multiprocessing.Process` per call + `terminate()`/`kill()`** | **Yes — the OS actually reclaims the CPU and memory** | Heavier (spawn cost, pickling, IPC), and has its own subtle pitfalls (Queue-drain deadlock, spawn re-import) — all manageable and enumerated in §8. |

**Decision: one fresh `multiprocessing.Process` per `(candidate, input)` call, killed on timeout.** It is the only option that genuinely terminates the CPU-bound hang, prevents zombie work from contaminating later timings, contains native crashes, and can't be defeated by a candidate's own `except:`. I'll provide a **SIGALRM-based fallback runner** as a lighter, optional mode for trusted single-threaded use, but the process runner is the default and the one demonstrated.

## 3. Harness design

### 3.1 Module layout (candidates.py stays untouched)
- `harness.py` — runner, result model, table renderer, `if __name__ == "__main__":` demo wiring against `candidates.py`.
- `test_harness.py` — verification suite with synthetic candidates (see §6).

### 3.2 Data model
```
class Status(enum.Enum): OK, FAIL, TIMEOUT, CRASH, HARNESS_ERROR

@dataclass(frozen=True)
class CallResult:
    candidate: str
    input_repr: str
    status: Status
    value: Any = None            # OK only (repr-truncated for table)
    duration_s: float | None = None   # OK only, measured INSIDE the child
    exc_type: str | None = None  # FAIL
    exc_msg: str | None = None   # FAIL
    traceback: str | None = None # FAIL (kept off the table, available for logs)
    detail: str | None = None    # TIMEOUT: limit; CRASH: exitcode/signal
```
Five statuses, not three: `CRASH` (child died with no result — segfault / OOM-kill / `os._exit`) and `HARNESS_ERROR` (pickling failure, etc.) are distinct from a candidate's clean `FAIL`. Collapsing them would hide real problems.

### 3.3 Core API
```
def run_one(fn, arg, *, timeout_s, repeats=1) -> CallResult
def run_matrix(candidates, inputs, *, timeout_s, repeats=1, oracle=None) -> list[CallResult]
def render_table(results, candidates, inputs) -> str
```
Execution is **sequential** (one child alive at a time). Parallelism is deliberately rejected: concurrent CPU-bound children would contaminate each other's timing, which defeats the benchmark's purpose.

### 3.4 Timeout mechanism (the careful part)
Worker target, run in the child:
```
def _worker(fn, arg, q):
    try:
        t0 = perf_counter(); val = fn(arg); dt = perf_counter() - t0
        q.put(("OK", _safe_repr(val), dt))      # small payload only
    except Exception as e:                        # NOT BaseException
        q.put(("FAIL", type(e).__name__, str(e), format_exc()))
    # any escape (segfault/os._exit) => nothing on q => parent infers CRASH
```
Parent control flow — **order matters to avoid the classic Queue deadlock**:
```
p.start()
try:
    payload = q.get(timeout=timeout_s)   # 1) DRAIN FIRST, with timeout
except queue.Empty:
    payload = None                        # timed out (or crashed)
p.join(timeout=GRACE)                      # 2) reap
if p.is_alive():
    p.terminate(); p.join(GRACE)           # 3) SIGTERM
if p.is_alive():
    p.kill(); p.join()                     # 4) SIGKILL escalation
# 5) classify: payload? -> OK/FAIL ; else if exitcode<0 -> CRASH(signal) ;
#    else if still alive after kill -> CRASH(unkillable) ; else -> TIMEOUT
```
Key points:
- **Drain the queue with `get(timeout=...)` *before* `join`.** Joining first while a large object sits in the queue's feeder buffer is the textbook multiprocessing deadlock. We only ever put tiny payloads, but we still order it correctly and never block unbounded.
- **Timing is measured inside the child** around the bare call, so process-spawn and IPC overhead are excluded from the reported `duration_s`.
- **Kill escalation** terminate → kill → report-unkillable means a candidate that ignores SIGTERM still gets SIGKILLed; if even that fails we report `CRASH(unkillable)` rather than hanging the harness.
- A `try/finally` at the matrix level calls `terminate()` on any `active_children()` — so Ctrl-C or an exception never leaves orphaned hung processes.
- `repeats>1` reports the **min** of N timings (standard noise-reduction), but a TIMEOUT/CRASH **short-circuits** — we never pay the timeout N times for a hang.

### 3.5 Exception isolation
- Catch `Exception` (so `KeyboardInterrupt`/`SystemExit` stay uncaught and Ctrl-C still works), record type name, message, and full `traceback.format_exc()`.
- The traceback is stored but kept out of the table (shown via a `--verbose`/footnote) so the table stays readable.
- Because each call is in its own process, a `FAIL` — even a native crash — cannot take down the harness. That is the "without crashing" requirement, enforced structurally rather than by hope.

### 3.6 Correctness cross-check
For each input, among candidates that returned `OK`, compare values. If they disagree, flag the input (e.g. a `*` marker + a "disagreement" note). Optional `oracle=fn` (e.g. the closed form) lets the harness mark a specific candidate *wrong* rather than just "in disagreement." For this demo all OK results agree, and `-1` is unverifiable (only `fast` produces a value) — the report should say so explicitly rather than imply agreement.

### 3.7 Table rendering
- Pure stdlib fixed-width formatting (no `rich`/`tabulate` dependency); rows = inputs, columns = candidates, cells = `12.3µs` / `TIMEOUT(2.0s)` / `FAIL(ZeroDivisionError)` / `CRASH(SIGKILL)`.
- A summary block per candidate: `#OK / #FAIL / #TIMEOUT / #CRASH`, total and mean time over OK calls.
- Long return reprs are truncated (`_safe_repr`, cap length) so one pathological value can't blow up the layout.
- Optional `--format csv|json` for machine consumption (timing data is more useful structured).

### 3.8 Config / defaults
- `timeout_s = 2.0` (default). Rationale: `slow_sum_to(100)` is microseconds, so 2s never false-positives a real result; `slow_sum_to(-1)` will reliably exceed it. **Note: each timeout costs the full `timeout_s` of wall-clock** — the demo run takes ~2s, dominated by the one hanging cell.
- `repeats = 1` default; `mp.get_context("spawn")` used explicitly (macOS default anyway) for determinism.

## 4. Ordered implementation steps
1. Define `Status` + `CallResult` (§3.2).
2. Implement `_worker` and `_safe_repr` (small, picklable payloads only).
3. Implement `run_one` with the drain-then-join-then-escalate control flow and full status classification (§3.4).
4. Implement `run_matrix` (sequential, `try/finally` orphan cleanup, repeats short-circuit, optional oracle).
5. Implement `render_table` + summary + disagreement markers.
6. Wire `if __name__ == "__main__":` to import `candidates.CANDIDATES`/`TEST_INPUTS` and print the table. **The `__main__` guard is mandatory** — without it, spawn re-importing the module would recursively launch the harness.
7. (Optional) Add the SIGALRM fallback runner behind a flag, with its limitations documented in-code.
8. Write `test_harness.py` (§6).

## 5. Verification
**Synthetic candidates** (don't rely only on the demo): `lambda` rejected-by-design, plus module-level `ok(n)`, `boom(n)` (raises `ValueError`), `hang(n)` (`while True: pass`), `wrong(n)` (returns a bad value to trip the disagreement check), `crasher(n)` (`os._exit(1)` → CRASH), `slow_but_ok(n)` (`sleep(0.1)`, under timeout). Assert each lands in the right `Status`.

**Against `candidates.py`:** assert `fast_sum_to` is OK on all five inputs with the exact values `[0,1,10,55? no →]` — i.e. `0,1,55,5050,0`; assert `slow_sum_to` is OK on `0/1/10/100` with `0,1,55,5050` and **TIMEOUT** on `-1`; assert `fast` timing ≪ `slow` at `n=100`; assert agreement holds where both OK.

**Harness-health checks (anxious-engineer essentials):**
- After the full run, assert `multiprocessing.active_children() == []` — no leaked processes.
- `ps`/exit-code check that the killed `slow_sum_to(-1)` child is actually gone and CPU returns to idle (proves the loop was *killed*, not just abandoned).
- Harness process exits `0` and prints the table within ~`timeout_s + ε`.
- Run on this macOS box specifically (spawn start method) to catch pickling/import-guard issues.

## 6. Risks & mitigations
1. **Queue-drain deadlock** — join-before-drain on a full feeder buffer hangs forever. → Drain with `get(timeout)` first; only tiny payloads ever sent (§3.4).
2. **Unkillable child** — SIGTERM-ignoring or uninterruptible-syscall candidate. → Escalate to SIGKILL; if still alive, report `CRASH(unkillable)` and move on, never block.
3. **spawn re-import / fork-bomb** — missing `__main__` guard or import-time side effects re-execute in every child. → Mandatory guard; candidates.py is verified side-effect-free; document the constraint.
4. **Pickling failures** — non-picklable candidate (closure/lambda), arg, or return value. → Distinct `HARNESS_ERROR` status; result `repr`'d in-child so an unpicklable *return* still reports.
5. **Timing contamination** — counting spawn/IPC, GC pauses, scheduler jitter, CPU scaling. → Measure inside child around the bare call; sequential execution; `repeats`+min; document single-sample noise.
6. **Memory growth during hang** — `slow_sum_to(-1)` grows unbounded ints; a long timeout could OOM the box. → Process isolation bounds blast radius; if the OS OOM-kills the child we correctly surface `CRASH`, not a frozen harness. Keep `timeout_s` modest.
7. **Oversized return value** — a candidate returning a huge object blows up pickle/Queue/table. → `_safe_repr` truncation; small-payload contract; guard the `q.put` in a try/except → `HARNESS_ERROR`.
8. **Ctrl-C mid-run** — orphaned hung children survive the harness. → matrix-level `try/finally` terminates all `active_children()`.
9. **Cost of timeouts** — wall-clock ≈ Σ timeouts; many hanging cells = slow run. → `log` the count of timed-out cells; never multiply by `repeats`.
10. **False correctness confidence** — harness can flag *disagreement* but cannot declare *correctness* without an oracle; `-1` is unverifiable here. → State this explicitly in the report; offer optional `oracle=`.
11. **Portability** — SIGALRM fallback and negative-exitcode→signal decoding are Unix-only. → Fine on this macOS target; documented; process runner is the portable-enough default.

## 7. Assumptions (sensible defaults, tunable)
- Default `timeout_s = 2.0`, `repeats = 1`, sequential execution, `spawn` context, plain-text table. None of these block the plan; all are flags.

---

The single most dangerous unhandled case I'd want your call on: if a candidate's infinite loop **also ignores SIGTERM** (e.g. it installs its own handler or is wedged in an uninterruptible state), my plan escalates to `SIGKILL` and, failing even that, reports `CRASH(unkillable)` and continues — but should the harness instead **abort the entire run loudly** when a child proves unkillable, on the theory that an unkillable process means the machine's state is no longer trustworthy for the remaining measurements?
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=3; wall=132.4s; answer_chars=11137; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
Read it. Now I have what I need to ground the plan.

# Design + Implementation Plan: Benchmark Harness

## 1. Goal & contract

Build a harness that takes a list of candidate functions and a list of shared inputs, calls each `candidate(input)` under a hard per-call timeout, records the outcome as one of `{ok, timeout, error, crashed}`, times only the successful calls, and prints a comparison table — and never lets a single misbehaving candidate hang or crash the harness itself.

Demonstrated against `candidates.py` (`fast_sum_to`, `slow_sum_to`, `TEST_INPUTS = [0, 1, 10, 100, -1]`).

## 2. What `candidates.py` actually forces (grounding the design)

The crux is in `slow_sum_to`:

```python
while i != n:   # i starts at 0 and only increments
```

For `n = -1` this is a **pure-CPU infinite loop** — no `sleep`, no I/O, no syscall, no checkpoint where the function voluntarily yields. This single fact eliminates the two "easy" timeout mechanisms (see §3) and drives the whole design. Expected per-input behavior the harness must produce:

| call | expected |
|---|---|
| `fast_sum_to(-1)` | `-1*0//2 = 0`, OK (fast path has no loop, doesn't hang) |
| `slow_sum_to(0/1/10/100)` | OK → `0/1/55/5050` |
| `slow_sum_to(-1)` | **must be killed by timeout**, recorded as `timeout`, harness keeps going |

So the demo's correctness hinges entirely on the timeout mechanism genuinely *terminating* a runaway loop, not just abandoning it.

## 3. Isolation mechanism — the key decision

Three candidate mechanisms; the infinite pure-CPU loop is the discriminator:

| Mechanism | Kills `slow_sum_to(-1)`? | Failure mode | Verdict |
|---|---|---|---|
| `threading.Thread` + `join(timeout)` | **No** — Python threads can't be force-killed; the loop runs forever as a leaked (daemon) thread, contending for the GIL and skewing every later measurement | Silent resource leak; timings degrade over the run | Reject |
| `signal.SIGALRM` + handler raising | Yes *here* (signals are checked between bytecodes in pure Python) | Main-thread-only, Unix-only, one timer at a time; cannot interrupt C-extension/blocking calls; fragile if a candidate installs its own handler | Reject as primary |
| **`multiprocessing.Process` per call + `join(timeout)` → `terminate()` → `kill()`** | **Yes, reliably** — SIGTERM/SIGKILL reclaim the core regardless of what the child is doing | Pickling constraints + spawn overhead (mitigated, see §6/§10) | **Choose** |

**Decision: one fresh child process per call.** It's the only option that truly kills a runaway loop *and* isolates hard crashes (segfault / `os._exit` / OOM) so they can't take down the harness — exactly the "capture failures without crashing" requirement. Cost is process-spawn + IPC overhead, which we keep out of the reported timings by measuring inside the child.

Note: a `ProcessPoolExecutor` + `future.result(timeout)` is explicitly **not** used — on timeout the future raises but the worker keeps running and the pool wedges. A disposable process we own lets us `terminate()` it.

## 4. Harness architecture

Single new file, e.g. `benchmark.py`, importing nothing from `candidates.py` except via the public lists (`CANDIDATES`, `TEST_INPUTS`). Components:

- **`run_one(func, arg, timeout) -> Result`** — spawns a child, runs the call, enforces timeout, returns a structured `Result`. Pure, no printing.
- **child worker `_worker(func, arg, conn)`** — runs in the child: times the call with `perf_counter`, wraps in try/except, sends back a result payload over a `Pipe`. Never raises into the parent.
- **`benchmark(candidates, inputs, timeout, repeats=1) -> list[Result]`** — nested loop over `(candidate, input)`, collects results, guarantees cleanup.
- **`format_table(results) -> str`** — renders the comparison table from results only (no recomputation).
- **`main()`** under `if __name__ == "__main__":` — wires `candidates.py` lists in, picks a timeout, prints the table. The guard is mandatory (see §6, spawn).

## 5. Data model

One explicit result record per call — no tuples-by-position, no `None`-means-many-things:

```
Result:
  candidate: str        # func.__name__
  arg: repr(arg)
  status: "ok" | "timeout" | "error" | "crashed"
  elapsed_s: float | None   # set only when status == ok
  value_repr: str | None    # repr of return value, ok only
  error_type: str | None    # exception class name, error only
  error_msg: str | None     # short message, error only
  exitcode: int | None      # for crashed (segfault → negative signal)
```

`status` is a closed set decided on purpose; the table renderer switches on it exhaustively.

## 6. Timeout + exception isolation mechanics (precise)

**Per call:**
1. Create a `multiprocessing.Pipe()` (or `Queue`). Start `Process(target=_worker, args=(func, arg, child_conn))`.
2. Parent `proc.join(timeout)`.
3. **If `proc.is_alive()` after join → timeout path:** `proc.terminate()` (SIGTERM); `proc.join(grace=~0.5s)`; if still alive, `proc.kill()` (SIGKILL); final `join()` to reap (no zombies). Record `status=timeout`. This is what catches `slow_sum_to(-1)`.
4. **Else child finished → drain the pipe:**
   - payload present and `status=ok` → record value + elapsed (measured in child).
   - payload present and `status=error` → record `error_type/error_msg` (candidate raised; captured, not propagated).
   - **no payload but exitcode ≠ 0 → `status=crashed`** (segfault, `os._exit`, OOM-kill, pickling-result failure). Record `exitcode`. This is the path that keeps a C-level crash from taking down the harness.
5. Always close pipe ends; the whole step sits in `try/finally` that force-kills any still-alive child so a harness exception can't orphan a process.

**Inside the child (`_worker`):** time `t0 = perf_counter()`, call `func(arg)`, `t1 = perf_counter()`; on success send `{ok, value, t1-t0}`; on `except BaseException as e` send `{error, type(e).__name__, str(e)}`. Wrap the *send* in its own try/except so an unpicklable return value degrades to a `crashed`/`error` record instead of a silent hang. Timing covers only the call — spawn, import, and IPC are excluded, keeping `fast_sum_to`'s microsecond timings honest.

**Spawn safety (macOS/Windows default = `spawn`):** the child re-imports the runner module, so `main()` **must** be under `if __name__ == "__main__":`; otherwise spawn recursively forks the harness. Candidates and inputs must be top-level importable/picklable — `fast_sum_to`, `slow_sum_to`, and the int inputs all satisfy this; document the constraint for future candidates (no lambdas/closures). Set the start method explicitly (`get_context("spawn")`) so behavior is identical across macOS/Linux rather than depending on the platform default.

## 7. Comparison table

Primary output = candidate × input matrix; cell shows `elapsed` for ok, `TIMEOUT`, `ERR:<Type>`, or `CRASH(<code>)`:

```
candidate       n=0        n=1        n=10       n=100      n=-1
fast_sum_to     0.4µs      0.4µs      0.4µs      0.4µs      0.4µs
slow_sum_to     0.8µs      0.9µs      2.1µs      14µs       TIMEOUT
```

Plus a per-candidate summary line: `# ok`, `# timeout`, `# error`, `# crashed`, total/mean time over ok calls. Renderer computes column widths from the data and never indexes a `None` — every non-ok cell is a label, so a fully-failing candidate still prints a clean row.

## 8. Ordered implementation steps

1. Create `benchmark.py` with the `Result` dataclass and the `status` enum/constants.
2. Implement `_worker` (child side): timed call, exception capture, safe send.
3. Implement `run_one`: spawn, `join(timeout)`, terminate→kill escalation, pipe drain, exitcode→`crashed` mapping, `try/finally` cleanup.
4. Implement `benchmark`: loop over `(candidate, input)`, optional `repeats` (best-of-N), collect `Result`s.
5. Implement `format_table` + summary, switching exhaustively on `status`.
6. Implement `main()` under `__main__` guard: import `CANDIDATES`/`TEST_INPUTS`, set `timeout` (e.g. 1–2 s), force `spawn` context, print table.
7. Add synthetic test candidates in a separate test module: a raiser (`ValueError`), a fast control, and (optionally) a `ctypes`/`os._exit` crasher — to exercise `error` and `crashed` paths without depending on the demo file.

## 9. Verification

- **Demo run:** `python benchmark.py` exits 0; table shows `fast_sum_to` all OK (incl. `n=-1 → 0`), `slow_sum_to` OK for `0/1/10/100` with values `0/1/55/5050`, `TIMEOUT` for `-1`.
- **No leaks:** capture `ps` child count before/after (or `multiprocessing.active_children()` is empty at exit); confirm the `slow_sum_to(-1)` child is gone, not lingering.
- **Wall-clock sanity:** total runtime ≈ one timeout (only the single hang pays it), not 5×; `fast` ≪ `slow` for `n=100`.
- **Path coverage (synthetic):** raiser → `error` row with `ValueError`; crasher → `crashed` with negative exitcode; harness still finishes and prints.
- **Unit tests:** `run_one` against `lambda x: x` (ok — defined at top level for picklability), a sleeper longer than timeout (timeout), a raiser (error). Assert `status` and that `elapsed_s` is set only for ok.
- Confirm reproducibility across two runs (statuses stable; timings within order of magnitude).

## 10. Risks & mitigations

- **Spawn recursion** if `__main__` guard is missing → harness fork-bomb. *Mitigation:* guard + explicit `spawn` context; called out in §6 as non-negotiable.
- **Non-picklable candidate/arg/return** (lambdas, closures, open handles) → child can't start or can't reply. *Mitigation:* document top-level-only constraint; catch send failures in child → degrade to `error`/`crashed`, never hang.
- **`terminate()` insufficient** (child ignores SIGTERM / uninterruptible) → escalate to `kill()` after grace, then `join()` to reap; final `finally` sweep kills survivors.
- **Spawn overhead dwarfs fast functions** (ms-scale spawn vs µs-scale `fast_sum_to`) → measure *inside* the child so reported time is call-only; note in output that cross-process overhead is excluded. Optionally `repeats`/best-of-N for stability.
- **Orphaned processes if the harness itself throws** mid-loop → all spawning wrapped in `try/finally` cleanup.
- **Timer skew under load** (busy machine inflates timings, or delays the join) → timeout is a generous bound (≥1 s) well above real call times; report is comparative, not absolute SLA.
- **Platform variance** (SIGALRM-style assumptions, fork-vs-spawn differences) → process approach + pinned `spawn` context removes main-thread/Unix-only constraints.
- **Silent misclassification** (a slow-but-correct call near the timeout boundary flips to `timeout`) → keep timeout comfortably above observed `slow_sum_to(100)`; surface the chosen timeout in the table header so a near-boundary result is interpretable.

---

The most dangerous unhandled case I'd want your call on before building: if a candidate spawns its *own* child processes or threads, `terminate()`/`kill()` on the worker won't reap that grandchild tree — do you want the harness to run each call in a new **process group** and signal the whole group (so descendants die too), or is single-process termination an acceptable scope limit for this benchmark?
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=4; wall=146.4s; answer_chars=11864; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
I have what I need. Here's the plan, grounded in the actual `candidates.py`.

---

# Plan: Benchmark Harness with Per-Call Timeout & Exception Isolation

## 1. What the target file actually contains (grounding)

`candidates.py` (24 lines) defines:

- `fast_sum_to(n) = n*(n+1)//2` — O(1), correct for **all** ints incl. negatives (`-1 → 0`).
- `slow_sum_to(n)` — `while i != n: i += 1` from `i=0`. Correct for `n ≥ 0`; **infinite loop for `n < 0`** because `i` only ever increases and never reaches a negative target. Pure-Python loop (no C extension, no syscall).
- `CANDIDATES = [fast_sum_to, slow_sum_to]`
- `TEST_INPUTS = [0, 1, 10, 100, -1]`

The harness must execute the 2×5 = 10 calls. Nine return quickly; `slow_sum_to(-1)` spins forever. This single hang is the entire reason the harness exists, so the timeout mechanism is the load-bearing design decision — everything else is plumbing.

Critical fact for the design: the hang is a **tight pure-Python CPU loop**. That rules out some timeout mechanisms (see §3).

## 2. Failure-mode analysis first (what can break)

Before the happy path, here's what a naive harness gets wrong:

| # | Failure mode | Consequence | Mitigation |
|---|---|---|---|
| F1 | Run candidate in-line | `slow_sum_to(-1)` hangs the whole harness; no table ever prints | Out-of-line execution with a hard timeout |
| F2 | Use a thread + `join(timeout)` | Python threads **cannot be killed**; the runaway loop keeps burning a core, steals the GIL, and **corrupts every subsequent timing** | Use a **separate OS process** that can be `terminate()`/`kill()`-ed |
| F3 | Use `ProcessPoolExecutor` + `future.result(timeout=)` | Timeout doesn't cancel the running task — the worker stays stuck on the infinite loop and **poisons the pool** for later calls | **Fresh `Process` per call**, not a pool |
| F4 | `signal.SIGALRM` only | Main-thread + Unix only; a broad `except Exception` in the candidate can **swallow the timeout**; no crash isolation | Acceptable as a lightweight fallback, not the primary path |
| F5 | `spawn` start method re-imports the module | If module top-level isn't `__main__`-guarded, **fork-bomb** of re-spawning processes | Guard entrypoint; keep target functions importable/picklable |
| F6 | SIGTERM ignored by child | Child lingers as a zombie consuming CPU | Escalate `terminate()` → grace period → `kill()` |
| F7 | Harness itself crashes/Ctrl-C mid-run | Orphaned child processes survive | `try/finally` reaper that terminates all live children |
| F8 | Time the call *including* process spawn | Fast O(1) function looks ~10–50ms slow; comparison is meaningless | Measure **inside the child** with `perf_counter`, send elapsed back; spawn cost excluded |
| F9 | Queue read ordering / large payloads | Classic `multiprocessing.Queue` join-deadlock | Read result from `Pipe`/`Queue` **before** final `join`; payloads here are tiny |
| F10 | Crown a fast-but-wrong candidate | Harness times but never checks correctness | Optional oracle column: compare each result to a reference |
| F11 | Treat "timeout" as a fixed property of the candidate | It's **data-dependent** (`slow_sum_to` is fine at `n=100`, hangs at `n=-1`) | Status is per (candidate, input) cell, never per candidate |

## 3. Timeout mechanism — decision

**Primary: one `multiprocessing.Process` per call, killed on timeout.** This is the only option that (a) actually stops a tight pure-Python loop, (b) isolates crashes (a segfault/OOM/`os._exit` in a candidate won't take the harness down), and (c) keeps timings clean by measuring inside the child.

Flow per call:
1. Parent creates a `Pipe` (or `Queue`) and a `Process(target=_run_in_child, args=(fn, x, conn, repeats))`.
2. Child: `t0 = perf_counter()`; call `fn(x)` (optionally `repeats` times, keep min); on success send `("OK", result, elapsed)`; on exception send `("ERROR", exc_type_name, repr(exc))` — **not** the exception object or traceback (tracebacks aren't picklable).
3. Parent: `proc.join(timeout)`.
   - Alive after timeout → `terminate()`, `join(grace=0.2s)`, still alive → `kill()`, `join()` → record `TIMEOUT`.
   - Exited → read message from pipe with a short `poll(timeout)`; map to `OK`/`ERROR`. If the process died with no message (e.g. SIGKILL/segfault), record `CRASHED` with exit code.
4. `finally`: ensure the process is reaped and the pipe closed.

Start method: use an explicit context. **`fork` on Linux** (fast, no re-import, fine because the harness is single-threaded at fork time); **`spawn` on macOS/Windows** (required) which needs the `if __name__ == "__main__":` guard and picklable module-level targets — `fast_sum_to`/`slow_sum_to` already qualify.

**Lightweight alternative (documented, not default): `signal.setitimer(ITIMER_REAL)` + `SIGALRM`.** Single-process, ~zero overhead, ideal for sub-millisecond timing fidelity. Works here because the loop is pure Python (the handler fires between bytecodes and raises). But it's Unix/main-thread-only, swallowable by a broad `except`, and gives no crash isolation. Offer it behind a `--mechanism={process,signal}` flag; default `process`.

## 4. Harness design

Single new file `bench.py` (keep `candidates.py` untouched). Pure standard library — `multiprocessing`, `time`, `signal` (fallback), `argparse`, `dataclasses`. No third-party deps (none are present in the project; don't introduce any).

### Data model
```
@dataclass
class CallResult:
    candidate: str        # fn.__name__
    input_repr: str       # repr(x), for display
    status: str           # "OK" | "TIMEOUT" | "ERROR" | "CRASHED"
    elapsed_s: float|None # child-measured, None unless OK
    value_repr: str|None  # repr(return), None unless OK
    detail: str|None      # exc type/message, exit code, etc.
```

### Core functions
- `run_one(fn, x, timeout, repeats, mechanism) -> CallResult` — the isolated single-call runner (§3). All timeout/exception handling lives here; it **never raises** to the caller — every outcome becomes a `CallResult`.
- `run_matrix(candidates, inputs, timeout, repeats, mechanism) -> list[CallResult]` — nested loop, prints each row as it completes (flush) so a hang shows progress, with a `finally` reaper.
- `validate(results, reference_name) -> results` *(optional, F10)* — for each input, compare `OK` values against the reference candidate; annotate mismatches as a `MISMATCH` flag.
- `format_table(results) -> str` — render.
- `main()` — argparse (`--timeout`, `--repeats`, `--mechanism`, `--module`), import candidates, run, print; guarded by `if __name__ == "__main__":`.

### Boundary validation (Anxious Engineer non-negotiable)
- `timeout > 0` and finite; reject `0`/negative/NaN.
- `repeats >= 1`.
- Each candidate is `callable`; `CANDIDATES`/`TEST_INPUTS` exist and are non-empty lists — fail fast with a clear message, not an `IndexError` mid-run.
- `mechanism` ∈ {process, signal}; if `signal` requested off the main thread or on Windows → refuse with explanation, don't silently mis-time.

### Table format (monospace, right-aligned numerics)
A **status+time matrix** (candidates × inputs) is the most readable for 2×5:

```
candidate      n=0       n=1       n=10      n=100     n=-1
-----------    -------   -------   -------   -------   ---------
fast_sum_to    0.42µs    0.41µs    0.40µs    0.41µs    0.40µs
slow_sum_to    0.9µs     1.1µs     3.8µs     31µs      TIMEOUT
```
Plus a per-candidate summary line (count OK / TIMEOUT / ERROR, total & mean time over OK cells). Rules: fixed-precision human units (ns/µs/ms/s auto-scale), right-align, render `None` as the status word (`TIMEOUT`/`ERROR`/`CRASHED`), never blank. If `validate` is on, suffix mismatched cells with `!`.

## 5. Ordered implementation steps

1. **Scaffold** `bench.py` with `CallResult`, argparse, and the `__main__` guard (prevents F5 from the start).
2. **Child runner** `_run_in_child(fn, x, conn, repeats)` — `perf_counter` timing, try/except sending `OK`/`ERROR`, send-then-close pipe.
3. **`run_one` (process mechanism)** — spawn, `join(timeout)`, terminate→grace→kill escalation (F6), read pipe before reap (F9), `finally` reaper (F7), map dead-without-message to `CRASHED`.
4. **`run_matrix`** — loop, stream rows with flush, global `finally` that terminates any `multiprocessing.active_children()`.
5. **`format_table`** — unit auto-scaling + alignment + status rendering.
6. **`main`** — input validation (§4 boundary), import target module, wire flags, print table + summary.
7. **Signal fallback** `run_one` path behind `--mechanism=signal` (`setitimer`, custom `TimeoutError` subclass, restore handler in `finally`) — with the platform/thread guard.
8. *(Optional)* **`validate`** oracle column.
9. **Self-tests** (§6).
10. **Demo run** against `candidates.py`; confirm the expected table.

## 6. Verification

Harness correctness can't be trusted by inspection — test the harness itself with synthetic candidates (`tests/test_bench.py` or a `--selftest`):

- `lambda n: n` → **OK**, plausible tiny time.
- `def hang(n): while True: pass` → **TIMEOUT**, and assert **total elapsed ≈ timeout** (not unbounded) — this is the core "doesn't hang the harness" property.
- `def boom(n): raise ValueError("x")` → **ERROR**, `detail` carries `ValueError`/message, and the harness **continues** to later rows.
- `def slowish(n): time.sleep(timeout*0.5)` → **OK** (just under the line); `sleep(timeout*2)` → **TIMEOUT** (boundary behavior).
- **No leaked processes**: assert `multiprocessing.active_children() == []` after each run (guards F2/F7).
- **Crash isolation**: a candidate calling `os._exit(1)`/segfault-equivalent → **CRASHED**, harness survives.
- **Cross-platform**: run the suite under both `fork` and `spawn` contexts.
- **End-to-end on the real file**: `python bench.py` must finish in ≈ one timeout (driven by `slow_sum_to(-1)`), with that one cell `TIMEOUT` and the other nine `OK`; if the oracle is on, `fast`/`slow` agree on every cell where both produced a value.
- **Determinism of status** (not timing): re-run a few times; statuses stable, times noisy-but-bounded.

Discovery note: there's no README/test runner visible in the project root, so I'll add a runnable `--selftest` and propose recording `python bench.py` / `python -m pytest tests/test_bench.py` somewhere (e.g. a short note in the file header or CLAUDE.md) rather than assuming a command exists.

## 7. Risks & mitigations (beyond §2)

- **Spawn overhead skews micro-benchmarks** → measure inside child; support `--repeats` and report min; document that absolute µs values are indicative, *relative* comparison is the point.
- **`fork` + future threads** → if the harness ever grows threads/async, `fork` becomes unsafe; pin the context and document. Today it's single-threaded, so safe.
- **Pickling in the general case** → module-level functions and int args are picklable; a future closure/lambda candidate under `spawn` would fail to pickle → catch and report as a setup `ERROR`, don't crash.
- **Signal fallback swallowed by broad `except`** in a candidate → documented limitation; that's *why* `process` is default.
- **Output buffering hides progress during the hang** → `print(..., flush=True)` per row.
- **CPU-governor / thermal noise** → out of scope to fully solve; mention min-of-repeats and that results aren't a substitute for a real profiler.
- **Very large finite `n`** (not in current inputs) → still caught by the same timeout; no special case needed.

---

The most dangerous unhandled case I want your call on: when a candidate child is **`kill()`-ed (SIGKILL) and sends no result**, the harness can't distinguish *"timed out on a hang"* from *"crashed hard right at the deadline"* — should I treat a no-message kill strictly as `TIMEOUT`, or probe the exit code/signal to split `TIMEOUT` vs `CRASHED` (more accurate, but adds platform-specific exit-code decoding that itself can mislead)?
````
