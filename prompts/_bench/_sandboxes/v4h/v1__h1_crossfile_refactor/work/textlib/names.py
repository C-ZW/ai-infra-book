def format_name(full_name):
    """Format a person's name as 'Last, First'.

    full_name must be a string containing at least one space, e.g. 'Ada Lovelace'.
    Raises ValueError for non-string input or a name missing a space.
    """
    if not isinstance(full_name, str):
        raise ValueError(
            f"format_name expects a str, got {type(full_name).__name__!r}"
        )
    parts = full_name.strip().rsplit(" ", 1)
    if len(parts) < 2 or not parts[0] or not parts[1]:
        raise ValueError(
            f"format_name requires 'First Last' with at least one space; got {full_name!r}"
        )
    first, last = parts
    return f"{last}, {first}"
