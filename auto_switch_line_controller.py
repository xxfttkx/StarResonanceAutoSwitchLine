from listener import EnemyListener
from utils import *
import game_logic

class AutoSwitchLineController:
    def __init__(self, target_window):
        self.target_window = target_window
        self.auto_switch = False
        self.first_failed = True
        self.place = None
        self.enemy_listener = EnemyListener(["小猪·闪闪"], self.notify_monster_dead)
        self.lock = False

    def notify_monster_dead(self):
        if not self.lock:
            self.lock = True
            log("监听到小猪闪闪死亡，等待新的情报")
            self.auto_switch = True 
    
    def reset_place(self):
        self.place = None
        log("重置位置成功")
        # screenshot_window(self.target_window)
    
    def set_place(self, place):
        self.place = place

    def ensure_window_active(self):
        """确保目标窗口处于激活状态"""
        for attempt in range(2):  # 最多尝试两次
            try:
                if not self.target_window.isActive:
                    pyautogui.press("alt")
                    self.target_window.activate()
                    time.sleep(0.2)
                    return True
                return True
            except Exception as e:
                log(f"activate_win failed: {e}")
                if attempt == 0:  # 第一次失败，尝试重新查找
                    log("窗口激活失败，尝试重新查找窗口")
                    self.target_window = find_target_window()
        return False

    def switch_line(self, target_line, target_place = None):
        """切换线路"""
        if not self.auto_switch:
            return

        log(f"自动切线模式，准备切换到线路 {target_line}")
        self.auto_switch = False

        if self.ensure_window_active():
            try:
                if self.place == target_place:
                    target_place = None
                game_logic.switch_line(self.target_window, target_line, target_place)
                if target_place:
                    self.set_place(target_place)
                self.lock = False
            except Exception as e:
                log(f"热键执行失败: {e}")

    def switch_auto_switch_line(self):
        self.auto_switch = not self.auto_switch
        log(f"自动切线状态切换为: {'开启' if self.auto_switch else '关闭'}")
    
    def switch_open_auto_switch_line(self):
        if not self.auto_switch:
            self.switch_auto_switch_line()
    
    def switch_close_auto_switch_line(self):
        if self.auto_switch:
            self.switch_auto_switch_line()

    def exit_program(self):
        log("检测到 / 键，退出程序")
        os._exit(0)
