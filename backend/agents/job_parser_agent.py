"""JD解析Agent - 结构化抽取招聘信息"""
import json
from typing import AsyncIterator
from langchain_core.messages import SystemMessage, HumanMessage
from jsonschema import validate, ValidationError
from tools.llm_client import get_llm_client
from config.prompts import JOB_PARSER_PROMPT
from config.config import MAX_RETRY

# JD解析结果JSON Schema
JD_PARSER_SCHEMA = {
    "type": "object",
    "properties": {
        "job_parser_result": {
            "type": "object",
            "properties": {
                "job_title": {"type": "string"},
                "required_skills": {"type": "array", "items": {"type": "string"}},
                "work_years": {"type": "string"},
                "education": {"type": "string"},
                "core_responsibilities": {"type": "array", "items": {"type": "string"}},
                "bonus_items": {"type": "array", "items": {"type": "string"}},
                "industry": {"type": "string"},
                "company_type": {"type": "string"}
            },
            "required": ["job_title", "required_skills", "work_years", "education",
                         "core_responsibilities", "bonus_items", "industry", "company_type"]
        }
    },
    "required": ["job_parser_result"]
}


class JobParserAgent:
    """JD解析Agent"""
    
    def __init__(self):
        self.llm = get_llm_client(streaming=False)
        self.name = "JobParserAgent"
    
    def _clean_json_response(self, text: str) -> str:
        """清理大模型返回的JSON文本"""
        text = text.strip()
        # 移除可能的markdown代码块标记
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()
    
    async def parse_jd(self, jd_text: str) -> dict:
        """
        解析JD文本，返回结构化JSON
        :param jd_text: 用户粘贴的JD文本
        :return: 结构化解析结果
        """
        messages = [
            SystemMessage(content=JOB_PARSER_PROMPT),
            HumanMessage(content=f"请解析以下JD文本：\n{jd_text}")
        ]
        
        for attempt in range(MAX_RETRY + 1):
            try:
                response = await self.llm.ainvoke(messages)
                cleaned = self._clean_json_response(response.content)
                result = json.loads(cleaned)
                validate(instance=result, schema=JD_PARSER_SCHEMA)
                return result
            except (json.JSONDecodeError, ValidationError) as e:
                if attempt < MAX_RETRY:
                    messages.append(HumanMessage(
                        content=f"你输出的JSON格式错误，请重新输出，严格按照模板，只输出JSON不添加任何多余文字。错误：{str(e)}"
                    ))
                else:
                    raise Exception(f"JD解析失败（重试{MAX_RETRY}次后）：{str(e)}")
    
    async def parse_jd_stream(self, jd_text: str) -> AsyncIterator[str]:
        """流式解析JD（用于前端展示进度）"""
        yield f"🔍 **{self.name}** 正在解析JD文本...\n\n"
        try:
            result = await self.parse_jd(jd_text)
            yield f"✅ JD解析完成！\n\n"
            yield f"**岗位名称**: {result['job_parser_result']['job_title']}\n\n"
            yield f"**核心技能要求**: {', '.join(result['job_parser_result']['required_skills'])}\n\n"
            yield f"**学历要求**: {result['job_parser_result']['education']}\n\n"
            yield f"**工作年限**: {result['job_parser_result']['work_years']}\n\n"
        except Exception as e:
            yield f"❌ JD解析失败: {str(e)}\n\n"
