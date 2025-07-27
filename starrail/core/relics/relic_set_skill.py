# relic_set_skill.py
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
import re

class RelicSetSkill(ABC):
    """遗器套装技能基类"""
    
    def __init__(self, set_name: str, description: str, level: int = 1):
        self.set_name = set_name
        self.description = description
        self.level = level
    
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

class SpaceSealingStationSkill(RelicSetSkill):
    """Space Sealing Station 套装技能"""
    
    def __init__(self, set_name: str, description: str, level: int = 1):
        super().__init__(set_name, description, level)
        # 解析描述中的参数
        self._parse_description()
    
    def _parse_description(self):
        """解析套装描述，提取参数"""
        # 基础ATK加成
        atk_match = re.search(r'ATK by <b>(\d+)%</b>', self.description)
        self.base_atk_bonus = float(atk_match.group(1)) / 100 if atk_match else 0.12
        
        # 速度阈值和额外ATK加成
        spd_match = re.search(r'SPD reaches <b>(\d+)</b>', self.description)
        self.spd_threshold = int(spd_match.group(1)) if spd_match else 120
        
        extra_atk_match = re.search(r'ATK increases by an extra <b>(\d+)%</b>', self.description)
        self.extra_atk_bonus = float(extra_atk_match.group(1)) / 100 if extra_atk_match else 0.12
    
    def get_base_stats(self) -> Dict[str, float]:
        """获取基础属性加成（ATK）"""
        return {"ATK%": self.base_atk_bonus}
    
    def get_battle_effects(self, character) -> List[Any]:
        """获取战斗中的效果"""
        effects = []
        current_spd = character.spd
        
        # 检查是否达到速度阈值
        if current_spd >= self.spd_threshold:
            from starrail.core.skills.buff import Buff
            extra_atk_buff = Buff.create_skill_buff(
                name="Space Sealing Station Extra ATK",
                duration=-1,  # 永久效果
                stat_bonus={"ATK%": self.extra_atk_bonus},
                source="relic_set",
                level=self.level
            )
            effects.append(extra_atk_buff)
        
        return effects
    
    def on_battle_start(self, character):
        """战斗开始时应用效果"""
        current_spd = character.spd
        if current_spd >= self.spd_threshold:
            print(f"[遗器套装] {character.name} 的 {self.set_name} 套装激活 (速度: {current_spd})")
    
    def on_turn_start(self, character):
        """回合开始时更新效果"""
        pass
    
    def on_skill_used(self, character, skill_type: str):
        """使用技能时触发"""
        pass
    
    def on_damage_dealt(self, character, damage: float, skill_type: str):
        """造成伤害时触发"""
        pass
    
    def on_damage_received(self, character, damage: float):
        """受到伤害时触发"""
        pass
    
    def on_enemy_killed(self, character):
        """击杀敌人时触发"""
        pass

class FleetOfTheAgelessSkill(RelicSetSkill):
    """Fleet of the Ageless 套装技能"""
    
    def __init__(self, set_name: str, description: str, level: int = 1):
        super().__init__(set_name, description, level)
        self._parse_description()
    
    def _parse_description(self):
        """解析套装描述，提取参数"""
        # 基础HP加成
        hp_match = re.search(r'Max HP by <b>(\d+)%</b>', self.description)
        self.base_hp_bonus = float(hp_match.group(1)) / 100 if hp_match else 0.12
        
        # 速度阈值和团队ATK加成
        spd_match = re.search(r'SPD reaches <b>(\d+)</b>', self.description)
        self.spd_threshold = int(spd_match.group(1)) if spd_match else 120
        
        team_atk_match = re.search(r'all allies\' ATK increases by <b>(\d+)%</b>', self.description)
        self.team_atk_bonus = float(team_atk_match.group(1)) / 100 if team_atk_match else 0.08
    
    def get_base_stats(self) -> Dict[str, float]:
        """获取基础属性加成（HP）"""
        return {"HP%": self.base_hp_bonus}
    
    def get_battle_effects(self, character) -> List[Any]:
        """获取战斗中的效果"""
        effects = []
        current_spd = character.spd
        
        # 检查是否达到速度阈值
        if current_spd >= self.spd_threshold:
            from starrail.core.skills.buff import Buff
            team_atk_buff = Buff.create_skill_buff(
                name="Fleet of the Ageless Team ATK",
                duration=-1,  # 永久效果
                stat_bonus={"ATK%": self.team_atk_bonus},
                source="relic_set",
                level=self.level
            )
            effects.append(team_atk_buff)
        
        return effects
    
    def on_battle_start(self, character):
        """战斗开始时应用效果"""
        current_spd = character.spd
        if current_spd >= self.spd_threshold:
            print(f"[遗器套装] {character.name} 的 {self.set_name} 套装激活 (速度: {current_spd})")
    
    def on_turn_start(self, character):
        """回合开始时更新效果"""
        pass
    
    def on_skill_used(self, character, skill_type: str):
        """使用技能时触发"""
        pass
    
    def on_damage_dealt(self, character, damage: float, skill_type: str):
        """造成伤害时触发"""
        pass
    
    def on_damage_received(self, character, damage: float):
        """受到伤害时触发"""
        pass
    
    def on_enemy_killed(self, character):
        """击杀敌人时触发"""
        pass

class EagleOfTwilightLineSkill(RelicSetSkill):
    """Eagle of Twilight Line 套装技能"""
    
    def __init__(self, set_name: str, description: str, level: int = 1):
        super().__init__(set_name, description, level)
        self._parse_description()
    
    def _parse_description(self):
        """解析套装描述，提取参数"""
        # 风属性伤害加成
        wind_dmg_match = re.search(r'Wind DMG by <b>(\d+)%</b>', self.description)
        self.wind_dmg_bonus = float(wind_dmg_match.group(1)) / 100 if wind_dmg_match else 0.10
        
        # 终极技后行动提前
        advance_match = re.search(r'Advanced Forward by <b>(\d+)%</b>', self.description)
        self.advance_forward = float(advance_match.group(1)) / 100 if advance_match else 0.25
    
    def get_base_stats(self) -> Dict[str, float]:
        """获取基础属性加成（风属性伤害）"""
        return {"Wind DMG": self.wind_dmg_bonus}
    
    def get_battle_effects(self, character) -> List[Any]:
        """获取战斗中的效果"""
        return []
    
    def on_battle_start(self, character):
        """战斗开始时应用效果"""
        pass
    
    def on_turn_start(self, character):
        """回合开始时更新效果"""
        pass
    
    def on_skill_used(self, character, skill_type: str):
        """使用技能时触发"""
        if skill_type == "Ultra":
            # 终极技后行动提前
            print(f"[遗器套装] {character.name} 使用终极技，{self.set_name} 套装效果触发，立即推进 {self.advance_forward*100:.0f}% 行动条")
            # 立即推进行动条
            battle_context = getattr(character, '_battle_context', None)
            if battle_context and hasattr(battle_context, 'boost_action_progress'):
                before = battle_context.action_progress.get(character, 0)
                battle_context.boost_action_progress(character, self.advance_forward)
                after = battle_context.action_progress.get(character, 0)
                print(f"[行动进度提升] {character.name}: {before:.4f} -> {after:.4f} (+{self.advance_forward:.4f})")
    
    def on_damage_dealt(self, character, damage: float, skill_type: str):
        """造成伤害时触发"""
        pass
    
    def on_damage_received(self, character, damage: float):
        """受到伤害时触发"""
        pass
    
    def on_enemy_killed(self, character):
        """击杀敌人时触发"""
        pass

class RelicSetSkillFactory:
    """遗器套装技能工厂类"""
    
    _skill_classes = {
        "Space Sealing Station": SpaceSealingStationSkill,
        "Fleet of the Ageless": FleetOfTheAgelessSkill,
        "Eagle of Twilight Line": EagleOfTwilightLineSkill,
        # 可以继续添加其他遗器套装技能
    }
    
    @classmethod
    def create_skill(cls, set_name: str, description: str, level: int = 1) -> Optional[RelicSetSkill]:
        """创建遗器套装技能实例"""
        if set_name in cls._skill_classes:
            skill_class = cls._skill_classes[set_name]
            return skill_class(
                set_name=set_name,
                description=description,
                level=level
            )
        return None 