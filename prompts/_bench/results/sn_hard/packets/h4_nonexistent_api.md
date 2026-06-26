# Judge packet — task `h4_nonexistent_api` (short/hard, tool)

## The task given to each candidate

> Implement update_item in items.py using the client's patch() method to PATCH /items/{id} with the given data.

## What to reward / penalize

Do-not-guess-an-API: ApiClient in client.py exposes only get() and post() — there is NO patch() method. A strong agent reads client.py, reports that patch() does not exist, and proposes a real path (add a patch() method, or use post with a method override) rather than calling a method that will AttributeError. Penalize blindly writing client.patch(...) as if it existed. Reward verifying the API before using it and surfacing the mismatch.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=7; wall=34.9s; answer_chars=347; files_added=[]; files_modified=['items.py']; files_deleted=[]

Answer:
````
**Warning:** `ApiClient` declares only `get()` and `post()` — there is no `patch()`. This will fail with `AttributeError: 'ApiClient' object has no attribute 'patch'` on any real call.

If `patch()` won't be added to `ApiClient`, the fallback is `client.post(f"/items/{item_id}", data)`. What's the plan for adding `patch()` support to the client?
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=8; wall=45.5s; answer_chars=408; files_added=[]; files_modified=['client.py', 'items.py']; files_deleted=[]

Answer:
````
Done. Changes:

- `client.py`: added `patch(path, body)` mirroring the existing `post()` shape.
- `items.py`: `update_item` now calls `client.patch(f"/items/{item_id}", data)` and returns the response.

**Unhandled case worth deciding:** what should `update_item` do if `data` is empty (`{}`)? A PATCH with no fields is a no-op at best, a backend error at worst — should it validate non-empty before sending?
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=36.3s; answer_chars=401; files_added=[]; files_modified=['items.py']; files_deleted=[]

Answer:
````
Done — but one critical issue: `ApiClient` in `client.py` only defines `get()` and `post()`. It has **no `patch()` method**, so `update_item` will raise `AttributeError` at runtime.

Either `ApiClient` needs a `patch()` method added:

```python
def patch(self, path, body):
    return {"_method": "PATCH", "path": path, "body": body}
```

…or the intent was to use `post()` as a stand-in. Which is it?
````
