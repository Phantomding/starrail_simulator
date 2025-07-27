# light_cone_skill.py
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

class LightConeSkill(ABC):
    """光锥技能基类"""
    
    def __init__(self, skill_id: str, name: str, desc: str, params: List[List[float]], level: int = 1):
        self.skill_id = skill_id
        self.name = name
        self.desc = desc
        self.params = params
        self.level = max(1, min(level, len(params)))
        self.current_params = params[self.level - 1]
    
    @abstractmethod
    def get_base_stats(self) -> Dict[str, float]:
        """获取基础属性加成"""
        pass
    
    @abstractmethod
    def get_battle_effects(self, character) -> List[Any]:
        """获取战斗中的效果（如Buff等）"""
        pass
    
    @abstractmethod
    def on_battle_start(self, character):
        """战斗开始时触发"""
        pass
    
    @abstractmethod
    def on_turn_start(self, character):
        """回合开始时触发"""
        pass
    
    @abstractmethod
    def on_skill_used(self, character, skill_type: str):
        """使用技能时触发"""
        pass
    
    @abstractmethod
    def on_damage_dealt(self, character, damage: float, skill_type: str):
        """造成伤害时触发"""
        pass
    
    @abstractmethod
    def on_damage_received(self, character, damage: float):
        """受到伤害时触发"""
        pass
    
    @abstractmethod
    def on_enemy_killed(self, character):
        """击杀敌人时触发"""
        pass

class InTheNightSkill(LightConeSkill):
    """In the Night 光锥技能：Flowers and Butterflies"""
    
    def __init__(self, skill_id: str, name: str, desc: str, params: List[List[float]], level: int = 1):
        super().__init__(skill_id, name, desc, params, level)
        # 解析参数
        self.crit_rate_bonus = self.current_params[0]  # 暴击率加成
        self.spd_threshold = self.current_params[1]    # 速度阈值（每10点速度）
        self.dmg_bonus_per_stack = self.current_params[2]  # 每层伤害加成
        self.ult_crit_dmg_bonus = self.current_params[3]   # 终极技暴击伤害加成
        self.max_stacks = int(self.current_params[4])       # 最大层数
        self.current_stacks = 0  # 当前层数
    
    def get_base_stats(self) -> Dict[str, float]:
        """获取基础属性加成（暴击率）"""
        return {"CRIT Rate": self.crit_rate_bonus}
    
    def get_battle_effects(self, character) -> List[Any]:
        """获取战斗中的效果（基础属性已在equipment_manager中计算，这里不需要Buff）"""
        # 基础属性（如暴击率）已经在equipment_manager.py中计算并加到角色属性中
        # 这里不需要创建Buff，只返回空列表
        return []
    
    def _get_current_stacks(self, character) -> int:
        """获取当前层数"""
        current_spd = character.spd
        spd_over_100 = max(0, current_spd - 100)
        return min(self.max_stacks, int(spd_over_100 / self.spd_threshold))
    
    def _create_skill_dmg_buff(self, character) -> Any:
        """创建普攻和战技伤害加成Buff"""
        from starrail.core.skills.buff import Buff
        
        stacks = self._get_current_stacks(character)
        if stacks > 0:
            return Buff.create_skill_buff(
                name="In the Night Skill DMG Boost",
                duration=1,  # 只持续1回合
                stat_bonus={},
                damage_bonus=stacks * self.dmg_bonus_per_stack,
                source="light_cone",
                level=self.level
            )
        return None
    
    def _create_ult_crit_dmg_buff(self, character) -> Any:
        """创建终极技暴击伤害加成Buff"""
        from starrail.core.skills.buff import Buff
        
        stacks = self._get_current_stacks(character)
        if stacks > 0:
            return Buff.create_skill_buff(
                name="In the Night Ultimate CRIT DMG",
                duration=1,  # 只持续1回合
                stat_bonus={"CRIT DMG": stacks * self.ult_crit_dmg_bonus},
                source="light_cone",
                level=self.level
            )
        return None
    
    def on_battle_start(self, character):
        """战斗开始时应用效果"""
        # 基础属性（如暴击率）已经在equipment_manager.py中计算
        # 这里不需要创建Buff，只显示层数信息
        stacks = self._get_current_stacks(character)
        if stacks > 0:
            print(f"[光锥效果] {character.name} 的 In the Night 光锥激活 (层数: {stacks})")
    
    def on_turn_start(self, character):
        """回合开始时更新效果"""
        # 移除临时的技能效果Buff
        if hasattr(character, 'buffs'):
            character.buffs = [b for b in character.buffs 
                             if not b.name.startswith("In the Night Skill") and 
                                not b.name.startswith("In the Night Ultimate")]
    
    def on_skill_used(self, character, skill_type: str):
        """使用技能时触发"""
        if skill_type in ["Normal", "BPSkill"]:
            # 普攻和战技：应用伤害加成
            dmg_buff = self._create_skill_dmg_buff(character)
            if dmg_buff and hasattr(character, 'add_buff'):
                character.add_buff(dmg_buff)
                stacks = self._get_current_stacks(character)
                print(f"[光锥效果] {character.name} 使用{skill_type}，获得伤害加成 (层数: {stacks})")
        
        elif skill_type == "Ultra":
            # 终极技：应用暴击伤害加成
            crit_buff = self._create_ult_crit_dmg_buff(character)
            if crit_buff and hasattr(character, 'add_buff'):
                character.add_buff(crit_buff)
                stacks = self._get_current_stacks(character)
                print(f"[光锥效果] {character.name} 使用终极技，获得暴击伤害加成 (层数: {stacks})")
    
    def on_damage_dealt(self, character, damage: float, skill_type: str):
        """造成伤害时触发（这里不需要特殊处理）"""
        pass
    
    def on_damage_received(self, character, damage: float):
        """受到伤害时触发（这里不需要特殊处理）"""
        pass
    
    def on_enemy_killed(self, character):
        """击杀敌人时触发（这里不需要特殊处理）"""
        pass

class LightConeSkillFactory:
    """光锥技能工厂类"""
    
    _skill_classes = {
        "23001": InTheNightSkill,  # In the Night
        # 可以继续添加其他光锥技能
    }
    
    @classmethod
    def create_skill(cls, skill_id: str, skill_data: Dict[str, Any], level: int = 1) -> Optional[LightConeSkill]:
        """创建光锥技能实例"""
        if skill_id in cls._skill_classes:
            skill_class = cls._skill_classes[skill_id]
            return skill_class(
                skill_id=skill_id,
                name=skill_data.get('name', ''),
                desc=skill_data.get('desc', ''),
                params=skill_data.get('params', []),
                level=level
            )
        return None 