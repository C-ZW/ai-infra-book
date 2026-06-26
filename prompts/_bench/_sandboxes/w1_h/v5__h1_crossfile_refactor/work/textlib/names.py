def format_name(full_name):
    """Format a person's name as 'Last, First'.

    full_name must be two whitespace-separated tokens, e.g. 'Ada Lovelace'.
    Raises ValueError if the string does not contain exactly one space-separated
    first and last component.
    """
    parts = full_name.split()
    if len(parts) != 2:
        raise ValueError(
            f"format_name expects 'First Last', got {full_name!r}"
        )
    first, last = parts
    return f"{last}, {first}"
