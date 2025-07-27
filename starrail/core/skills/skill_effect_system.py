# skill_effect_system.py - 技能效果组合系统
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from enum import Enum
from starrail.core.skills.base_skill import BaseSkill

class EffectTiming(Enum):
    """效果执行时机"""
    BEFORE_ALL = "before_all"        # 所有效果之前
    BEFORE_DAMAGE = "before_damage"  # 伤害之前
    AFTER_DAMAGE = "after_damage"    # 伤害之后
    AFTER_ALL = "after_all"          # 所有效果之后

class SkillEffect(ABC):
    """技能效果基类"""
    
    def __init__(self, timing: EffectTiming = EffectTiming.AFTER_DAMAGE, 
                 target_type: str = "enemies"):
        self.timing = timing
        self.target_type = target_type  # "enemies", "allies", "self", "all"
    
    @abstractmethod
    def execute(self, user, targets, context, **kwargs):
        """执行效果"""
        pass
    
    def get_valid_targets(self, user, targets, context):
        """根据target_type筛选有效目标"""
        if self.target_type == "self":
            return [user]
        elif self.target_type == "allies":
            return [t for t in targets if t.side == user.side]
        elif self.target_type == "enemies":
            return [t for t in targets if t.side != user.side]
        else:  # "all"
            return targets

class DamageEffect(SkillEffect):
    """伤害效果"""
    
    def __init__(self, multiplier: float, element: str, 
                 timing: EffectTiming = EffectTiming.AFTER_DAMAGE,
                 target_type: str = "enemies"):
        super().__init__(timing, target_type)
        self.multiplier = multiplier
        self.element = element
    
    def execute(self, user, targets, context, skill_manager=None, **kwargs):
        if not skill_manager:
            return []
        
        valid_targets = self.get_valid_targets(user, targets, context)
        results = []
        
        for target in valid_targets:
            intent = {
                "multiplier": self.multiplier,
                "element": self.element,
                "skill_name": kwargs.get("skill_name", "Unknown")
            }
            result = skill_manager._apply_damage_to_target(
                user, target, intent, kwargs.get("skill_type", "Normal")
            )
            results.append(result)
        
        return results

class BuffEffect(SkillEffect):
    """Buff效果"""
    
    def __init__(self, buff, timing: EffectTiming = EffectTiming.BEFORE_DAMAGE,
                 target_type: str = "self"):
        super().__init__(timing, target_type)
        self.buff = buff
    
    def execute(self, user, targets, context, skill_manager=None, **kwargs):
        if not skill_manager:
            return []
        
        valid_targets = self.get_valid_targets(user, targets, context)
        results = []
        
        for target in valid_targets:
            result = skill_manager._apply_buff_to_target(
                target, self.buff, kwargs.get("skill_name", "Unknown")
            )
            if result:
                results.append(result)
        
        return results

class HealEffect(SkillEffect):
    """治疗效果"""
    
    def __init__(self, base_heal: float = 0, heal_ratio: float = 0,
                 stat_scaling: Dict[str, float] = None,
                 timing: EffectTiming = EffectTiming.AFTER_DAMAGE,
                 target_type: str = "allies"):
        super().__init__(timing, target_type)
        self.base_heal = base_heal
        self.heal_ratio = heal_ratio
        self.stat_scaling = stat_scaling or {}
    
    def execute(self, user, targets, context, skill_manager=None, **kwargs):
        if not skill_manager:
            return []
        
        valid_targets = self.get_valid_targets(user, targets, context)
        results = []
        
        from .heal_system import HealCalculator
        
        for target in valid_targets:
            heal_amount = HealCalculator.calculate_heal_amount(
                user, target, self.base_heal, self.heal_ratio, self.stat_scaling
            )
            result = skill_manager._apply_heal_to_target(
                target, heal_amount, kwargs.get("skill_name", "Unknown")
            )
            if result:
                results.append(result)
        
        return results

class ProgressBoostEffect(SkillEffect):
    """行动进度提升效果"""
    
    def __init__(self, boost_amount: float, boost_timing: str = "current_turn",
                 timing: EffectTiming = EffectTiming.AFTER_ALL,
                 target_type: str = "self"):
        super().__init__(timing, target_type)
        self.boost_amount = boost_amount
        self.boost_timing = boost_timing
    
    def execute(self, user, targets, context, skill_manager=None, **kwargs):
        valid_targets = self.get_valid_targets(user, targets, context)
        
        for target in valid_targets:
            if hasattr(target, '_battle_context'):
                battle_context = target._battle_context
                if hasattr(battle_context, 'boost_action_progress'):
                    if self.boost_timing == "next_turn":
                        battle_context.delayed_boost_next_turn_progress(target, self.boost_amount)
                    else:
                        battle_context.boost_action_progress(target, self.boost_amount)
        
        return []

class CompositeSkill(BaseSkill):
    """组合技能类"""
    
    def __init__(self, skill_data, effects: List[SkillEffect]):
        super().__init__(skill_data)
        self.effects = effects
        # 按执行时机分组
        self.effects_by_timing = {}
        for effect in effects:
            timing = effect.timing
            if timing not in self.effects_by_timing:
                self.effects_by_timing[timing] = []
            self.effects_by_timing[timing].append(effect)
    
    def use(self, user, targets, context, level=1):
        """返回组合效果意图"""
        return {
            "type": "composite_skill",
            "effects": self.effects,
            "effects_by_timing": self.effects_by_timing,
            "skill_name": self.name,
            "desc": self.description
        }

# 在SkillManager中添加处理函数
def _handle_composite_skill(self, user, targets, intent, skill_type):
    """处理组合技能"""
    all_results = []
    effects_by_timing = intent.get("effects_by_timing", {})
    
    # 按时机顺序执行效果
    execution_order = [
        EffectTiming.BEFORE_ALL,
        EffectTiming.BEFORE_DAMAGE,
        EffectTiming.AFTER_DAMAGE,
        EffectTiming.AFTER_ALL
    ]
    
    for timing in execution_order:
        effects = effects_by_timing.get(timing, [])
        for effect in effects:
            results = effect.execute(
                user, targets, context,
                skill_manager=self,
                skill_name=intent["skill_name"],
                skill_type=skill_type
            )
            all_results.extend(results)
    
    return all_results

# 使用示例：重新设计希儿的战技
class SeeleSkillComposite(CompositeSkill):
    """希儿战技 - 组合版本"""
    
    def __init__(self, skill_data):
        # 获取技能参数
        params = skill_data["params"][0]  # 假设使用1级参数
        damage_multiplier = params[0]
        spd_bonus = params[1]
        buff_duration = params[2]
        
        # 创建速度Buff
        from .buff import Buff
        spd_buff = Buff.create_skill_buff(
            name="Sheathed Blade SPD Boost",
            duration=buff_duration,
            stat_bonus={"SPD%": spd_bonus}
        )
        
        # 组合效果：先Buff后伤害
        effects = [
            BuffEffect(spd_buff, EffectTiming.BEFORE_DAMAGE, "self"),
            DamageEffect(damage_multiplier, "Quantum", EffectTiming.AFTER_DAMAGE, "enemies")
        ]
        
        super().__init__(skill_data, effects)

# # 复杂技能示例：AOE伤害 + 治疗 + Buff
# class ComplexHealerSkill(CompositeSkill):
#     """复杂奶妈技能示例"""
    
#     def __init__(self, skill_data):
#         effects = [
#             # 先给自己加攻击力Buff
#             BuffEffect(
#                 Buff.create_skill_buff("ATK Boost", 3, {"ATK%": 0.3}),
#                 EffectTiming.BEFORE_ALL, "self"
#             ),
#             # 然后对敌人造成伤害
#             DamageEffect(1.2, "Fire", EffectTiming.BEFORE_DAMAGE, "enemies"),
#             # 伤害后治疗队友
#             HealEffect(
#                 base_heal=500, heal_ratio=0.15,
#                 timing=EffectTiming.AFTER_DAMAGE, target_type="allies"
#             ),
#             # 最后提升自己的行动进度
#             ProgressBoostEffect(
#                 0.3, "next_turn",
#                 EffectTiming.AFTER_ALL, "self"
#             )
#         ]
        
#         super().__init__(skill_data, effects)