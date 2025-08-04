# natasha_skills.py
from .base_skill import BaseSkill
from .buff import Buff
from .effects import HealEffect, BuffEffect, DamageEffect

class NatashaBasicSkill(BaseSkill):
    """娜塔莎普攻 (110501)"""
    def use(self, user, targets, context, level=1):
        multiplier = self.skill_data["params"][level-1][0]
        return [
            DamageEffect(user, targets, context, "Physical", multiplier, self.type)
        ]

class NatashaSkill(BaseSkill):
    """娜塔莎战技 (110502)"""
    def use(self, user, targets, context, level=1):
        params = self.skill_data["params"][level-1]
        immediate_heal_ratio, dot_heal_ratio, buff_duration, immediate_heal_base, dot_heal_base = params
        
        natasha_max_hp = user.get_max_hp()
        base_immediate_heal = immediate_heal_ratio * natasha_max_hp + immediate_heal_base
        
        # 持续治疗Buff
        dot_buff = Buff(name="Natasha's Healing Over Time", duration=buff_duration)
        dot_buff.on_turn_start_data = {
            "type": "heal_from_caster",
            "caster_id": user.id, # 存储施法者ID
            "heal_ratio": dot_heal_ratio,
            "heal_base": dot_heal_base,
            "source_stat": "max_hp"
        }
        
        return [
            HealEffect(user, targets, context, base_immediate_heal),
            BuffEffect(user, targets, context, dot_buff)
        ]

class NatashaUltimateSkill(BaseSkill):
    """娜塔莎终结技 (110503)"""
    def use(self, user, targets, context, level=1):
        params = self.skill_data["params"][level-1]
        heal_ratio, heal_base = params
        
        natasha_max_hp = user.get_max_hp()
        base_heal_amount = heal_ratio * natasha_max_hp + heal_base
        
        allies = [char for char in context.characters if char.side == user.side and char.is_alive()]
        
        return [
            HealEffect(user, allies, context, base_heal_amount)
        ]

class NatashaTalent(BaseSkill):
    """娜塔莎天赋 (110504)"""
    # 天赋通常是被动触发，由其他系统（如治疗效果）查询。
    # use方法可以为空，或者在特定时机被调用。目前保持为空。
    pass