"""One-time script to add missing columns to sessions table"""
import sqlite3
import os

db_path = os.path.join("data", "vector_db", "global_memory.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

for col_sql in [
    "ALTER TABLE sessions ADD COLUMN title TEXT DEFAULT ''",
    "ALTER TABLE sessions ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
]:
    try:
        cursor.execute(col_sql)
        print(f"OK: {col_sql}")
    except Exception as e:
        print(f"Skip: {e}")

conn.commit()

cursor.execute("PRAGMA table_info(sessions)")
cols = [r[1] for r in cursor.fetchall()]
print("Final columns:", cols)
conn.close()
