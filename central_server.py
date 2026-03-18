from fastapi import FastAPI, Request
import httpx
import uvicorn

app = FastAPI()

# 关键字配置
REPLY_RULES = {
    "加群": "请加群：123456789",
    "人工": "正在为您接入人工，请稍候...",
    "合作": "商务合作请私信：xxx"
}


@app.post("/")
async def handle_qq_msg(request: Request):
    data = await request.json()

    # 仅处理私聊或群聊消息
    if data.get("post_type") != "message":
        return {"status": "ok"}

    content = data.get("message", "")
    user_id = data.get("user_id")
    group_id = data.get("group_id")
    self_id = data.get("self_id")  # 核心：知道是哪个 QQ 号收到的
    message_type = data.get("message_type")

    # 匹配关键字
    response_text = None
    for kw, reply in REPLY_RULES.items():
        if kw in content:
            response_text = reply
            break

    if response_text:
        # 这里的上报是异步的，我们需要根据收到消息的机器人发送回去
        # NapCat 默认开启了反向 HTTP API，我们可以直接在请求里返回响应
        return {
            "reply": response_text,
            "at_sender": True
        }

    return {"status": "no_match"}


if __name__ == "__main__":
    # 启动中控服务器
    uvicorn.run(app, host="0.0.0.0", port=8000)