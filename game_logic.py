import keyboard
from utils import *
import pyautogui
import time
from record import replay

def switch_line(win, line, place=None):
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
        log(f"正在切换到线路 {line}")
        wait_and_press_h(win, place)
    except Exception as e:
        log(f"switch_line failed:{e}")
    

def ensure_window_active(win):
    """确保目标窗口处于激活状态"""
    try:
        if not win.isActive:
            pyautogui.press("alt")
            win.activate()
            time.sleep(0.2)
        return True
    except Exception as e:
        log(f"activate_win failed:{e}")
    return False

def wait_black(win, delay_start, timeout, delay_judge):
    time.sleep(delay_start)
    log("等待黑屏结束...")

    x1, y1, x2, y2 = get_client_rect(win)
    width = x2 - x1
    height = y2 - y1

    # 监测点位置（客户区下方90%高度处中间）
    p1 = (x1 + width // 2, y1 + int(height * 0.90))
    p2 = (x1 + width // 2, y1 + int(height * 0.1))
    p3 = (x1 + width // 4, y1 + int(height * 0.05))

    def is_black(rgb, threshold=30):
        # 判断是否接近黑色（R/G/B 都低于阈值）
        return all(channel < threshold for channel in rgb)
    
    start_time = time.time()

    while True:
        color_1 = get_pixel_color(p1[0], p1[1])
        color_2 = get_pixel_color(p2[0], p2[1])
        color_3 = get_pixel_color(p3[0], p3[1])
        if not is_black(color_1) or not is_black(color_2)  or not is_black(color_3):
            log("检测到非黑屏，切线完成")
            break
        
        if time.time() - start_time > timeout:
            log("等待超时，强制继续")
            break
        time.sleep(delay_judge)

    time.sleep(0.5)
    log("黑屏结束")

def place_to_key(place):
    if place in {"左上","右上","右"}:
        return 'f10'
    elif place == "崖之遗迹":
        return 'f5'
    elif place == "麦田":
        return 'f9'
    elif place == "卡":
        return 'f11'
    elif place == "驿站":
        return 'f8'
    elif place == "帐篷":
        return 'f7'
    return None

def wait_and_press_h(win, place=None):
    wait_black(win,10,25,2)
    ensure_window_active(win)
    if place:
        log("即将前往位置: " + place)
        key = place_to_key(place)
        if key:
            keyboard.press_and_release(key)
            wait_and_move(win, place)
    start_attack()

def start_attack():
    keyboard.press_and_release('p')
    time.sleep(0.1)
    keyboard.press_and_release('h')


def wait_and_move(win, place=None):
    wait_black(win,5,15,1)
    log("到达位置，开始移动")
    if place:
        if place == "卡":
            replay("records/record_ka.json")
        elif place == "麦田":
            replay("records/record_m.json")
        elif place == "崖之遗迹":
            replay("records/record_y.json")
        elif place == "左上":
            replay("records/record_z.json")
        elif place == "右上":
            replay("records/record_ys.json")
        elif place == "右":
            replay("records/record_you.json")
        elif place == "帐篷":
            replay("records/record_zp.json")
        elif place == "驿站":
            replay("records/record_yz.json")