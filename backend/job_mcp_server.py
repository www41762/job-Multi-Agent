import asyncio
import sys
import json
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# 实例化 MCP Server
app = Server("job_search_server")

@app.list_tools()
async def handle_list_tools() -> list[Tool]:
    """
    声明此 MCP Server 提供哪些工具。
    这里提供一个 'search_jobs' 工具。
    """
    return [
        Tool(
            name="search_jobs",
            description="根据搜索条件搜索国内互联网招聘岗位信息，支持按关键词、城市、薪资范围和经验要求进行过滤。",
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "搜索关键词（如 '大模型应用开发'）"},
                    "city": {"type": "string", "description": "城市（可选）"},
                    "salary_min": {"type": "integer", "description": "最低薪资 (K)"},
                    "salary_max": {"type": "integer", "description": "最高薪资 (K)"},
                    "experience": {"type": "string", "description": "经验要求（如 '1-3年'）"}
                },
                "required": ["keyword"]
            }
        )
    ]

@app.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """
    当客户端调用工具时执行的业务逻辑。
    """
    if name != "search_jobs":
        raise ValueError(f"未知的工具: {name}")

    keyword = arguments.get("keyword", "")
    city = arguments.get("city", "不限")
    salary_min = arguments.get("salary_min", 0)
    salary_max = arguments.get("salary_max", 0)
    experience = arguments.get("experience", "经验不限")

    # TODO: 接入真实的招聘网站 API (Boss直聘、拉勾、猎聘等)。
    # 此处为演示 MCP 通信，返回高仿真的 Mock 数据，证明 MCP 链路已打通。
    mock_jobs = [
        {
            "company": "字节跳动",
            "title": f"高级{keyword}工程师",
            "city": city if city else "北京",
            "salary": f"{max(20, salary_min)}-{max(40, salary_max) or 40}K",
            "experience": experience if experience else "3-5年",
            "education": "本科",
            "tags": [keyword, "Python", "分布式", "AI"],
            "jd_text": f"岗位职责：\n1. 负责{keyword}相关产品的研发落地；\n2. 构建大模型应用引擎（Agent/RAG等）。\n任职要求：\n1. 熟悉Python/Go，熟练使用LangChain/LlamaIndex；\n2. 有良好的系统架构设计能力。"
        },
        {
            "company": "阿里通义",
            "title": f"AI专家 - {keyword}",
            "city": city if city else "杭州",
            "salary": f"{max(25, salary_min)}-{max(50, salary_max) or 50}K",
            "experience": experience if experience else "5-10年",
            "education": "硕士",
            "tags": [keyword, "大模型微调", "算法落地"],
            "jd_text": f"岗位职责：\n1. 贴近业务场景，深度参与基于大模型的应用落地，包含不仅限于智能体、RAG；\n2. 追踪前沿研究。\n任职要求：\n1. {experience}工作经验；\n2. 对 {keyword} 有深入见解和实战经验。"
        }
    ]

    # MCP 要求返回列表形式的内容块，我们将最终 JSON 序列化为一个长字符串返回
    return [
        TextContent(
            type="text",
            text=json.dumps(mock_jobs, ensure_ascii=False, indent=2)
        )
    ]

async def main():
    # 启动 stdio 通信，该 Server 将通过标准输入输出与外部交互
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    # 在 Windows 下兼容 async，设置合适的 event loop policy
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
