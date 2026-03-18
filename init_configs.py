import os
import json


def generate_cluster_configs(total=2000):
    base_dir = os.path.expanduser("~/my_bot_cluster/configs")
    # 宿主机 IP（Mac 在 Docker 中的固定域名）
    central_api = "http://host.docker.internal:8000/report"

    for i in range(1, total + 1):
        bot_path = os.path.join(base_dir, f"bot_{i}")
        os.makedirs(bot_path, exist_ok=True)

        # 核心配置文件: napcat.json
        # 预设好所有参数，让容器启动即工作，无需进入 WebUI
        config = {
            "httpPost": [
                {
                    "url": central_api,
                    "enable": True,
                    "debug": False
                }
            ],
            "quickInteraction": {"enable": True},
            "webUi": {"enable": False, "port": 6099},  # 禁用 WebUI 提高性能
            "network": {"proxy": ""}  # 留空，稍后在 Docker 环境变量中注入
        }

        with open(os.path.join(bot_path, "napcat.json"), "w") as f:
            json.dump(config, f, indent=4)

    print(f"✅ 已完成 {total} 个账号的预置配置写入！路径: {base_dir}")


if __name__ == "__main__":
    generate_cluster_configs(2000)