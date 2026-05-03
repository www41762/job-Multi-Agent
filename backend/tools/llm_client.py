"""大模型调用客户端 - 统一封装，支持流式输出与 Langfuse 追踪"""
import os
from typing import AsyncIterator, Optional, List
from langchain_openai import ChatOpenAI
from langchain_core.callbacks import BaseCallbackHandler
from config.config import LLM_TYPE, LLM_MODEL, LLM_API_KEY, LLM_BASE_URL, LLM_TEMPERATURE


def get_llm_client(
    streaming: bool = False,
    callbacks: Optional[List[BaseCallbackHandler]] = None,
):
    """
    统一封装大模型客户端，通过OpenAI兼容接口对接各种大模型
    :param streaming: 是否启用流式输出
    :param callbacks: LangChain 回调列表（如 Langfuse CallbackHandler）
    :return: 大模型客户端实例
    """
    return ChatOpenAI(
        model=LLM_MODEL,
        api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL,
        temperature=LLM_TEMPERATURE,
        streaming=streaming,
        max_tokens=4096,
        callbacks=callbacks or [],
    )


async def stream_llm_response(
    messages: list,
    callbacks: Optional[List[BaseCallbackHandler]] = None,
) -> AsyncIterator[str]:
    """
    流式调用大模型，逐token返回
    :param messages: 对话消息列表
    :param callbacks: LangChain 回调列表（如 Langfuse CallbackHandler）
    :return: 异步迭代器，逐token返回
    """
    llm = get_llm_client(streaming=True, callbacks=callbacks)
    async for chunk in llm.astream(messages):
        if chunk.content:
            yield chunk.content
