import asyncio
import sys
import threading
import tkinter as tk
from tkinter import scrolledtext
import keyboard
from auto_switch_line_controller import AutoSwitchLineController
from query import listen
from text_redirector import TextRedirector
from utils import *

stop_event = asyncio.Event()  # 用于安全退出 listen()


def on_input_enter(event, controller):
    text = input_box.get("1.0", "end-1c").strip()
    if text:
        log(f"输入: {text}")
        handle_input(text, controller)
        input_box.delete("1.0", "end")
    return "break"  # 防止 Tkinter 在输入框里插入换行


def handle_input(text, controller):
    log(f"收到输入: {text}")
    line, place = parse_line_place(text)
    log(f"line: {line}; place: {place}")
    controller.auto_switch = True
    controller.switch_line(line, place)


def on_close(root):
    """退出程序时调用"""
    log("正在退出程序...")
    keyboard.unhook_all()             # 解除所有热键
    stop_event.set()                  # 通知异步任务结束
    root.destroy()                    # 关闭 Tk 窗口
    sys.exit(0)                       # 彻底退出


def start_gui():
    controller = AutoSwitchLineController(find_target_window())
    root = tk.Tk()
    root.title("Simple GUI")
    root.geometry("1200x800")
    root.configure(bg="#f0f4f7")

    # 左侧输入框
    left_frame = tk.Frame(root, bg="#f0f4f7")
    left_frame.grid(row=0, column=0, sticky="nswe", padx=20, pady=20)

    tk.Label(left_frame, text="输入命令并按回车", font=("Microsoft YaHei", 16, "bold"), bg="#f0f4f7").pack(anchor="w", pady=10)
    global input_box
    input_box = tk.Text(left_frame, height=5, width=40, font=("Consolas", 14))
    input_box.pack(fill="x", pady=10)
    input_box.bind("<Return>", lambda e: on_input_enter(e, controller))

    # 日志区
    right_frame = tk.Frame(root, bg="#ffffff")
    right_frame.grid(row=0, column=1, sticky="nswe", padx=20, pady=20)

    tk.Label(right_frame, text="运行日志", font=("Microsoft YaHei", 16, "bold"), bg="#ffffff").pack(anchor="w", pady=10)
    log_area = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, width=80, height=40,
                                         font=("Consolas", 12), bg="#1e1e1e", fg="#dcdcdc")
    log_area.pack(fill="both", expand=True)

    sys.stdout = TextRedirector(log_area, "stdout")
    sys.stderr = TextRedirector(log_area, "stderr")
    log_area.tag_configure("stderr", foreground="red")
    log_area.tag_configure("stdout", foreground="white")

    # 底部控制按钮区域
    bottom_frame = tk.Frame(root, bg="#f0f4f7")
    bottom_frame.grid(row=1, column=0, columnspan=2, pady=20)

    quit_btn = tk.Button(
        bottom_frame,
        text="✖ 结束程序",
        font=("Microsoft YaHei", 14),
        width=15,
        height=2,
        bg="#E53935",
        fg="white",
        relief="flat",
        command=lambda: on_close(root)
    )
    quit_btn.pack(side="left", padx=10)

    # 网格布局调整
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)
    root.grid_columnconfigure(1, weight=2)

    # 注册热键
    keyboard.add_hotkey('-', controller.switch_open_auto_switch_line)
    keyboard.add_hotkey('*', controller.switch_close_auto_switch_line)
    keyboard.add_hotkey('+', controller.reset_place)

    # 启动异步监听线程
    threading.Thread(target=lambda: asyncio.run(listen(controller, stop_event)), daemon=True).start()
    threading.Thread(target=lambda: asyncio.run(controller.enemy_listener.try_listen()), daemon=True).start()

    # 绑定关闭事件（窗口关闭或点击“结束程序”按钮都触发）
    root.protocol("WM_DELETE_WINDOW", lambda: on_close(root))

    root.mainloop()


if __name__ == "__main__":
    start_gui()
