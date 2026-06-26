from .names import format_name


def roster(people):
    """people: list of 'First Last' strings -> sorted 'Last, First' lines."""
    return sorted(format_name(name) for name in people)
