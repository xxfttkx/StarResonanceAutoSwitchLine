# 后端 Flask / FastAPI
from fastapi import FastAPI
import sys
import keyboard
import uvicorn
from utils import *
import asyncio
from auto_switch_line_controller import AutoSwitchLineController

sys.stdout.reconfigure(encoding='utf-8')
app = FastAPI()
controller = AutoSwitchLineController(find_target_window())

@app.post("/line")
def add_line(data: dict):
    line = data["line"]
    pos = data["pos"]
    log(f"{line}{pos}: ✅")
    controller.switch_line(line)
    return {"status": "done"}

if __name__ == "__main__":
    keyboard.add_hotkey('-', controller.switch_open_auto_switch_line)
    keyboard.add_hotkey('*', controller.switch_close_auto_switch_line)
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=5000,
        access_log=False  # 关闭 uvicorn 的请求日志
    )
