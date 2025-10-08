#!/usr/bin/env python3
"""
record/replay 鼠标+键盘（含按下/释放）事件
按键说明:
  F7 - 开始录制
  F8 - 停止并保存 record.json
  F9 - 回放 record.json
  ESC - 退出程序或在回放时中止回放

依赖:
  pip install keyboard pynput pyautogui
"""
import time
import json
import threading
import os
from typing import List, Dict

import keyboard            # 监听并模拟键盘（press/release）
import pyautogui           # 模拟鼠标、移动、点击、滚轮
from pynput import mouse as pmouse  # 监听鼠标事件

RECORD_FILE = "record.json"

# 状态
recording = False
actions: List[Dict] = []
start_time = 0.0
lock = threading.Lock()
mouse_listener = None

# 控制鼠标移动记录采样，避免大量冗余点
MOVE_SAMPLE_INTERVAL = 0.05  # 秒
MOVE_MIN_DIST = 2            # 像素

_last_move_time = 0.0
_last_move_pos = None


def _t() -> float:
    """相对于录制开始的时间（秒）"""
    return time.time() - start_time


# ------------ event handlers ------------
def _on_key_event(e: keyboard.KeyboardEvent):
    """keyboard 的回调，记录按下/抬起"""
    global actions
    if not recording:
        return
    # e.event_type: 'down' or 'up', e.name: key name
    with lock:
        actions.append({
            "type": "key",
            "event": e.event_type,   # 'down' / 'up'
            "name": e.name,
            "time": _t()
        })


def _on_move(x, y):
    """鼠标移动（采样）"""
    global _last_move_time, _last_move_pos, actions
    if not recording:
        return
    now_ts = time.time()
    if now_ts - _last_move_time < MOVE_SAMPLE_INTERVAL:
        return
    pos = (int(x), int(y))
    if _last_move_pos is not None:
        dx = pos[0] - _last_move_pos[0]
        dy = pos[1] - _last_move_pos[1]
        if dx * dx + dy * dy < MOVE_MIN_DIST * MOVE_MIN_DIST:
            return
    _last_move_time = now_ts
    _last_move_pos = pos
    with lock:
        actions.append({
            "type": "mouse",
            "event": "move",
            "pos": [pos[0], pos[1]],
            "time": _t()
        })


def _on_click(x, y, button, pressed):
    """鼠标按下/抬起"""
    if not recording:
        return
    bname = getattr(button, "name", str(button))
    with lock:
        actions.append({
            "type": "mouse",
            "event": "down" if pressed else "up",
            "button": bname,
            "pos": [int(x), int(y)],
            "time": _t()
        })


def _on_scroll(x, y, dx, dy):
    """鼠标滚轮"""
    if not recording:
        return
    with lock:
        actions.append({
            "type": "mouse",
            "event": "scroll",
            "dx": dx,
            "dy": dy,
            "pos": [int(x), int(y)],
            "time": _t()
        })


# ------------ control functions ------------
def start_record():
    """开始录制（在主线程通过按键触发）"""
    global recording, actions, start_time, mouse_listener, _last_move_time, _last_move_pos
    if recording:
        print("Already recording.")
        return
    actions = []
    start_time = time.time()
    _last_move_time = start_time
    _last_move_pos = pyautogui.position()
    recording = True

    # 钩子：keyboard 和 pynput mouse
    keyboard.hook(_on_key_event)
    mouse_listener = pmouse.Listener(on_move=_on_move, on_click=_on_click, on_scroll=_on_scroll)
    mouse_listener.start()

    print("Recording started. Press F3 to stop.")


def stop_record():
    """停止录制并保存文件"""
    global recording, mouse_listener
    if not recording:
        return
    recording = False
    # 取消 hook
    try:
        keyboard.unhook(_on_key_event)
    except Exception:
        pass
    if mouse_listener:
        try:
            mouse_listener.stop()
        except Exception:
            pass
        mouse_listener = None

    # 保存 actions
    os.makedirs(os.path.dirname(RECORD_FILE) or ".", exist_ok=True)
    with open(RECORD_FILE, "w", encoding="utf-8") as f:
        json.dump(actions, f, ensure_ascii=False, indent=2)
    print(f"Recording stopped. {len(actions)} events saved to {RECORD_FILE}")


def replay(record_file=RECORD_FILE):
    """读 JSON 回放事件（可被 ESC 中断）"""
    if not os.path.exists(record_file):
        print("No record file:", record_file)
        return
    with open(record_file, "r", encoding="utf-8") as f:
        acts = json.load(f)

    print("Replay start:", len(acts), "events")
    t0 = time.time()
    for a in acts:
        # 支持在回放时按 ESC 中止
        if keyboard.is_pressed("esc"):
            print("Replay aborted by ESC")
            return

        target = a["time"]
        # 等待到事件时间
        while True:
            elapsed = time.time() - t0
            if elapsed >= target:
                break
            # 可快速中止
            if keyboard.is_pressed("esc"):
                print("Replay aborted by ESC")
                return
            time.sleep(0.001)

        # 执行事件
        if a["type"] == "key":
            name = a["name"]
            if a["event"] == "down":
                try:
                    keyboard.press(name)
                except Exception as e:
                    print("keyboard.press error:", name, e)
            else:
                try:
                    keyboard.release(name)
                except Exception as e:
                    print("keyboard.release error:", name, e)

        elif a["type"] == "mouse":
            ev = a["event"]
            if ev == "move":
                x, y = a["pos"]
                # pyautogui.moveTo(x, y, duration=0)
            elif ev == "down":
                x, y = a["pos"]
                btn = a.get("button", "left")
                try:
                    pyautogui.mouseDown(x=x, y=y, button=btn)
                except Exception as e:
                    # pyautogui 有时要求小写 'left'/'right'
                    try:
                        pyautogui.mouseDown(x=x, y=y, button=btn.lower())
                    except Exception:
                        print("mouseDown error:", btn, e)
            elif ev == "up":
                x, y = a["pos"]
                btn = a.get("button", "left")
                try:
                    pyautogui.mouseUp(x=x, y=y, button=btn)
                except Exception as e:
                    try:
                        pyautogui.mouseUp(x=x, y=y, button=btn.lower())
                    except Exception:
                        print("mouseUp error:", btn, e)
            elif ev == "scroll":
                dx = int(a.get("dx", 0))
                dy = int(a.get("dy", 0))
                if dy:
                    pyautogui.scroll(dy)
                if dx:
                    pyautogui.hscroll(dx)

    print("Replay finished.")


# ------------ main loop ------------
def main_loop():
    print("Controls: F1 start record, F3 stop & save, F4 replay, ESC exit.")
    print("Note: run with sufficient privileges if keyboard hook fails on Windows/Linux.")
    while True:
        try:
            if keyboard.is_pressed("f1") and not recording:
                # start record in background thread to not block key polling loop
                threading.Thread(target=start_record, daemon=True).start()
                time.sleep(0.5)  # 防抖

            if keyboard.is_pressed("f3") and recording:
                stop_record()
                time.sleep(0.5)

            if keyboard.is_pressed("f4") and not recording:
                # replay in background thread so ESC can be polled
                t = threading.Thread(target=replay, daemon=True)
                t.start()
                # 等待一点防止多次触发
                time.sleep(0.5)

            if keyboard.is_pressed("esc"):
                print("Exit requested.")
                # 若正在录制则先停止并保存
                if recording:
                    stop_record()
                break

            time.sleep(0.05)
        except KeyboardInterrupt:
            print("KeyboardInterrupt, exiting.")
            if recording:
                stop_record()
            break


if __name__ == "__main__":
    # pyautogui 的 fail-safe（鼠标移动到左上角立即抛出）可根据喜好设置
    pyautogui.FAILSAFE = True
    main_loop()
