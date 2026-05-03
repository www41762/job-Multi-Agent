"""中枢调度Agent - 基于LangGraph实现Agent协作与流程控制"""
import json
import asyncio
from typing import TypedDict, AsyncIterator, Optional
from langgraph.graph import StateGraph, END, START
from agents.job_parser_agent import JobParserAgent
from agents.resume_analyzer_agent import ResumeAnalyzerAgent
from agents.matcher_agent import MatcherAgent
from agents.resume_writer_agent import ResumeWriterAgent
from agents.interview_qa_agent import InterviewQAAgent
from tools.db_memory import GlobalSQLMemory


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
        
        # 定义流程边（并行触发解析JD和简历）
        workflow.add_edge(START, "parse_jd")
        workflow.add_edge(START, "analyze_resume")
        
        # 两个解析节点完成后汇聚到匹配节点
        workflow.add_edge("parse_jd", "match")
        workflow.add_edge("analyze_resume", "match")
        
        workflow.add_edge("match", "write_resume")
        workflow.add_edge("match", "generate_qa")
        
        workflow.add_edge("write_resume", "summarize")
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
        
        # LangGraph并行汇聚时，_match_node会被触发两次。
        # 这里判断必须两者都解析完成后，才进行实际的匹配，否则直接跳过
        if "jd_result" not in state or "resume_result" not in state:
            return {}
            
        # 避免重复执行
        if "matcher_result" in state:
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
            
        # LangGraph并行汇聚时，需判断前置节点是否都已执行完
        if "optimized_resume" not in state or "interview_qa" not in state:
            return {}
            
        if "final_report" in state:
            return {}
        
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
                         memory: Optional[GlobalSQLMemory] = None) -> AsyncIterator[str]:
        """
        流式运行分析流程，逐步输出每个Agent的结果
        :param jd_text: JD文本
        :param resume_content: 简历文本
        :param memory: 记忆存储
        """
        yield "## 🚀 智能求职分析开始 (启用LangGraph并行加速)\n\n"
        yield "---\n\n"
        
        # Step 1: 并行解析JD与简历
        yield "### Step 1/3: 并行解析 JD与简历 ⏳\n\n"
        
        jd_result = None
        resume_result = None
        
        async def par_jd():
            res = await self.job_parser.parse_jd(jd_text)
            if memory: memory.save_analysis_result("jd_result", res)
            return res
            
        async def par_resume():
            res = await self.resume_analyzer.analyze_resume(resume_content)
            if memory: memory.save_analysis_result("resume_result", res)
            return res

        try:
            # 开启真正的并行任务
            res_jd, res_resume = await asyncio.gather(par_jd(), par_resume())
            jd_result = res_jd
            resume_result = res_resume
            
            yield f"✅ **JD解析完成**: {jd_result['job_parser_result']['job_title']}\n\n"
            yield f"✅ **简历解析完成**: {resume_result['resume_analyzer_result']['name']}\n\n"
        except Exception as e:
            yield f"❌ 并行解析失败: {str(e)}\n\n"
            return
            
        yield "---\n\n"
        
        # Step 2: 匹配分析
        yield "### Step 2/3: 简历JD匹配分析\n\n"
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
        
        # Step 3: 并行优化简历与生成面试题
        yield "### Step 3/3: 并行优化简历 与 面试题生成 ⏳\n\n"
        
        optimized_resume = None
        interview_qa = None
        
        async def par_write():
            res = await self.resume_writer.write_resume(resume_result, jd_result, matcher_result)
            if memory: memory.save_analysis_result("optimized_resume", res)
            return res
            
        async def par_qa():
            res = await self.interview_qa.generate_qa(jd_result, resume_result)
            if memory: memory.save_analysis_result("interview_qa", res)
            return res
            
        try:
            # 开启真正的并行任务
            res_write, res_qa = await asyncio.gather(par_write(), par_qa())
            optimized_resume = res_write
            interview_qa = res_qa
            
            yield "✅ **简历定向优化完成** (已保存在左侧分析结果)\n\n"
            yield "✅ **针对性面试题生成完成** (已保存在左侧分析结果)\n\n"
            yield f"💡 **亮点摘录**:\n"
            for h in optimized_resume.get("optimization_highlights", ["已对齐核心职责"]):
                yield f"- ⭐ {h}\n"
            yield "\n"
        except Exception as e:
            yield f"❌ 并行处理失败: {str(e)}\n\n"
            return
            
        yield "---\n\n"
        yield "## ✅ 全部分析完成！\n\n"
        yield "您可以在聊天框中继续提问（如“帮我列出技术面试题”、“看看我的简历优化了哪里”），我会结合分析结果为您详细解答。\n"
