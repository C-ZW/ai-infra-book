from .names import format_name


def greeting(full_name):
    """Return a greeting line for a user given their full name ('First Last')."""
    return "Hello, " + format_name(full_name)
