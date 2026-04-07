"""中枢调度Agent - 基于LangGraph实现Agent协作与流程控制"""
import json
import asyncio
from typing import TypedDict, AsyncIterator, Optional
from langgraph.graph import StateGraph, END
from agents.job_parser_agent import JobParserAgent
from agents.resume_analyzer_agent import ResumeAnalyzerAgent
from agents.matcher_agent import MatcherAgent
from agents.resume_writer_agent import ResumeWriterAgent
from agents.interview_qa_agent import InterviewQAAgent
from tools.rag_tool import SimpleMemoryStore


class AgentState(TypedDict, total=False):
    """Agent流程状态定义"""
    # 输入
    jd_text: str
    resume_content: str
    # 各Agent输出
    jd_result: dict
    resume_result: dict
    matcher_result: dict
    optimized_resume: dict
    interview_qa: dict
    # 最终汇总
    final_report: dict
    # 错误信息
    error: str


class PlannerAgent:
    """中枢调度Agent - 串联所有子Agent的执行流程"""
    
    def __init__(self):
        self.job_parser = JobParserAgent()
        self.resume_analyzer = ResumeAnalyzerAgent()
        self.matcher = MatcherAgent()
        self.resume_writer = ResumeWriterAgent()
        self.interview_qa = InterviewQAAgent()
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """构建LangGraph工作流"""
        workflow = StateGraph(AgentState)
        
        # 添加节点
        workflow.add_node("parse_jd", self._parse_jd_node)
        workflow.add_node("analyze_resume", self._analyze_resume_node)
        workflow.add_node("match", self._match_node)
        workflow.add_node("write_resume", self._write_resume_node)
        workflow.add_node("generate_qa", self._generate_qa_node)
        workflow.add_node("summarize", self._summarize_node)
        
        # 定义流程边
        workflow.set_entry_point("parse_jd")
        workflow.add_edge("parse_jd", "analyze_resume")
        workflow.add_edge("analyze_resume", "match")
        workflow.add_edge("match", "write_resume")
        workflow.add_edge("write_resume", "generate_qa")
        workflow.add_edge("generate_qa", "summarize")
        workflow.add_edge("summarize", END)
        
        return workflow.compile()
    
    async def _parse_jd_node(self, state: AgentState) -> dict:
        """JD解析节点"""
        try:
            result = await self.job_parser.parse_jd(state["jd_text"])
            return {"jd_result": result}
        except Exception as e:
            return {"error": f"JD解析失败: {str(e)}"}
    
    async def _analyze_resume_node(self, state: AgentState) -> dict:
        """简历解析节点"""
        if state.get("error"):
            return {}
        try:
            result = await self.resume_analyzer.analyze_resume(state["resume_content"])
            return {"resume_result": result}
        except Exception as e:
            return {"error": f"简历解析失败: {str(e)}"}
    
    async def _match_node(self, state: AgentState) -> dict:
        """匹配分析节点"""
        if state.get("error"):
            return {}
        try:
            result = await self.matcher.match(
                state["jd_result"],
                state["resume_result"]
            )
            return {"matcher_result": result}
        except Exception as e:
            return {"error": f"匹配分析失败: {str(e)}"}
    
    async def _write_resume_node(self, state: AgentState) -> dict:
        """简历优化节点"""
        if state.get("error"):
            return {}
        try:
            result = await self.resume_writer.write_resume(
                state["resume_result"],
                state["jd_result"],
                state["matcher_result"]
            )
            return {"optimized_resume": result}
        except Exception as e:
            return {"error": f"简历优化失败: {str(e)}"}
    
    async def _generate_qa_node(self, state: AgentState) -> dict:
        """面试题生成节点"""
        if state.get("error"):
            return {}
        try:
            result = await self.interview_qa.generate_qa(
                state["jd_result"],
                state["resume_result"]
            )
            return {"interview_qa": result}
        except Exception as e:
            return {"error": f"面试题生成失败: {str(e)}"}
    
    async def _summarize_node(self, state: AgentState) -> dict:
        """汇总节点"""
        if state.get("error"):
            return {"final_report": {"error": state["error"]}}
        
        return {
            "final_report": {
                "jd_result": state.get("jd_result", {}),
                "resume_result": state.get("resume_result", {}),
                "matcher_result": state.get("matcher_result", {}),
                "optimized_resume": state.get("optimized_resume", {}),
                "interview_qa": state.get("interview_qa", {}),
                "status": "success"
            }
        }
    
    async def run(self, jd_text: str, resume_content: str) -> dict:
        """
        运行完整分析流程（非流式）
        :param jd_text: JD文本
        :param resume_content: 简历文本
        :return: 最终分析报告
        """
        initial_state: AgentState = {
            "jd_text": jd_text,
            "resume_content": resume_content,
        }
        result = await self.graph.ainvoke(initial_state)
        return result.get("final_report", {"error": "流程执行异常"})
    
    async def run_stream(self, jd_text: str, resume_content: str,
                         memory: Optional[SimpleMemoryStore] = None) -> AsyncIterator[str]:
        """
        流式运行分析流程，逐步输出每个Agent的结果
        :param jd_text: JD文本
        :param resume_content: 简历文本
        :param memory: 记忆存储
        """
        yield "## 🚀 智能求职分析开始\n\n"
        yield "---\n\n"
        
        # Step 1: 解析JD
        yield "### Step 1/5: 解析JD\n\n"
        jd_result = None
        try:
            async for chunk in self.job_parser.parse_jd_stream(jd_text):
                yield chunk
            jd_result = await self.job_parser.parse_jd(jd_text)
            if memory:
                memory.save_analysis_result("jd_result", jd_result)
        except Exception as e:
            yield f"❌ JD解析失败: {str(e)}\n\n"
            return
        
        yield "---\n\n"
        
        # Step 2: 解析简历
        yield "### Step 2/5: 解析简历\n\n"
        resume_result = None
        try:
            async for chunk in self.resume_analyzer.analyze_resume_stream(resume_content):
                yield chunk
            resume_result = await self.resume_analyzer.analyze_resume(resume_content)
            if memory:
                memory.save_analysis_result("resume_result", resume_result)
        except Exception as e:
            yield f"❌ 简历解析失败: {str(e)}\n\n"
            return
        
        yield "---\n\n"
        
        # Step 3: 匹配分析
        yield "### Step 3/5: 匹配分析\n\n"
        matcher_result = None
        try:
            async for chunk in self.matcher.match_stream(jd_result, resume_result):
                yield chunk
            matcher_result = await self.matcher.match(jd_result, resume_result)
            if memory:
                memory.save_analysis_result("matcher_result", matcher_result)
        except Exception as e:
            yield f"❌ 匹配分析失败: {str(e)}\n\n"
            return
        
        yield "---\n\n"
        
        # Step 4: 优化简历
        yield "### Step 4/5: 优化简历\n\n"
        optimized_resume = None
        try:
            async for chunk in self.resume_writer.write_resume_stream(
                resume_result, jd_result, matcher_result
            ):
                yield chunk
            optimized_resume = await self.resume_writer.write_resume(
                resume_result, jd_result, matcher_result
            )
            if memory:
                memory.save_analysis_result("optimized_resume", optimized_resume)
        except Exception as e:
            yield f"❌ 简历优化失败: {str(e)}\n\n"
            return
        
        yield "---\n\n"
        
        # Step 5: 生成面试题
        yield "### Step 5/5: 生成面试题库\n\n"
        interview_qa = None
        try:
            async for chunk in self.interview_qa.generate_qa_stream(jd_result, resume_result):
                yield chunk
            interview_qa = await self.interview_qa.generate_qa(jd_result, resume_result)
            if memory:
                memory.save_analysis_result("interview_qa", interview_qa)
        except Exception as e:
            yield f"❌ 面试题生成失败: {str(e)}\n\n"
            return
        
        yield "---\n\n"
        yield "## ✅ 全部分析完成！\n\n"
        yield "您可以在上方查看各步骤的详细结果，也可以在聊天框中继续提问，我会结合分析结果为您解答。\n"
