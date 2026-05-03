# -*- coding: utf-8 -*-
"""
岗位搜索工具 - 基于大模型智能生成匹配岗位
支持按关键词、城市、薪资范围搜索，返回结构化的岗位列表
未来可无缝替换为真实招聘平台 API（如 Boss直聘/猎聘/拉勾）
"""
import os
import json
import logging
from typing import List, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from tools.llm_client import get_llm_client

logger = logging.getLogger(__name__)

SEARCH_SYSTEM_PROMPT = """你是一个专业的招聘信息生成系统。用户会给你搜索条件（关键词、城市、薪资范围等），
你需要根据这些条件，生成 5 条高度真实、结构化的招聘岗位信息。

要求：
1. 每条岗位信息必须包含：公司名、岗位名称、城市、薪资范围、经验要求、学历要求、岗位标签、完整的JD文本
2. 公司名要使用真实存在的互联网/科技公司名
3. JD 文本要详细（至少150字），包含岗位职责和任职要求
4. 薪资要符合市场行情
5. 严格按照 JSON 格式输出

输出格式（JSON数组）：
[
  {
    "company": "公司名称",
    "title": "岗位名称",
    "city": "城市",
    "salary": "薪资范围（如 15-25K）",
    "experience": "经验要求（如 1-3年）",
    "education": "学历要求",
    "tags": ["标签1", "标签2", "标签3"],
    "jd_text": "完整的岗位描述文本，包含岗位职责和任职要求..."
  }
]
"""


class JobSearchTool:
    """岗位搜索工具"""

    def __init__(self):
        self.llm = get_llm_client(streaming=False)
        self.mcp_cmd = os.getenv("JOB_MCP_CMD", "")
        self.mcp_args = os.getenv("JOB_MCP_ARGS", "")
        self.mcp_tool_name = os.getenv("JOB_MCP_TOOL_NAME", "search_jobs")

    def _clean_json_response(self, text: str) -> str:
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()

    async def _search_via_mcp(self, keyword, city, salary_min, salary_max, experience):
        """通过 MCP 客户端调用外部能力获取岗位"""
        try:
            from mcp.client.session import ClientSession
            from mcp.client.stdio import stdio_client, StdioServerParameters
        except ImportError:
            logger.warning("mcp 包未安装，请执行 pip install mcp")
            return None

        args = self.mcp_args.split() if self.mcp_args else []
        server_params = StdioServerParameters(command=self.mcp_cmd, args=args)
        
        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    result = await session.call_tool(self.mcp_tool_name, arguments={
                        "keyword": keyword,
                        "city": city,
                        "salary_min": salary_min,
                        "salary_max": salary_max,
                        "experience": experience
                    })
                    
                    if hasattr(result, "content") and len(result.content) > 0:
                        text = result.content[0].text
                        cleaned = self._clean_json_response(text)
                        return json.loads(cleaned)
                    return []
        except Exception as e:
            logger.error(f"MCP 调用失败: {str(e)}")
            return None

    async def search(
        self,
        keyword: str,
        city: str = "",
        salary_min: int = 0,
        salary_max: int = 0,
        experience: str = "",
    ) -> List[dict]:
        """
        搜索岗位
        :param keyword: 搜索关键词（如 "大模型应用开发"、"Python后端"）
        :param city: 城市筛选（如 "北京"、"上海"）
        :param salary_min: 最低薪资 (K)
        :param salary_max: 最高薪资 (K)
        :param experience: 经验要求（如 "1-3年"、"应届"）
        :return: 岗位列表
        """
        # 测试是否启用 MCP
        if self.mcp_cmd:
            mcp_results = await self._search_via_mcp(keyword, city, salary_min, salary_max, experience)
            if mcp_results is not None:
                return mcp_results

        conditions = [f"关键词：{keyword}"]
        if city:
            conditions.append(f"城市：{city}")
        if salary_min > 0 or salary_max > 0:
            salary_str = f"{salary_min}K" if salary_min > 0 else "不限"
            salary_str += f" - {salary_max}K" if salary_max > 0 else " - 不限"
            conditions.append(f"薪资范围：{salary_str}")
        if experience:
            conditions.append(f"经验要求：{experience}")

        user_input = "请根据以下搜索条件生成招聘岗位列表：\n" + "\n".join(conditions)

        messages = [
            SystemMessage(content=SEARCH_SYSTEM_PROMPT),
            HumanMessage(content=user_input),
        ]

        for attempt in range(3):
            try:
                response = await self.llm.ainvoke(messages)
                cleaned = self._clean_json_response(response.content)
                results = json.loads(cleaned)
                if isinstance(results, list) and len(results) > 0:
                    return results
            except (json.JSONDecodeError, Exception) as e:
                if attempt < 2:
                    messages.append(
                        HumanMessage(content=f"JSON格式错误，请严格输出JSON数组。错误：{str(e)}")
                    )
                else:
                    return []
        return []


# 单例
_search_tool: Optional[JobSearchTool] = None


def get_job_search_tool() -> JobSearchTool:
    global _search_tool
    if _search_tool is None:
        _search_tool = JobSearchTool()
    return _search_tool
