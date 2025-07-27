from .base_skill import BaseSkill
from .buff import Buff
from .heal_system import HealSkillIntent, HealTargetStrategy

class NatashaBasicSkill(BaseSkill):
    """娜塔莎普攻：单体物理伤害 (110501)"""
    def __init__(self, skill_data):
        super().__init__(skill_data)
        self.skill_data = skill_data

    def use(self, user, targets, context, level=1):
        multiplier = self.skill_data["params"][level-1][0]
        return {
            "type": "damage_only",
            "element": "Physical",
            "multiplier": multiplier,
            "targets": targets,
            "skill_name": self.name,
            "desc": self.description
        }

# 使用示例：改进娜塔莎的治疗技能
class NatashaSkillImproved(BaseSkill):
    """娜塔莎改进版战技"""
    
    def use(self, user, targets, context, level=1):
        params = self.skill_data["params"][level-1]
        heal_ratio = params[0]  # 基于最大生命值的治疗比例
        heal_base = params[3]   # 固定治疗量
        
        heal_intent = HealSkillIntent(
            skill_name=self.name,
            base_heal=heal_base,
            heal_ratio=heal_ratio,
            target_strategy=HealTargetStrategy.LOWEST_HP_RATIO,
            max_targets=1
        )
        
        return heal_intent.to_dict()