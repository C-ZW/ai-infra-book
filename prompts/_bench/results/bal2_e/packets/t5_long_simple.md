# Judge packet — task `t5_long_simple` (long/simple, text)

## The task given to each candidate

> Write a Python function chunk(lst, n) that splits lst into consecutive chunks of size n; the final chunk may be shorter. Include a docstring and sensible handling of n <= 0.

## What to reward / penalize

Correct, idiomatic code with edge-case handling (n<=0 raises or documented behavior; empty list) and a useful docstring. Penalize over-commenting/narration, bugs, or ignoring the n<=0 requirement.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=1; wall=9.8s; answer_chars=1062; files_added=[]; files_modified=[]; files_deleted=[]

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
        raise ValueError(f"Chunk size must be a positive integer, got {n}")
    return [lst[i:i + n] for i in range(0, len(lst), n)]
```

**Failure modes worth noting:**

- `n <= 0` — raises `ValueError` with the bad value in the message rather than producing an infinite loop (`range(0, len, 0)` would raise `ValueError` from `range` anyway, but with a cryptic message).
- Empty list — `range(0, 0, n)` is empty, so returns `[]` naturally; no special case needed.
- `n > len(lst)` — returns a single-element list containing all of `lst`; that's correct per the spec.

**What's the most dangerous unhandled case here?** If the caller passes a non-sequence iterable (e.g. a generator), slicing silently fails with `TypeError`. Should `chunk` accept iterables by converting with `lst = list(lst)` first, or is it intentionally sequence-only?
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=1; wall=7.4s; answer_chars=893; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
```python
def chunk(lst, n):
    """
    Split lst into consecutive chunks of size n.

    The final chunk may be shorter than n if len(lst) is not evenly divisible.

    Args:
        lst: Any sequence.
        n:   Chunk size. Must be a positive integer.

    Returns:
        A list of lists.

    Raises:
        ValueError: If n is less than or equal to 0.
    """
    if n <= 0:
        raise ValueError(f"Chunk size must be a positive integer, got {n!r}")
    return [lst[i : i + n] for i in range(0, len(lst), n)]
```

Calling `chunk([], n)` safely returns `[]`. The `ValueError` carries the bad value so the caller knows exactly what was passed.

What's the most dangerous unhandled case for your use: could `lst` be a lazy iterator rather than an indexable sequence? If so, slicing silently returns empty chunks — you'd want to materialise it first with `lst = list(lst)` at the top.
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=1; wall=8.5s; answer_chars=1064; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
```python
def chunk(lst, n):
    """
    Split lst into consecutive chunks of size n.

    The final chunk may be shorter than n if len(lst) is not a multiple of n.

    Args:
        lst: Any sequence supporting slicing.
        n:   Chunk size; must be a positive integer.

    Returns:
        A list of sub-lists.

    Raises:
        ValueError: If n <= 0.
    """
    if n <= 0:
        raise ValueError(f"Chunk size must be a positive integer, got {n!r}")
    return [lst[i : i + n] for i in range(0, len(lst), n)]
```

Edge cases covered:
- `n <= 0` → `ValueError` with the bad value in the message (silent truncation to empty or infinite loop would be worse)
- empty `lst` → returns `[]` (the `range` is empty, no special case needed)
- `n > len(lst)` → returns one chunk containing the whole list

Dangerous unhandled case: `lst` is a lazy iterator (generator, file object). `len()` and slicing both fail. If callers might pass iterables, `lst = list(lst)` at the top, or replace with `itertools.islice` — worth deciding before this lands in shared code.
````

### Candidate D

Behavioral telemetry: exit=0; timed_out=False; turns=1; wall=7.3s; answer_chars=972; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
```python
def chunk(lst, n):
    """
    Split *lst* into consecutive chunks of size *n*.

    The final chunk may be shorter than *n* if len(lst) is not a multiple of n.

    Args:
        lst: Any sequence (list, tuple, str, …).
        n:   Positive integer chunk size.

    Returns:
        A list of sub-lists.

    Raises:
        ValueError: If *n* is not a positive integer.
    """
    if not isinstance(n, int) or n <= 0:
        raise ValueError(f"chunk size must be a positive integer, got {n!r}")
    return [lst[i : i + n] for i in range(0, len(lst), n)]
```

Edge cases covered:
- `n <= 0` and non-integer `n` raise `ValueError` with a useful message.
- Empty `lst` returns `[]` (the `range` produces no iterations).
- Works on any sliceable sequence — not just `list`.

What happens if `lst` is a lazy iterator (generator, file object)? It won't slice — you'd need to materialise it first with `list(lst)`. Worth guarding against if callers might pass one.
````
