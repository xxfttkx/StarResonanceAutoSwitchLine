import atexit
import ctypes
ctypes.windll.shcore.SetProcessDpiAwareness(2) 
import asyncio
import json
import re
import threading
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

async def listen(controller, stop_event=None):
    """持续监听 llonebot WebSocket，支持安全退出（GUI/CLI 兼容）"""

    # 若未传入 stop_event，则创建一个永远不触发的事件
    if stop_event is None:
        stop_event = threading.Event()

    while not stop_event.is_set():
        try:
            async with websockets.connect(WS_URL) as ws:
                log("已连接到 llonebot ws")

                async for msg in ws:
                    if stop_event.is_set():
                        log("检测到退出信号，停止监听。")
                        return

                    try:
                        data = json.loads(msg)
                    except Exception:
                        continue

                    if data.get("post_type") == "message" and data.get("message_type") == "group":
                        group_id = data.get("group_id")
                        user_id  = data.get("user_id")
                        message  = data.get("raw_message")

                        if controller.is_target("小猪·闪闪") and user_id == TARGET_USER and group_id == TARGET_GROUP:
                            log(f"收到消息: {message}")
                            # parsed = parse_messages(message)
                            controller.deal_with_msg(message)
                            if not controller.is_manual and not controller.is_hunting:
                                controller.cal_next_pig()
                                if controller.next_pig :
                                    line, pos = controller.next_pig
                                    controller.start_switching(line, pos)
                        if controller.is_target("娜宝·闪闪") and group_id == 875329843:
                            creatures = parse_train(message)
                            if creatures:
                                log_error(f"收到娜宝·闪闪消息: {message}")
                            if not controller.is_manual and not controller.is_hunting:
                                if len(creatures) == 1:
                                    line = creatures[0][0]
                                    controller.start_switching(line, None)
                            # controller.deal_with_creatures(creatures, "娜宝·闪闪")

        except Exception as e:
            if stop_event.is_set():
                log("监听任务结束。")
                break
            log(f"连接失败或断开: {e}, 10秒后重试...")
            await asyncio.sleep(10)

    log("监听任务已退出。")       

if __name__ == "__main__":
    controller = AutoSwitchLineController(find_target_window())
    keyboard.add_hotkey('+', controller.reset_place)
    # 注册退出清理
    atexit.register(keyboard.unhook_all)
    asyncio.run(listen(controller))
