# Judge packet — task `h6_convention_trap` (medium/hard, tool)

## The task given to each candidate

> Add a delete_item handler for DELETE /items/{id}.

## What to reward / penalize

Follow-the-codebase-conventions: handlers.py uses an established in-house pattern — the @route decorator, ok()/err() helpers (errors are returned as err('...'), never raised), and str.format() instead of f-strings. A strong agent mirrors this exact pattern. A weak agent imports mainstream idioms (raises exceptions, uses f-strings, returns raw dicts, ignores @route/ok/err), breaking consistency. Reward stylistic fidelity to the existing handlers; penalize importing outside habits even if technically functional.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=8; wall=46.8s; answer_chars=629; files_added=[]; files_modified=['framework.py', 'handlers.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
Changes:

- **`framework.py`**: `route()` now accepts `method="GET"` (existing routes are unaffected). `_ROUTES` keys on `(method, path)` tuples instead of bare paths.
- **`handlers.py`**: `delete_item` checks presence before deleting (avoids a `KeyError`), returns the deleted id on success, or `err(...)` if not found — consistent with `get_item`.

One open question: `DB` is module-level mutable state. If the dispatch layer ever calls handlers concurrently, a delete racing a read on the same id will produce a `KeyError` between the `if id not in DB` guard and the `del`. Is there a lock or request-isolation story for `DB`?
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=6; wall=43.0s; answer_chars=646; files_added=[]; files_modified=['framework.py', 'handlers.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
Done. Two changes:

- **`framework.py`**: `route()` now accepts an optional `method="GET"` parameter; routes are keyed by `(method, path)` tuples. Existing `@route(path)` calls default to `"GET"` with no breakage.
- **`handlers.py`**: `delete_item` checks existence first (returning `err` if missing), removes the item, and returns `ok({"id": id, "deleted": True})` — follows the project's conventions (`str.format()`, `ok`/`err`, no raw dicts).

One thing to verify: whatever dispatches `_ROUTES` will need to pass the method alongside the path when looking up `(method, path)` — that lookup site isn't visible here, so confirm it's updated too.
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=4; wall=36.2s; answer_chars=468; files_added=[]; files_modified=['handlers.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
Done. Added `delete_item` at `handlers.py:21` following the same `@route`, `ok`/`err`, `.format()` conventions as the existing handlers.

One sharp question: does the `@route` decorator distinguish HTTP method, or does it dispatch purely on path? If it's path-only, `get_item` and `delete_item` both match `/items/{id}` and one will silently shadow the other — you'll need a method parameter (e.g. `@route("/items/{id}", method="DELETE")`) before this works correctly.
````

### Candidate D

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=46.0s; answer_chars=619; files_added=[]; files_modified=['handlers.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
Added `delete_item` at `handlers.py:20`. It looks up the item first (returns `err` if missing rather than silently no-oping), removes it from `DB`, and returns the deleted item via `ok(item)` — consistent with `get_item`'s response shape.

One thing to watch: the `_ROUTES` dict in `framework.py` has no method-aware dispatch — if the router resolves a `DELETE /items/1` request by looking up `"/items/{id}"` (without the method prefix), this handler will never match. Confirm whether the dispatch layer already strips or prefixes the HTTP method, or whether you need to update the router to support method+path keying.
````
