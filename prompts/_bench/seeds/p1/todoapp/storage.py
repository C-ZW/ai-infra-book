import json

from .model import Task


def save(tasks, path):
    """Serialize a list of Task to JSON at path."""
    with open(path, "w") as f:
        json.dump([{"id": t.id, "title": t.title, "done": t.done} for t in tasks], f)


def load(path):
    """Load a list of Task from JSON at path."""
    with open(path) as f:
        return [Task(id=d["id"], title=d["title"], done=d["done"]) for d in json.load(f)]
