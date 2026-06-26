import os
import sqlite3

DB = "app.db"


def reset():
    """Drop and recreate the schema."""
    tmp = DB + ".new"
    con = sqlite3.connect(tmp)
    try:
        cur = con.cursor()
        cur.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT)")
        con.commit()
    except Exception:
        con.close()
        os.remove(tmp)
        raise
    con.close()
    if os.path.exists(DB):
        os.remove(DB)
    os.rename(tmp, DB)
    print("reset done")


if __name__ == "__main__":
    reset()
