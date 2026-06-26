def format_name(full_name):
    """Format a person's name as 'Last, First'.

    Args:
        full_name: A string of the form 'First Last'.

    Raises:
        ValueError: If full_name does not contain exactly one space-separated
            first and last component.
    """
    parts = full_name.split(' ', 1)
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise ValueError(
            f"format_name expects a 'First Last' string, got: {full_name!r}"
        )
    first, last = parts
    return f"{last}, {first}"
