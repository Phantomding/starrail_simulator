# effects.py
from typing import List, Callable, Dict, Any

# 前向声明，避免循环导入
class Character: ...
class Buff: ...
class BattleContext: ...

class BaseEffect:
    """效果基类，所有效果都继承自它"""
    def __init__(self, caster: Character, targets: List[Character], context: BattleContext):
        self.caster = caster
        # 确保目标列表总是列表形式
        self.targets = targets if isinstance(targets, list) else [targets]
        self.context = context

    def execute(self, **kwargs):
        """
        执行效果的通用接口。
        kwargs 用于传入执行时依赖的外部函数或数据，如 damage_calc。
        """
        raise NotImplementedError

class DamageEffect(BaseEffect):
    """造成伤害的效果"""
    def __init__(self, caster: Character, targets: List[Character], context: BattleContext, element: str, multiplier: float, skill_type: str):
        super().__init__(caster, targets, context)
        self.element = element
        self.multiplier = multiplier
        self.skill_type = skill_type

    def execute(self, damage_calc_func: Callable, **kwargs):
        print(f"  [效果执行] 伤害效果: 对 {len(self.targets)} 个目标造成 {self.element} 伤害")
        for target in self.targets:
            if target.is_alive():
                # 调用外部传入的伤害计算函数
                damage_calc_func(self.caster, target, self.multiplier, self.element, self.skill_type)

class BuffEffect(BaseEffect):
    """施加Buff的效果"""
    def __init__(self, caster: Character, targets: List[Character], context: BattleContext, buff: Buff):
        super().__init__(caster, targets, context)
        self.buff = buff

    def execute(self, **kwargs):
        print(f"  [效果执行] Buff效果: 对 {[t.name for t in self.targets]} 施加 '{self.buff.name}'")
        for target in self.targets:
            if target.is_alive():
                # 设定buff来源和是否为对自己施加
                self.buff.self_buff = (target == self.caster)
                target.add_buff(self.buff)

class HealEffect(BaseEffect):
    """治疗效果"""
    def __init__(self, caster: Character, targets: List[Character], context: BattleContext, base_heal_amount: float):
        super().__init__(caster, targets, context)
        self.base_heal_amount = base_heal_amount

    def execute(self, calculate_final_heal_func: Callable, **kwargs):
        skill_type = getattr(self.caster, '_last_skill_type', 'Unknown')
        final_heal = calculate_final_heal_func(self.caster, self.base_heal_amount, skill_type)
        
        print(f"  [效果执行] 治疗效果: 为 {[t.name for t in self.targets]} 治疗 {final_heal:.1f} 生命值")
        for target in self.targets:
            if target.is_alive():
                target.heal(final_heal, source=self.caster.name)

class ExtraTurnEffect(BaseEffect):
    """获得额外回合的效果"""
    def execute(self, **kwargs):
        print(f"  [效果执行] 额外回合: {self.caster.name} 获得一个额外回合")
        if hasattr(self.caster, 'set_extra_turn'):
            self.caster.set_extra_turn(True)

class ProgressBoostEffect(BaseEffect):
    """行动进度提升效果"""
    def __init__(self, caster: Character, targets: List[Character], context: BattleContext, boost_amount: float, timing: str = "next_turn"):
        super().__init__(caster, targets, context)
        self.boost_amount = boost_amount
        self.timing = timing

    def execute(self, **kwargs):
        print(f"  [效果执行] 行动值推进: {self.targets[0].name} 的行动值推进 {self.boost_amount:.0%}")
        for target in self.targets:
            if hasattr(self.context, 'boost_action_progress'):
                if self.timing == "next_turn":
                    self.context.delayed_boost_next_turn_progress(target, self.boost_amount)
                else:
                    self.context.boost_action_progress(target, self.boost_amount)