# Judge packet — task `t5_long_simple` (long/simple, text)

## The task given to each candidate

> Write a Python function chunk(lst, n) that splits lst into consecutive chunks of size n; the final chunk may be shorter. Include a docstring and sensible handling of n <= 0.

## What to reward / penalize

Correct, idiomatic code with edge-case handling (n<=0 raises or documented behavior; empty list) and a useful docstring. Penalize over-commenting/narration, bugs, or ignoring the n<=0 requirement.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=1; wall=9.8s; answer_chars=910; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
```python
def chunk(lst, n):
    """Split lst into consecutive chunks of size n.

    The final chunk may be shorter than n if len(lst) is not divisible by n.

    Args:
        lst: Any sequence supporting slicing.
        n: Positive integer chunk size.

    Returns:
        A list of sublists.

    Raises:
        ValueError: If n is less than or equal to 0.
    """
    if n <= 0:
        raise ValueError(f"Chunk size must be a positive integer, got {n!r}")
    return [lst[i : i + n] for i in range(0, len(lst), n)]
```

The `range(0, len(lst), n)` stepping handles the short final chunk automatically — slicing past the end of a list is safe in Python and just returns whatever remains.

What happens on the dangerous edge: an empty `lst` returns `[]` (the range produces no iterations), which is the least-surprising behavior. What's the expected behavior if `lst` is not a list but e.g. a generator?
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=1; wall=9.1s; answer_chars=1152; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
```python
def chunk(lst, n):
    """
    Split *lst* into consecutive chunks of size *n*.

    The final chunk may be shorter than *n* if len(lst) is not divisible by *n*.

    Args:
        lst: Any sequence (list, tuple, str, etc.).
        n:   Positive integer chunk size.

    Returns:
        A list of slices of *lst*.

    Raises:
        ValueError: If *n* is less than or equal to zero.
    """
    if n <= 0:
        raise ValueError(f"Chunk size must be a positive integer, got {n!r}")
    return [lst[i : i + n] for i in range(0, len(lst), n)]
```

Key decisions:

- **`n <= 0` raises `ValueError`** — silently returning `[]` or the whole list would mask bugs at the call site; an explicit error with the bad value surfaces them immediately.
- **Returns `[]`** for an empty `lst` naturally (the `range` produces no iterations), no special case needed.
- Works on any subscriptable sequence (list, tuple, string) without modification.

What's the behavior you want if `lst` is `None`? That's the one case not handled — it'll raise `TypeError` from the `len()` call, which is probably correct but worth confirming if callers can pass `None`.
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=1; wall=7.4s; answer_chars=922; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
```python
def chunk(lst, n):
    """
    Split lst into consecutive chunks of size n.

    The final chunk may be shorter than n if len(lst) is not a multiple of n.

    Args:
        lst: Any sequence supporting slicing.
        n:   Positive integer chunk size.

    Returns:
        A list of slices of lst.

    Raises:
        ValueError: If n <= 0.
    """
    if n <= 0:
        raise ValueError(f"Chunk size must be a positive integer, got {n!r}")
    return [lst[i : i + n] for i in range(0, len(lst), n)]
```

`range(0, len(lst), n)` naturally produces an empty sequence when `lst` is empty, so `chunk([], 3)` returns `[]` without any special case.

What happens when `lst` is a non-list sequence (tuple, string)? The slices preserve the original type — `chunk("hello", 2)` yields `['he', 'll', 'o']`. If callers need uniform `list` chunks regardless of input type, wrap the slices: `[list(lst[i : i + n]) ...]`.
````

### Candidate D

Behavioral telemetry: exit=0; timed_out=False; turns=1; wall=9.0s; answer_chars=1138; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
```python
def chunk(lst, n):
    """
    Split *lst* into consecutive chunks of at most *n* items.

    The final chunk may be shorter than *n* if len(lst) is not evenly
    divisible by *n*.

    Args:
        lst: Any sequence (list, tuple, str, …).
        n:   Chunk size; must be a positive integer.

    Returns:
        A list of slices of *lst*.

    Raises:
        ValueError: If *n* is less than or equal to zero.
    """
    if n <= 0:
        raise ValueError(f"Chunk size must be a positive integer, got {n!r}")
    return [lst[i : i + n] for i in range(0, len(lst), n)]
```

Usage:

```python
chunk([1, 2, 3, 4, 5], 2)   # [[1, 2], [3, 4], [5]]
chunk([], 3)                 # []
chunk([1, 2, 3], 0)          # ValueError: Chunk size must be a positive integer, got 0
```

**Dangerous unhandled case worth thinking about:** if `lst` is a generator rather than a sequence, `len(lst)` raises `TypeError` and the slice notation doesn't apply. If callers might pass iterables, add `lst = list(lst)` at the top (with the cost that it materialises the whole thing into memory — fine for finite iterables, fatal for infinite ones).
````
