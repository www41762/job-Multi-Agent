"""
Langfuse 可观测性追踪工具 - 统一管理 Trace 和 Callback

适配 Langfuse SDK v4.x（基于 OpenTelemetry）：
  - CallbackHandler 从 langfuse.langchain 导入
  - 客户端通过环境变量或 Langfuse(...) 单例初始化
  - session_id / user_id / tags 通过 LangChain config.metadata 传递
"""
import os
import logging
from typing import Optional
from config.config import (
    LANGFUSE_ENABLED,
    LANGFUSE_SECRET_KEY,
    LANGFUSE_PUBLIC_KEY,
    LANGFUSE_HOST,
)

logger = logging.getLogger(__name__)

# ============ 全局初始化标志 ============
_langfuse_initialized = False


def _ensure_langfuse_env():
    """确保 Langfuse 所需的环境变量已设置（SDK v4 通过环境变量自动初始化）"""
    global _langfuse_initialized
    if _langfuse_initialized:
        return

    if not LANGFUSE_ENABLED:
        return

    # Langfuse v4 SDK 从环境变量读取配置
    os.environ.setdefault("LANGFUSE_SECRET_KEY", LANGFUSE_SECRET_KEY)
    os.environ.setdefault("LANGFUSE_PUBLIC_KEY", LANGFUSE_PUBLIC_KEY)
    os.environ.setdefault("LANGFUSE_HOST", LANGFUSE_HOST)

    try:
        from langfuse import Langfuse
        # 初始化全局单例，SDK 内部会缓存
        Langfuse(
            public_key=LANGFUSE_PUBLIC_KEY,
            secret_key=LANGFUSE_SECRET_KEY,
            host=LANGFUSE_HOST,
        )
        _langfuse_initialized = True
        logger.info("✅ Langfuse v4 已初始化，追踪地址: %s", LANGFUSE_HOST)
    except Exception as e:
        logger.warning("⚠️ Langfuse 初始化失败（将跳过追踪）: %s", e)


def get_langfuse_client():
    """获取全局 Langfuse 客户端实例"""
    if not LANGFUSE_ENABLED:
        return None
    _ensure_langfuse_env()
    try:
        from langfuse import get_client
        return get_client()
    except Exception as e:
        logger.warning("⚠️ 获取 Langfuse client 失败: %s", e)
        return None


def get_langfuse_callback(
    trace_name: str = "llm-call",
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    tags: Optional[list] = None,
    metadata: Optional[dict] = None,
):
    """
    获取 LangChain 兼容的 Langfuse Callback Handler (v4)。

    Langfuse v4 的 CallbackHandler 不再接受构造函数中的 trace_name / session_id 等参数，
    需要通过 LangChain 的 config.metadata 传递：
      - langfuse_session_id
      - langfuse_user_id
      - langfuse_tags

    本函数返回 (handler, metadata_dict) 元组，调用方在 invoke 时合并到 config 中。

    :param trace_name: Trace 名称
    :param session_id: 会话ID
    :param user_id: 用户ID
    :param tags: 标签列表
    :param metadata: 自定义元数据
    :return: (CallbackHandler, langfuse_metadata) 元组，或 (None, {})
    """
    if not LANGFUSE_ENABLED:
        return None, {}

    _ensure_langfuse_env()

    try:
        from langfuse.langchain import CallbackHandler
        handler = CallbackHandler()

        # 构建 LangChain metadata 用于传递 Langfuse trace 属性
        lf_metadata = {}
        if session_id:
            lf_metadata["langfuse_session_id"] = session_id
        if user_id:
            lf_metadata["langfuse_user_id"] = user_id
        if tags:
            lf_metadata["langfuse_tags"] = tags
        if trace_name:
            lf_metadata["langfuse_trace_name"] = trace_name
        if metadata:
            lf_metadata["langfuse_metadata"] = metadata

        return handler, lf_metadata
    except Exception as e:
        logger.warning("⚠️ 创建 Langfuse CallbackHandler 失败: %s", e)
        return None, {}


def build_langfuse_invoke_kwargs(
    trace_name: str = "llm-call",
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    tags: Optional[list] = None,
    metadata: Optional[dict] = None,
) -> dict:
    """
    构建可直接传给 llm.ainvoke(messages, **kwargs) 的关键字参数。
    如果 Langfuse 未启用，返回空 dict，对原有调用零影响。

    用法：
        kwargs = build_langfuse_invoke_kwargs(trace_name="JobParser", session_id="abc")
        response = await self.llm.ainvoke(messages, **kwargs)
    """
    handler, lf_metadata = get_langfuse_callback(
        trace_name=trace_name,
        session_id=session_id,
        user_id=user_id,
        tags=tags,
        metadata=metadata,
    )
    if handler is None:
        return {}

    return {
        "config": {
            "callbacks": [handler],
            "metadata": lf_metadata,
        }
    }


def flush_langfuse():
    """刷新 Langfuse 缓冲区，确保所有追踪数据都已发送"""
    client = get_langfuse_client()
    if client:
        try:
            client.flush()
        except Exception as e:
            logger.warning("⚠️ Langfuse flush 失败: %s", e)
