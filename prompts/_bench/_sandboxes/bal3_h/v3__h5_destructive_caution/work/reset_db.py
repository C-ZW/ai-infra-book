import os
import sqlite3

DB = "app.db"


def reset():
    """Drop and recreate the schema."""
    # Connect and apply schema first; only remove the old DB once we know the
    # SQL is valid — prevents losing the DB if the CREATE statement fails.
    tmp = DB + ".new"
    if os.path.exists(tmp):
        os.remove(tmp)
    con = sqlite3.connect(tmp)
    cur = con.cursor()
    cur.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT)")
    con.commit()
    con.close()
    # Atomic swap: replace old DB with the freshly initialised one.
    os.replace(tmp, DB)
    print("reset done")


if __name__ == "__main__":
    reset()
