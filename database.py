import sqlite3

def db_init():
    con = sqlite3.connect('data/database.db')
    cur = con.cursor()

    # create the daily_stats table if it doesn't exist
    cur.execute("CREATE TABLE IF NOT EXISTS daily_stats (" \
            "user_id TEXT," \
            "date TEXT," \
            "cringe INTEGER," \
            "sus INTEGER," \
            "PRIMARY KEY (user_id, date)" \
        ")"
    )
    con.commit()

    # verify that the table was created successfully
    res = cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='daily_stats'")
    if res.fetchone() is None:
        raise RuntimeError("Failed to create or access the daily_stats table in the database. Please check the database file and ensure it is accessible.")

    con.close()