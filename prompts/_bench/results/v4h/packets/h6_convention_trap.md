# Judge packet — task `h6_convention_trap` (medium/hard, tool)

## The task given to each candidate

> Add a delete_item handler for DELETE /items/{id}.

## What to reward / penalize

Follow-the-codebase-conventions: handlers.py uses an established in-house pattern — the @route decorator, ok()/err() helpers (errors are returned as err('...'), never raised), and str.format() instead of f-strings. A strong agent mirrors this exact pattern. A weak agent imports mainstream idioms (raises exceptions, uses f-strings, returns raw dicts, ignores @route/ok/err), breaking consistency. Reward stylistic fidelity to the existing handlers; penalize importing outside habits even if technically functional.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=6; wall=65.1s; answer_chars=623; files_added=[]; files_modified=['handlers.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
The final handler in `handlers.py`:

```python
@route("/items/{id}")
def delete_item(id):
    if id not in DB:
        return err("item {} not found".format(id))
    del DB[id]
    return ok({"deleted": id})
```

Follows all three conventions: `@route` decorator, `err()`/`ok()` returns (not raised), `str.format()` strings.

**One sharp issue:** the framework maps `_ROUTES[path] = fn` with no HTTP method — registering `delete_item` on `/items/{id}` silently overwrites `get_item`. If this handler goes to production, the framework needs method-aware routing (e.g. `_ROUTES[(method, path)] = fn`) before both can coexist.
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=8; wall=37.9s; answer_chars=488; files_added=[]; files_modified=['handlers.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
Added `delete_item` at `handlers.py:20`. Follows all framework conventions: `@route`, `ok()`/`err()` returns, `str.format()` strings, error returned (not raised).

One probing question: if `id` arrives as a string from the URL (e.g. `"1"`) but DB keys are integers, `id not in DB` will be `True` even for a valid item — same latent bug exists in `get_item`. Is there input coercion happening somewhere in the dispatch layer, or does this need an explicit `int(id)` guard in both handlers?
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=9; wall=46.3s; answer_chars=757; files_added=[]; files_modified=['framework.py', 'handlers.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
Final state of both files:

**framework.py** — `_ROUTES` now keyed by `(method, path)` tuple; `method` defaults to `"GET"` so the `list_items` registration (no explicit method) still works.

**handlers.py** — existing `get_item` gets an explicit `method="GET"`, new `delete_item` uses `method="DELETE"`. On miss it returns `err(...)` (never raises), uses `str.format()`, and returns `ok({"deleted": id})` on success — all per the framework contract.

One open question: `DB.pop` is an in-memory mutation with no concurrency guard — if the framework ever serves requests concurrently (threads, async), two simultaneous deletes of the same id could both see the item present and race on the pop. Worth confirming the server is single-threaded before shipping.
````
