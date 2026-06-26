def format_name(full_name):
    """Format a person's name as 'Last, First'.

    Args:
        full_name: A string like 'Ada Lovelace'.

    Raises:
        ValueError: If full_name contains no space to split on.
    """
    parts = full_name.split(" ", 1)
    if len(parts) != 2:
        raise ValueError(f"format_name expects 'First Last', got: {full_name!r}")
    first, last = parts
    return f"{last}, {first}"
