def format_name(full_name):
    """Format a person's name as 'Last, First'.

    Args:
        full_name: A string like 'Ada Lovelace'. The last whitespace-delimited
                   token is treated as the last name; everything before it is
                   the first name.

    Raises:
        ValueError: If full_name contains fewer than two whitespace-delimited
                    tokens (i.e. no space is present).
    """
    parts = full_name.rsplit(" ", 1)
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise ValueError(
            f"format_name expects 'First Last' (at least two tokens); got {full_name!r}"
        )
    first, last = parts
    return f"{last}, {first}"
