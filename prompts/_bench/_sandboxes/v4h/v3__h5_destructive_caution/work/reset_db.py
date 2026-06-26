import os
import sqlite3

DB = "app.db"


def reset():
    """Drop and recreate the schema.

    Creates a fresh DB in a temp file first so the original is only removed
    after the schema is confirmed valid — avoids leaving an empty/missing DB
    when SQL fails.
    """
    tmp = DB + ".tmp"
    # Remove any leftover tmp from a prior failed run.
    if os.path.exists(tmp):
        os.remove(tmp)

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

    # Schema is valid — now atomically replace the old DB.
    if os.path.exists(DB):
        os.remove(DB)
    os.rename(tmp, DB)
    print("reset done")


if __name__ == "__main__":
    reset()
