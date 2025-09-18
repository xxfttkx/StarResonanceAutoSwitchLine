from utils import *
import game_logic

class AutoSwitchLineController:
    def __init__(self, target_window):
        self.target_window = target_window
        self.auto_switch = False
        self.first_failed = True

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

    def switch_line(self, target_line):
        """切换线路"""
        if not self.auto_switch:
            return

        log(f"自动切线模式，准备切换到线路 {target_line}")
        self.auto_switch = False

        if self.ensure_window_active():
            try:
                game_logic.switch_line(self.target_window, target_line)
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
