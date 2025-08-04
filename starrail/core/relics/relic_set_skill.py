# starrail/core/skills/relic_set_skill.py (最终版)
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from starrail.utils.logger import logger

# 前向声明以支持类型提示
if False:
    from starrail.core.character import Character
    from starrail.core.skills.buff import Buff

class RelicSetSkill(ABC):
    """遗器套装技能基类"""
    
    def __init__(self, set_name: str, description: str, level: int = 1):
        self.set_name = set_name
        self.description = description
        self.level = level
    
    @abstractmethod
    def get_base_stats(self) -> Dict[str, float]:
        """获取静态的基础属性加成 (通常用于2件套效果)"""
        pass
    
    # --- 事件钩子 (通常用于4件套或更复杂的效果) ---
    def on_battle_start(self, character: 'Character'):
        """战斗开始时触发"""
        logger.log(f"[遗器] {character.name} 装备了 '{self.set_name}'", color="cyan")

    def on_turn_start(self, character: 'Character'): pass
    def on_skill_used(self, character: 'Character', skill_type: str): pass
    def on_damage_dealt(self, character: 'Character', damage: float, skill_type: str): pass
    def on_damage_received(self, character: 'Character', damage: float): pass
    def on_enemy_killed(self, character: 'Character'): pass

class GeniusOfBrilliantStarsSkill(RelicSetSkill):
    """繁星璀璨的天才 (Genius of Brilliant Stars)"""

    def __init__(self, set_name: str, description: str, level: int = 1):
        super().__init__(set_name, description, level)
        self.quantum_dmg_bonus = 0.10
        self.base_def_ignore = 0.10
        self.extra_def_ignore = 0.10

    def get_base_stats(self) -> Dict[str, float]:
        # 2-piece effect
        return {"Quantum DMG": self.quantum_dmg_bonus}

    def on_battle_start(self, character: 'Character'):
        # 4-piece effect
        super().on_battle_start(character)
        from starrail.core.skills.buff import Buff

        def dynamic_genius_bonus(char: 'Character') -> Dict[str, float]:
            total_ignore = self.base_def_ignore
            target = getattr(char, '_current_target', None)
            if target and 'Quantum' in getattr(target, 'weaknesses', []):
                total_ignore += self.extra_def_ignore
            
            if total_ignore > 0:
                logger.log_verbose(f"-> [遗器效果] '{self.set_name}' 提供 {total_ignore:.0%} 防御穿透")
                return {"DEF Ignore %": total_ignore}
            return {}

        genius_buff = Buff(name="Genius DEF Ignore", duration=-1, dynamic_stat_bonus_func=dynamic_genius_bonus)
        character.add_buff(genius_buff)

class SpaceSealingStationSkill(RelicSetSkill):
    """太空封印站 (Space Sealing Station)"""
    
    def __init__(self, set_name: str, description: str, level: int = 1):
        super().__init__(set_name, description, level)
        self.base_atk_bonus = 0.12
        self.extra_atk_bonus = 0.12
        self.spd_threshold = 120

    def get_base_stats(self) -> Dict[str, float]:
        return {"ATK%": self.base_atk_bonus}
    
    def on_battle_start(self, character: 'Character'):
        super().on_battle_start(character)
        from starrail.core.skills.buff import Buff

        def dynamic_station_bonus(char: 'Character') -> Dict[str, float]:
            current_spd = char.get_current_stats().get("SPD", 0)
            if current_spd >= self.spd_threshold:
                logger.log_verbose(f"-> [遗器效果] '{self.set_name}' 速度达标({current_spd:.0f})，提供额外ATK")
                return {"ATK%": self.extra_atk_bonus}
            return {}

        station_buff = Buff(name="Space Sealing Station Bonus", duration=-1, dynamic_stat_bonus_func=dynamic_station_bonus)
        character.add_buff(station_buff)

class FleetOfTheAgelessSkill(RelicSetSkill):
    """不老者的仙舟 (Fleet of the Ageless)"""
    
    def __init__(self, set_name: str, description: str, level: int = 1):
        super().__init__(set_name, description, level)
        self.base_hp_bonus = 0.12
        self.team_atk_bonus = 0.08
        self.spd_threshold = 120

    def get_base_stats(self) -> Dict[str, float]:
        return {"HP%": self.base_hp_bonus}
    
    def on_battle_start(self, character: 'Character'):
        super().on_battle_start(character)
        current_spd = character.get_current_stats().get("SPD", 0)
        
        if current_spd >= self.spd_threshold:
            logger.log(f"[遗器光环] '{self.set_name}' 速度达标({current_spd:.0f})，为全队提供ATK光环！", color="green")
            from starrail.core.skills.buff import Buff
            
            battle_context = getattr(character, '_battle_context', None)
            if not battle_context: return

            allies = [c for c in battle_context.characters if c.side == character.side and c.is_alive()]
            for ally in allies:
                team_buff = Buff(name=f"Fleet Aura (from {character.name})", duration=-1, stat_bonus={"ATK%": self.team_atk_bonus})
                ally.add_buff(team_buff)

class EagleOfTwilightLineSkill(RelicSetSkill):
    """晨昏交界的翔鹰 (Eagle of Twilight Line)"""
    
    def __init__(self, set_name: str, description: str, level: int = 1):
        super().__init__(set_name, description, level)
        self.wind_dmg_bonus = 0.10
        self.advance_forward = 0.25
    
    def get_base_stats(self) -> Dict[str, float]:
        # 2-piece effect
        return {"Wind DMG": self.wind_dmg_bonus}
    
    def on_skill_used(self, character: 'Character', skill_type: str):
        # 4-piece effect
        if skill_type == "Ultra":
            logger.log(f"[遗器事件] '{self.set_name}' 效果触发，行动提前 {self.advance_forward:.0%}", color="blue")
            battle_context = getattr(character, '_battle_context', None)
            if battle_context:
                battle_context.boost_action_progress(character, self.advance_forward)

class InertSalsottoSkill(RelicSetSkill):
    """停转的萨尔索图 (Inert Salsotto)"""
    
    def __init__(self, set_name: str, description: str, level: int = 1):
        super().__init__(set_name, description, level)
        self.base_crit_rate_bonus = 0.08
        self.crit_rate_threshold = 0.50
        self.dmg_bonus = 0.15

    def get_base_stats(self) -> Dict[str, float]:
        return {"CRIT Rate": self.base_crit_rate_bonus}
    
    def on_battle_start(self, character: 'Character'):
        super().on_battle_start(character)
        from starrail.core.skills.buff import Buff

        def dynamic_salsotto_bonus(char: 'Character') -> float:
            current_stats = char.get_current_stats()
            current_crit_rate = current_stats.get("CRIT Rate", 0)
            last_skill_type = getattr(char, '_last_skill_type', 'Normal')

            if current_crit_rate >= self.crit_rate_threshold and last_skill_type in ["Ultra", "Follow-up"]:
                logger.log_verbose(f"-> [遗器效果] '{self.set_name}' 生效，提供 {self.dmg_bonus:.0%} 增伤")
                return self.dmg_bonus
            return 0.0

        salsotto_buff = Buff(name="Salsotto DMG Bonus", duration=-1, dynamic_damage_bonus_func=dynamic_salsotto_bonus)
        character.add_buff(salsotto_buff)

# --- 新增套装: 云无留迹的过客 ---
class PasserbyOfWanderingCloudSkill(RelicSetSkill):
    """云无留迹的过客 (Passerby of Wandering Cloud)"""

    def __init__(self, set_name: str, description: str, level: int = 1):
        super().__init__(set_name, description, level)
        self.healing_bonus = 0.10

    def get_base_stats(self) -> Dict[str, float]:
        """2件套效果: 治疗量提高10%"""
        return {"Outgoing Healing Boost": self.healing_bonus}

    def on_battle_start(self, character: 'Character'):
        """4件套效果: 在战斗开始时，立即为我方恢复1个战技点"""
        super().on_battle_start(character)
        battle_context = getattr(character, '_battle_context', None)
        if battle_context:
            logger.log(f"[遗器效果] '{self.set_name}' 4件套效果触发，为 {character.side} 阵营恢复1个战技点。", color="green")
            battle_context.gain_skill_point(character)
# --- 新增结束 ---


class RelicSetSkillFactory:
    """遗器套装技能工厂类"""
    
    _skill_classes = {
        "Genius of Brilliant Stars": GeniusOfBrilliantStarsSkill,
        "Space Sealing Station": SpaceSealingStationSkill,
        "Fleet of the Ageless": FleetOfTheAgelessSkill,
        "Eagle of Twilight Line": EagleOfTwilightLineSkill,
        "Inert Salsotto": InertSalsottoSkill,
        # --- 注册新套装 ---
        "Passerby of Wandering Cloud": PasserbyOfWanderingCloudSkill,
    }
    
    @classmethod
    def create_skill(cls, set_name: str, description: str, level: int = 1) -> Optional[RelicSetSkill]:
        skill_class = cls._skill_classes.get(set_name)
        if skill_class:
            return skill_class(set_name=set_name, description=description, level=level)
        logger.log(f"[警告] 找不到名为 '{set_name}' 的遗器套装技能实现。", color="yellow")
        return None
