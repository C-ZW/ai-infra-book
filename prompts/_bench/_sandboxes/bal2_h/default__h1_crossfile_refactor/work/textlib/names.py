def format_name(full_name):
    """Format a person's name as 'Last, First'."""
    first, last = full_name.rsplit(" ", 1)
    return f"{last}, {first}"
