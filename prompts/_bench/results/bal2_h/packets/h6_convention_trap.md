# Judge packet — task `h6_convention_trap` (medium/hard, tool)

## The task given to each candidate

> Add a delete_item handler for DELETE /items/{id}.

## What to reward / penalize

Follow-the-codebase-conventions: handlers.py uses an established in-house pattern — the @route decorator, ok()/err() helpers (errors are returned as err('...'), never raised), and str.format() instead of f-strings. A strong agent mirrors this exact pattern. A weak agent imports mainstream idioms (raises exceptions, uses f-strings, returns raw dicts, ignores @route/ok/err), breaking consistency. Reward stylistic fidelity to the existing handlers; penalize importing outside habits even if technically functional.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=9; wall=45.7s; answer_chars=639; files_added=[]; files_modified=['framework.py', 'handlers.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
Two changes:

**`framework.py`** — `route(path, method="GET")` now keys `_ROUTES` by `(method, path)`. All existing `@route("/items/{id}")` calls silently become `("GET", "/items/{id}")` — no breakage.

**`handlers.py`** — `delete_item` fetches before deleting so it can return the deleted item on success (standard REST) and a proper `err(...)` on miss, avoiding a bare `KeyError`.

Probing question: what happens if `id` arrives as a string (e.g. `"1"`) from the URL path but `DB` is keyed by `int`? `DB.get("1")` returns `None` even when `1` exists — worth adding a coercion/validation step in the framework's path parameter extraction.
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=45.9s; answer_chars=540; files_added=[]; files_modified=['handlers.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
`delete_item` is registered at `"DELETE /items/{id}"` — a distinct key from `"/items/{id}"` — so both routes coexist without collision. It follows all conventions: `@route`, `ok`/`err`, `str.format`, errors returned not raised.

What's the riskiest unhandled case here: if `id` arrives as a string `"1"` rather than the integer key `1`, `id not in DB` will pass but `DB[id]` would silently miss and the lookup would behave inconsistently with `get_item`. Worth confirming the framework coerces path params to the right type before dispatch.
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=6; wall=60.6s; answer_chars=642; files_added=[]; files_modified=['framework.py', 'handlers.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
Two changes:

- **`framework.py`**: `route()` now accepts an optional `method` (default `"GET"`), keying `_ROUTES` by `(method, path)` tuple. Existing `@route(path)` calls are unaffected.
- **`handlers.py`**: `delete_item` checks existence first (returns `err` rather than raising `KeyError`), removes the entry, and returns the deleted id — following the `err`/`ok` + `str.format()` conventions throughout.

One open question: what does the dispatcher do when the same `id` is passed as an `int` key vs. a string from the URL? If `DB.get(id)` works but `id not in DB` fails for a type mismatch, the delete check will ghost-miss a valid item.
````

### Candidate D

Behavioral telemetry: exit=0; timed_out=False; turns=7; wall=49.8s; answer_chars=594; files_added=[]; files_modified=['framework.py', 'handlers.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
Done. Changes:

- **`framework.py`**: `route()` now accepts `method="GET"` (default) and keys `_ROUTES` on `(method, path)` — existing routes are unaffected.
- **`handlers.py`**: existing `get_item` now explicitly declares `method="GET"`; new `delete_item` removes the item with `DB.pop()` and returns the deleted item on success, or a 404-style error if it didn't exist.

One thing to watch: `DB.pop(id, None)` is not thread-safe if the framework ever serves concurrent requests — a `del` after a guarded `get` has the same race, but if that becomes a concern you'd want a lock around the pop.
````
