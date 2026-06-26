import os
import sqlite3

DB = "app.db"


def reset():
    """Drop and recreate the schema."""
    tmp = DB + ".new"
    # Build the new DB first; only remove the old one once we know the schema is valid.
    if os.path.exists(tmp):
        os.remove(tmp)
    con = sqlite3.connect(tmp)
    cur = con.cursor()
    cur.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT)")
    con.commit()
    con.close()
    if os.path.exists(DB):
        os.remove(DB)
    os.rename(tmp, DB)
    print("reset done")


if __name__ == "__main__":
    reset()
