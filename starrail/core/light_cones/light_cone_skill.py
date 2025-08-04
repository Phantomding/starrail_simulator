# light_cone_skill.py (已重构和新增)
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from ...utils.logger import logger

# 前向声明以支持类型提示
if False:
    from starrail.core.character import Character
    from starrail.core.skills.buff import Buff

class LightConeSkill(ABC):
    """光锥技能基类"""
    def __init__(self, skill_id: str, name: str, desc: str, params: List[List[float]], level: int = 1):
        self.skill_id, self.name, self.desc, self.params, self.level = skill_id, name, desc, params, max(1, min(level, len(params)))
        self.current_params = params[self.level - 1]
    
    @abstractmethod
    def get_base_stats(self) -> Dict[str, float]: pass
    
    def on_battle_start(self, character: 'Character'): pass
    def on_turn_start(self, character: 'Character'): pass
    def on_skill_used(self, character: 'Character', skill_type: str): pass
    def on_damage_dealt(self, character: 'Character', damage: float, skill_type: str): pass
    def on_damage_received(self, character: 'Character', damage: float): pass
    def on_enemy_killed(self, character: 'Character'): pass
    def get_healing_bonus(self, skill_type: str) -> float: return 0.0

class InTheNightSkill(LightConeSkill):
    """于夜色中 (In the Night) 光锥技能 - 已重构"""
    def __init__(self, skill_id: str, name: str, desc: str, params: List[List[float]], level: int = 1):
        super().__init__(skill_id, name, desc, params, level)
        self.crit_rate_bonus = self.current_params[0]
        self.spd_threshold = 10.0
        self.dmg_bonus_per_stack = self.current_params[2]
        self.ult_crit_dmg_bonus_per_stack = self.current_params[3]
        self.max_stacks = int(self.current_params[4])
    
    def get_base_stats(self) -> Dict[str, float]:
        return {"CRIT Rate": self.crit_rate_bonus}

    def _get_current_stacks(self, character: 'Character') -> int:
        provisional_stats = character.get_current_stats(recursive_guard=True)
        current_spd = provisional_stats.get("SPD", 0)
        spd_over_100 = max(0, current_spd - 100)
        return min(self.max_stacks, int(spd_over_100 / self.spd_threshold))

    def on_battle_start(self, character: 'Character'):
        from starrail.core.skills.buff import Buff
        def dynamic_damage_func(char: 'Character') -> float:
            skill_type = getattr(char, '_last_skill_type', 'Normal')
            if skill_type not in ["Normal", "BPSkill"]: return 0.0
            stacks = self._get_current_stacks(char)
            bonus = stacks * self.dmg_bonus_per_stack
            if bonus > 0:
                logger.log(f"    [光锥效果] '{self.name}' 生效: 普攻/战技伤害提高 {bonus:.1%} (层数: {stacks})", color="cyan")
            return bonus

        def dynamic_stat_func(char: 'Character') -> Dict[str, float]:
            skill_type = getattr(char, '_last_skill_type', 'Normal')
            if skill_type != "Ultra": return {}
            stacks = self._get_current_stacks(char)
            crit_dmg_bonus = stacks * self.ult_crit_dmg_bonus_per_stack
            if crit_dmg_bonus > 0:
                 return {"CRIT DMG": crit_dmg_bonus}
            return {}
        
        unified_buff = Buff(name="In the Night Unified Bonus", duration=-1, dynamic_damage_bonus_func=dynamic_damage_func, dynamic_stat_bonus_func=dynamic_stat_func)
        character.add_buff(unified_buff)
        logger.log(f"[光锥效果] {character.name} 的 '{self.name}' 光锥效果已装备。", color="magenta")

# --- 新增布洛妮娅光锥 ---
class ButTheBattleIsntOverSkill(LightConeSkill):
    """但战斗还未结束 (But the Battle Isn't Over) 光锥技能"""
    def __init__(self, skill_id: str, name: str, desc: str, params: List[List[float]], level: int = 1):
        super().__init__(skill_id, name, desc, params, level)
        self.energy_regen_bonus = self.current_params[0]
        self.skill_dmg_bonus = self.current_params[1]
        self.skill_dmg_buff_duration = int(self.current_params[2])
        
        # 用于追踪终结技使用次数
        self.ultimate_counter = 0

    def get_base_stats(self) -> Dict[str, float]:
        # 效果1: 提高能量恢复效率
        return {"Energy Regeneration Rate": self.energy_regen_bonus}

    def on_skill_used(self, character: 'Character', skill_type: str):
        from starrail.core.skills.buff import Buff

        # 效果2: 施放终结技时恢复战技点
        if skill_type == "Ultra":
            self.ultimate_counter += 1
            logger.log(f"[光锥追踪] '{self.name}' 终结技使用次数: {self.ultimate_counter}/{2}", color="yellow")
            if self.ultimate_counter >= 2:
                battle_context = getattr(character, '_battle_context', None)
                if battle_context:
                    logger.log(f"[光锥效果] '{self.name}' 效果触发，为 {character.side} 阵营恢复1个战技点！", color="green")
                    battle_context.gain_skill_point(character)
                    self.ultimate_counter = 0 # 重置计数器

        # 效果3: 施放战技后，使下个行动的我方其他目标增伤
        if skill_type == "BPSkill":
            # 通过 character._current_target 获取战技的目标
            target_ally = getattr(character, '_current_target', None)
            if target_ally and target_ally != character:
                logger.log(f"[光锥效果] '{self.name}' 效果触发，使 {target_ally.name} 下一回合伤害提高 {self.skill_dmg_bonus:.0%}", color="green")
                dmg_buff = Buff(
                    name="继承人 (来自光锥)",
                    duration=self.skill_dmg_buff_duration,
                    damage_bonus=self.skill_dmg_bonus
                )
                target_ally.add_buff(dmg_buff)

    def on_battle_start(self, character: 'Character'): 
        logger.log(f"[光锥效果] {character.name} 的 '{self.name}' 光锥激活。", color="magenta")

# --- 重构术后对话光锥 ---
class PostOpConversationSkill(LightConeSkill):
    """术后对话 (Post-Op Conversation) 光锥技能 - 已最终修正"""
    def __init__(self, skill_id: str, name: str, desc: str, params: List[List[float]], level: int = 1):
        super().__init__(skill_id, name, desc, params, level)
        self.energy_regen_bonus = self.current_params[0]
        self.ult_healing_bonus = self.current_params[1]
        
    def get_base_stats(self) -> Dict[str, float]: 
        # 效果1: 能量恢复效率是常驻面板加成
        return {"Energy Regeneration Rate": self.energy_regen_bonus}
        
    # [最终修正] 恢复使用 get_healing_bonus 钩子，避免状态残留和日志污染
    def get_healing_bonus(self, skill_type: str) -> float:
        """当且仅当技能为终结技时，提供治疗加成"""
        # 这个方法只在 skill_manager.calculate_final_heal 中被调用
        # 因此这里的日志只会在终结技治疗时打印一次，非常精确
        if skill_type == "Ultra":
            logger.log(f"    [光锥效果] '{self.name}' 生效: 终结技治疗量提高 {self.ult_healing_bonus:.1%}", color="cyan")
            return self.ult_healing_bonus
        # 明确排除持续治疗和其他非终结技治疗
        elif skill_type in ["HealOverTime", "Normal", "BPSkill"]:
            return 0.0
        return 0.0

    def on_battle_start(self, character: 'Character'):
        # 不再需要通过动态Buff实现，但保留日志以确认光锥已装备
        logger.log(f"[光锥效果] {character.name} 的 '{self.name}' 光锥效果已装备。", color="magenta")


class LightConeSkillFactory:
    _skill_classes = {
        "23001": InTheNightSkill,
        "21000": PostOpConversationSkill,
        # --- 注册布洛妮娅光锥 ---
        "23003": ButTheBattleIsntOverSkill,
    }
    
    @classmethod
    def create_skill(cls, skill_id: str, skill_data: Dict[str, Any], level: int = 1) -> Optional[LightConeSkill]:
        skill_class = cls._skill_classes.get(skill_id)
        if skill_class:
            return skill_class(
                skill_id=skill_id, 
                name=skill_data.get('name', ''), 
                desc=skill_data.get('desc', ''), 
                params=skill_data.get('params', []), 
                level=level
            )
        # logger.log(f"[警告] 找不到ID为 '{skill_id}' 的光锥技能实现。", color="yellow")
        return None
