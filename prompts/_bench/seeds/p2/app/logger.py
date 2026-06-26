from app.config import CONFIG


def log(message):
    """Print message only when verbose is enabled."""
    if CONFIG["verbose"]:
        print(message)
    return CONFIG["verbose"]
