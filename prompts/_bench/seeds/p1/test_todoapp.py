import os
import tempfile

from todoapp.model import Task
from todoapp.storage import save, load


def test_roundtrip():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "t.json")
        save([Task(1, "a"), Task(2, "b", done=True)], path)
        got = load(path)
        assert got[0].title == "a" and got[1].done is True
