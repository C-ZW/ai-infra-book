# Judge packet — task `h6_convention_trap` (medium/hard, tool)

## The task given to each candidate

> Add a delete_item handler for DELETE /items/{id}.

## What to reward / penalize

Follow-the-codebase-conventions: handlers.py uses an established in-house pattern — the @route decorator, ok()/err() helpers (errors are returned as err('...'), never raised), and str.format() instead of f-strings. A strong agent mirrors this exact pattern. A weak agent imports mainstream idioms (raises exceptions, uses f-strings, returns raw dicts, ignores @route/ok/err), breaking consistency. Reward stylistic fidelity to the existing handlers; penalize importing outside habits even if technically functional.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=8; wall=67.4s; answer_chars=1052; files_added=[]; files_modified=['__pycache__/handlers.cpython-313.pyc', 'handlers.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
Added `delete_item` at `handlers.py:14`, mirroring `get_item`'s conventions: `@route` decorator, `err()` returned (not raised) on miss, `str.format()` over f-strings, `ok()` with the deleted item. Verified the miss path, the delete, and that the row is gone afterward.

One failure mode worth flagging: `framework.route` keys `_ROUTES` by **path only** (`_ROUTES[path] = fn`), and it has no concept of HTTP methods. So `delete_item` and `get_item` both register under `"/items/{id}"`, and whichever is defined last wins — `delete_item` now silently shadows `get_item` in the dispatch table. My direct-call test passes because it bypasses the registry, but a real request router built on `_ROUTES` would no longer reach GET. The framework simply can't express "DELETE /items/{id}" distinctly from "GET /items/{id}".

Do you want me to extend `route` to take a method (e.g. `@route("/items/{id}", method="DELETE")`) so GET and DELETE can coexist — which means touching `framework.py` and the existing handlers — or is direct-call dispatch all this needs?
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=6; wall=41.6s; answer_chars=1142; files_added=[]; files_modified=['__pycache__/handlers.cpython-313.pyc', 'handlers.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
Done. Added `delete_item` to `handlers.py`, following the four conventions from `framework.py` exactly — `@route` decorator, `err()` returned (not raised) for the missing case, `ok()` for success, and `str.format()` instead of an f-string. It mirrors `get_item`'s not-found guard, then deletes and returns the removed item. The smoke test confirms all three paths: missing id, successful delete, and idempotent re-delete.

One failure mode worth flagging, since it's baked into the framework rather than my handler: **`@route` keys `_ROUTES` by path only, with no HTTP-method dimension.** `get_item` and `delete_item` both register `"/items/{id}"`, so whichever module-loads second silently clobbers the first in the dispatch table — there's no GET-vs-DELETE distinction for the router to use. My handler matches the existing convention faithfully, but the convention itself can't express "DELETE /items/{id}" as distinct from "GET /items/{id}".

Do you want me to extend `route()` to take a method (e.g. `@route("/items/{id}", method="DELETE")`) and key `_ROUTES` on `(method, path)` — or is the single-path-keyed router intentional for now?
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=8; wall=58.1s; answer_chars=1280; files_added=[]; files_modified=['handlers.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
Done — `handlers.py:19`. The handler follows the existing conventions: `@route` decorator, mirrors `get_item`'s missing-check, returns `err()` (not raised) on miss, returns `ok()` on success, and builds the message with `str.format()`.

One real problem you should know about, though: `framework.py` keys routes by **path only** (`_ROUTES[path] = fn`), with no HTTP method in the signature. Since `get_item` already registers `/items/{id}`, importing this module now silently overwrites that entry — whichever of `get_item`/`delete_item` is defined last wins, and the other becomes unreachable. The framework as written cannot distinguish `GET /items/{id}` from `DELETE /items/{id}`. I didn't touch `framework.py` since adding method dispatch is a change to shared infrastructure you didn't ask for.

To actually serve both, the framework needs a method dimension — e.g. `@route("/items/{id}", method="DELETE")` keying on `(method, path)`. Want me to make that change?

One more sharp edge: routes pass `id` straight through, and `DB.get(id)` won't coerce — if the dispatcher hands you the string `"1"` instead of int `1`, the lookup misses and you'd 404 a row that exists. `get_item` has the identical exposure. Do you know whether the router parses `{id}` as a string or an int?
````
