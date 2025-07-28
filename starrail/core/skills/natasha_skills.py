from .base_skill import BaseSkill
from .buff import Buff

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

class NatashaSkill(BaseSkill):
    """娜塔莎战技：单体治疗 + 持续治疗Buff (110502)"""
    def __init__(self, skill_data):
        super().__init__(skill_data)
        self.skill_data = skill_data

    def use(self, user, targets, context, level=1):
        params = self.skill_data["params"][level-1]
        immediate_heal_ratio = params[0]  # 立即治疗比例
        dot_heal_ratio = params[1]        # 持续治疗比例
        buff_duration = params[2]         # Buff持续时间
        immediate_heal_base = params[3]   # 立即治疗固定值
        dot_heal_base = params[4]         # 持续治疗固定值
        
        # 计算立即治疗量（基于娜塔莎的最大生命值）
        natasha_max_hp = user.get_max_hp() if hasattr(user, 'get_max_hp') else 0
        immediate_heal_amount = immediate_heal_ratio * natasha_max_hp + immediate_heal_base
        
        # 创建持续治疗Buff（也基于娜塔莎的最大生命值）
        dot_heal_amount = dot_heal_ratio * natasha_max_hp + dot_heal_base
        
        # 创建持续治疗Buff
        from .buff import Buff
        dot_buff = Buff(
            name="Natasha's Healing Over Time",
            duration=buff_duration,
            stat_bonus={},
            damage_bonus=0,
            element_penetration=0,
            stackable=False
        )
        
        # 添加自定义的回合开始治疗效果
        def on_turn_start(character):
            if character.is_alive():
                # 重新计算治疗量（基于娜塔莎当前的最大生命值）
                current_natasha_max_hp = user.get_max_hp() if hasattr(user, 'get_max_hp') else 0
                current_dot_heal_amount = dot_heal_ratio * current_natasha_max_hp + dot_heal_base
                character.heal(current_dot_heal_amount, source="Natasha's Healing Over Time")
                print(f"[持续治疗] {character.name} 受到持续治疗效果，回复 {current_dot_heal_amount:.1f} 点生命值")
        
        dot_buff.on_turn_start = on_turn_start
        dot_buff.source = "skill"
        dot_buff.level = level
        
        return {
            "type": "heal_before_buff",
            "heal_amount": immediate_heal_amount,
            "targets": targets,
            "buff": dot_buff,
            "skill_name": self.name,
            "desc": f"立即治疗{immediate_heal_amount:.1f}点生命值，并提供持续{ buff_duration}回合的治疗效果"
        } 