def format_name(full_name):
    """Format a person's name as 'Last, First'.

    Args:
        full_name: Full name string, e.g. 'Ada Lovelace'. The last
                   whitespace-separated token is treated as the last name;
                   everything before it is the first name / given names.

    Raises:
        ValueError: If full_name contains fewer than two whitespace-separated
                    parts (cannot determine a last name).
    """
    if not isinstance(full_name, str) or not full_name.strip():
        raise ValueError(f"full_name must be a non-empty string, got {full_name!r}")
    parts = full_name.rsplit(None, 1)
    if len(parts) < 2:
        raise ValueError(
            f"full_name must contain at least two words to determine a last name, got {full_name!r}"
        )
    first, last = parts
    return f"{last}, {first}"
