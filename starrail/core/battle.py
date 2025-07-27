# battle.py
from typing import List
from .character import Character
from .ai_strategies import seele_should_cast_ultimate, default_should_cast_ultimate

class Battle:
    def __init__(self, characters: List[Character]):
        self.characters = characters
        self.turn = 0
        self.is_over = False
        # 初始化每个角色的行动条
        self.action_gauges = {char: 0 for char in self.characters}
        
        # 行动进度管理（作为实例变量）
        self.action_progress = {char: 0.0 for char in self.characters}
        
        # 按阵营管理战技点
        self.skill_points_by_side = {}
        self.max_skill_points_by_side = {}
        self.character_skill_points = {char: 0 for char in self.characters}
        
        # 初始化各阵营的战技点
        sides = set(char.side for char in self.characters)
        for side in sides:
            self.skill_points_by_side[side] = 3  # 默认初始3点战技点
            self.max_skill_points_by_side[side] = 5  # 默认最大5点战技点
        
        # 初始化延迟进度提升队列
        self._delayed_progress_boosts = []
        # 新增：记录每个角色的下回合提前量
        self.pending_next_turn_boosts = {}

    def get_skill_points(self, side: str) -> int:
        """获取指定阵营的战技点数量"""
        return self.skill_points_by_side.get(side, 0)

    def get_max_skill_points(self, side: str) -> int:
        """获取指定阵营的最大战技点数量"""
        return self.max_skill_points_by_side.get(side, 5)

    def can_use_skill(self, character: Character) -> bool:
        """检查角色是否可以使用战技"""
        side = character.side
        skill_points = self.skill_points_by_side.get(side, 0)
        if skill_points <= 0:
            return False
        return True

    def use_skill_point(self, character: Character):
        """消耗战技点"""
        side = character.side
        if self.skill_points_by_side.get(side, 0) > 0:
            self.skill_points_by_side[side] -= 1
            self.character_skill_points[character] += 1
            current = self.skill_points_by_side[side]
            max_points = self.max_skill_points_by_side.get(side, 5)
            print(f"[战技点] {character.name}({side}) 消耗1点战技点，{side}阵营剩余: {current}/{max_points}")

    def gain_skill_point(self, character: Character):
        """获得战技点"""
        side = character.side
        current = self.skill_points_by_side.get(side, 0)
        max_points = self.max_skill_points_by_side.get(side, 5)
        if current < max_points:
            self.skill_points_by_side[side] = current + 1
            print(f"[战技点] {character.name}({side}) 回复1点战技点，{side}阵营当前: {current + 1}/{max_points}")

    def set_skill_points(self, side: str, points: int):
        """设置指定阵营的战技点数量"""
        self.skill_points_by_side[side] = points

    def set_max_skill_points(self, side: str, max_points: int):
        """设置指定阵营的最大战技点数量"""
        self.max_skill_points_by_side[side] = max_points

    def run(self, max_turns=10):
        print("战斗开始！（全局池子+角色进度累积机制-全局回合修正版）")
        # 显示各阵营初始战技点
        for side in self.skill_points_by_side:
            points = self.skill_points_by_side[side]
            max_points = self.max_skill_points_by_side[side]
            print(f"[战技点] {side}阵营初始战技点: {points}/{max_points}")
        
        # 初始化
        for char in self.characters:
            if char.is_alive():
                self.action_gauges[char] = 0  # 不再用作推进条
                
                # 光锥技能战斗开始效果
                if hasattr(char, 'light_cone') and char.light_cone and hasattr(char.light_cone, 'skill_instance') and char.light_cone.skill_instance:
                    char.light_cone.skill_instance.on_battle_start(char)
                
                # 遗器套装技能战斗开始效果
                if hasattr(char, 'relic_set_skills') and char.relic_set_skills:
                    for skill_instance in char.relic_set_skills:
                        skill_instance.on_battle_start(char)
        
        # 重置行动进度
        for char in self.characters:
            if char.is_alive():
                self.action_progress[char] = 0.0
        round_count = 1
        EPS = 1e-6
        while not self.is_over and round_count <= max_turns:
            action_value_pool = 150 if round_count == 1 else 100
            print(f"=== [全局回合 {round_count}] 行动值池: {action_value_pool} ===")
            # 1. 优先处理所有可立即释放终极技的角色
            self._check_and_cast_instant_ultimates()
            if self.is_over:
                break
            while action_value_pool > 0:
                # 先让所有ready角色行动
                ready = [c for c in self.action_progress if self.action_progress[c] >= 1 - EPS and c.is_alive()]
                ready.sort(key=lambda c: (-c.spd))
                
                while ready:
                    for c in ready:
                        spd = c.spd
                        print(f"[回合{round_count}] {c.name}({c.side}) 行动！（SPD={spd} 进度={self.action_progress[c]:.4f} 剩余池={action_value_pool:.4f}）")
                        c.take_turn(self)
                        self.action_progress[c] -= 1
                        # 行动后立即应用下回合提前
                        boost = self.pending_next_turn_boosts.pop(c, 0)
                        if boost > 0:
                            before = self.action_progress[c]
                            self.action_progress[c] = min(self.action_progress[c] + boost, 1.0)
                            print(f"[下回合提前] {c.name}: {before:.4f} -> {self.action_progress[c]:.4f} (+{boost:.4f})")
                        # 行动后立即检测终极技插队
                        self._check_and_cast_instant_ultimates()
                        if self.is_over:
                            break
                        # 检查是否需要额外回合
                        if hasattr(c, 'is_in_extra_turn') and c.is_in_extra_turn():
                            print(f"[额外回合] {c.name} 立即进行额外回合！")
                            c.take_turn(self)
                            c.set_extra_turn(False)
                            self.check_battle_end()
                            if self.is_over:
                                break
                    if self.is_over:
                        break
                    ready = [c for c in self.action_progress if self.action_progress[c] >= 1 - EPS and c.is_alive()]
                    ready.sort(key=lambda c: (-c.spd))
                if self.is_over:
                    break
                # 计算每个角色距离进度=1还差多少池子
                min_need = float('inf')
                debug_needs = []
                for char in self.characters:
                    if char.is_alive():
                        spd = char.spd
                        action_cost = 10000 / spd if spd > 0 else float('inf')
                        need = (1 - self.action_progress[char]) * action_cost
                        debug_needs.append((char.name, self.action_progress[char], need, action_cost))
                        if need > 0 and need < min_need:
                            min_need = need
                # print(f"推进前角色进度和到下次行动所需池子:")
                # for name, prog, need, cost in debug_needs:
                #     print(f"  {name}: 进度={prog:.4f} 需池={need:.4f} 行动消耗={cost:.4f}")
                # 如果池子不足以让任何角色进度达到1，则advance=action_value_pool
                if min_need == float('inf') or min_need <= 0 or min_need > action_value_pool:
                    advance = action_value_pool
                else:
                    advance = min_need
                print(f"本次推进量: {advance:.4f} (池子剩余: {action_value_pool:.4f})")
                # 所有角色均匀积累进度
                for c in self.action_progress:
                    spd = c.spd
                    cost = 10000 / spd if spd > 0 else float('inf')
                    before = self.action_progress[c]
                    self.action_progress[c] += advance / cost
                    # print(f"  {c.name}: 进度 {before:.4f} -> {self.action_progress[c]:.4f}")
                action_value_pool -= advance
                # print(f"推进后池子剩余: {action_value_pool:.4f}")
                
                # 处理延迟的进度提升（在进度推进完成后）
                if hasattr(self, '_delayed_progress_boosts'):
                    for character, boost_amount in self._delayed_progress_boosts:
                        if character in self.action_progress:
                            current_progress = self.action_progress[character]
                            new_progress = min(current_progress + boost_amount, 1.0)
                            self.action_progress[character] = new_progress
                            print(f"[延迟进度提升] {character.name}: {current_progress:.4f} -> {new_progress:.4f} (+{boost_amount:.4f})")
                    self._delayed_progress_boosts = []  # 清空延迟队列
                
                # 推进后如果池子耗尽且没有角色能行动，直接break
                ready = [c for c in self.action_progress if self.action_progress[c] >= 1 - EPS and c.is_alive()]
                if action_value_pool <= 0 and not ready:
                    print(f"[DEBUG] 池子耗尽且没有角色能行动，当前所有角色进度：")
                    for c in self.action_progress:
                        print(f"  {c.name}: 进度={self.action_progress[c]:.4f}")
                    break
            round_count += 1
        print("战斗结束！")

    def check_battle_end(self):
        # 检查是否只剩一方存活
        sides = set(char.side for char in self.characters if char.is_alive())
        if len(sides) <= 1:
            self.is_over = True
            if len(sides) == 1:
                winning_side = list(sides)[0]
                print(f"战斗结束！{winning_side}阵营获胜！")
            else:
                print("战斗结束！双方都阵亡了！") 

    def boost_action_progress(self, character, boost_amount):
        """
        提升指定角色的当前行动进度
        character: 要提升行动进度的角色
        boost_amount: 提升的进度量（0-1之间的小数）
        """
        if character in self.action_progress:
            current_progress = self.action_progress[character]
            new_progress = min(current_progress + boost_amount, 1.0)  # 不超过1.0
            self.action_progress[character] = new_progress
            print(f"[行动进度提升] {character.name}: {current_progress:.4f} -> {new_progress:.4f} (+{boost_amount:.4f})")

    def boost_next_turn_progress(self, character, boost_amount):
        """
        提升指定角色的下一回合行动进度
        character: 要提升行动进度的角色
        boost_amount: 提升的进度量（0-1之间的小数）
        """
        if character in self.action_progress:
            current_progress = self.action_progress[character]
            # 如果当前进度已经达到1.0，说明角色已经行动过，直接提升下一回合进度
            if current_progress >= 1.0:
                # 角色已经行动，为下一回合提升进度
                new_progress = min(boost_amount, 1.0)  # 不超过1.0
                self.action_progress[character] = new_progress
                print(f"[下一回合进度提升] {character.name}: 0.0000 -> {new_progress:.4f} (+{boost_amount:.4f})")
                
                # 如果提升后的进度达到或超过1.0，角色应该立即行动
                if new_progress >= 1.0:
                    print(f"[立即行动] {character.name} 因进度提升而立即行动！")
            else:
                # 角色还未行动，提升当前进度
                new_progress = min(current_progress + boost_amount, 1.0)
                self.action_progress[character] = new_progress
                print(f"[当前回合进度提升] {character.name}: {current_progress:.4f} -> {new_progress:.4f} (+{boost_amount:.4f})")

    def delayed_boost_next_turn_progress(self, character, boost_amount):
        """
        延迟提升指定角色的下一回合行动进度（在进度推进完成后调用）
        character: 要提升行动进度的角色
        boost_amount: 提升的进度量（0-1之间的小数）
        """
        # 将进度提升添加到 pending_next_turn_boosts 字典中
        self.pending_next_turn_boosts[character] = self.pending_next_turn_boosts.get(character, 0) + boost_amount
        print(f"[延迟进度提升] {character.name} 的下一回合行动进度将提前 {boost_amount*100:.0f}%")

    def _check_and_cast_instant_ultimates(self):
        for char in self.characters:
            if char.can_instant_ultimate and char.is_alive() and not char.is_in_extra_turn():
                # AI决策是否释放终极技
                ai_should_cast = getattr(char, 'should_cast_ultimate', default_should_cast_ultimate)
                if not ai_should_cast(char, self):
                    continue
                # 查找终极技
                ultimate_skill = None
                for s in char.skills:
                    if getattr(s, 'type', '') == 'Ultra':
                        ultimate_skill = s
                        break
                if ultimate_skill:
                    enemies = [c for c in self.characters if c.side != char.side and c.is_alive()]
                    if enemies:
                        import random
                        target = random.choice(enemies)
                        max_level = getattr(ultimate_skill, 'max_level', 1)
                        print(f"[插队终极技] {char.name} 能量满，立即释放终极技 [{getattr(ultimate_skill, 'name', str(ultimate_skill))}] 攻击 {target.name}")
                        char.set_last_skill_type("Ultra")
                        char.consume_energy(char.max_sp)
                        if hasattr(char, 'light_cone') and char.light_cone and hasattr(char.light_cone, 'skill_instance') and char.light_cone.skill_instance:
                            char.light_cone.skill_instance.on_skill_used(char, "Ultra")
                        if hasattr(char, 'relic_set_skills') and char.relic_set_skills:
                            for skill_instance in char.relic_set_skills:
                                skill_instance.on_skill_used(char, "Ultra")
                        if hasattr(char, 'skill_manager') and char.skill_manager is not None:
                            char.skill_manager.use_skill(getattr(ultimate_skill, 'skill_id', ''), char, [target], self, level=max_level)
                        else:
                            ultimate_skill.use(char, [target], self, level=max_level)
                        char.on_skill_used("Ultra")
                        char.can_instant_ultimate = False
                        self.check_battle_end()
                        if self.is_over:
                            break 