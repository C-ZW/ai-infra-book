from app.config import CONFIG


def connect(host):
    """Return a connection descriptor honoring the global timeout/retries."""
    return {
        "host": host,
        "timeout": CONFIG["timeout"],
        "retries": CONFIG["retries"],
    }
