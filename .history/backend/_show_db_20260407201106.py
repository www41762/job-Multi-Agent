"""Show how data is actually stored in the SQLite DB"""
import sqlite3, os, json

db_path = os.path.join("data", "vector_db", "global_memory.db")
print("=" * 60)
print(f"DATABASE FILE: {os.path.abspath(db_path)}")
print(f"File size: {os.path.getsize(db_path)} bytes")
print("=" * 60)

conn = sqlite3.connect(db_path)

# 1. All tables
print("\n[1] TABLES")
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
for t in tables:
    print(f"  - {t[0]}")

# 2. sessions
print("\n[2] SESSIONS TABLE (session data + analysis results)")
cols = conn.execute("PRAGMA table_info(sessions)").fetchall()
print(f"  Columns: {[c[1] for c in cols]}")
rows = conn.execute("SELECT session_id, title, created_at, updated_at FROM sessions LIMIT 10").fetchall()
print(f"  Total records: {len(rows)}")
for r in rows:
    title = r[1] if r[1] else "(untitled)"
    print(f"    ID={r[0]}, Title={title}, Created={r[2]}, Updated={r[3]}")

# 3. chat_messages
print("\n[3] CHAT_MESSAGES TABLE")
count = conn.execute("SELECT COUNT(*) FROM chat_messages").fetchone()[0]
print(f"  Total messages: {count}")
sample = conn.execute("SELECT session_id, role, substr(content, 1, 50), created_at FROM chat_messages ORDER BY id DESC LIMIT 5").fetchall()
for s in sample:
    print(f"    [{s[0]}] {s[1]}: {s[2]}...  ({s[3]})")

# 4. user_profile
print("\n[4] USER_PROFILE TABLE (long-term memory)")
profiles = conn.execute("SELECT user_id, weaknesses, strong_skills, last_updated FROM user_profile").fetchall()
if profiles:
    for p in profiles:
        w = json.loads(p[1]) if p[1] else []
        s = json.loads(p[2]) if p[2] else []
        print(f"  User: {p[0]}")
        print(f"    Weaknesses ({len(w)}): {w}")
        print(f"    Skills ({len(s)}): {s}")
        print(f"    Last updated: {p[3]}")
else:
    print("  (empty - will be populated after first analysis)")

conn.close()
print("\n" + "=" * 60)
