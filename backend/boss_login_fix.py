# -*- coding: utf-8 -*-
"""
手动登录 Boss 直聘并将 Cookie 注入 boss-agent-cli 的 session。
解决 boss login 因页面加载超时（30s）而失败的问题。
"""
import asyncio
import json
import os
import sys


async def main():
    from patchright.async_api import async_playwright

    boss_dir = os.path.expanduser(r'~\.boss-agent-cli')
    os.makedirs(boss_dir, exist_ok=True)
    session_file = os.path.join(boss_dir, 'session.json')

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        print("正在打开 Boss 直聘登录页...")
        await page.goto("https://www.zhipin.com/web/user/?ka=header-login", wait_until="domcontentloaded", timeout=60000)
        print("登录页已打开，请扫码或手机号登录...")
        print("(等待最多 180 秒，登录后自动提取 Cookie)")

        # 等待 URL 变化（登录成功后会跳转）
        try:
            await page.wait_for_url("**/web/geek/**", timeout=180000)
        except Exception:
            # 也可能跳转到首页
            pass

        # 再等一小会儿让 cookie 写入
        await asyncio.sleep(3)

        # 提取所有 Cookie
        cookies = await context.cookies(["https://www.zhipin.com"])
        await browser.close()

    if not cookies:
        print("❌ 未获取到 Cookie，登录可能未成功")
        return False

    # 构建 session
    cookie_dict = {c['name']: c['value'] for c in cookies}
    cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in cookies)

    print(f"\n提取到 {len(cookies)} 个 Cookie")
    print(f"Cookie names: {list(cookie_dict.keys())}")

    if 'wt2' not in cookie_dict:
        print("⚠️  未找到 wt2 Cookie，但仍尝试保存...")

    session_data = {
        "cookie": cookie_str,
        "wt2": cookie_dict.get("wt2", ""),
        "source": "manual_patchright"
    }

    with open(session_file, 'w', encoding='utf-8') as f:
        json.dump(session_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 登录凭证已保存到: {session_file}")
    print("现在可以运行 boss status 验证登录态")
    return True


if __name__ == '__main__':
    # Windows 需要 ProactorEventLoop 来支持子进程
    asyncio.run(main())
