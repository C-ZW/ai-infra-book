from app.client import connect
from app.runner import run


def test_connect_defaults():
    c = connect("h1")
    assert c["timeout"] == 30 and c["retries"] == 3


def test_run_deadline():
    assert run("h1")["deadline"] == 30
