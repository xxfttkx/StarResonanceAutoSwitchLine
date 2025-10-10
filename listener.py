import asyncio
import time
import aiohttp
from utils import log

TARGET_GROUP = ["小猪·闪闪", "娜宝·闪闪"]

def find_enemy(enemies, target_group):
        for eid, info in enemies.items():
            for name in target_group:
                if info.get('name') == name:
                    return eid, info
        return None

class EnemyListener:
    def __init__(self, target_group=None, callback=None):
        self.target_group = target_group if target_group else TARGET_GROUP
        self.on_monster_dead = None
        self.enemy_url = "http://localhost:8989/api/enemies"
        self.poll_interval_sec = 1
        self.set_monster_dead_callback(callback)
    
    def set_target_group(self, target_group):
        self.target_group = target_group
        log(f"设置监听目标: {self.target_group}")

    def set_monster_dead_callback(self, func):
        self.on_monster_dead = func

    async def try_listen(self):
        while True:
            try:
                log("开始监听...")
                await self.listen()
            except Exception as e:
                log(f"监听过程中发生错误: {e}")
                time.sleep(10)

    async def listen(self):
        async with aiohttp.ClientSession() as session:
            targethp = 0
            lastHP = -1
            count = 0
            while True:
                async with session.get(self.enemy_url) as response:
                    if response.status != 200:
                        log(f"GET {self.enemy_url} -> HTTP {response.status}")
                        return
                    data = await response.json(content_type=None)
                    enimies = data.get('enemy', {})
                    target = find_enemy(enimies, self.target_group)
                    if target:
                        target = target[1]
                        targethp = target.get('hp', -1)
                        if lastHP != targethp or targethp==target.get('max_hp', 0):
                            log(f"target: {target}")
                    if target and target.get('max_hp', 0)>0:
                        targethp = target.get('hp', -1)
                        if targethp == 0:
                            if callable(self.on_monster_dead):
                                await self.on_monster_dead()
                        if lastHP == targethp:
                            # 丢包
                            count +=1
                            if (count > 10 and targethp < 1000) or (count>20):
                                if callable(self.on_monster_dead):
                                    await self.on_monster_dead()
                        else:
                            count = 0
                            lastHP = targethp
                    else:
                        if callable(self.on_monster_dead):
                            await self.on_monster_dead()
                await asyncio.sleep(self.poll_interval_sec)
