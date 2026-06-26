def format_name(full_name):
    """Format a person's full name as 'Last, First'.

    Args:
        full_name: A string with at least two words, e.g. 'Ada Lovelace'.

    Returns:
        'Last, First' — last word becomes the surname; everything before it
        becomes the given name, preserving compound first names.

    Raises:
        ValueError: If full_name is empty or contains no space.
    """
    if not isinstance(full_name, str) or not full_name.strip():
        raise ValueError(f"full_name must be a non-empty string, got {full_name!r}")
    parts = full_name.strip().rsplit(" ", 1)
    if len(parts) < 2:
        raise ValueError(
            f"full_name must contain at least a first and last name, got {full_name!r}"
        )
    first, last = parts
    return f"{last}, {first}"
