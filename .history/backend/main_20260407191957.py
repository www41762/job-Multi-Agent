"""FastAPI后端入口 - 支持SSE流式输出、聊天、记忆功能"""
import os
import sys
import json
import uuid
import asyncio
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

# 确保项目根目录在path中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.planner_agent import PlannerAgent
from tools.pdf_parser import parse_pdf
from tools.llm_client import get_llm_client, stream_llm_response
from tools.db_memory import get_sql_memory_store as get_memory_store, list_sql_sessions as list_sessions
from config.prompts import CHAT_ASSISTANT_PROMPT
from config.config import RESUMES_DIR

app = FastAPI(title="多Agent智能求职助手", version="1.0.0")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局PlannerAgent实例
planner = PlannerAgent()


# ==================== 数据模型 ====================

class ChatRequest(BaseModel):
    """聊天请求"""
    session_id: str
    message: str


class SessionRequest(BaseModel):
    """会话请求"""
    session_id: Optional[str] = None


# ==================== 会话管理接口 ====================

@app.post("/api/session/create")
async def create_session():
    """创建新会话"""
    session_id = str(uuid.uuid4())[:8]
    memory = get_memory_store(session_id)
    return {"session_id": session_id, "message": "会话创建成功"}


@app.get("/api/session/list")
async def list_all_sessions():
    """列出所有会话"""
    sessions = list_sessions()
    session_list = []
    for sid in sessions:
        memory = get_memory_store(sid)
        has_results = bool(memory.get_all_analysis_results())
        chat_count = len(memory.get_chat_history())
        session_list.append({
            "session_id": sid,
            "has_analysis": has_results,
            "chat_count": chat_count
        })
    return {"sessions": session_list}


@app.get("/api/session/{session_id}/history")
async def get_session_history(session_id: str):
    """获取会话的聊天历史"""
    memory = get_memory_store(session_id)
    return {
        "chat_history": memory.get_chat_history(limit=50),
        "analysis_results": memory.get_all_analysis_results()
    }


@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str):
    """删除会话"""
    memory = get_memory_store(session_id)
    memory.clear()
    return {"message": "会话已删除"}


# ==================== 核心分析接口（SSE流式输出） ====================

@app.post("/api/analyze")
async def analyze_stream(
    session_id: str = Form(...),
    jd_text: str = Form(...),
    resume_file: Optional[UploadFile] = File(None),
    resume_text: Optional[str] = Form(None),
):
    """
    核心分析接口 - SSE流式输出
    支持上传PDF简历或直接粘贴简历文本
    """
    # 获取简历内容
    resume_content = ""
    if resume_file:
        try:
            file_content = await resume_file.read()
            resume_content = parse_pdf(file_content)
            # 保存简历文件
            save_path = os.path.join(RESUMES_DIR, f"{session_id}_{resume_file.filename}")
            with open(save_path, "wb") as f:
                f.write(file_content)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"简历文件解析失败: {str(e)}")
    elif resume_text:
        resume_content = resume_text
    else:
        raise HTTPException(status_code=400, detail="请上传简历文件或粘贴简历文本")
    
    if not jd_text.strip():
        raise HTTPException(status_code=400, detail="请输入JD文本")
    
    # 获取记忆存储
    memory = get_memory_store(session_id)
    memory.set_context("jd_text", jd_text)
    memory.set_context("resume_content", resume_content)
    
    async def event_generator():
        """SSE事件生成器"""
        try:
            async for chunk in planner.run_stream(jd_text, resume_content, memory):
                # SSE格式: data: xxx\n\n
                yield f"data: {json.dumps({'type': 'content', 'data': chunk}, ensure_ascii=False)}\n\n"
            
            # 发送完成信号
            yield f"data: {json.dumps({'type': 'done', 'data': ''}, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'data': str(e)}, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


# ==================== 单独Agent接口 ====================

@app.post("/api/parse-jd")
async def parse_jd_only(session_id: str = Form(...), jd_text: str = Form(...)):
    """单独解析JD"""
    memory = get_memory_store(session_id)
    
    async def event_generator():
        try:
            from agents.job_parser_agent import JobParserAgent
            agent = JobParserAgent()
            result = await agent.parse_jd(jd_text)
            memory.save_analysis_result("jd_result", result)
            yield f"data: {json.dumps({'type': 'result', 'data': result}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'data': ''}, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'data': str(e)}, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/api/parse-resume")
async def parse_resume_only(
    session_id: str = Form(...),
    resume_file: Optional[UploadFile] = File(None),
    resume_text: Optional[str] = Form(None),
):
    """单独解析简历"""
    memory = get_memory_store(session_id)
    resume_content = ""
    
    if resume_file:
        file_content = await resume_file.read()
        resume_content = parse_pdf(file_content)
    elif resume_text:
        resume_content = resume_text
    else:
        raise HTTPException(status_code=400, detail="请上传简历或粘贴文本")
    
    async def event_generator():
        try:
            from agents.resume_analyzer_agent import ResumeAnalyzerAgent
            agent = ResumeAnalyzerAgent()
            result = await agent.analyze_resume(resume_content)
            memory.save_analysis_result("resume_result", result)
            yield f"data: {json.dumps({'type': 'result', 'data': result}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'data': ''}, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'data': str(e)}, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ==================== 聊天接口（SSE流式输出 + 记忆） ====================

@app.post("/api/chat")
async def chat_stream(request: ChatRequest):
    """
    聊天接口 - SSE流式输出
    结合分析结果上下文进行对话，支持多轮记忆
    """
    memory = get_memory_store(request.session_id)
    
    # 保存用户消息
    memory.add_chat_message("user", request.message)
    
    # 构建上下文
    analysis_results = memory.get_all_analysis_results()
    context_parts = []
    
    if analysis_results.get("jd_result"):
        context_parts.append(f"【JD解析结果】\n{json.dumps(analysis_results['jd_result'], ensure_ascii=False, indent=2)}")
    if analysis_results.get("resume_result"):
        context_parts.append(f"【简历解析结果】\n{json.dumps(analysis_results['resume_result'], ensure_ascii=False, indent=2)}")
    if analysis_results.get("matcher_result"):
        context_parts.append(f"【匹配分析结果】\n{json.dumps(analysis_results['matcher_result'], ensure_ascii=False, indent=2)}")
    if analysis_results.get("optimized_resume"):
        context_parts.append(f"【优化后简历】\n{json.dumps(analysis_results['optimized_resume'], ensure_ascii=False, indent=2)}")
    if analysis_results.get("interview_qa"):
        context_parts.append(f"【面试题库】\n{json.dumps(analysis_results['interview_qa'], ensure_ascii=False, indent=2)}")
    
    # 注入长期用户画像（跨会话持久化）
    user_profile = memory.get_user_profile("default_user")
    if user_profile.get("weaknesses") or user_profile.get("strong_skills"):
        profile_parts = []
        if user_profile["weaknesses"]:
            profile_parts.append(f"历史弱项：{', '.join(user_profile['weaknesses'])}")
        if user_profile["strong_skills"]:
            profile_parts.append(f"核心优势：{', '.join(user_profile['strong_skills'])}")
        context_parts.append(f"【用户长期画像（跨会话记忆）】\n{'; '.join(profile_parts)}")

    context = "\n\n".join(context_parts) if context_parts else "暂无分析结果，用户还没有进行求职分析。"
    
    # 构建消息列表
    system_prompt = CHAT_ASSISTANT_PROMPT.format(context=context)
    messages = [SystemMessage(content=system_prompt)]
    
    # 添加历史对话（最近10轮）
    chat_history = memory.get_chat_history(limit=20)
    for msg in chat_history[:-1]:  # 排除刚添加的当前消息
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))
    
    # 添加当前用户消息
    messages.append(HumanMessage(content=request.message))
    
    async def event_generator():
        """SSE流式输出聊天回复"""
        full_response = ""
        try:
            async for chunk in stream_llm_response(messages):
                full_response += chunk
                yield f"data: {json.dumps({'type': 'content', 'data': chunk}, ensure_ascii=False)}\n\n"
            
            # 保存AI回复到记忆
            memory.add_chat_message("assistant", full_response)
            yield f"data: {json.dumps({'type': 'done', 'data': ''}, ensure_ascii=False)}\n\n"
        except Exception as e:
            error_msg = f"回复生成失败: {str(e)}"
            memory.add_chat_message("assistant", error_msg)
            yield f"data: {json.dumps({'type': 'error', 'data': error_msg}, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


# ==================== 获取分析结果接口 ====================

@app.get("/api/results/{session_id}")
async def get_results(session_id: str):
    """获取指定会话的所有分析结果"""
    memory = get_memory_store(session_id)
    return {
        "session_id": session_id,
        "results": memory.get_all_analysis_results()
    }


# ==================== 用户画像接口（长期记忆） ====================

@app.get("/api/profile")
async def get_user_profile():
    """获取用户长期画像（弱项 + 优势技能，跨会话持久化）"""
    memory = get_memory_store("__profile__")
    profile = memory.get_user_profile("default_user")
    return profile


@app.post("/api/profile/weakness")
async def add_weakness(data: dict):
    """手动添加弱项"""
    memory = get_memory_store("__profile__")
    weakness = data.get("weakness", "").strip()
    if weakness:
        memory.update_user_weakness(weakness)
    return {"message": "弱项已记录", "profile": memory.get_user_profile("default_user")}


@app.post("/api/profile/strength")
async def add_strength(data: dict):
    """手动添加优势技能"""
    memory = get_memory_store("__profile__")
    skill = data.get("skill", "").strip()
    if skill:
        memory.update_user_strength(skill)
    return {"message": "技能已记录", "profile": memory.get_user_profile("default_user")}


# ==================== 健康检查 ====================

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "服务正常运行"}


if __name__ == "__main__":
    import uvicorn
    from config.config import BACKEND_PORT
    uvicorn.run("main:app", host="0.0.0.0", port=BACKEND_PORT, reload=True)
