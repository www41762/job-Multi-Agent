"""匹配Agent - 对比JD与简历，计算匹配度"""
import json
from typing import AsyncIterator
from langchain_core.messages import SystemMessage, HumanMessage
from jsonschema import validate, ValidationError
from tools.llm_client import get_llm_client
from tools.langfuse_tracer import build_langfuse_invoke_kwargs
from config.prompts import MATCHER_PROMPT
from config.config import MAX_RETRY

# 匹配结果JSON Schema
MATCHER_SCHEMA = {
    "type": "object",
    "properties": {
        "matcher_result": {
            "type": "object",
            "properties": {
                "match_score": {"type": "number", "minimum": 0, "maximum": 100},
                "advantages": {"type": "array", "items": {"type": "string"}},
                "shortcomings": {"type": "array", "items": {"type": "string"}},
                "optimization_suggestions": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["match_score", "advantages", "shortcomings", "optimization_suggestions"]
        }
    },
    "required": ["matcher_result"]
}


class MatcherAgent:
    """匹配Agent"""
    
    def __init__(self):
        self.llm = get_llm_client(streaming=False)
        self.name = "MatcherAgent"
    
    def _clean_json_response(self, text: str) -> str:
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()
    
    async def match(self, jd_result: dict, resume_result: dict, session_id: str = None) -> dict:
        """
        匹配JD与简历
        :param jd_result: JD解析结果
        :param resume_result: 简历解析结果
        :param session_id: 会话ID（用于Langfuse追踪）
        :return: 匹配分析结果
        """
        input_text = f"""请对比以下JD要求和简历信息，进行匹配分析：

【JD要求】
{json.dumps(jd_result, ensure_ascii=False, indent=2)}

【简历信息】
{json.dumps(resume_result, ensure_ascii=False, indent=2)}"""
        
        messages = [
            SystemMessage(content=MATCHER_PROMPT),
            HumanMessage(content=input_text)
        ]
        
        # Langfuse 追踪
        invoke_kwargs = build_langfuse_invoke_kwargs(
            trace_name=self.name,
            session_id=session_id,
            tags=["matching"],
        )
        
        for attempt in range(MAX_RETRY + 1):
            try:
                response = await self.llm.ainvoke(messages, **invoke_kwargs)
                cleaned = self._clean_json_response(response.content)
                result = json.loads(cleaned)
                validate(instance=result, schema=MATCHER_SCHEMA)
                return result
            except (json.JSONDecodeError, ValidationError) as e:
                if attempt < MAX_RETRY:
                    messages.append(HumanMessage(
                        content=f"JSON格式错误，请严格按照模板重新输出。错误：{str(e)}"
                    ))
                else:
                    raise Exception(f"匹配分析失败：{str(e)}")
    
    async def match_stream(self, jd_result: dict, resume_result: dict) -> AsyncIterator[str]:
        """流式匹配分析"""
        yield f"🔗 **{self.name}** 正在进行匹配分析...\n\n"
        try:
            result = await self.match(jd_result, resume_result)
            m = result['matcher_result']
            yield f"✅ 匹配分析完成！\n\n"
            yield f"**匹配度评分**: {m['match_score']}/100\n\n"
            yield f"**优势**:\n"
            for adv in m['advantages']:
                yield f"- ✅ {adv}\n"
            yield f"\n**不足**:\n"
            for sc in m['shortcomings']:
                yield f"- ⚠️ {sc}\n"
            yield f"\n**优化建议**:\n"
            for sug in m['optimization_suggestions']:
                yield f"- 💡 {sug}\n"
            yield "\n"
        except Exception as e:
            yield f"❌ 匹配分析失败: {str(e)}\n\n"
