from utils import *
import game_logic

class AutoSwitchLineController:
    def __init__(self, target_window):
        self.target_window = target_window
        self.auto_switch = False

    def switch_line(self, target_line):
        if self.auto_switch:
            log(f"自动切线模式，准备切换到线路 {target_line}")
            self.auto_switch = False
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
