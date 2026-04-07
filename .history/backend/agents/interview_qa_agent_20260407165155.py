"""面试问答Agent - 生成针对性面试题库"""
import json
from typing import AsyncIterator
from langchain_core.messages import SystemMessage, HumanMessage
from jsonschema import validate, ValidationError
from tools.llm_client import get_llm_client
from config.prompts import INTERVIEW_QA_PROMPT
from config.config import MAX_RETRY

# 面试题库JSON Schema
INTERVIEW_QA_SCHEMA = {
    "type": "object",
    "properties": {
        "interview_qa_result": {
            "type": "object",
            "properties": {
                "technical_qa": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "question": {"type": "string"},
                            "answer": {"type": "string"}
                        },
                        "required": ["question", "answer"]
                    }
                },
                "project_qa": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "question": {"type": "string"},
                            "answer": {"type": "string"}
                        },
                        "required": ["question", "answer"]
                    }
                },
                "behavior_qa": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "question": {"type": "string"},
                            "answer": {"type": "string"}
                        },
                        "required": ["question", "answer"]
                    }
                }
            },
            "required": ["technical_qa", "project_qa", "behavior_qa"]
        }
    },
    "required": ["interview_qa_result"]
}


class InterviewQAAgent:
    """面试问答Agent"""
    
    def __init__(self):
        self.llm = get_llm_client(streaming=False)
        self.name = "InterviewQAAgent"
    
    def _clean_json_response(self, text: str) -> str:
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()
    
    async def generate_qa(self, jd_result: dict, resume_result: dict) -> dict:
        """
        生成面试题库
        :param jd_result: JD解析结果
        :param resume_result: 简历解析结果
        :return: 面试题库
        """
        input_text = f"""请根据以下JD要求和简历信息，生成针对性面试题库：

【JD要求】
{json.dumps(jd_result, ensure_ascii=False, indent=2)}

【简历信息】
{json.dumps(resume_result, ensure_ascii=False, indent=2)}"""
        
        messages = [
            SystemMessage(content=INTERVIEW_QA_PROMPT),
            HumanMessage(content=input_text)
        ]
        
        for attempt in range(MAX_RETRY + 1):
            try:
                response = await self.llm.ainvoke(messages)
                cleaned = self._clean_json_response(response.content)
                result = json.loads(cleaned)
                validate(instance=result, schema=INTERVIEW_QA_SCHEMA)
                return result
            except (json.JSONDecodeError, ValidationError) as e:
                if attempt < MAX_RETRY:
                    messages.append(HumanMessage(
                        content=f"JSON格式错误，请严格按照模板输出。错误：{str(e)}"
                    ))
                else:
                    raise Exception(f"面试题生成失败：{str(e)}")
    
    async def generate_qa_stream(self, jd_result: dict, resume_result: dict) -> AsyncIterator[str]:
        """流式生成面试题"""
        yield f"🎯 **{self.name}** 正在生成面试题库...\n\n"
        try:
            result = await self.generate_qa(jd_result, resume_result)
            qa = result['interview_qa_result']
            yield f"✅ 面试题库生成完成！\n\n"
            
            yield "### 📚 技术面试题\n\n"
            for i, item in enumerate(qa['technical_qa'], 1):
                yield f"**Q{i}: {item['question']}**\n\n"
                yield f"参考答案: {item['answer']}\n\n---\n\n"
            
            yield "### 💼 项目深挖题\n\n"
            for i, item in enumerate(qa['project_qa'], 1):
                yield f"**Q{i}: {item['question']}**\n\n"
                yield f"参考答案: {item['answer']}\n\n---\n\n"
            
            yield "### 🤝 行为面试题\n\n"
            for i, item in enumerate(qa['behavior_qa'], 1):
                yield f"**Q{i}: {item['question']}**\n\n"
                yield f"参考答案: {item['answer']}\n\n---\n\n"
        except Exception as e:
            yield f"❌ 面试题生成失败: {str(e)}\n\n"
