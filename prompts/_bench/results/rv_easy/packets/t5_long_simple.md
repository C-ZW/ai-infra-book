# Judge packet — task `t5_long_simple` (long/simple, text)

## The task given to each candidate

> Write a Python function chunk(lst, n) that splits lst into consecutive chunks of size n; the final chunk may be shorter. Include a docstring and sensible handling of n <= 0.

## What to reward / penalize

Correct, idiomatic code with edge-case handling (n<=0 raises or documented behavior; empty list) and a useful docstring. Penalize over-commenting/narration, bugs, or ignoring the n<=0 requirement.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=1; wall=16.2s; answer_chars=1895; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
```python
def chunk(lst, n):
    """Split lst into consecutive chunks of size n.

    The final chunk may be shorter if len(lst) is not a multiple of n.

    Args:
        lst: A sequence (list, tuple, str, ...) supporting slicing.
        n: Positive integer chunk size.

    Returns:
        A list of slices of lst, each of length n except possibly the last.
        An empty input yields an empty list.

    Raises:
        TypeError: If n is not an integer (bool is rejected too).
        ValueError: If n <= 0.
    """
    if isinstance(n, bool) or not isinstance(n, int):
        raise TypeError(f"n must be an int, got {type(n).__name__}")
    if n <= 0:
        raise ValueError(f"n must be a positive integer, got {n}")
    return [lst[i:i + n] for i in range(0, len(lst), n)]
```

Design notes on the failure cases, since they're the whole point here:

- **`n <= 0`** → `ValueError`. Returning `[]` or `[lst]` would silently swallow a caller bug (e.g. a miscomputed batch size); raising forces it to surface. `range(0, len, 0)` would also throw a less informative `ValueError` anyway.
- **non-int `n`** (e.g. `2.0`, `"2"`) → `TypeError`. A float would make `lst[i:i+n]` raise a cryptic slice error deep in the comprehension; catching it at the boundary gives a clear message.
- **`bool` rejected** — `True`/`False` are `int` subclasses, so without the explicit guard `chunk(x, True)` would "work" as `n=1`. Almost always a bug, so it's blocked.
- **empty `lst`** → `[]`, naturally.
- Works on any sliceable sequence (`str`, `tuple`, `list`); chunks preserve the input type.

One thing I did *not* do: handle generators/iterators. This relies on slicing and `len()`, so a lazy iterator would raise `TypeError` on `len()`.

Do you need a variant that consumes arbitrary iterables (generators, streams) lazily via `itertools.islice`, or is sliceable-sequence input the contract you want?
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=3; wall=23.9s; answer_chars=1210; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
Verified — all cases pass.

```python
def chunk(lst, n):
    """Split lst into consecutive chunks of size n.

    Returns a list of lists; the final chunk may be shorter if len(lst)
    is not a multiple of n. An empty input yields an empty list.

    Args:
        lst: A sequence to split (list, tuple, str, etc.).
        n: Positive integer chunk size.

    Returns:
        list: Consecutive chunks, each of at most n elements.

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

On `n <= 0` I raise `ValueError` rather than guessing intent — returning `[]` or `[lst]` would silently hide a caller bug (e.g. an `n` computed as `len(other)//k` that hit zero). The `bool` guard matters because `True == 1` in Python, so `chunk(lst, True)` would otherwise be accepted as `n=1`.

Want the invalid-`n` case to return a fallback (e.g. one chunk of the whole list) instead of raising, given how this gets called?
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=4; wall=25.8s; answer_chars=1196; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
`/Users/cheweichen/chunk.py:1` already contains a correct implementation, and it passes the smoke tests.

```python
def chunk(lst, n):
    """Split lst into consecutive chunks of size n; the final chunk may be shorter.
    ...
    """
    if isinstance(n, bool) or not isinstance(n, int):
        raise TypeError(f"n must be an int, got {type(n).__name__}")
    if n <= 0:
        raise ValueError(f"n must be a positive integer, got {n}")
    return [lst[i:i + n] for i in range(0, len(lst), n)]
```

Behavior verified:
- `chunk([1,2,3,4,5], 2)` → `[[1, 2], [3, 4], [5]]` (short final chunk)
- `chunk([], 3)` → `[]`
- `chunk('abcdef', 4)` → `['abcd', 'ef']` (works on any sliceable)
- `n <= 0` → `ValueError` instead of an infinite loop (a `range` with step 0 would raise, but step `<0` would silently return `[]` — so the guard is load-bearing, not cosmetic)
- `bool` is rejected before the `int` check, since `True == 1` would otherwise sneak through as a chunk size.

One design choice worth surfacing: this returns a fully materialized list. If `lst` is large, that doubles peak memory. Do you want a generator variant (`yield lst[i:i+n]`) for streaming, or is the list return what you need?
````
