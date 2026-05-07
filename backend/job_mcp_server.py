# -*- coding: utf-8 -*-
"""
岗位搜索 MCP Server - 对接 Boss 直聘真实 API
通过 boss-agent-cli 的 TokenStore 读取登录凭证，直接调用 Boss 直聘 wapi 获取真实岗位数据。
"""
import asyncio
import sys
import os
import json
import logging
from pathlib import Path

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Boss 直聘城市代码映射（常用城市）
CITY_CODE_MAP = {
    "北京": "101010100", "上海": "101020100", "广州": "101280100",
    "深圳": "101280600", "杭州": "101210100", "成都": "101270100",
    "南京": "101190100", "武汉": "101200100", "西安": "101110100",
    "苏州": "101190400", "长沙": "101250100", "郑州": "101180100",
    "天津": "101030100", "重庆": "101040100", "厦门": "101230200",
    "合肥": "101220100", "东莞": "101281600", "佛山": "101280800",
    "珠海": "101280700", "全国": "100010000", "不限": "100010000",
}


def _load_cookies() -> dict:
    """从 boss-agent-cli 的 TokenStore 加载登录凭证"""
    try:
        from boss_agent_cli.auth.token_store import TokenStore
        boss_dir = Path(os.path.expanduser(r'~\.boss-agent-cli'))
        store = TokenStore(boss_dir / 'auth')
        token = store.load()
        if token and token.get("cookies", {}).get("wt2"):
            return token
    except Exception as e:
        logger.warning(f"从 TokenStore 加载失败: {e}")

    # Fallback: 尝试读取 session.json
    session_path = Path(os.path.expanduser(r'~\.boss-agent-cli\session.json'))
    if session_path.exists():
        with open(session_path, 'r', encoding='utf-8') as f:
            raw = json.load(f)
        cookie_str = raw.get("cookie", "")
        cookies = {}
        for pair in cookie_str.split("; "):
            if "=" in pair:
                k, v = pair.split("=", 1)
                cookies[k] = v
        if cookies.get("wt2"):
            return {"cookies": cookies, "user_agent": "Mozilla/5.0"}

    return {}


def _search_boss_zhipin(keyword: str, city: str = "", salary_min: int = 0,
                         salary_max: int = 0, experience: str = "") -> list[dict]:
    """调用 Boss 直聘真实搜索 API"""
    token = _load_cookies()
    if not token:
        raise RuntimeError("未登录 Boss 直聘，请先运行 python backend/boss_login_fix.py 扫码登录")

    cookies = token.get("cookies", {})
    user_agent = token.get("user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)")

    # 解析城市代码
    city_code = CITY_CODE_MAP.get(city, "100010000")  # 默认全国

    params = {
        "query": keyword,
        "city": city_code,
        "page": "1",
        "pageSize": "10",
    }

    # 经验筛选映射
    exp_map = {"应届": "108", "1年以内": "101", "1-3年": "102", "3-5年": "103", "5-10年": "104", "10年以上": "105"}
    if experience and experience in exp_map:
        params["experience"] = exp_map[experience]

    headers = {
        "User-Agent": user_agent,
        "Referer": "https://www.zhipin.com/",
        "Cookie": "; ".join(f"{k}={v}" for k, v in cookies.items()),
    }

    resp = httpx.get(
        "https://www.zhipin.com/wapi/zpgeek/search/joblist.json",
        params=params,
        cookies=cookies,
        headers=headers,
        timeout=30,
    )

    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"Boss 直聘 API 返回错误: {data.get('message', '未知错误')}")

    job_list = data.get("zpData", {}).get("jobList", [])

    # 转换为标准格式
    results = []
    for job in job_list:
        results.append({
            "company": job.get("brandName", ""),
            "title": job.get("jobName", ""),
            "city": job.get("cityName", ""),
            "salary": job.get("salaryDesc", ""),
            "experience": job.get("jobExperience", ""),
            "education": job.get("jobDegree", ""),
            "tags": job.get("skills", []),
            "jd_text": job.get("jobLabels", []),
            "boss_url": f"https://www.zhipin.com/job_detail/{job.get('encryptJobId', '')}.html",
            "brand_industry": job.get("brandIndustry", ""),
            "brand_scale": job.get("brandScaleName", ""),
        })

    return results


# ============ MCP Server 定义 ============

app = Server("job_search_server")


@app.list_tools()
async def handle_list_tools() -> list[Tool]:
    """声明此 MCP Server 提供的工具"""
    return [
        Tool(
            name="search_jobs",
            description="搜索 Boss 直聘真实岗位信息，返回包含公司、薪资、JD 等结构化数据。支持按关键词、城市、经验要求过滤。",
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "搜索关键词（如 '大模型应用开发'、'Python后端'）"},
                    "city": {"type": "string", "description": "城市名（如 '深圳'、'北京'、'上海'），不填则搜全国"},
                    "salary_min": {"type": "integer", "description": "最低薪资 (K)，可选"},
                    "salary_max": {"type": "integer", "description": "最高薪资 (K)，可选"},
                    "experience": {"type": "string", "description": "经验要求（如 '1-3年'、'3-5年'、'应届'），可选"}
                },
                "required": ["keyword"]
            }
        )
    ]


@app.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """处理工具调用"""
    if name != "search_jobs":
        raise ValueError(f"未知的工具: {name}")

    keyword = arguments.get("keyword", "")
    city = arguments.get("city", "")
    salary_min = arguments.get("salary_min", 0)
    salary_max = arguments.get("salary_max", 0)
    experience = arguments.get("experience", "")

    try:
        jobs = _search_boss_zhipin(keyword, city, salary_min, salary_max, experience)
        return [
            TextContent(
                type="text",
                text=json.dumps(jobs, ensure_ascii=False, indent=2)
            )
        ]
    except Exception as e:
        error_msg = {"error": str(e), "hint": "请确保已通过 boss_login_fix.py 登录 Boss 直聘"}
        return [
            TextContent(
                type="text",
                text=json.dumps(error_msg, ensure_ascii=False)
            )
        ]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
