# -*- coding: utf-8 -*-
"""
将手动提取的 Cookie 通过 boss-agent-cli 的 TokenStore 正确保存。
TokenStore 使用 Fernet 加密 + PBKDF2 + salt + machine_id 派生密钥。
"""
import json
import os
from pathlib import Path


def main():
    # 读取我们之前手动提取的 session.json
    boss_dir = Path(os.path.expanduser(r'~\.boss-agent-cli'))
    session_json_path = boss_dir / 'session.json'

    if not session_json_path.exists():
        print("❌ session.json 不存在，请先运行 boss_login_fix.py")
        return

    with open(session_json_path, 'r', encoding='utf-8') as f:
        raw_session = json.load(f)

    # 解析 cookie string 为 dict
    cookie_str = raw_session.get("cookie", "")
    cookies = {}
    for pair in cookie_str.split("; "):
        if "=" in pair:
            name, value = pair.split("=", 1)
            cookies[name] = value

    if not cookies.get("wt2"):
        print("❌ Cookie 中没有 wt2")
        return

    # 构建 boss-agent-cli 期望的 token 格式
    token_data = {
        "cookies": cookies,
        "stoken": cookies.get("__zp_stoken__", ""),
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0"
    }

    # 使用 boss-agent-cli 的 TokenStore 保存
    from boss_agent_cli.auth.token_store import TokenStore

    auth_dir = boss_dir / "auth"
    store = TokenStore(auth_dir)
    store.save(token_data)

    print(f"✅ Token 已通过 TokenStore 加密保存到: {auth_dir / 'session.enc'}")
    print(f"   cookies count: {len(cookies)}")
    print(f"   wt2 length: {len(cookies['wt2'])}")
    print(f"\n现在运行 'boss status' 验证登录态...")

    # 验证
    loaded = store.load()
    if loaded and loaded.get("cookies", {}).get("wt2"):
        print("✅ 验证通过：TokenStore 可以正确读取 session")
    else:
        print("❌ 验证失败")


if __name__ == '__main__':
    main()
