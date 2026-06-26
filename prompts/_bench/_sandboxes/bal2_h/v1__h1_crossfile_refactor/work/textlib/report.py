from .names import format_name


def roster(people):
    """people: list of full-name strings -> sorted 'Last, First' strings."""
    return sorted(format_name(name) for name in people)
