import os
import sqlite3
import tempfile

DB = "app.db"


def reset():
    """Drop and recreate the schema.

    Writes to a temp file first so the original DB is untouched if schema
    creation fails.  The temp file is renamed over DB only after a successful
    commit.
    """
    tmp_fd, tmp_path = tempfile.mkstemp(dir=".", prefix=".reset_db_tmp_")
    os.close(tmp_fd)
    try:
        con = sqlite3.connect(tmp_path)
        cur = con.cursor()
        cur.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT)")
        con.commit()
        con.close()
    except Exception:
        os.unlink(tmp_path)
        raise
    os.replace(tmp_path, DB)
    print("reset done")


if __name__ == "__main__":
    reset()
