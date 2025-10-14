import asyncio
import threading
from listener import EnemyListener
from utils import *
import game_logic

class AutoSwitchLineController:
    def __init__(self, target_window):
        self.target_window = target_window
        self.first_failed = True
        self.place = None
        self.enemy_listener = EnemyListener(["小猪·闪闪"], self.on_monster_dead)
        self.is_hunting = False
        self.hunting_lock = threading.Lock()

        self.curr_pig = None
        self.next_pig = None
        self.states = []

        self.last_time = 0

        self.is_manual = False
        self.is_manual = True
        self.strat = 'none'  # 'current' or 'none' or 'manual'

        self.wait_pig_die = False
        self.task = None

    def reset_pigs(self):
        # self.stop_task()
        self.states = []
        # self.reset_place()
        # self.curr_pig = None
        self.next_pig = None
        log("重置小猪状态成功")

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
    
    def get_next_pig(self):
        if not self.curr_pig:
            for state in self.states:
                if state[2] == 'a':
                    return (state[0], state[1])
        found_curr = False
        place = self.curr_pig[1]
        for state in self.states:
            if self.strat == 'none':
                if found_curr and state[2] == 'a':
                    self.next_pig = (state[0], state[1])
                    break
            elif self.strat == 'current':
                if found_curr and state[2] == 'a' and state[1] == place:
                    return (state[0], state[1])

            if state[0] == self.curr_pig[0] and state[1] == self.curr_pig[1]:
                if state[2] == 'a':
                    break
                found_curr = True
        # 没找到则从头找
        for state in self.states:
            if state[2] == 'a':
                return (state[0], state[1])

    def cal_next_pig(self):
        self.log_all_pig()
        if self.all_pig_dead():
            self.curr_pig = None
            self.next_pig = None
        else:
            self.next_pig = self.get_next_pig()
        log(f"计算得到下一只小猪为: {self.next_pig if self.next_pig else '无'}")

    def deal_with_msg(self, msg):
        results = parse_msg(msg)
        for line, place, state in results:
            # 查找是否已有相同的 line 和 place
            for s in self.states:
                if s[0] == line: # and s[1] == place:
                    # 更新状态
                    if state == 's':
                        s[2] = state
                    break
            else:
                # 未找到则添加新的记录
                self.states.append([line, place, state])
        
                    
    async def on_monster_dead(self):
        if self.is_hunting and self.wait_pig_die:
            self.wait_pig_die = False
            log("监听到小猪闪闪死亡")
            if self.is_manual:
                log("手动模式中，不自动杀猪")
                return
            await asyncio.sleep(1)
            if self.curr_pig:
                for state in self.states:
                    if state[0] == self.curr_pig[0] and state[1] == self.curr_pig[1]:
                        state[2] = 's'
                        break
            self.cal_next_pig()
            if self.next_pig:
                line, place = self.next_pig
                log(f"准备去往： {line}{place}")
                self.start_switching(line, place)
    
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

    def start_switching(self, target_line, target_place=None):
        """启动同步切线，确保只有一个线程在执行切线操作"""
        if self.task is not None and self.task.is_alive():
            log("已有切线操作正在进行，无法启动新的切线")
            return
        self.stop_switching = False  # 确保没有停止标志
        self.task = threading.Thread(target=self.switch_line, args=(target_line, target_place))
        self.task.start()
    
    def stop_switching_thread(self):
        """停止切线操作"""
        self.stop_switching = True
        log("切线操作已请求停止")
        # 等待线程结束
        if self.task is not None:
            self.task.join()
            log("切线操作线程已停止")

    def switch_line(self, target_line, target_place=None):
        """切换线路"""
        with self.hunting_lock:  # 🔒 使用同步锁来确保线程安全
            if self.curr_pig:
                target_place = self.curr_pig[1]==target_place and None or target_place
            log(f"自动追踪，目标：{target_line }{target_place if target_place else 'None'}")
            if self.ensure_window_active():
                try:
                    self.curr_pig = (target_line, target_place)
                    if self.place == target_place:
                        target_place = None
                    if target_place:
                        self.set_place(target_place)
                    game_logic.switch_line(self.target_window, target_line, target_place)
                    self.wait_pig_die = True
                except Exception as e:
                    log(f"切线执行失败: {e}")

    def exit_program(self):
        log("检测到 / 键，退出程序")
        os._exit(0)
