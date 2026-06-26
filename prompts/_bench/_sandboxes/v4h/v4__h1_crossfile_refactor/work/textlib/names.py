def format_name(full_name):
    """Format a person's name as 'Last, First'.

    Args:
        full_name: A string containing at least two whitespace-separated words,
                   e.g. 'Ada Lovelace' or 'Mary Ann Evans'.

    Returns:
        'Last, First' — last word becomes Last, everything before it becomes First.

    Raises:
        ValueError: If full_name contains fewer than two words.
    """
    parts = full_name.rsplit(" ", 1)
    if len(parts) < 2:
        raise ValueError(
            f"format_name requires at least two words, got: {full_name!r}"
        )
    first, last = parts
    return f"{last}, {first}"
