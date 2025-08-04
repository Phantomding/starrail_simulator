# seele_skills.py
from .base_skill import BaseSkill
from .buff import Buff
from .effects import DamageEffect, BuffEffect, ExtraTurnEffect, ProgressBoostEffect

class SeeleBasicSkill(BaseSkill):
    """希儿普攻 (110201)"""
    def use(self, user, targets, context, level=1):
        multiplier = self.skill_data["params"][level-1][0]
        return [
            DamageEffect(user, targets, context, "Quantum", multiplier, self.type),
            ProgressBoostEffect(user, [user], context, boost_amount=0.2, timing="next_turn")
        ]

class SeeleSkill(BaseSkill):
    """希儿战技 (110202)"""
    def use(self, user, targets, context, level=1):
        params = self.skill_data["params"][level-1]
        damage_multiplier, spd_bonus, buff_duration = params
        
        spd_buff = Buff.create_skill_buff(
            name="Sheathed Blade SPD Boost",
            duration=buff_duration,
            stat_bonus={"SPD%": spd_bonus}
        )
        
        return [
            BuffEffect(user, [user], context, spd_buff),
            DamageEffect(user, targets, context, "Quantum", damage_multiplier, self.type)
        ]

class SeeleUltimateSkill(BaseSkill):
    """希儿终结技 (110203)"""
    def use(self, user, targets, context, level=1):
        damage_multiplier = self.skill_data["params"][level-1][0]
        
        resurgence_skill = next((s for s in user.skills if getattr(s, 'skill_id', '') == '110204'), None)
        if resurgence_skill:
            enhanced_buff = resurgence_skill.create_resurgence_buff(user, level)
            enhanced_buff.duration = 1
        else: # Fallback
            enhanced_buff = Buff(name="Resurgence", duration=1, damage_bonus=0.4, element_penetration=0.2)
        
        return [
            BuffEffect(user, [user], context, enhanced_buff),
            DamageEffect(user, targets, context, "Quantum", damage_multiplier, self.type)
        ]

class SeeleTalent(BaseSkill):
    """希儿天赋 (110204)"""
    def create_resurgence_buff(self, user, level=1):
        params = self.skill_data["params"][level-1]
        damage_bonus, duration = params
        return Buff(
            name="Resurgence",
            duration=duration,
            damage_bonus=damage_bonus,
            element_penetration=0.2
        )

    def use(self, user, targets, context, level=1):
        enhanced_buff = self.create_resurgence_buff(user, level)
        return [
            BuffEffect(user, [user], context, enhanced_buff),
            ExtraTurnEffect(user, [user], context)
        ]

# 其他技能保持返回空列表即可
class SeeleTechnique(BaseSkill): ...
class SeeleBonusSkill(BaseSkill): ...