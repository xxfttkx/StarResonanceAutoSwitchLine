import asyncio
import json
import re
import websockets
import keyboard
from auto_switch_line_controller import AutoSwitchLineController
from utils import *
import sys, io
# sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8')

def parse_messages(msg: str):
    """
    解析多行消息，返回所有符合的 (num, place)
    """
    pattern = r"(\d+)(\S+):\s*✅"
    results = []
    for line in msg.splitlines():
        m = re.match(pattern, line.strip())
        if m:
            num = int(m.group(1))
            place = m.group(2)
            results.append((num, place))
    return results

# 你要监听的群号和QQ号
TARGET_GROUP = 940409582   # 群号
TARGET_USER  = 592184299   # QQ号

# 连接 LLOneBot 的反向 WS 地址
# 注意：这里的端口要和 LLOneBot 配置文件中的 ws 端口一致
WS_URL = "ws://127.0.0.1:3001"

async def listen():
    async with websockets.connect(WS_URL) as ws:
        log("已连接到 llonebot ws")

        # 持续监听事件
        async for msg in ws:
            try:
                data = json.loads(msg)
            except Exception:
                continue

            # 只处理群消息
            if data.get("post_type") == "message" and data.get("message_type") == "group":
                group_id = data.get("group_id")
                user_id  = data.get("user_id")
                message  = data.get("raw_message")

                if user_id == TARGET_USER and group_id == TARGET_GROUP:
                    log(f"收到消息: {message}")
                    parsed = parse_messages(message)
                    if parsed:
                        line = parsed[0][0]
                        controller.switch_line(line)

if __name__ == "__main__":
    controller = AutoSwitchLineController(find_target_window())
    keyboard.add_hotkey('-', controller.switch_open_auto_switch_line)
    keyboard.add_hotkey('*', controller.switch_close_auto_switch_line)
    asyncio.run(listen())
