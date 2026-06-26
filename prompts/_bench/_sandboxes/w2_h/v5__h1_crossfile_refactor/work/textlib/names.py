def format_name(full_name):
    """Format a person's name as 'Last, First'. Expects a 'First Last' string."""
    parts = full_name.split(" ", 1)
    if len(parts) != 2:
        raise ValueError(f"format_name expected 'First Last', got: {full_name!r}")
    first, last = parts
    return f"{last}, {first}"
