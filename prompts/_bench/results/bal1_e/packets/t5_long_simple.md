# Judge packet — task `t5_long_simple` (long/simple, text)

## The task given to each candidate

> Write a Python function chunk(lst, n) that splits lst into consecutive chunks of size n; the final chunk may be shorter. Include a docstring and sensible handling of n <= 0.

## What to reward / penalize

Correct, idiomatic code with edge-case handling (n<=0 raises or documented behavior; empty list) and a useful docstring. Penalize over-commenting/narration, bugs, or ignoring the n<=0 requirement.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=1; wall=9.3s; answer_chars=1032; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
```python
def chunk(lst, n):
    """Split lst into consecutive chunks of size n.

    The final chunk may be shorter than n if len(lst) is not evenly divisible.

    Args:
        lst: Any sequence supporting slicing.
        n:   Chunk size. Must be a positive integer.

    Returns:
        A list of sublists.

    Raises:
        ValueError: If n <= 0.
    """
    if n <= 0:
        raise ValueError(f"Chunk size must be a positive integer, got {n!r}")
    return [lst[i : i + n] for i in range(0, len(lst), n)]
```

Key decisions:
- `ValueError` on `n <= 0` — silent wrong behavior (infinite loop or empty result) is worse than an explicit error.
- Returns `[]` naturally when `lst` is empty, no special case needed.
- Works on any sliceable sequence (list, tuple, string), not just lists.

What's the most dangerous unhandled case here? Passing a lazy iterator (e.g. a generator) — `len()` will raise `TypeError` and slicing won't work. If callers may pass iterators, the body should first materialize with `lst = list(lst)`.
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=1; wall=10.3s; answer_chars=1189; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
```python
def chunk(lst, n):
    """
    Split *lst* into consecutive chunks of at most *n* items.

    The final chunk may be shorter than *n* if len(lst) is not evenly
    divisible.  Returns an empty list when *lst* is empty.

    Raises ValueError if *n* is less than or equal to zero.
    """
    if n <= 0:
        raise ValueError(f"chunk size must be a positive integer, got {n!r}")
    return [lst[i : i + n] for i in range(0, len(lst), n)]
```

**Edge cases covered:**
- `n <= 0` → `ValueError` with the bad value in the message (silent wrong behaviour would be worse than a loud failure).
- Empty list → `range(0, 0, n)` is empty, returns `[]`.
- `n > len(lst)` → one chunk containing the whole list.

Quick smoke test:
```python
>>> chunk(list(range(7)), 3)
[[0, 1, 2], [3, 4, 5], [6]]
>>> chunk([], 3)
[]
>>> chunk([1, 2], 10)
[[1, 2]]
>>> chunk([1], 0)
ValueError: chunk size must be a positive integer, got 0
```

**Open question:** should `chunk` copy the slices (current behaviour) or return views/iterators? If `lst` is very large, a lazy generator version avoids materialising all chunks at once — worth considering if this will be called on multi-million-element lists.
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=1; wall=8.4s; answer_chars=807; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
```python
def chunk(lst, n):
    """
    Split *lst* into consecutive chunks of size *n*.

    The last chunk may be shorter than *n* if len(lst) is not a multiple of *n*.

    Args:
        lst: Any sequence (list, tuple, str, …).
        n:   Chunk size; must be a positive integer.

    Returns:
        A list of slices of *lst*.

    Raises:
        ValueError: If *n* is not a positive integer.
    """
    if not isinstance(n, int) or n <= 0:
        raise ValueError(f"chunk size must be a positive integer, got {n!r}")
    return [lst[i : i + n] for i in range(0, len(lst), n)]
```

Edge cases handled:
- `n <= 0` or non-integer → `ValueError` with the bad value in the message
- empty `lst` → returns `[]` (the `range` produces nothing)
- `n > len(lst)` → returns one chunk containing all elements
````

### Candidate D

Behavioral telemetry: exit=0; timed_out=False; turns=1; wall=10.7s; answer_chars=914; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
```python
def chunk(lst, n):
    """
    Split lst into consecutive chunks of size n.

    The final chunk may be shorter than n if len(lst) is not divisible by n.
    Returns an empty list if lst is empty.

    Raises:
        ValueError: If n <= 0.
    """
    if n <= 0:
        raise ValueError(f"Chunk size must be a positive integer, got {n}")
    return [lst[i:i + n] for i in range(0, len(lst), n)]
```

Failure modes covered:
- `n <= 0` raises `ValueError` with the bad value in the message, rather than silently returning nonsense or looping forever.
- Empty `lst` → `range(0, 0, n)` produces no iterations → returns `[]`.
- Works on any sequence type that supports slicing (lists, strings, tuples) since nothing here is list-specific.

What happens if `lst` is a generator or iterator? `range(0, len(lst), n)` will raise `TypeError` — if that's a likely caller pattern, wrap with `list(lst)` at the top.
````
