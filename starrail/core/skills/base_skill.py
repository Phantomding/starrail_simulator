# base_skill.py
from typing import List
from .effects import BaseEffect, DamageEffect

class BaseSkill:
    def __init__(self, skill_data):
        self.skill_id = skill_data.get("id")
        self.name = skill_data.get("name")
        self.type = skill_data.get("type") # e.g., "Normal", "BPSkill", "Ultra"
        self.description = skill_data.get("description")
        self.skill_data = skill_data # 确保子类可以访问

    def use(self, user, targets, context, level=1) -> List[BaseEffect]:
        """
        技能释放的主入口，返回一个效果列表。
        默认实现为空，表示该技能未实装或无效果。
        """
        print(f"[技能跳过] {user.name} 使用了未实装的技能 [{self.name}]")
        return []
    
    @classmethod
    def create_default_attack(cls, user):
        """创建一个默认攻击技能，造成攻击力100%的伤害"""
        skill_data = {
            "id": "default_attack",
            "name": "默认攻击",
            "type": "Normal",
            "description": "造成攻击力100%的伤害"
        }
        
        class DefaultAttack(cls):
            def use(self, user, targets, context, level=1) -> List[BaseEffect]:
                """默认攻击：造成攻击力100%的伤害"""
                effects = []
                for target in targets:
                    # 创建伤害效果，倍率为1.0（100%攻击力）
                    damage_effect = DamageEffect(
                        caster=user,
                        targets=[target],
                        context=context,
                        multiplier=1.0,
                        element="Physical",  # 默认物理属性
                        skill_type="Normal"
                    )
                    effects.append(damage_effect)
                return effects
        
        return DefaultAttack(skill_data)