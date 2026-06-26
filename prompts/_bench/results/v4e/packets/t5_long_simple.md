# Judge packet — task `t5_long_simple` (long/simple, text)

## The task given to each candidate

> Write a Python function chunk(lst, n) that splits lst into consecutive chunks of size n; the final chunk may be shorter. Include a docstring and sensible handling of n <= 0.

## What to reward / penalize

Correct, idiomatic code with edge-case handling (n<=0 raises or documented behavior; empty list) and a useful docstring. Penalize over-commenting/narration, bugs, or ignoring the n<=0 requirement.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=1; wall=10.5s; answer_chars=1134; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
```python
def chunk(lst, n):
    """Split lst into consecutive chunks of size n.

    The final chunk may be shorter than n if len(lst) is not divisible by n.

    Args:
        lst: Any sequence to split.
        n:   Chunk size; must be a positive integer.

    Returns:
        A list of lists.

    Raises:
        ValueError: If n <= 0.
    """
    if n <= 0:
        raise ValueError(f"Chunk size must be a positive integer, got {n!r}")
    return [lst[i : i + n] for i in range(0, len(lst), n)]
```

Edge cases covered:
- `n <= 0` → explicit `ValueError` with the bad value in the message
- empty `lst` → returns `[]` (the `range` produces nothing)
- `len(lst) % n != 0` → last slice naturally falls short, no special case needed
- works on any sequence (`list`, `str`, `tuple`) since slicing is the only operation

What's the most dangerous unhandled case here? Passing a lazy iterator (e.g. a generator) — `range(0, len(lst), n)` will raise `TypeError` on `len()`, and even if you worked around that, the slice `lst[i:i+n]` would fail. If callers might pass generators, wrap with `lst = list(lst)` at the top of the function.
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=1; wall=7.2s; answer_chars=808; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
```python
def chunk(lst, n):
    """
    Split *lst* into consecutive chunks of size *n*.

    The final chunk may be shorter than *n* if len(lst) is not evenly divisible.

    Args:
        lst: Any sequence.
        n:   Positive chunk size.

    Returns:
        A list of lists.

    Raises:
        ValueError: If *n* is not a positive integer.
    """
    if not isinstance(n, int) or n <= 0:
        raise ValueError(f"chunk size must be a positive integer, got {n!r}")
    return [lst[i : i + n] for i in range(0, len(lst), n)]
```

Edge cases covered:
- `n <= 0` or non-integer → `ValueError` with the bad value in the message
- empty `lst` → returns `[]` (the `range` produces nothing)
- `len(lst)` not divisible by `n` → last slice is naturally shorter (Python slice never raises on out-of-bounds)
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=1; wall=11.2s; answer_chars=1195; files_added=[]; files_modified=[]; files_deleted=[]

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
        A list of sublists (same type as lst if sliceable, otherwise list).

    Raises:
        ValueError: If n is not a positive integer.
    """
    if not isinstance(n, int) or n <= 0:
        raise ValueError(f"chunk size must be a positive integer, got {n!r}")
    return [lst[i : i + n] for i in range(0, len(lst), n)]
```

Usage:

```python
chunk([1, 2, 3, 4, 5], 2)  # [[1, 2], [3, 4], [5]]
chunk([], 3)                # []
chunk([1, 2], 10)           # [[1, 2]]
chunk([1, 2], 0)            # ValueError: chunk size must be a positive integer, got 0
```

One thing to watch: the docstring says the return is "a list of sublists", but `lst[i:i+n]` preserves the input type for strings and tuples too — `chunk("hello", 2)` yields `['he', 'll', 'o']`. If callers will pass non-list sequences and need consistent `list` output, wrap the comprehension with `list(...)`: `[list(lst[i:i+n]) for ...]`.
````
