"""闈㈣瘯闂瓟Agent - 鐢熸垚閽堝鎬ч潰璇曢搴?""
import json
from typing import AsyncIterator
from langchain_core.messages import SystemMessage, HumanMessage
from jsonschema import validate, ValidationError
from tools.llm_client import get_llm_client
from config.prompts import INTERVIEW_QA_PROMPT
from config.config import MAX_RETRY

# 闈㈣瘯棰樺簱JSON Schema
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
    """闈㈣瘯闂瓟Agent"""
    
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
    
    async def generate_qa(self, jd_result: dict, resume_result: dict, user_profile: dict = None) -> dict:
        """
        鐢熸垚闈㈣瘯棰樺簱
        :param jd_result: JD瑙ｆ瀽缁撴灉
        :param resume_result: 绠€鍘嗚В鏋愮粨鏋?
        :return: 闈㈣瘯棰樺簱
        """
        prompt_add = ""
        if user_profile and user_profile.get("weaknesses"):
            weak_str = ", ".join(user_profile["weaknesses"])
            prompt_add = f"\n\n【注意：历史弱项】\n求职者在先前的面试中有以下薄弱环节：{weak_str}。请在此次出的面试题中，务必包含针对这些弱项的【追问题】或【技术题】，以帮助求职者克服短板！"

        input_text = f"""璇锋牴鎹互涓婮D瑕佹眰鍜岀畝鍘嗕俊鎭紝鐢熸垚閽堝鎬ч潰璇曢搴擄細

銆怞D瑕佹眰銆?
{json.dumps(jd_result, ensure_ascii=False, indent=2)}

銆愮畝鍘嗕俊鎭€?
{json.dumps(resume_result, ensure_ascii=False, indent=2)}{prompt_add}"""
        
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
                        content=f"JSON鏍煎紡閿欒锛岃涓ユ牸鎸夌収妯℃澘杈撳嚭銆傞敊璇細{str(e)}"
                    ))
                else:
                    raise Exception(f"闈㈣瘯棰樼敓鎴愬け璐ワ細{str(e)}")
    
    async def generate_qa_stream(self, jd_result: dict, resume_result: dict, user_profile: dict = None) -> AsyncIterator[str]:
        """娴佸紡鐢熸垚闈㈣瘯棰?""
        yield f"馃幆 **{self.name}** 姝ｅ湪鐢熸垚闈㈣瘯棰樺簱...\n\n"
        try:
            result = await self.generate_qa(jd_result, resume_result, user_profile)
            qa = result['interview_qa_result']
            yield f"鉁?闈㈣瘯棰樺簱鐢熸垚瀹屾垚锛乗n\n"
            
            yield "### 馃摎 鎶€鏈潰璇曢\n\n"
            for i, item in enumerate(qa['technical_qa'], 1):
                yield f"**Q{i}: {item['question']}**\n\n"
                yield f"鍙傝€冪瓟妗? {item['answer']}\n\n---\n\n"
            
            yield "### 馃捈 椤圭洰娣辨寲棰榎n\n"
            for i, item in enumerate(qa['project_qa'], 1):
                yield f"**Q{i}: {item['question']}**\n\n"
                yield f"鍙傝€冪瓟妗? {item['answer']}\n\n---\n\n"
            
            yield "### 馃 琛屼负闈㈣瘯棰榎n\n"
            for i, item in enumerate(qa['behavior_qa'], 1):
                yield f"**Q{i}: {item['question']}**\n\n"
                yield f"鍙傝€冪瓟妗? {item['answer']}\n\n---\n\n"
        except Exception as e:
            yield f"鉂?闈㈣瘯棰樼敓鎴愬け璐? {str(e)}\n\n"

