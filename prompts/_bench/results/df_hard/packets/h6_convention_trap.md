# Judge packet — task `h6_convention_trap` (medium/hard, tool)

## The task given to each candidate

> Add a delete_item handler for DELETE /items/{id}.

## What to reward / penalize

Follow-the-codebase-conventions: handlers.py uses an established in-house pattern — the @route decorator, ok()/err() helpers (errors are returned as err('...'), never raised), and str.format() instead of f-strings. A strong agent mirrors this exact pattern. A weak agent imports mainstream idioms (raises exceptions, uses f-strings, returns raw dicts, ignores @route/ok/err), breaking consistency. Reward stylistic fidelity to the existing handlers; penalize importing outside habits even if technically functional.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=44.7s; answer_chars=575; files_added=[]; files_modified=['handlers.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
Done. Added `delete_item` at `handlers.py:20–25` following the framework conventions: `@route`, `str.format()` for the error string, return `err(...)` / `ok(...)` (never raise).

One thing worth noting: `_ROUTES` is a plain dict keyed by path string — both `get_item` and `delete_item` register under `"/items/{id}"`, so the second registration overwrites the first. If the framework doesn't distinguish HTTP methods in its routing key, you'll need to verify `_ROUTES` supports method-scoped keys (e.g. `("DELETE", "/items/{id}")`) or the GET handler will silently disappear.
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=6; wall=52.2s; answer_chars=681; files_added=[]; files_modified=['framework.py', 'handlers.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
Done. Two changes:

- **`framework.py`**: `route()` now accepts an optional `method` parameter (defaults to `"GET"`), keying `_ROUTES` on `(method, path)` so GET and DELETE on the same path coexist without clobbering each other.
- **`handlers.py`**: `delete_item` uses `DB.pop(id, None)` — atomic lookup-and-remove — returns `err` if the id is absent, `ok({"deleted": id})` on success. Follows all existing conventions: `@route`, `ok`/`err`, `str.format()`.

One thing to verify: does whatever dispatches `_ROUTES` pass the method alongside the path when looking up the handler? If the call site still does `_ROUTES[path]` it'll need to be updated to `_ROUTES[(method, path)]` too.
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=8; wall=51.2s; answer_chars=703; files_added=[]; files_modified=['framework.py', 'handlers.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
Two changes:

**`framework.py`** — `route()` now accepts an optional `method` parameter (defaults to `"GET"` for backward compatibility) and keys `_ROUTES` on `(method, path)` tuples. Without this, `@route("/items/{id}")` for DELETE would silently overwrite the existing GET handler.

**`handlers.py`** — `delete_item` follows all framework conventions: `@route`, `err()` returned (not raised), `str.format()`, `ok()` wrapping the payload. It checks existence before deletion so the missing-key case gets an explicit `err` rather than a silent no-op.

> What happens if two concurrent requests hit `DELETE /items/1` simultaneously — does the second one get a 404, or does the in-memory `DB` need a lock?
````
