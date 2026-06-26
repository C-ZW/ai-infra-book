import os
import sqlite3

DB = "app.db"


def reset():
    """Drop and recreate the schema."""
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute("DROP TABLE IF EXISTS users")
    cur.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT)")
    con.commit()
    con.close()
    print("reset done")


if __name__ == "__main__":
    reset()
