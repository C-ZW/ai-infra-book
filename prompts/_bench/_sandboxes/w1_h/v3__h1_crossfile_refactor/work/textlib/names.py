def format_name(full_name):
    """Format a person's name as 'Last, First'.

    Accepts a full name string (e.g. 'Ada Lovelace').  The last
    whitespace-separated token is treated as the last name; everything
    before it is the first name / given names.
    """
    parts = full_name.rsplit(" ", 1)
    if len(parts) != 2:
        raise ValueError(f"format_name requires at least two name parts, got: {full_name!r}")
    first, last = parts
    return f"{last}, {first}"
