import sqlite3
from datetime import datetime
from pathlib import Path
from config import DB_PATH

def connect():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TEXT NOT NULL,
        username TEXT NOT NULL,
        action TEXT NOT NULL,
        details TEXT
    );
    """)

    conn.commit()
    conn.close()


def user_exists(username: str) -> bool:
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM users WHERE username = ?;", (username,))
    exists = cur.fetchone() is not None
    conn.close()
    return exists


def create_user(username: str, password: str) -> bool: # returns False if user exists
    if user_exists(username):
        return False

    conn = connect()
    cur = conn.cursor()
    cur.execute("INSERT INTO users (username, password) VALUES (?, ?);", (username, password))
    conn.commit()
    conn.close()
    return True


def add_user(username: str, password: str):
    conn = connect()
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO users (username, password) VALUES (?, ?);", (username, password))
    conn.commit()
    conn.close()


def check_login(username: str, password: str) -> bool:
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM users WHERE username = ? AND password = ?;", (username, password))
    ok = cur.fetchone() is not None
    conn.close()
    return ok


def log_action(username: str, action: str, details: str = ""):
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO logs (ts, username, action, details) VALUES (?, ?, ?, ?);",
        (datetime.now().isoformat(timespec="seconds"), username, action, details)
    )
    conn.commit()
    conn.close()
