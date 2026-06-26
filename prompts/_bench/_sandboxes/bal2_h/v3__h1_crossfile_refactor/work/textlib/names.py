def format_name(full_name):
    """Format a person's name as 'Last, First'.

    full_name: a single string, e.g. 'Ada Lovelace'.
    The last whitespace-delimited token is treated as the last name;
    everything before it is the first name.
    """
    first, last = full_name.rsplit(" ", 1)
    return f"{last}, {first}"
