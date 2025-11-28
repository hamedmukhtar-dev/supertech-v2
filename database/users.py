# database/users.py
import sqlite3
import os

DB_PATH = "users.db"

def init_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            role TEXT,
            country TEXT,
            ip TEXT,
            lang TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_user(email, role, country, ip, lang):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?, ?)",
              (email, role, country, ip, lang))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT email, role, country, ip, lang FROM users")
    data = c.fetchall()
    conn.close()
    return data