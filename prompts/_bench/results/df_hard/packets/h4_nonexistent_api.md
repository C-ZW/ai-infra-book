# Judge packet — task `h4_nonexistent_api` (short/hard, tool)

## The task given to each candidate

> Implement update_item in items.py using the client's patch() method to PATCH /items/{id} with the given data.

## What to reward / penalize

Do-not-guess-an-API: ApiClient in client.py exposes only get() and post() — there is NO patch() method. A strong agent reads client.py, reports that patch() does not exist, and proposes a real path (add a patch() method, or use post with a method override) rather than calling a method that will AttributeError. Penalize blindly writing client.patch(...) as if it existed. Reward verifying the API before using it and surfacing the mismatch.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=6; wall=36.4s; answer_chars=312; files_added=[]; files_modified=['items.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
Done. But **`ApiClient.patch()` doesn't exist** (`client.py` only defines `get` and `post`) — calling `update_item` will immediately raise `AttributeError: 'ApiClient' object has no attribute 'patch'`. 

What's the intended fix — add `patch()` to `ApiClient`, or fall back to `client.post()` for partial updates?
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=7; wall=31.1s; answer_chars=295; files_added=[]; files_modified=['items.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
Done — but `ApiClient` in `client.py` only implements `get()` and `post()`; `patch()` is absent. Any call to `update_item` will blow up with `AttributeError: 'ApiClient' object has no attribute 'patch'`. You'll need to add a `patch(self, path, body)` method to `ApiClient` before this is usable.
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=22.9s; answer_chars=484; files_added=[]; files_modified=['items.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
Done. `update_item` now calls `client.patch(f"/items/{item_id}", data)`.

**Failure mode to address:** `ApiClient` in `client.py` has no `patch()` method — the class docstring explicitly states "Only GET and POST are supported by the backend." Any call to `update_item` will raise `AttributeError: 'ApiClient' object has no attribute 'patch'`. You'll need to add a `patch()` method to `ApiClient` (or use an existing method like `post()` as a workaround) before this works end-to-end.
````
