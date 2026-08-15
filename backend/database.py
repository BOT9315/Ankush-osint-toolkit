import sqlite3
import json
from datetime import datetime

DB_NAME = "osint.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS investigations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tool TEXT NOT NULL,
            target TEXT NOT NULL,
            result TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def save_result(tool, target, result):
    conn = get_connection()
    conn.execute(
        "INSERT INTO investigations (tool, target, result, created_at) VALUES (?, ?, ?, ?)",
        (tool, target, json.dumps(result), datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def get_history(limit=50, offset=0, tool=None):
    conn = get_connection()
    if tool and tool != "all":
        rows = conn.execute(
            "SELECT id, tool, target, result, created_at FROM investigations "
            "WHERE tool = ? ORDER BY id DESC LIMIT ? OFFSET ?",
            (tool, limit, offset)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, tool, target, result, created_at FROM investigations "
            "ORDER BY id DESC LIMIT ? OFFSET ?",
            (limit, offset)
        ).fetchall()
    conn.close()
    return [
        {"id": r["id"], "tool": r["tool"], "target": r["target"],
         "result": json.loads(r["result"]), "created_at": r["created_at"]}
        for r in rows
    ]


def delete_entry(entry_id):
    conn = get_connection()
    cur = conn.execute("DELETE FROM investigations WHERE id = ?", (entry_id,))
    conn.commit()
    deleted = cur.rowcount > 0
    conn.close()
    return deleted


def clear_history():
    conn = get_connection()
    conn.execute("DELETE FROM investigations")
    conn.commit()
    conn.close()


def get_stats():
    conn = get_connection()
    result = {
        "total": conn.execute("SELECT COUNT(*) FROM investigations").fetchone()[0],
        "usernames": conn.execute("SELECT COUNT(*) FROM investigations WHERE tool='username'").fetchone()[0],
        "emails": conn.execute("SELECT COUNT(*) FROM investigations WHERE tool='email'").fetchone()[0],
        "ips": conn.execute("SELECT COUNT(*) FROM investigations WHERE tool='ip'").fetchone()[0],
        "domains": conn.execute("SELECT COUNT(*) FROM investigations WHERE tool='domain'").fetchone()[0],
        "images": conn.execute("SELECT COUNT(*) FROM investigations WHERE tool='image'").fetchone()[0],
    }
    conn.close()
    return result
