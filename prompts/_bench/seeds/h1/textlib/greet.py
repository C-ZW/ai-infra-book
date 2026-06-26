from .names import format_name


def greeting(first, last):
    """Return a greeting line for a user given first and last name."""
    return "Hello, " + format_name(first, last)
