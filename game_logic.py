from utils import *
import pyautogui
import time

def switch_line(win, line):
    """激活窗口并切换线路"""
    try:
        # 点击线路输入框（根据实际位置修改）
        input_box_pos = (1492,1007)  # 示例为屏幕中心，请替换为实际坐标
        input_box_pos = get_scale_point(input_box_pos, *get_window_width_and_height(win))
        input_box_pos = point_add_win(input_box_pos, win)  # 将窗口位置添加到点击位置
        pyautogui.click(input_box_pos)
        time.sleep(0.2)
        # 输入线路号
        pyautogui.typewrite(str(line), interval=0.05)
        # 按回车确认
        pyautogui.press('enter')
        log(f"已切换到线路 {line}")

    except Exception as e:
        log(f"switch_line failed:{e}")