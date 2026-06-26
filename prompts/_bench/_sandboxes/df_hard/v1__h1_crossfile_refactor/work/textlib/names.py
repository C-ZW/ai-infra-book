def format_name(full_name):
    """Format a person's name as 'Last, First'.

    Args:
        full_name: A string like 'Ada Lovelace'. The last whitespace-separated
                   token is treated as the last name; everything before it is
                   the first name.

    Raises:
        ValueError: If full_name contains fewer than two whitespace-separated
                    tokens (no last name can be determined).
    """
    parts = full_name.rsplit(None, 1)
    if len(parts) < 2:
        raise ValueError(
            f"format_name requires at least a first and last name, got: {full_name!r}"
        )
    first, last = parts
    return f"{last}, {first}"
