# Judge packet — task `t5_long_simple` (long/simple, text)

## The task given to each candidate

> Write a Python function chunk(lst, n) that splits lst into consecutive chunks of size n; the final chunk may be shorter. Include a docstring and sensible handling of n <= 0.

## What to reward / penalize

Correct, idiomatic code with edge-case handling (n<=0 raises or documented behavior; empty list) and a useful docstring. Penalize over-commenting/narration, bugs, or ignoring the n<=0 requirement.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=1; wall=8.9s; answer_chars=1055; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
```python
def chunk(lst, n):
    """
    Split *lst* into consecutive chunks of size *n*.

    The final chunk may be shorter than *n* if len(lst) is not evenly
    divisible.  Returns an empty list when *lst* is empty.

    Args:
        lst: Any sequence (list, tuple, str, …).
        n:   Positive integer chunk size.

    Raises:
        ValueError: If *n* is less than or equal to zero.
    """
    if n <= 0:
        raise ValueError(f"chunk size must be a positive integer, got {n!r}")
    return [lst[i : i + n] for i in range(0, len(lst), n)]
```

Key failure modes handled:

- `n <= 0` — raises `ValueError` with the bad value in the message rather than silently looping forever or returning garbage.
- Empty `lst` — `range(0, 0, n)` produces no iterations, returning `[]`.
- `n > len(lst)` — one chunk containing all elements, which is correct.

Works on any sequence (list, tuple, string) since it only uses slicing and `len`. If you need it to always return `list` chunks regardless of input type, wrap the slice: `[list(lst[i : i + n]) …]`.
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=1; wall=9.9s; answer_chars=1212; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
```python
def chunk(lst, n):
    """
    Split *lst* into consecutive chunks of size *n*.

    The final chunk may be shorter than *n* if len(lst) is not evenly
    divisible.  Raises ValueError for n <= 0.

    Args:
        lst: Any sequence (list, tuple, str, …).
        n:   Positive integer chunk size.

    Returns:
        A list of sub-lists.

    Examples:
        >>> chunk([1, 2, 3, 4, 5], 2)
        [[1, 2], [3, 4], [5]]
        >>> chunk([], 3)
        []
    """
    if n <= 0:
        raise ValueError(f"chunk size must be a positive integer, got {n!r}")
    return [lst[i : i + n] for i in range(0, len(lst), n)]
```

**Failure modes handled:**

- `n <= 0` — raises `ValueError` with the bad value in the message rather than returning nonsense or looping forever.
- Empty `lst` — `range(0, 0, n)` is empty, returns `[]` cleanly.
- `n > len(lst)` — single chunk containing the whole list; no special case needed.
- Works on any sliceable sequence (list, tuple, str), not just lists — the caller decides the input type.

What's the most dangerous unhandled case here: a caller passing a generator or other non-sliceable iterable. If that's a real use case, wrap with `lst = list(lst)` at the top.
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=1; wall=11.6s; answer_chars=920; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
```python
def chunk(lst, n):
    """
    Split lst into consecutive chunks of size n.

    The final chunk may be shorter than n if len(lst) is not evenly divisible.

    Raises ValueError if n <= 0.
    """
    if n <= 0:
        raise ValueError(f"chunk size must be a positive integer, got {n}")
    return [lst[i:i + n] for i in range(0, len(lst), n)]
```

**Failure modes worth noting:**

- `n <= 0` — raises `ValueError` with the bad value in the message rather than silently returning garbage or looping forever.
- Empty list — `range(0, 0, n)` produces no iterations, so `[]` is returned correctly.
- `n > len(lst)` — produces a single chunk containing the whole list, which is the expected behavior.

What should happen if `lst` is not a sequence type (e.g., a generator or a set)? The current implementation slices, so it only works on indexable types — worth a `TypeError` guard if callers may pass iterables.
````
