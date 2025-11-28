# core/finance/ledger.py
import sqlite3

DB = "finance.db"

def init_ledger():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT,
            amount REAL,
            type TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def add_transaction(user, amount, type):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT INTO ledger (user, amount, type) VALUES (?, ?, ?)",
              (user, amount, type))
    conn.commit()
    conn.close()

def get_transactions():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT * FROM ledger ORDER BY timestamp DESC")
    data = c.fetchall()
    conn.close()
    return data