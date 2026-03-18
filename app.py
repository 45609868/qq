from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
import sqlite3
import uvicorn

app = FastAPI()

# 存储机器人在线状态：{ "bot_1": {"logged_in": True, "qq": "12345"} }
bot_status = {}


# 数据库初始化
def init_db():
    conn = sqlite3.connect('config.db')
    conn.execute('CREATE TABLE IF NOT EXISTS rules (id INTEGER PRIMARY KEY, user_qq TEXT, kw TEXT, reply TEXT)')
    conn.commit()
    conn.close()


# --- 页面 1：登录中转页 ---
@app.get("/", response_class=HTMLResponse)
async def login_page():
    # 这里的 token 需与 napcat.json 一致
    token = "123456"
    html = f"""
    <html>
    <head>
        <title>机器人中控集群</title>
        <script>
            async function checkLoginState() {{
                try {{
                    // 关键：请求我们自己的后端 8000 端口，不再跨域访问 6099
                    let response = await fetch('/check_status');
                    let data = await response.json();

                    if (data.logged_in) {{
                        console.log("检测到机器人已上报登录，正在跳转...");
                        window.location.href = "/admin?qq=" + data.qq;
                    }}
                }} catch (e) {{
                    console.log("等待后端同步状态...");
                }}
            }}
            setInterval(checkLoginState, 1500);
        </script>
    </head>
    <body style="margin:0; display:flex; flex-direction:column; align-items:center; background:#f0f2f5; font-family:sans-serif;">
        <div style="background:white; padding:20px; margin-top:40px; border-radius:15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); text-align:center;">
            <h2>🤖 账号授权 (Bot_1)</h2>
            <iframe src="http://localhost:6099/webui?token={token}" 
                    style="width:500px; height:600px; border:1px solid #eee; border-radius:10px;"></iframe>
            <p style="color:#666; margin-top:15px;">扫码成功后，系统将自动识别并跳转。</p>
        </div>
    </body>
    </html>
    """
    return html


# --- 核心：统一消息/状态接收端口 ---
@app.post("/report")
async def bot_report(request: Request):
    data = await request.json()

    # 1. 处理登录/连接事件 (Meta Event)
    if data.get("post_type") == "meta_event":
        if data.get("sub_type") == "connect":
            user_id = str(data.get("self_id"))
            print(f"✅ [系统上报] 机器人 {user_id} 已连接！")
            bot_status["bot_1"] = {"logged_in": True, "qq": user_id}
        return {"status": "ok"}

    # 2. 处理聊天消息 (Message Event)
    if data.get("post_type") == "message":
        self_id = str(data.get("self_id"))
        msg = data.get("raw_message", "").strip()

        # 查询数据库中属于该 QQ 的规则
        conn = sqlite3.connect('config.db')
        cur = conn.cursor()
        # 使用模糊匹配规则
        cur.execute("SELECT reply FROM rules WHERE user_qq = ? AND ? LIKE '%' || kw || '%'", (self_id, msg))
        res = cur.fetchone()
        conn.close()

        if res:
            print(f"📩 [自动回复] 账号 {self_id} 匹配到关键词，回复: {res[0]}")
            return {"reply": res[0], "at_sender": True}

    return {"status": "ignore"}


import httpx


@app.get("/check_status")
async def check_status():
    # 1. 先看有没有收到机器人的主动上报 (Webhook)
    if bot_status.get("bot_1"):
        return bot_status["bot_1"]

    # 2. 如果没收到上报，Python 后端亲自去请求 6099 端口
    # 后端请求后端，不存在“跨域”和“Unauthorized”的浏览器限制
    try:
        async with httpx.AsyncClient() as client:
            # 注意：这里用 127.0.0.1，Token 必须和你 docker run 里的 -e NAPCAT_TOKEN 一致
            token = "123456"
            url = f"http://127.0.0.1:6099/api/get_login_info?token={token}"

            resp = await client.get(url, timeout=1.0)
            res_data = resp.json()

            # 如果机器人说它登录了
            if res_data.get("code") == 0 and res_data.get("data", {}).get("isLogin"):
                qq = res_data['data'].get('user_id') or res_data['data'].get('uin')
                # 把状态存入内存，下次就不用再请求了
                bot_status["bot_1"] = {"logged_in": True, "qq": qq}
                return bot_status["bot_1"]

    except Exception as e:
        # 如果机器人还没启动好，这里会报错，我们忽略它即可
        print(f"等待机器人响应... {e}")

    return {"logged_in": False}
# --- 页面 3：专属配置管理页 ---
@app.get("/admin", response_class=HTMLResponse)
async def admin_page(qq: str):
    conn = sqlite3.connect('config.db')
    rules = conn.execute("SELECT * FROM rules WHERE user_qq = ?", (qq,)).fetchall()
    conn.close()

    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: sans-serif; background: #f0f2f5; padding: 20px; }}
            .container {{ max-width: 800px; margin: auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }}
            .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
            table {{ width:100%; border-collapse:collapse; margin-top:20px; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eee; }}
            .btn-del {{ color: #ff4d4f; text-decoration: none; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>配置管理中心</h2>
                <span>当前账号：<b>{qq}</b></span>
            </div>
            <table>
                <tr style="background:#fafafa;"><th>关键词</th><th>回复内容</th><th>操作</th></tr>
    """
    for r in rules:
        html += f"<tr><td>{r[2]}</td><td>{r[3]}</td><td><a class='btn-del' href='/del/{r[0]}?qq={qq}'>删除</a></td></tr>"

    html += f"""
            </table>
            <form action="/add" method="post" style="margin-top:20px; background:#f9f9f9; padding:20px; border-radius:8px;">
                <input type="hidden" name="qq" value="{qq}">
                <strong>添加新规则：</strong><br><br>
                <input name="k" placeholder="当别人说..." required style="padding:8px; width:200px;">
                <input name="v" placeholder="我就回复..." required style="padding:8px; width:300px;">
                <button type="submit" style="padding:8px 20px; background:#52c41a; color:white; border:none; border-radius:4px; cursor:pointer;">保存规则</button>
            </form>
            <div style="margin-top:20px; text-align:right;">
                <a href="/" style="color:#999; text-decoration:none;">← 切换/退出账号</a>
            </div>
        </div>
    </body>
    </html>
    """
    return html


@app.post("/add")
async def add_rule(qq: str = Form(...), k: str = Form(...), v: str = Form(...)):
    conn = sqlite3.connect('config.db')
    conn.execute("INSERT INTO rules (user_qq, kw, reply) VALUES (?, ?, ?)", (qq, k, v))
    conn.commit()
    conn.close()
    return RedirectResponse(url=f"/admin?qq={qq}", status_code=303)


@app.get("/del/{idx}")
async def del_rule(idx: int, qq: str):
    conn = sqlite3.connect('config.db')
    conn.execute("DELETE FROM rules WHERE id=?", (idx,))
    conn.commit()
    conn.close()
    return RedirectResponse(url=f"/admin?qq={qq}", status_code=303)


if __name__ == "__main__":
    init_db()
    uvicorn.run(app, host="0.0.0.0", port=8000)