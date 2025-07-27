# damage_system.py - 重构的伤害系统
from dataclasses import dataclass
from typing import Optional, Dict, List
from enum import Enum
import random

class DamageType(Enum):
    """伤害类型"""
    NORMAL = "normal"           # 普通伤害
    CRITICAL = "critical"       # 暴击伤害
    FOLLOW_UP = "follow_up"     # 追击伤害
    COUNTER = "counter"         # 反击伤害
    DOT = "dot"                 # 持续伤害
    BREAK = "break"             # 击破伤害
    ULTIMATE = "ultimate"       # 终极技伤害

@dataclass
class DamageInstance:
    """伤害实例数据类"""
    base_damage: float
    final_damage: float
    element: Optional[str]
    damage_type: DamageType
    is_critical: bool
    attacker_name: str
    target_name: str
    modifiers: Dict[str, float]  # 各种修正系数
    
    def __post_init__(self):
        self.damage_breakdown = self._calculate_breakdown()
    
    def _calculate_breakdown(self) -> Dict[str, float]:
        """计算伤害构成"""
        return {
            "base": self.base_damage,
            "element_bonus": self.modifiers.get("element_bonus", 0),
            "damage_bonus": self.modifiers.get("damage_bonus", 0),
            "critical_bonus": self.modifiers.get("critical_bonus", 0) if self.is_critical else 0,
            "defense_reduction": self.modifiers.get("defense_reduction", 0),
            "resistance_reduction": self.modifiers.get("resistance_reduction", 0),
            "final": self.final_damage
        }

class DamageCalculator:
    """伤害计算器"""
    
    def __init__(self):
        self.damage_history: List[DamageInstance] = []
    
    def calculate_damage(self, attacker, target, multiplier: float, element: Optional[str] = None, 
                        damage_type: DamageType = DamageType.NORMAL, 
                        force_crit: bool = False, crit_immunity: bool = False) -> DamageInstance:
        """
        计算伤害的主函数
        """
        # 1. 基础伤害计算
        base_damage = self._calculate_base_damage(attacker, multiplier)
        
        # 2. 元素伤害加成
        element_bonus = self._calculate_element_bonus(attacker, element)
        
        # 3. 独立增伤区
        damage_bonus = self._calculate_damage_bonus(attacker, damage_type)
        
        # 4. 暴击计算
        crit_info = self._calculate_critical(attacker, force_crit, crit_immunity)
        
        # 5. 理论伤害
        theory_damage = base_damage * (1 + element_bonus + damage_bonus) * crit_info["multiplier"]
        
        # 6. 防御修正
        defense_reduction = self._calculate_defense_reduction(attacker, target, theory_damage)
        
        # 7. 抗性修正
        resistance_reduction = self._calculate_resistance_reduction(target, element, attacker)
        
        # 8. 独立减伤/增伤
        damage_modifier = self._calculate_damage_modifiers(target, attacker, damage_type)
        
        # 9. 最终伤害
        final_damage = defense_reduction * resistance_reduction * damage_modifier
        final_damage = max(final_damage, 1)  # 最低1点伤害
        
        # 创建伤害实例
        damage_instance = DamageInstance(
            base_damage=base_damage,
            final_damage=final_damage,
            element=element,
            damage_type=damage_type,
            is_critical=crit_info["is_crit"],
            attacker_name=attacker.name,
            target_name=target.name,
            modifiers={
                "element_bonus": element_bonus,
                "damage_bonus": damage_bonus,
                "critical_bonus": crit_info["bonus"] if crit_info["is_crit"] else 0,
                "defense_reduction": defense_reduction / theory_damage if theory_damage > 0 else 1,
                "resistance_reduction": resistance_reduction,
                "damage_modifier": damage_modifier
            }
        )
        
        # 记录到历史
        self.damage_history.append(damage_instance)
        
        # 输出详细日志
        self._log_damage_calculation(damage_instance, theory_damage)
        
        return damage_instance
    
    def _calculate_base_damage(self, attacker, multiplier: float) -> float:
        """计算基础伤害"""
        atk = getattr(attacker, "atk", 0)
        return atk * multiplier
    
    def _calculate_element_bonus(self, attacker, element: Optional[str]) -> float:
        """计算元素伤害加成"""
        if not element:
            return 0
        return attacker.get_current_stats().get(f"{element} DMG", 0)
    
    def _calculate_damage_bonus(self, attacker, damage_type: DamageType) -> float:
        """计算独立增伤区"""
        damage_bonus = 0
        
        # 来自Buff的增伤
        for buff in getattr(attacker, 'buffs', []):
            damage_bonus += getattr(buff, 'damage_bonus', 0)
        
        # 来自特定伤害类型的加成
        if damage_type == DamageType.ULTIMATE:
            damage_bonus += attacker.get_current_stats().get("Ultimate DMG", 0)
        elif damage_type == DamageType.FOLLOW_UP:
            damage_bonus += attacker.get_current_stats().get("Follow-up Attack DMG", 0)
        
        return damage_bonus
    
    def _calculate_critical(self, attacker, force_crit: bool, crit_immunity: bool) -> Dict:
        """计算暴击"""
        if crit_immunity:
            return {"is_crit": False, "multiplier": 1.0, "bonus": 0}
        
        crit_rate = attacker.get_current_stats().get("CRIT Rate", 0.05)
        crit_dmg = attacker.get_current_stats().get("CRIT DMG", 0.5)
        
        is_crit = force_crit or random.random() < crit_rate
        multiplier = 1 + crit_dmg if is_crit else 1.0
        
        return {
            "is_crit": is_crit,
            "multiplier": multiplier,
            "bonus": crit_dmg if is_crit else 0
        }
    
    def _calculate_defense_reduction(self, attacker, target, theory_damage: float) -> float:
        """计算防御修正后的伤害"""
        if hasattr(target, 'defense_reduction'):
            return target.defense_reduction(theory_damage, attacker, target)
        
        # 默认防御计算
        def_val = target.get_current_stats().get("DEF", 0)
        level = getattr(attacker, 'level', 80)
        reduction = def_val / (def_val + level * 10 + 200)
        return theory_damage * (1 - reduction)
    
    def _calculate_resistance_reduction(self, target, element: Optional[str], attacker) -> float:
        """计算抗性修正"""
        if not element:
            return 1.0
        
        # 目标抗性
        element_resistance = 0
        if hasattr(target, 'resistances') and target.resistances:
            element_resistance = target.resistances.get(element, 0)
        
        # 攻击者的穿透
        element_penetration = 0
        for buff in getattr(attacker, 'buffs', []):
            element_penetration += getattr(buff, 'element_penetration', 0)
        
        return max(1 - (element_resistance - element_penetration), 0.1)  # 最低10%伤害
    
    def _calculate_damage_modifiers(self, target, attacker, damage_type: DamageType) -> float:
        """计算独立减伤/增伤区间"""
        modifier = 1.0
        
        # 目标的独立减伤
        for buff in getattr(target, 'buffs', []):
            modifier *= (1 - getattr(buff, 'independent_damage_reduction', 0))
        
        # 韧性减伤
        if (hasattr(target, 'toughness') and target.toughness is not None and 
            target.toughness > 0 and damage_type != DamageType.BREAK):
            modifier *= 0.9  # 10%韧性减伤
        
        # 目标受到伤害增加
        for buff in getattr(target, 'buffs', []):
            modifier *= (1 + getattr(buff, 'damage_taken_increase', 0))
        
        return modifier
    
    def _log_damage_calculation(self, damage_instance: DamageInstance, theory_damage: float):
        """输出伤害计算日志"""
        print(f"[伤害计算] {damage_instance.attacker_name} -> {damage_instance.target_name}")
        print(f"  基础伤害: {damage_instance.base_damage:.1f}")
        print(f"  元素加成: +{damage_instance.modifiers['element_bonus']*100:.1f}%")
        print(f"  独立增伤: +{damage_instance.modifiers['damage_bonus']*100:.1f}%")
        if damage_instance.is_critical:
            print(f"  暴击加成: +{damage_instance.modifiers['critical_bonus']*100:.1f}%")
        print(f"  理论伤害: {theory_damage:.1f}")
        print(f"  防御修正: {damage_instance.modifiers['defense_reduction']:.3f}")
        print(f"  抗性修正: {damage_instance.modifiers['resistance_reduction']:.3f}")
        print(f"  其他修正: {damage_instance.modifiers['damage_modifier']:.3f}")
        print(f"  最终伤害: {damage_instance.final_damage:.1f}")
    
    def preview_damage(self, attacker, target, multiplier: float, element: Optional[str] = None) -> Dict:
        """预览伤害（不实际造成伤害）"""
        # 计算期望伤害
        crit_rate = attacker.get_current_stats().get("CRIT Rate", 0.05)
        
        # 非暴击伤害
        non_crit = self.calculate_damage(attacker, target, multiplier, element, 
                                       crit_immunity=True)
        # 暴击伤害
        crit = self.calculate_damage(attacker, target, multiplier, element, 
                                   force_crit=True)
        
        # 期望伤害
        expected = non_crit.final_damage * (1 - crit_rate) + crit.final_damage * crit_rate
        
        return {
            "non_critical": non_crit.final_damage,
            "critical": crit.final_damage,
            "expected": expected,
            "crit_rate": crit_rate
        }
    
    def get_damage_statistics(self, attacker_name: Optional[str] = None) -> Dict:
        """获取伤害统计"""
        filtered_history = self.damage_history
        if attacker_name:
            filtered_history = [d for d in self.damage_history if d.attacker_name == attacker_name]
        
        if not filtered_history:
            return {}
        
        total_damage = sum(d.final_damage for d in filtered_history)
        crit_count = sum(1 for d in filtered_history if d.is_critical)
        
        return {
            "total_damage": total_damage,
            "average_damage": total_damage / len(filtered_history),
            "max_damage": max(d.final_damage for d in filtered_history),
            "min_damage": min(d.final_damage for d in filtered_history),
            "critical_hits": crit_count,
            "critical_rate": crit_count / len(filtered_history),
            "damage_instances": len(filtered_history)
        }

# 在SkillManager中集成新的伤害系统
class SkillManagerWithNewDamage(SkillManager):
    """集成新伤害系统的SkillManager"""
    
    def __init__(self, skill_data_dict):
        super().__init__(skill_data_dict)
        self.damage_calculator = DamageCalculator()
    
    def _apply_damage_to_target(self, user, target, intent, skill_type):
        """使用新伤害系统的伤害处理"""
        # 确定伤害类型
        damage_type_map = {
            "Normal": DamageType.NORMAL,
            "BPSkill": DamageType.NORMAL,
            "Ultra": DamageType.ULTIMATE,
            "Talent": DamageType.FOLLOW_UP,
            "Break": DamageType.BREAK
        }
        damage_type = damage_type_map.get(skill_type, DamageType.NORMAL)
        
        # 计算伤害
        damage_instance = self.damage_calculator.calculate_damage(
            user, target, intent["multiplier"], intent["element"], damage_type
        )
        
        target_was_alive = target.is_alive()
        
        # 造成伤害
        if hasattr(target, "receive_damage"):
            target.receive_damage(
                damage_instance.final_damage, 
                attacker=user, 
                skill_type=skill_type,
                damage_instance=damage_instance
            )
        
        # 削韧（仅对Enemy）
        if isinstance(target, Enemy):
            toughness_amount = self.toughness_map.get(skill_type, 0)
            target.reduce_toughness(toughness_amount, element=intent.get("element"), attacker=user)
        
        # 击杀检查
        if target_was_alive and not target.is_alive():
            user.on_enemy_killed()
        
        return {
            "target": target,
            "damage": damage_instance.final_damage,
            "damage_instance": damage_instance,
            "element": intent["element"],
            "skill_name": intent["skill_name"],
            "desc": intent.get("desc", "")
        }
    
    def get_battle_damage_report(self) -> Dict:
        """获取战斗伤害报告"""
        return self.damage_calculator.get_damage_statistics()