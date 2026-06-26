import argparse

from .model import Task
from .storage import load, save

STORE = "tasks.json"


def cmd_add(args):
    try:
        tasks = load(STORE)
    except FileNotFoundError:
        tasks = []
    next_id = max((t.id for t in tasks), default=0) + 1
    tasks.append(Task(id=next_id, title=args.title))
    save(tasks, STORE)
    print("added #{}".format(next_id))


def cmd_list(args):
    try:
        tasks = load(STORE)
    except FileNotFoundError:
        tasks = []
    for t in tasks:
        mark = "x" if t.done else " "
        print("[{}] #{} {}".format(mark, t.id, t.title))


def build_parser():
    p = argparse.ArgumentParser(prog="todo")
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add")
    a.add_argument("title")
    a.set_defaults(func=cmd_add)
    ls = sub.add_parser("list")
    ls.set_defaults(func=cmd_list)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
