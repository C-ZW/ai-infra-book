def format_name(full_name):
    """Format a person's name as 'Last, First'.

    Args:
        full_name: A string like 'Ada Lovelace'. The last whitespace-delimited
                   token is treated as the last name; everything before it is
                   the first name (supports multi-word first names).

    Raises:
        ValueError: If full_name is empty or contains no space.
    """
    if not isinstance(full_name, str) or not full_name.strip():
        raise ValueError(f"format_name requires a non-empty string, got {full_name!r}")
    parts = full_name.strip().rsplit(None, 1)
    if len(parts) < 2:
        raise ValueError(
            f"format_name requires 'First Last' format with at least one space, got {full_name!r}"
        )
    first, last = parts
    return f"{last}, {first}"
