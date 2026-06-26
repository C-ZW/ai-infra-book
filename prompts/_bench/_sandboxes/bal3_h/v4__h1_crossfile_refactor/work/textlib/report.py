from .names import format_name


def roster(people):
    """people: list of full-name strings (e.g. ['Ada Lovelace']) -> sorted 'Last, First' lines."""
    return sorted(format_name(full_name) for full_name in people)
