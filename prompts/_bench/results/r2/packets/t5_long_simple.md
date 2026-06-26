# Judge packet — task `t5_long_simple` (long/simple, text)

## The task given to each candidate

> Write a Python function chunk(lst, n) that splits lst into consecutive chunks of size n; the final chunk may be shorter. Include a docstring and sensible handling of n <= 0.

## What to reward / penalize

Correct, idiomatic code with edge-case handling (n<=0 raises or documented behavior; empty list) and a useful docstring. Penalize over-commenting/narration, bugs, or ignoring the n<=0 requirement.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=1; wall=15.8s; answer_chars=1567; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
```python
def chunk(lst, n):
    """Split lst into consecutive chunks of at most n items.

    Iterates over lst in steps of n, yielding successive slices. The final
    chunk holds the remainder and may be shorter than n. An empty input
    yields an empty list.

    Args:
        lst: A sliceable sequence (e.g. list, tuple, str).
        n: Positive integer chunk size.

    Returns:
        A list of slices of lst, each of length n except possibly the last.

    Raises:
        TypeError: If n is not an integer.
        ValueError: If n <= 0.
    """
    if isinstance(n, bool) or not isinstance(n, int):
        raise TypeError(f"n must be an int, got {type(n).__name__}")
    if n <= 0:
        raise ValueError(f"n must be positive, got {n}")
    return [lst[i:i + n] for i in range(0, len(lst), n)]
```

Notes on the failure cases, since they're the part that bites:
- `n <= 0` raises `ValueError` rather than looping forever (`range(0, len, 0)` would error anyway, but the message is opaely) or silently returning `[]`.
- `bool` is rejected explicitly because `True`/`False` are `int` subclasses in Python, so `chunk(lst, True)` would otherwise mean "chunks of 1" — almost never intended.
- Works on anything sliceable (`str`, `tuple`, `list`); chunks come back as the same type as `lst`.
- Empty `lst` → `[]`.

It does require `len()` and slicing, so it won't accept a bare generator. If you need to chunk a lazy iterator (unknown/infinite length, no `__getitem__`), that's a different implementation built on `itertools.islice` — want that version too?
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=1; wall=12.0s; answer_chars=1898; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
```python
def chunk(lst, n):
    """Split lst into consecutive chunks of size n.

    Yields successive sublists of lst, each of length n; the final
    chunk may be shorter if len(lst) is not divisible by n.

    Args:
        lst: A sequence (e.g. list) to split. Must support slicing.
        n: Desired chunk size. Must be a positive integer.

    Returns:
        A list of sublists, each a contiguous slice of lst. Returns an
        empty list when lst is empty.

    Raises:
        TypeError: If n is not an integer (bool is rejected too).
        ValueError: If n <= 0.

    Examples:
        >>> chunk([1, 2, 3, 4, 5], 2)
        [[1, 2], [3, 4], [5]]
        >>> chunk([], 3)
        []
    """
    if isinstance(n, bool) or not isinstance(n, int):
        raise TypeError(f"n must be an int, got {type(n).__name__}")
    if n <= 0:
        raise ValueError(f"n must be a positive integer, got {n}")
    return [lst[i:i + n] for i in range(0, len(lst), n)]
```

Why this shape rather than "it should be fine":

- `n <= 0` raises `ValueError` instead of returning silently. A `range(0, len, 0)` raises a bare `ValueError: range() arg 3 must not be zero`, and negatives produce an empty list quietly — both hide the caller's bug. Explicit beats either.
- `bool` is rejected before the `int` check, because `True == 1` would otherwise make `chunk(data, True)` silently "work" with chunk size 1.
- Slicing (`lst[i:i+n]`) means the last chunk is naturally short with no off-by-one math, and it works on any sliceable sequence (strings, tuples) — returning sublists of the same kind.

One thing I assumed: that you want an eager `list` of `list`s. If `lst` is huge or a one-shot iterable (a generator, a file), this materializes everything and will also fail on the non-sliceable input. Do you need a lazy, iterator-based version that streams chunks without holding the whole input in memory?
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=3; wall=43.3s; answer_chars=1775; files_added=['__pycache__/chunk.cpython-313.pyc', 'chunk.py']; files_modified=[]; files_deleted=[]

Answer:
````
All cases pass. Written to `chunk.py`.

```python
def chunk(lst, n):
    if isinstance(n, bool) or not isinstance(n, int):
        raise TypeError(f"n must be an int, got {type(n).__name__}")
    if n <= 0:
        raise ValueError(f"n must be a positive integer, got {n}")
    try:
        length = len(lst)
    except TypeError as exc:
        raise TypeError(f"lst must be a sized sequence, got {type(lst).__name__}") from exc
    return [list(lst[i:i + n]) for i in range(0, length, n)]
```

**Design choices, and why:**

- **`n <= 0` → `ValueError`** (not silent `[]` or a hang). Returning `[]` would mask a caller bug — they asked for an impossible chunk size and got "success" with no data. Raising forces the bug into the open at the call site. This is the "sensible handling" the spec asked for; `n=0` specifically would otherwise be an infinite loop or an opaque `range` error.
- **`bool` rejected before `int`** — `True == 1` in Python, so `chunk(data, True)` would silently chunk into size-1 pieces. Almost always a mistake, so it's caught.
- **`lst` validated for `len()`** — a generator has no length and can't be sliced; without the guard you'd get a confusing error deep in the comprehension. Note this is deliberate: the function requires a *re-readable, sized sequence*, not a one-shot iterator.
- **`list(lst[...])`** normalizes chunks to `list` regardless of input type (so `chunk("abcde", 2)` yields lists of chars, not substrings — consistent return type).

The most dangerous unhandled case left: **if a caller passes a huge `lst`, this materializes every chunk eagerly in memory at once.** Do you need a lazy/generator variant (`yield`ing chunks) for large or streaming inputs, where holding the full result list would be the thing that breaks at 3am?
````
