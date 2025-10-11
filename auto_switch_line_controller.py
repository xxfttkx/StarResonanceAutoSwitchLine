import asyncio
import threading
from listener import EnemyListener
from utils import *
import game_logic

class AutoSwitchLineController:
    def __init__(self, target_window):
        self.target_window = target_window
        self.auto_switch = False
        self.first_failed = True
        self.place = None
        self.enemy_listener = EnemyListener(["小猪·闪闪"], self.on_monster_dead)
        self.lock = False

        self.auto_switch_lock = threading.Lock()

        self.curr_pig = None
        self.next_pig = None
        self.states = []

        self.last_time = 0

    def all_pig_dead(self):
        for state in self.states:
            if state[2] == 'a':
                return False
        return True
    
    def log_all_pig(self):
        log("当前小猪状态:")
        for state in self.states:
            status = "✅" if state[2] == 'a' else "❌"
            log(f"{state[0]}{state[1]}: {status}")
    
    def cal_next_pig(self):
        self.log_all_pig()
        if self.all_pig_dead():
            self.curr_pig = None
            self.next_pig = None
        else:
            if self.curr_pig == None:
                for state in self.states:
                    if state[2] == 'a':
                        self.next_pig = (state[0], state[1])
                        break
            else:
                found_curr = False
                for state in self.states:
                    if found_curr and state[2] == 'a':
                        self.next_pig = (state[0], state[1])
                        break
                    if state[0] == self.curr_pig[0] and state[1] == self.curr_pig[1]:
                        if state[2] == 'a':
                            break
                        found_curr = True
                else:
                    for state in self.states:
                        if state[2] == 'a':
                            self.next_pig = (state[0], state[1])
                            break
        log(f"计算得到下一只小猪为: {self.next_pig if self.next_pig else '无'}")

    def deal_with_msg(self, msg):
        results = parse_msg(msg)
        for line, place, state in results:
            # 查找是否已有相同的 line 和 place
            for s in self.states:
                if s[0] == line and s[1] == place:
                    # 更新状态
                    if state == 's':
                        s[2] = state
                    break
            else:
                # 未找到则添加新的记录
                self.states.append([line, place, state])
        
                    
    async def on_monster_dead(self):
        if not self.lock:
            self.lock = True
            log("监听到小猪闪闪死亡，等待新的情报")
            await asyncio.sleep(1)
            if self.curr_pig:
                for state in self.states:
                    if state[0] == self.curr_pig[0] and state[1] == self.curr_pig[1]:
                        state[2] = 's'
                        break
            self.auto_switch = True
            self.cal_next_pig()
            if self.next_pig:
                line, place = self.next_pig
                log(f"准备切换到线路 {line} 位置 {place}")
                self.task = asyncio.create_task(self.switch_line(line, place))

    def stop_task(self):
        if hasattr(self, 'task') and self.task and not self.task.done():
            self.task.cancel()
            log("已取消当前切线任务")
        self.reset_place()
    
    def reset_place(self):
        self.place = None
        self.curr_pig = None
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

    async def switch_line(self, target_line, target_place = None):
        """切换线路"""
        if not self.auto_switch:
            log(f"非自动切线模式，不切线")
            return

        log(f"自动切线模式，准备切换到线路 {target_line}")
        self.auto_switch = False

        if self.ensure_window_active():
            try:
                self.curr_pig = (target_line, target_place)
                if self.place == target_place:
                    target_place = None
                await asyncio.to_thread(game_logic.switch_line, self.target_window, target_line, target_place)
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
