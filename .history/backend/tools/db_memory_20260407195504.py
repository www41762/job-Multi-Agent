# -*- coding: utf-8 -*-
"""基于SQLite的长期记忆存储，支持会话持久化、用户画像（弱项/技能）"""
import sqlite3
import os
import json
from typing import List, Optional
from config.config import VECTOR_DB_DIR

DB_PATH = os.path.join(VECTOR_DB_DIR, "global_memory.db")


class GlobalSQLMemory:
    """基于 SQLite 的长期记忆存储，支持会话持久化、用户画像（弱项/技能）"""

    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        os.makedirs(VECTOR_DB_DIR, exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self._init_db()
        self._ensure_session()

    def _init_db(self):
        cursor = self.conn.cursor()
        # 1. 会话表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                title TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                analysis_results TEXT,
                context_data TEXT
            )
        ''')
        # 兼容旧表：如果缺少 title/updated_at 列则动态添加
        try:
            cursor.execute("ALTER TABLE sessions ADD COLUMN title TEXT DEFAULT ''")
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE sessions ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        except Exception:
            pass
        # 2. 聊天历史表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                role TEXT,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # 3. 长期用户画像表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_profile (
                user_id TEXT PRIMARY KEY,
                weaknesses TEXT,
                strong_skills TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def _ensure_session(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT session_id FROM sessions WHERE session_id=?", (self.session_id,))
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO sessions (session_id, analysis_results, context_data) VALUES (?, ?, ?)",
                (self.session_id, '{}', '{}')
            )
            self.conn.commit()

    # --- 短期会话记忆 (Session Memory) ---

    def save_analysis_result(self, key: str, result: dict):
        """保存分析结果"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT analysis_results FROM sessions WHERE session_id=?", (self.session_id,))
        row = cursor.fetchone()
        data = json.loads(row[0]) if row and row[0] else {}
        data[key] = result
        cursor.execute(
            "UPDATE sessions SET analysis_results=? WHERE session_id=?",
            (json.dumps(data, ensure_ascii=False), self.session_id)
        )
        self.conn.commit()

    def get_analysis_result(self, key: str) -> Optional[dict]:
        """获取分析结果"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT analysis_results FROM sessions WHERE session_id=?", (self.session_id,))
        row = cursor.fetchone()
        if row and row[0]:
            return json.loads(row[0]).get(key)
        return None

    def get_all_analysis_results(self) -> dict:
        """获取所有分析结果"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT analysis_results FROM sessions WHERE session_id=?", (self.session_id,))
        row = cursor.fetchone()
        if row and row[0]:
            return json.loads(row[0])
        return {}

    def add_chat_message(self, role: str, content: str):
        """添加聊天消息"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO chat_messages (session_id, role, content) VALUES (?, ?, ?)",
            (self.session_id, role, content)
        )
        self.conn.commit()

    def get_chat_history(self, limit: int = 50) -> List[dict]:
        """获取最近的聊天历史"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT role, content FROM chat_messages WHERE session_id=? ORDER BY id ASC LIMIT ?",
            (self.session_id, limit)
        )
        return [{"role": row[0], "content": row[1]} for row in cursor.fetchall()]

    def set_context(self, key: str, value):
        """设置上下文信息"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT context_data FROM sessions WHERE session_id=?", (self.session_id,))
        row = cursor.fetchone()
        data = json.loads(row[0]) if row and row[0] else {}
        data[key] = value
        cursor.execute(
            "UPDATE sessions SET context_data=? WHERE session_id=?",
            (json.dumps(data, ensure_ascii=False), self.session_id)
        )
        self.conn.commit()

    def get_context(self, key: str, default=None):
        """获取上下文信息"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT context_data FROM sessions WHERE session_id=?", (self.session_id,))
        row = cursor.fetchone()
        if row and row[0]:
            return json.loads(row[0]).get(key, default)
        return default

    def rename_session(self, title: str):
        """重命名会话"""
        cursor = self.conn.cursor()
        cursor.execute("UPDATE sessions SET title=? WHERE session_id=?", (title, self.session_id))
        self.conn.commit()

    def get_session_info(self) -> dict:
        """获取会话信息（含标题、时间）"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT session_id, title, created_at, updated_at FROM sessions WHERE session_id=?",
            (self.session_id,)
        )
        row = cursor.fetchone()
        if row:
            return {
                "session_id": row[0],
                "title": row[1] or "",
                "created_at": row[2] or "",
                "updated_at": row[3] or "",
            }
        return {"session_id": self.session_id, "title": "", "created_at": "", "updated_at": ""}

    def touch_updated(self):
        """更新会话的 updated_at 时间戳"""
        cursor = self.conn.cursor()
        cursor.execute("UPDATE sessions SET updated_at=CURRENT_TIMESTAMP WHERE session_id=?", (self.session_id,))
        self.conn.commit()

    def clear(self):
        """清除当前会话的所有记忆"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM chat_messages WHERE session_id=?", (self.session_id,))
        cursor.execute("DELETE FROM sessions WHERE session_id=?", (self.session_id,))
        self.conn.commit()

    def clear_chat_only(self):
        """仅清空聊天记录，保留分析结果"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM chat_messages WHERE session_id=?", (self.session_id,))
        self.conn.commit()

    # --- 长期用户画像记忆 (Long-term User Profile) ---

    def update_user_weakness(self, new_weakness: str, user_id: str = "default_user"):
        """记录用户面试弱项（跨会话持久化）"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT weaknesses FROM user_profile WHERE user_id=?", (user_id,))
        row = cursor.fetchone()

        weaknesses = []
        if row and row[0]:
            weaknesses = json.loads(row[0])

        if new_weakness not in weaknesses:
            weaknesses.append(new_weakness)

        if not row:
            cursor.execute(
                "INSERT INTO user_profile (user_id, weaknesses, strong_skills) VALUES (?, ?, ?)",
                (user_id, json.dumps(weaknesses, ensure_ascii=False), '[]')
            )
        else:
            cursor.execute(
                "UPDATE user_profile SET weaknesses=?, last_updated=CURRENT_TIMESTAMP WHERE user_id=?",
                (json.dumps(weaknesses, ensure_ascii=False), user_id)
            )
        self.conn.commit()

    def update_user_strength(self, new_skill: str, user_id: str = "default_user"):
        """记录用户优势技能（跨会话持久化）"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT strong_skills FROM user_profile WHERE user_id=?", (user_id,))
        row = cursor.fetchone()

        skills = []
        if row and row[0]:
            skills = json.loads(row[0])

        if new_skill not in skills:
            skills.append(new_skill)

        if not row:
            cursor.execute(
                "INSERT INTO user_profile (user_id, weaknesses, strong_skills) VALUES (?, ?, ?)",
                (user_id, '[]', json.dumps(skills, ensure_ascii=False))
            )
        else:
            cursor.execute(
                "UPDATE user_profile SET strong_skills=?, last_updated=CURRENT_TIMESTAMP WHERE user_id=?",
                (json.dumps(skills, ensure_ascii=False), user_id)
            )
        self.conn.commit()

    def get_user_profile(self, user_id: str = "default_user") -> dict:
        """获取用户长期画像"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT weaknesses, strong_skills FROM user_profile WHERE user_id=?", (user_id,))
        row = cursor.fetchone()
        if row:
            return {
                "weaknesses": json.loads(row[0]) if row[0] else [],
                "strong_skills": json.loads(row[1]) if row[1] else []
            }
        return {"weaknesses": [], "strong_skills": []}


def get_sql_memory_store(session_id: str) -> GlobalSQLMemory:
    """获取指定会话的记忆存储"""
    return GlobalSQLMemory(session_id)


def list_sql_sessions() -> List[str]:
    """列出所有会话ID"""
    os.makedirs(VECTOR_DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT session_id FROM sessions ORDER BY updated_at DESC, created_at DESC")
        return [row[0] for row in cursor.fetchall()]
    except Exception:
        return []
    finally:
        conn.close()


def list_sql_sessions_rich() -> List[dict]:
    """列出所有会话（含标题、时间、消息数量等丰富信息）"""
    os.makedirs(VECTOR_DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT s.session_id, s.title, s.created_at, s.updated_at, s.analysis_results,
                   (SELECT COUNT(*) FROM chat_messages cm WHERE cm.session_id = s.session_id) as chat_count
            FROM sessions s
            ORDER BY s.updated_at DESC, s.created_at DESC
        """)
        results = []
        for row in cursor.fetchall():
            has_analysis = False
            try:
                ar = json.loads(row[4]) if row[4] else {}
                has_analysis = bool(ar)
            except Exception:
                pass
            results.append({
                "session_id": row[0],
                "title": row[1] or "",
                "created_at": row[2] or "",
                "updated_at": row[3] or "",
                "has_analysis": has_analysis,
                "chat_count": row[5] or 0,
            })
        return results
    except Exception:
        return []
    finally:
        conn.close()
