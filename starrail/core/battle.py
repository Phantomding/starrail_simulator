# starrail/core/battle.py (基于你的本地文件进行美化和修正)
from typing import List
from .character import Character
from .ai_strategies import seele_should_cast_ultimate, default_should_cast_ultimate
from ..utils.logger import logger # 引入日志记录器

class Battle:
    def __init__(self, characters: List[Character]):
        self.characters = characters
        self.turn = 0
        self.is_over = False
        self.action_gauges = {char: 0 for char in self.characters}
        self.action_progress = {char: 0.0 for char in self.characters}
        self.skill_points_by_side = {}
        self.max_skill_points_by_side = {}
        self.character_skill_points = {char: 0 for char in self.characters}
        
        sides = set(char.side for char in self.characters)
        for side in sides:
            self.skill_points_by_side[side] = 3
            self.max_skill_points_by_side[side] = 5
        
        self.pending_next_turn_boosts = {}

    def get_skill_points(self, side: str) -> int:
        return self.skill_points_by_side.get(side, 0)

    def get_max_skill_points(self, side: str) -> int:
        return self.max_skill_points_by_side.get(side, 5)

    def can_use_skill(self, character: Character) -> bool:
        side = character.side
        skill_points = self.skill_points_by_side.get(side, 0)
        return skill_points > 0

    def use_skill_point(self, character: Character):
        side = character.side
        if self.skill_points_by_side.get(side, 0) > 0:
            self.skill_points_by_side[side] -= 1
            self.character_skill_points[character] += 1
            current = self.skill_points_by_side[side]
            max_points = self.max_skill_points_by_side.get(side, 5)
            logger.log(f"[战技点] {character.name}({side}) 消耗1点，{side}阵营剩余: {current}/{max_points}", color="yellow")

    def gain_skill_point(self, character: Character):
        side = character.side
        current = self.skill_points_by_side.get(side, 0)
        max_points = self.max_skill_points_by_side.get(side, 5)
        if current < max_points:
            self.skill_points_by_side[side] = current + 1
            logger.log(f"[战技点] {character.name}({side}) 回复1点，{side}阵营当前: {current + 1}/{max_points}", color="green")

    def set_skill_points(self, side: str, points: int):
        self.skill_points_by_side[side] = points

    def set_max_skill_points(self, side: str, max_points: int):
        self.max_skill_points_by_side[side] = max_points

    def display_character_stats(self):
        logger.start_block("📊 角色初始属性信息", color="blue")
        sides = sorted(list(set(char.side for char in self.characters)))
        for side in sides:
            logger.log(f"🎯 {side.upper()} 阵营:")
            side_chars = [char for char in self.characters if char.side == side]
            for char in side_chars:
                if not char.is_alive(): continue
                stats = char.get_current_stats()
                hp_str = f"HP: {char.hp:.0f}/{stats.get('HP', 0):.1f}"
                spd_str = f"速度: {stats.get('SPD', 0):.1f}"
                crit_str = f"暴击: {stats.get('CRIT Rate', 0):.1%}/{stats.get('CRIT DMG', 0):.1%}"
                energy_str = f"能量: {char.current_sp:.0f}/{char.max_sp:.0f}"
                logger.log(f"  - {char.name:<15} | {hp_str:<20} | {spd_str:<15} | {crit_str} | {energy_str}")
        logger.end_block()

    def run(self, max_turns=10):
        logger.log("="*60, color="purple")
        logger.log("⚔️ 战斗开始！", color="purple")
        logger.log("="*60, color="purple")
        
        self.display_character_stats()
        
        for side in self.skill_points_by_side:
            points = self.skill_points_by_side[side]
            max_points = self.max_skill_points_by_side[side]
            logger.log(f"[战技点] {side}阵营初始: {points}/{max_points}", color="yellow")
        
        for char in self.characters:
            if char.is_alive():
                # --- 关键修正: 在触发任何战斗开始效果前，为角色设置战斗上下文 ---
                char._battle_context = self
                # --- 修正结束 ---
                
                self.action_gauges[char] = 0
                
                # 现在，这些on_battle_start调用将能正确访问战斗上下文
                if hasattr(char, 'light_cone') and char.light_cone and hasattr(char.light_cone, 'skill_instance') and char.light_cone.skill_instance:
                    char.light_cone.skill_instance.on_battle_start(char)
                if hasattr(char, 'relic_set_skills') and char.relic_set_skills:
                    for skill_instance in char.relic_set_skills:
                        skill_instance.on_battle_start(char)
        
        for char in self.characters:
            if char.is_alive():
                self.action_progress[char] = 0.0

        round_count = 1
        EPS = 1e-6
        while not self.is_over and round_count <= max_turns:
            action_value_pool = 150 if round_count == 1 else 100
            logger.log(f"\n{'='*20} [全局回合 {round_count}] | 行动值池: {action_value_pool} {'='*20}", color="yellow")
            
            self._check_and_cast_instant_ultimates()
            if self.is_over: break

            current_speeds = {c: c.spd for c in self.characters}

            while action_value_pool > 0:
                ready = [c for c in self.action_progress if c.is_alive() and self.action_progress[c] >= 1 - EPS]
                ready.sort(key=lambda c: (-c.spd))
                
                while ready:
                    for c in ready:
                        logger.start_block(f"🎬 {c.name}({c.side}) 行动！ (SPD={c.spd:.1f})", color="green")
                        c.take_turn(self)
                        self.action_progress[c] -= 1
                        logger.end_block()
                        
                        self.check_battle_end()
                        if self.is_over: break
                        
                        boost = self.pending_next_turn_boosts.pop(c, 0)
                        if boost > 0:
                            self.boost_action_progress(c, boost)
                        
                        self._check_and_cast_instant_ultimates()
                        if self.is_over: break
                        
                        if hasattr(c, 'is_in_extra_turn') and c.is_in_extra_turn():
                            logger.start_block(f"🔁 {c.name} 获得额外回合！", color="green")
                            c.take_turn(self)
                            c.set_extra_turn(False)
                            logger.end_block()
                            self.check_battle_end()
                            if self.is_over: break
                    if self.is_over: break
                    ready = [c for c in self.action_progress if c.is_alive() and self.action_progress[c] >= 1 - EPS]
                    ready.sort(key=lambda c: (-c.spd))
                if self.is_over: break

                min_need = float('inf')
                for char in self.characters:
                    if char.is_alive():
                        spd = char.spd
                        action_cost = 10000 / spd if spd > 0 else float('inf')
                        need = (1 - self.action_progress[char]) * action_cost
                        if need > 0 and need < min_need:
                            min_need = need
                
                advance = action_value_pool if (min_need == float('inf') or min_need <= 0 or min_need > action_value_pool) else min_need
                
                logger.log(f"-> 行动值池推进: {advance:.2f} | 剩余: {action_value_pool - advance:.2f}", color="cyan")
                
                for c in self.action_progress:
                    spd = c.spd
                    cost = 10000 / spd if spd > 0 else float('inf')
                    self.action_progress[c] += advance / cost
                action_value_pool -= advance
                
                for character, boost_amount in self.pending_next_turn_boosts.items():
                    self.boost_action_progress(character, boost_amount)
                self.pending_next_turn_boosts = {}
                
                ready_after_advance = [c for c in self.action_progress if c.is_alive() and self.action_progress[c] >= 1 - EPS]
                if action_value_pool <= 0 and not ready_after_advance:
                    logger.log_verbose(f"池子耗尽且无角色行动，回合结束。")
                    break
            round_count += 1
        
        logger.log("\n" + "="*60, color="purple")
        logger.log("🎉 战斗结束！", color="purple")

    def check_battle_end(self):
        sides = set(char.side for char in self.characters if char.is_alive())
        if len(sides) <= 1:
            self.is_over = True
            winning_side = list(sides)[0] if sides else "无"
            logger.log(f"\n🏆 战斗结束！{winning_side} 阵营获胜！", color="green")

    def boost_action_progress(self, character, boost_amount):
        if character in self.action_progress:
            current_progress = self.action_progress[character]
            new_progress = min(current_progress + boost_amount, 1.0)
            self.action_progress[character] = new_progress
            logger.log(f"[行动提前] {character.name} 进度: {current_progress:.1%} -> {new_progress:.1%}", color="blue")

    def boost_next_turn_progress(self, character, boost_amount):
        if character in self.action_progress:
            current_progress = self.action_progress[character]
            if current_progress >= 1.0:
                new_progress = min(boost_amount, 1.0)
                self.action_progress[character] = new_progress
                logger.log(f"[下回合提前] {character.name}: 0.0% -> {new_progress:.1%}", color="blue")
                if new_progress >= 1.0:
                    logger.log(f"[立即行动] {character.name} 因进度提升而立即行动！", color="green")
            else:
                new_progress = min(current_progress + boost_amount, 1.0)
                self.action_progress[character] = new_progress
                logger.log(f"[当前回合提前] {character.name}: {current_progress:.1%} -> {new_progress:.1%}", color="blue")

    def delayed_boost_next_turn_progress(self, character, boost_amount):
        self.pending_next_turn_boosts[character] = self.pending_next_turn_boosts.get(character, 0) + boost_amount
        logger.log_verbose(f"{character.name} 预约了 {boost_amount:.1%} 的下次行动提前。")

    def _check_and_cast_instant_ultimates(self):
        for char in self.characters:
            if char.can_instant_ultimate and char.is_alive() and not char.is_in_extra_turn():
                ai_should_cast = getattr(char, 'should_cast_ultimate', default_should_cast_ultimate)
                if not ai_should_cast(char, self): continue
                
                ultimate_skill = next((s for s in char.skills if getattr(s, 'type', '') == 'Ultra'), None)
                if ultimate_skill:
                    enemies = [c for c in self.characters if c.side != char.side and c.is_alive()]
                    if enemies:
                        import random
                        target = random.choice(enemies)
                        max_level = getattr(ultimate_skill, 'max_level', 1)
                        logger.start_block(f"⚡ {char.name} 插队释放终结技 [{getattr(ultimate_skill, 'name', 'Ultra')}]!", color="purple")
                        char.set_last_skill_type("Ultra")
                        char.consume_energy(char.max_sp)
                        if hasattr(char, 'light_cone') and char.light_cone and hasattr(char.light_cone, 'skill_instance') and char.light_cone.skill_instance:
                            char.light_cone.skill_instance.on_skill_used(char, "Ultra")
                        if hasattr(char, 'relic_set_skills'):
                            for skill_instance in char.relic_set_skills:
                                skill_instance.on_skill_used(char, "Ultra")
                        if hasattr(char, 'skill_manager') and char.skill_manager is not None:
                            char.skill_manager.use_skill(getattr(ultimate_skill, 'skill_id', ''), char, [target], self, level=max_level)
                        else:
                            ultimate_skill.use(char, [target], self, level=max_level)
                        char.on_skill_used("Ultra")
                        char.can_instant_ultimate = False
                        logger.end_block()
                        self.check_battle_end()
                        if self.is_over: break
