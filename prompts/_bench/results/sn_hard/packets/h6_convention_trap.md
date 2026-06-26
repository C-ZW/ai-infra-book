# Judge packet — task `h6_convention_trap` (medium/hard, tool)

## The task given to each candidate

> Add a delete_item handler for DELETE /items/{id}.

## What to reward / penalize

Follow-the-codebase-conventions: handlers.py uses an established in-house pattern — the @route decorator, ok()/err() helpers (errors are returned as err('...'), never raised), and str.format() instead of f-strings. A strong agent mirrors this exact pattern. A weak agent imports mainstream idioms (raises exceptions, uses f-strings, returns raw dicts, ignores @route/ok/err), breaking consistency. Reward stylistic fidelity to the existing handlers; penalize importing outside habits even if technically functional.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=6; wall=74.6s; answer_chars=589; files_added=[]; files_modified=['framework.py', 'handlers.py']; files_deleted=[]

Answer:
````
Two changes:

1. **`framework.py`**: `route(path)` → `route(path, method="GET")`, registry key changed from `path` string to `(method, path)` tuple. Without this, `delete_item` would silently clobber `get_item` — same path, last writer wins.

2. **`handlers.py`**: Existing handlers now pass explicit `method="GET"`, `delete_item` checks for existence before deleting (returns the same `"item {} not found"` error on miss), then removes from `DB` and returns `{"deleted": id}`.

What happens if `delete_item` is called twice on the same id — should the second call return 404 or 200/no-op?
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=6; wall=54.7s; answer_chars=706; files_added=[]; files_modified=['framework.py', 'handlers.py']; files_deleted=[]

Answer:
````
Two changes:

- **`framework.py`**: `route(path)` → `route(path, method="GET")`, keying `_ROUTES` on `(method, path)` instead of `path` alone. Existing handlers keep working unchanged since they get `method="GET"` by default.
- **`handlers.py`**: Added `delete_item` decorated with `@route("/items/{id}", method="DELETE")`. Uses `dict.pop(id, None)` to atomically remove and return the item, returning 404-style `err` if missing or the deleted item on success.

Dangerous unhandled case: if `id` arrives as a string (e.g., from a URL param) but `DB` keys are integers, `DB.pop("1", None)` will always return `None` — does the framework coerce path parameters to the correct type before calling the handler?
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=56.4s; answer_chars=416; files_added=[]; files_modified=['handlers.py']; files_deleted=[]

Answer:
````
Added `delete_item` at `handlers.py:20–26`. It checks existence first (returns `err` if missing), removes from `DB`, and returns the deleted item via `ok()` — following all framework conventions: `@route`, `ok`/`err`, `str.format()`.

What happens if `id` arrives as a string but the `DB` keys are ints — has the framework's dispatch layer been validated to coerce the path parameter type before it reaches handlers?
````
