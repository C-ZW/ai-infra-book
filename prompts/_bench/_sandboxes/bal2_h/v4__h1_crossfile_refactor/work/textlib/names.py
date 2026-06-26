def format_name(full_name):
    """Format a person's name as 'Last, First'.

    Args:
        full_name: Full name string, e.g. 'Ada Lovelace'.

    Returns:
        'Last, First' formatted string.

    Raises:
        ValueError: If full_name contains no space (cannot split first/last).
    """
    parts = full_name.rsplit(" ", 1)
    if len(parts) != 2:
        raise ValueError(f"format_name: expected 'First Last', got {full_name!r}")
    first, last = parts
    return f"{last}, {first}"
