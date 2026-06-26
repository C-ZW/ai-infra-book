from app.config import CONFIG
from app.client import connect


def run(host):
    """Connect and return the effective deadline (timeout) used."""
    conn = connect(host)
    deadline = CONFIG["timeout"]
    return {"conn": conn, "deadline": deadline}
