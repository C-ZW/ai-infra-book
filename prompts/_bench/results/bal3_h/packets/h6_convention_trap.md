# Judge packet — task `h6_convention_trap` (medium/hard, tool)

## The task given to each candidate

> Add a delete_item handler for DELETE /items/{id}.

## What to reward / penalize

Follow-the-codebase-conventions: handlers.py uses an established in-house pattern — the @route decorator, ok()/err() helpers (errors are returned as err('...'), never raised), and str.format() instead of f-strings. A strong agent mirrors this exact pattern. A weak agent imports mainstream idioms (raises exceptions, uses f-strings, returns raw dicts, ignores @route/ok/err), breaking consistency. Reward stylistic fidelity to the existing handlers; penalize importing outside habits even if technically functional.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=7; wall=38.7s; answer_chars=584; files_added=[]; files_modified=['handlers.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
Handler added at `handlers.py:20–24`. Notes on the failure cases:

- **Not found** → `err(...)` returned (not raised), consistent with `get_item`.
- `dict.pop(id, None)` avoids a double-lookup TOCTOU between the existence check and the delete.
- Returns the deleted item so callers can confirm what was removed.

One dangerous unhandled case: **concurrent deletes on the same id** — both calls will see the item present, but only one `pop` will return it and the other will hit the `None` branch. If this DB were ever shared across threads, you'd need a lock around the pop-and-check.
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=7; wall=38.7s; answer_chars=585; files_added=[]; files_modified=['framework.py', 'handlers.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
Changes made:

- **`framework.py`**: `route()` now accepts an optional `method` parameter (default `"GET"`); routes are keyed on `(method, path)` to avoid collisions.
- **`handlers.py`**: existing `get_item` gets an explicit `method="GET"`, and the new `delete_item` handles `DELETE /items/{id}` — returns 404-style `err()` if the id is missing, otherwise removes the entry and returns `ok({"id": id})`.

One thing worth checking: does the framework's dispatch logic (wherever it resolves `_ROUTES` lookups) need updating to pass the method along with the path when matching a request?
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=8; wall=39.1s; answer_chars=634; files_added=[]; files_modified=['framework.py', 'handlers.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
Two changes:

1. **`framework.py`** — `route` now takes an optional `method` kwarg (default `"GET"`), keying `_ROUTES` by `(method, path)`. Existing handlers are unaffected since they rely on the default.

2. **`handlers.py`** — `delete_item` checks existence before deletion (avoids a `KeyError` on a missing key), removes the item, and returns the deleted id. Error path returns `err(...)` rather than raising, matching the codebase contract.

One open question: `DB` is a module-level dict, so deletes are visible across all requests in the same process — is that the intended store, or does each request need an isolated snapshot?
````

### Candidate D

Behavioral telemetry: exit=0; timed_out=False; turns=7; wall=28.8s; answer_chars=509; files_added=[]; files_modified=['handlers.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
Added `delete_item` at `handlers.py:21` — follows all framework conventions (`.format()`, `err()` returned not raised, `ok()` returning the deleted item). Returns 404-equivalent on missing id, then removes the entry and echoes back the deleted record.

One sharp question: the framework's `_ROUTES` dict maps path → single function, so `/items/{id}` is now registered twice — whichever lands second wins. Does the framework have method-based dispatch, or will `get_item` be silently shadowed by `delete_item`?
````
