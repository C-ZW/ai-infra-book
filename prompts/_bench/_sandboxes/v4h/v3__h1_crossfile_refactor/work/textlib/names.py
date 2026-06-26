def format_name(full_name):
    """Format a person's name as 'Last, First'.

    Splits on the rightmost space so middle names stay with the first name,
    e.g. 'Mary Ann Evans' -> 'Evans, Mary Ann'.

    Raises ValueError if full_name contains no space (can't split first/last).
    """
    if not isinstance(full_name, str):
        raise TypeError(f"full_name must be a str, got {type(full_name).__name__!r}")
    parts = full_name.rsplit(" ", 1)
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise ValueError(f"full_name must contain at least one space: {full_name!r}")
    first, last = parts
    return f"{last}, {first}"
