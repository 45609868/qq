from fastapi import FastAPI, Request
import sqlite3
import uvicorn

app = FastAPI()


# --- 1. 数据库初始化 ---
def init_db():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reply_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT UNIQUE,
            reply_content TEXT
        )
    ''')
    # 预设一个例子
    cursor.execute("INSERT OR IGNORE INTO reply_rules (keyword, reply_content) VALUES (?, ?)",
                   ("合作", "您好，商务合作请联系微信：work_123"))
    conn.commit()
    conn.close()


# --- 2. 消息上报核心逻辑 ---
@app.post("/report")
async def handle_report(request: Request):
    data = await request.json()

    # 过滤非消息事件
    if data.get("post_type") != "message":
        return {"status": "ok"}

    msg = data.get("raw_message", "").strip()
    self_id = data.get("self_id")  # 收到消息的 QQ 号

    # 查询数据库匹配关键字
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT reply_content FROM reply_rules WHERE ? LIKE '%' || keyword || '%'", (msg,))
    result = cursor.fetchone()
    conn.close()

    if result:
        reply = result[0]
        print(f"[机器人 {self_id}] 匹配成功: {msg} -> {reply}")
        return {"reply": reply, "at_sender": True}

    return {"status": "no_match"}


# --- 3. 简单的关键字管理接口 (你可以用 API 工具调用) ---
@app.post("/add_rule")
async def add_rule(keyword: str, content: str):
    try:
        conn = sqlite3.connect('bot_data.db')
        conn.execute("INSERT INTO reply_rules (keyword, reply_content) VALUES (?, ?)", (keyword, content))
        conn.commit()
        return {"msg": "添加成功"}
    except:
        return {"msg": "关键字已存在"}


if __name__ == "__main__":
    init_db()
    uvicorn.run(app, host="0.0.0.0", port=8000)