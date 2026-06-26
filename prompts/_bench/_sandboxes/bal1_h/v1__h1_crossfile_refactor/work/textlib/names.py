def format_name(full_name):
    """Format a person's name as 'Last, First'.

    Accepts a single string (e.g. 'Ada Lovelace').  The last whitespace-
    separated token is treated as the last name; everything before it is the
    first name / given names.  Raises ValueError if no space is found.
    """
    parts = full_name.rsplit(" ", 1)
    if len(parts) != 2:
        raise ValueError(f"format_name expects 'First Last', got: {full_name!r}")
    first, last = parts
    return f"{last}, {first}"
