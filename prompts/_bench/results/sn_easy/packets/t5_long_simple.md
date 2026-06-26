# Judge packet — task `t5_long_simple` (long/simple, text)

## The task given to each candidate

> Write a Python function chunk(lst, n) that splits lst into consecutive chunks of size n; the final chunk may be shorter. Include a docstring and sensible handling of n <= 0.

## What to reward / penalize

Correct, idiomatic code with edge-case handling (n<=0 raises or documented behavior; empty list) and a useful docstring. Penalize over-commenting/narration, bugs, or ignoring the n<=0 requirement.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=1; wall=9.7s; answer_chars=1132; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
```python
def chunk(lst, n):
    """
    Split *lst* into consecutive chunks of size *n*.

    The final chunk may be shorter than *n* if len(lst) is not
    evenly divisible by *n*.

    Args:
        lst: Any sequence (list, tuple, str, …).
        n:   Chunk size. Must be a positive integer.

    Returns:
        A list of sub-lists.

    Raises:
        ValueError: If *n* is not a positive integer.
    """
    if not isinstance(n, int) or n <= 0:
        raise ValueError(f"chunk size must be a positive integer, got {n!r}")
    return [lst[i : i + n] for i in range(0, len(lst), n)]
```

A few notes on failure modes worth being aware of:

- `range(0, 0, n)` is empty, so `chunk([], n)` correctly returns `[]` without special-casing.
- The slice `lst[i : i + n]` is safe even when `i + n` exceeds `len(lst)` — Python clips it.
- The `isinstance(n, int)` guard rejects `float` values like `2.0` that would otherwise pass a truthiness check but produce confusing behavior; `bool` is a subclass of `int`, so `chunk(lst, True)` would silently use `n=1` — add `or isinstance(n, bool)` to the guard if you want to block that too.
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=1; wall=10.9s; answer_chars=1156; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
```python
def chunk(lst, n):
    """Split lst into consecutive chunks of size n.

    The final chunk may be shorter than n if len(lst) is not a multiple of n.

    Args:
        lst: Any sequence (list, tuple, str, etc.).
        n:   Chunk size. Must be a positive integer.

    Returns:
        A list of sub-lists.

    Raises:
        ValueError: If n is less than or equal to 0.
    """
    if not isinstance(n, int) or n <= 0:
        raise ValueError(f"Chunk size must be a positive integer, got {n!r}")
    return [lst[i : i + n] for i in range(0, len(lst), n)]
```

Failure modes considered:
- `n <= 0` would cause `range(0, len(lst), 0)` to raise a cryptic `ValueError: range() arg 3 must not be zero` — replaced with an explicit, descriptive raise.
- `n` as a float (e.g. `2.0`) passes a truthiness check but breaks `range()`; the `isinstance(n, int)` guard catches it.
- Empty `lst` returns `[]` cleanly — `range(0, 0, n)` produces no iterations.

What's the most dangerous unhandled case for your use? If `lst` is a lazy iterator (generator), `lst[i:i+n]` silently fails — worth adding `lst = list(lst)` at the top if that's a possible input.
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=1; wall=9.8s; answer_chars=1190; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
```python
def chunk(lst, n):
    """
    Split *lst* into consecutive chunks of size *n*.

    The final chunk may be shorter than *n* if len(lst) is not evenly divisible.

    Args:
        lst: Any sequence (list, tuple, str, etc.).
        n:   Positive integer chunk size.

    Returns:
        A list of chunks (same type as *lst* if it supports slicing, otherwise list slices).

    Raises:
        ValueError: If *n* is less than or equal to zero.
    """
    if n <= 0:
        raise ValueError(f"Chunk size must be a positive integer, got {n!r}")
    return [lst[i : i + n] for i in range(0, len(lst), n)]
```

**Failure modes worth noting:**

- `n > len(lst)` — returns a single chunk containing the whole list; that's intentional and correct.
- Empty `lst` — `range(0, 0, n)` produces nothing, so you get `[]` back, not an error.
- Non-integer `n` (e.g. `2.0`) — `range` will raise a `TypeError` at runtime; add `isinstance(n, int)` to the guard if callers are untrusted.

What's the most dangerous unhandled case for your use? If `lst` is a lazy iterator (generator), the slicing silently returns empty chunks — worth a `list(lst)` materialisation at the top if that's in scope.
````
