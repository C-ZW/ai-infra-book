from .names import format_name


def roster(people):
    """people: list of (first, last) tuples -> sorted 'Last, First' lines."""
    return sorted(format_name(first, last) for first, last in people)
