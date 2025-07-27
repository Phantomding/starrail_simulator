# enemy.py
from typing import Optional
from starrail.core.character import Character
from starrail.core.light_cones.light_cone import LightCone

class Enemy(Character):
    def __init__(self, name, stats, id, skills, traces=None, side="enemy", drop=None, ai_type="default", light_cone: Optional[LightCone] = None, weaknesses=None, resistances=None, level=80, toughness=100, max_toughness=100):
        super().__init__(name, stats, skills, id, traces, side=side, light_cone=light_cone, level=level)
        self.drop = drop  # 敌人掉落物
        self.ai_type = ai_type  # 敌人AI类型
        self.weaknesses = weaknesses or []  # 属性弱点，如["Fire", "Ice"]
        self.resistances = resistances or {}  # 属性抗性，如{"Fire": 0.2, "Ice": 0.1}
        # 韧性相关
        self.toughness = toughness
        self.max_toughness = max_toughness
        self.toughness_broken = False

    def reduce_toughness(self, amount, element=None, attacker=None):
        """削减韧性，只有攻击属性在weaknesses中时才生效，韧性归零时触发击破伤害"""
        if self.toughness is None:
            return
        if element is not None:
            if element not in self.weaknesses:
                print(f"[韧性] 攻击属性{element}不在{self.name}的弱点中，韧性不变。")
                return
        before = self.toughness
        self.toughness = max(self.toughness - amount, 0)
        print(f"[韧性] {self.name} 的韧性: {before} -> {self.toughness} (-{amount})")
        # 击破判定
        if before > 0 and self.toughness == 0 and not self.toughness_broken:
            self.toughness_broken = True
            print(f"[韧性击破] {self.name} 被击破，触发击破伤害！")
            break_damage = self.calculate_break_damage(element, attacker)
            print(f"[击破伤害] {self.name} 受到击破伤害: {break_damage:.1f}")
            from starrail.core.skills.skill_manager import break_damage_calc
            dmg = break_damage_calc(attacker, self, break_damage, element)
            self.receive_damage(dmg, attacker=attacker, skill_type="Break")

    def calculate_break_damage(self, element, attacker=None):
        """计算击破伤害，仅返回基础击破伤害，区间修正交由receive_damage处理"""
        element_coeff_map = {
            "Physical": 2.0,
            "Fire": 2.0,
            "Wind": 1.5,
            "Lightning": 1.0,
            "Ice": 1.0,
            "Quantum": 0.5,
            "Imaginary": 0.5
        }
        break_coeff = 1883.8
        attr_coeff = element_coeff_map.get(element, 1.0)
        toughness_length = self.max_toughness
        break_effect = 0.0
        if attacker is not None:
            break_effect = getattr(attacker, 'break_effect', 0.0)
        # 只计算基础击破伤害
        break_damage = break_coeff * attr_coeff * ((toughness_length + 20) / 40) * (1 + break_effect)
        return break_damage

    def take_turn(self, battle_context):
        # 行动开始时自动回复韧性（如被击破）
        if self.toughness is not None and self.toughness_broken:
            print(f"[韧性恢复] {self.name} 行动开始，韧性自动恢复到最大值 {self.max_toughness}")
            self.toughness = self.max_toughness
            self.toughness_broken = False
        super().take_turn(battle_context)
    # 可扩展敌人专属方法 