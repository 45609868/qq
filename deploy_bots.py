import os


def deploy(count=100):
    # 你的 Mac 局域网 IP (不要用 127.0.0.1，因为容器内访问不到宿主机)
    # 请在终端输入 ifconfig 查看，通常是 192.168.x.x
    HOST_IP = "192.168.10.90"
    BASE_HTTP_PORT = 6000  # WebUI 端口从 6001 开始
    PYTHON_SERVER_URL = f"http://{HOST_IP}:8000/"

    for i in range(1, count + 1):
        web_port = BASE_HTTP_PORT + i
        config_path = os.path.abspath(f"./Users/macbook/my_bot_cluster/configs/bot_{i}")

        if not os.path.exists(config_path):
            os.makedirs(config_path)

        # 启动命令
        # -d: 后台运行
        # -e HTTP_POST: 消息往哪发 (发给我们的 Python 脚本)
        # -p: 映射 WebUI 端口供你扫码
        docker_cmd = f"""
        docker run -d \
          --name napcat_{i} \
          -e HTTP_POST={PYTHON_SERVER_URL} \
          -p {web_port}:6099 \
          -v {config_path}:/app/config \
          mlikiowa/napcat-docker:latest
        """
        os.system(docker_cmd)
        print(f"机器人 {i} 已启动 | 扫码地址: http://localhost:{web_port}")


if __name__ == "__main__":
    deploy(5)  # 建议先填 5 测试，没问题再改 100