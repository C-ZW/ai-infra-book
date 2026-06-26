import os
import sqlite3

DB = "app.db"


def reset():
    """Drop and recreate the schema."""
    # Validate the DDL against a throw-away in-memory DB first so we never
    # delete the real file and then fail to recreate it.
    try:
        probe = sqlite3.connect(":memory:")
        probe.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT)")
        probe.close()
    except sqlite3.OperationalError as exc:
        raise RuntimeError(f"Schema DDL is invalid; aborting before touching {DB!r}: {exc}") from exc

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
