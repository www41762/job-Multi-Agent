"""简历优化Agent - 定向改写简历"""
import json
from typing import AsyncIterator
from langchain_core.messages import SystemMessage, HumanMessage
from tools.llm_client import get_llm_client, stream_llm_response
from tools.langfuse_tracer import build_langfuse_invoke_kwargs
from config.prompts import RESUME_WRITER_PROMPT
from config.config import MAX_RETRY


class ResumeWriterAgent:
    """简历优化Agent"""
    
    def __init__(self):
        self.llm = get_llm_client(streaming=False)
        self.name = "ResumeWriterAgent"
    
    def _clean_json_response(self, text: str) -> str:
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()
    
    async def write_resume(self, resume_result: dict, jd_result: dict, matcher_result: dict, session_id: str = None) -> dict:
        """
        优化简历
        :param resume_result: 简历解析结果
        :param jd_result: JD解析结果
        :param matcher_result: 匹配分析结果
        :param session_id: 会话ID（用于Langfuse追踪）
        :return: 优化后的简历
        """
        input_text = f"""请根据以下信息优化简历：

【原始简历信息】
{json.dumps(resume_result, ensure_ascii=False, indent=2)}

【目标JD要求】
{json.dumps(jd_result, ensure_ascii=False, indent=2)}

【匹配分析与优化建议】
{json.dumps(matcher_result, ensure_ascii=False, indent=2)}"""
        
        messages = [
            SystemMessage(content=RESUME_WRITER_PROMPT),
            HumanMessage(content=input_text)
        ]
        
        # Langfuse 追踪
        invoke_kwargs = build_langfuse_invoke_kwargs(
            trace_name=self.name,
            session_id=session_id,
            tags=["resume-writing"],
        )
        
        for attempt in range(MAX_RETRY + 1):
            try:
                response = await self.llm.ainvoke(messages, **invoke_kwargs)
                cleaned = self._clean_json_response(response.content)
                result = json.loads(cleaned)
                if "optimized_resume" in result:
                    return result
                raise ValueError("缺少optimized_resume字段")
            except Exception as e:
                if attempt < MAX_RETRY:
                    messages.append(HumanMessage(
                        content=f"格式错误，请输出包含optimized_resume字段的JSON。错误：{str(e)}"
                    ))
                else:
                    raise Exception(f"简历优化失败：{str(e)}")
    
    async def write_resume_stream(self, resume_result: dict, jd_result: dict, matcher_result: dict) -> AsyncIterator[str]:
        """流式优化简历"""
        yield f"✍️ **{self.name}** 正在优化简历...\n\n"
        try:
            result = await self.write_resume(resume_result, jd_result, matcher_result)
            yield f"✅ 简历优化完成！\n\n"
            yield f"**版本**: {result.get('resume_version', '定制版')}\n\n"
            yield "---\n\n"
            yield result.get("optimized_resume", "")
            yield "\n\n---\n\n"
            if "optimization_highlights" in result:
                yield "**优化亮点**:\n"
                for h in result["optimization_highlights"]:
                    yield f"- ⭐ {h}\n"
                yield "\n"
        except Exception as e:
            yield f"❌ 简历优化失败: {str(e)}\n\n"
