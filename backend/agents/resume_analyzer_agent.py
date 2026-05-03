"""简历解析Agent - 结构化抽取简历信息"""
import json
from typing import AsyncIterator
from langchain_core.messages import SystemMessage, HumanMessage
from jsonschema import validate, ValidationError
from tools.llm_client import get_llm_client
from tools.langfuse_tracer import build_langfuse_invoke_kwargs
from config.prompts import RESUME_ANALYZER_PROMPT
from config.config import MAX_RETRY

# 简历解析结果JSON Schema
RESUME_ANALYZER_SCHEMA = {
    "type": "object",
    "properties": {
        "resume_analyzer_result": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "education": {"type": "string"},
                "work_years": {"type": "string"},
                "skills": {"type": "array", "items": {"type": "string"}},
                "projects": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "project_name": {"type": "string"},
                            "role": {"type": "string"},
                            "responsibilities": {"type": "string"},
                            "tech_stack": {"type": "string"},
                            "achievements": {"type": "string"}
                        }
                    }
                },
                "education_background": {"type": "string"},
                "self_introduction": {"type": "string"}
            },
            "required": ["name", "education", "work_years", "skills", "projects",
                         "education_background", "self_introduction"]
        }
    },
    "required": ["resume_analyzer_result"]
}


class ResumeAnalyzerAgent:
    """简历解析Agent"""
    
    def __init__(self):
        self.llm = get_llm_client(streaming=False)
        self.name = "ResumeAnalyzerAgent"
    
    def _clean_json_response(self, text: str) -> str:
        """清理大模型返回的JSON文本"""
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()
    
    async def analyze_resume(self, resume_content: str, session_id: str = None) -> dict:
        """
        解析简历文本，返回结构化JSON
        :param resume_content: 简历文本内容
        :param session_id: 会话ID（用于Langfuse追踪）
        :return: 结构化解析结果
        """
        messages = [
            SystemMessage(content=RESUME_ANALYZER_PROMPT),
            HumanMessage(content=f"请解析以下简历内容：\n{resume_content}")
        ]
        
        # Langfuse 追踪
        invoke_kwargs = build_langfuse_invoke_kwargs(
            trace_name=self.name,
            session_id=session_id,
            tags=["resume-analysis"],
        )
        
        for attempt in range(MAX_RETRY + 1):
            try:
                response = await self.llm.ainvoke(messages, **invoke_kwargs)
                cleaned = self._clean_json_response(response.content)
                result = json.loads(cleaned)
                validate(instance=result, schema=RESUME_ANALYZER_SCHEMA)
                return result
            except (json.JSONDecodeError, ValidationError) as e:
                if attempt < MAX_RETRY:
                    messages.append(HumanMessage(
                        content=f"JSON格式错误，请严格按照模板重新输出，只输出JSON。错误：{str(e)}"
                    ))
                else:
                    raise Exception(f"简历解析失败：{str(e)}")
    
    async def analyze_resume_stream(self, resume_content: str) -> AsyncIterator[str]:
        """流式解析简历"""
        yield f"📄 **{self.name}** 正在解析简历...\n\n"
        try:
            result = await self.analyze_resume(resume_content)
            r = result['resume_analyzer_result']
            yield f"✅ 简历解析完成！\n\n"
            yield f"**姓名**: {r['name']}\n\n"
            yield f"**学历**: {r['education']}\n\n"
            yield f"**工作年限**: {r['work_years']}\n\n"
            yield f"**技能**: {', '.join(r['skills'])}\n\n"
            yield f"**项目数量**: {len(r['projects'])}个\n\n"
        except Exception as e:
            yield f"❌ 简历解析失败: {str(e)}\n\n"
