def format_name(full_name):
    """Format a person's name as 'Last, First'.

    Splits on the rightmost space, so 'Mary Ann Evans' → 'Evans, Mary Ann'.
    Raises ValueError if full_name contains no space (cannot determine last name).
    """
    parts = full_name.rsplit(" ", 1)
    if len(parts) < 2:
        raise ValueError(f"format_name requires at least a first and last name, got: {full_name!r}")
    first, last = parts
    return f"{last}, {first}"
