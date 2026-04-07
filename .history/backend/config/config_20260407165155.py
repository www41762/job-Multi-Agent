"""项目全局配置"""
import os
from dotenv import load_dotenv

load_dotenv()

# 大模型配置
LLM_TYPE = os.getenv("LLM_TYPE", "openai")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen-plus")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
LLM_TEMPERATURE = 0.3  # 结构化生成，温度调低

# 嵌入模型配置
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# 路径配置
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
RESUMES_DIR = os.path.join(DATA_DIR, "resumes")
VECTOR_DB_DIR = os.path.join(DATA_DIR, "vector_db")
CHAT_HISTORY_DIR = os.path.join(DATA_DIR, "chat_history")

# 确保目录存在
for d in [DATA_DIR, RESUMES_DIR, VECTOR_DB_DIR, CHAT_HISTORY_DIR]:
    os.makedirs(d, exist_ok=True)

# 服务配置
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))
MAX_RETRY = 2  # Agent重试次数
