import os
import sqlite3

DB = "app.db"


def reset():
    """Drop and recreate the schema."""
    if os.path.exists(DB):
        os.remove(DB)
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT)")
    con.commit()
    con.close()
    print("reset done")


if __name__ == "__main__":
    reset()
