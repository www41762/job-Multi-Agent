"""RAG工具 - 向量库操作，用于记忆存储和相似性检索"""
import os
import json
import hashlib
from typing import List, Optional
from config.config import VECTOR_DB_DIR


class SimpleMemoryStore:
    """简单的基于文件的记忆存储（不依赖FAISS，降低部署复杂度）"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.store_path = os.path.join(VECTOR_DB_DIR, f"{session_id}.json")
        self._load()
    
    def _load(self):
        """加载已有记忆"""
        if os.path.exists(self.store_path):
            with open(self.store_path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        else:
            self.data = {
                "session_id": self.session_id,
                "analysis_results": {},  # 分析结果缓存
                "chat_history": [],       # 聊天历史
                "context": {}            # 上下文信息
            }
    
    def _save(self):
        """持久化存储"""
        os.makedirs(os.path.dirname(self.store_path), exist_ok=True)
        with open(self.store_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def save_analysis_result(self, key: str, result: dict):
        """保存分析结果"""
        self.data["analysis_results"][key] = result
        self._save()
    
    def get_analysis_result(self, key: str) -> Optional[dict]:
        """获取分析结果"""
        return self.data["analysis_results"].get(key)
    
    def get_all_analysis_results(self) -> dict:
        """获取所有分析结果"""
        return self.data["analysis_results"]
    
    def add_chat_message(self, role: str, content: str):
        """添加聊天消息"""
        self.data["chat_history"].append({
            "role": role,
            "content": content
        })
        # 保留最近50轮对话
        if len(self.data["chat_history"]) > 100:
            self.data["chat_history"] = self.data["chat_history"][-100:]
        self._save()
    
    def get_chat_history(self, limit: int = 20) -> List[dict]:
        """获取最近的聊天历史"""
        return self.data["chat_history"][-limit:]
    
    def set_context(self, key: str, value):
        """设置上下文信息"""
        self.data["context"][key] = value
        self._save()
    
    def get_context(self, key: str, default=None):
        """获取上下文信息"""
        return self.data["context"].get(key, default)
    
    def clear(self):
        """清除所有记忆"""
        self.data = {
            "session_id": self.session_id,
            "analysis_results": {},
            "chat_history": [],
            "context": {}
        }
        self._save()


def get_memory_store(session_id: str) -> SimpleMemoryStore:
    """获取指定会话的记忆存储"""
    return SimpleMemoryStore(session_id)


def list_sessions() -> List[str]:
    """列出所有会话ID"""
    sessions = []
    if os.path.exists(VECTOR_DB_DIR):
        for f in os.listdir(VECTOR_DB_DIR):
            if f.endswith(".json"):
                sessions.append(f.replace(".json", ""))
    return sessions
