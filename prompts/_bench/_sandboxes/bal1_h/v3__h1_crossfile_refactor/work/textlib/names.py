def format_name(full_name):
    """Format a person's name as 'Last, First'.

    Args:
        full_name: A string with at least two whitespace-separated tokens,
                   e.g. 'Ada Lovelace'. The last token is treated as the
                   last name; everything before it is the first name.

    Raises:
        ValueError: If full_name contains fewer than two tokens.
    """
    parts = full_name.rsplit(" ", 1)
    if len(parts) < 2:
        raise ValueError(
            f"format_name requires 'First Last' but got: {full_name!r}"
        )
    first, last = parts
    return f"{last}, {first}"
