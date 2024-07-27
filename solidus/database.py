import sqlite3
from sqlite3 import Error


def get_db():
    conn = None
    try:
        conn = sqlite3.connect('database.db')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                method TEXT NOT NULL,
                payload TEXT NOT NULL
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS statistics (
                id INTEGER PRIMARY KEY,
                numRequestSuccess INTEGER NOT NULL,
                numRequestFailed INTEGER NOT NULL
            )
        ''')
        conn.execute('INSERT OR IGNORE INTO statistics (id, numRequestSuccess, numRequestFailed) VALUES (1, 0, 0)')
    except Error as e:
        print(e)
    return conn
