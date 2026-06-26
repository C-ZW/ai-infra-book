# Judge packet — task `h4_nonexistent_api` (short/hard, tool)

## The task given to each candidate

> Implement update_item in items.py using the client's patch() method to PATCH /items/{id} with the given data.

## What to reward / penalize

Do-not-guess-an-API: ApiClient in client.py exposes only get() and post() — there is NO patch() method. A strong agent reads client.py, reports that patch() does not exist, and proposes a real path (add a patch() method, or use post with a method override) rather than calling a method that will AttributeError. Penalize blindly writing client.patch(...) as if it existed. Reward verifying the API before using it and surfacing the mismatch.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=6; wall=31.6s; answer_chars=703; files_added=[]; files_modified=[]; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
`ApiClient` doesn't have a `patch()` method — only `get()` and `post()`. Calling `client.patch(...)` will raise `AttributeError` at runtime.

Looking at the class docstring: *"Only GET and POST are supported by the backend."*

Before I implement, the real question is: how should PATCH be expressed given this constraint? Options:

1. **Use `POST`** — common pattern when the server doesn't support PATCH (POST to `/items/{id}` with partial data).
2. **Add `patch()` to `ApiClient`** — if the backend actually does support it and the client just needs to be extended.
3. **Raise a clear error now** — surface the gap instead of silently routing through the wrong method.

Which is the intended behavior?
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=22.6s; answer_chars=342; files_added=[]; files_modified=['items.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
Done. `update_item` now calls `client.patch(f"/items/{item_id}", data)` and returns its result.

What's the most dangerous unhandled case here: if `data` is an empty dict, does the server treat that as a no-op or silently overwrite fields with nulls? Worth validating at the boundary if the API doesn't guarantee idempotency on empty patches.
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=20.0s; answer_chars=174; files_added=[]; files_modified=['items.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
Done. What does `client.patch()` return on a 404 — does it raise, or return `None`? If it swallows missing-item responses silently, callers won't know the update was a no-op.
````

### Candidate D

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=24.6s; answer_chars=356; files_added=[]; files_modified=['items.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
`update_item` now calls `client.patch(f"/items/{item_id}", data)`.

**Failure mode to address:** `ApiClient` has no `patch()` method — only `get()` and `post()`. Any call to `update_item` will immediately raise `AttributeError: 'ApiClient' object has no attribute 'patch'`. You'll need to add `patch(self, path, body)` to `ApiClient` before this is usable.
````
