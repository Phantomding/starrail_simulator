# 修正：BaseSkill需保存skill_data
from .base_skill import BaseSkill
from .buff import Buff

class SeeleBasicSkill(BaseSkill):
    """希儿普攻：Thwack (110201)"""
    def __init__(self, skill_data):
        super().__init__(skill_data)
        self.skill_data = skill_data

    def use(self, user, targets, context, level=1):
        multiplier = self.skill_data["params"][level-1][0]
        
        # 添加行动进度提前效果（为下一回合提前）
        action_progress_boost = 0.2  # 20%的行动进度提前
        boost_timing = "next_turn"  # 为下一回合提前
        
        return {
            "type": "damage_with_progress_boost",
            "element": "Quantum",
            "multiplier": multiplier,
            "targets": targets,
            "skill_name": self.name,
            "desc": self.description,
            "action_progress_boost": action_progress_boost,
            "progress_target": user,  # 效果作用于施法者自己
            "boost_timing": boost_timing  # 指定提升时机
        }

class SeeleSkill(BaseSkill):
    """希儿战技：Sheathed Blade (110202)"""
    def __init__(self, skill_data):
        super().__init__(skill_data)
        self.skill_data = skill_data

    def use(self, user, targets, context, level=1):
        # 获取技能参数
        params = self.skill_data["params"][level-1]
        damage_multiplier = params[0]  # 伤害倍率
        spd_bonus = params[1]  # 速度加成百分比
        buff_duration = params[2]  # Buff持续时间
        
        # 创建速度Buff
        spd_buff = Buff.create_skill_buff(
            name="Sheathed Blade SPD Boost",
            duration=buff_duration,
            stat_bonus={"SPD%": spd_bonus},
            source="skill",
            level=level
        )
        
        return {
            "type": "buff_before_damage",
            "element": "Quantum",
            "multiplier": damage_multiplier,
            "targets": targets,
            "buff": spd_buff,
            "buff_target": user,  # Buff给自己
            "skill_name": self.name,
            "desc": f"造成量子伤害并提升自身速度{spd_bonus*100:.0f}%，持续{buff_duration}回合"
        }

class SeeleUltimateSkill(BaseSkill):
    """希儿终结技：Butterfly Flurry (110203)"""
    def __init__(self, skill_data):
        super().__init__(skill_data)
        self.skill_data = skill_data

    def use(self, user, targets, context, level=1):
        # 获取技能参数
        params = self.skill_data["params"][level-1]
        damage_multiplier = params[0]  # 伤害倍率
        
        # 直接调用天赋的Resurgence Buff
        # 查找Resurgence天赋技能
        resurgence_skill = None
        for skill in user.skills:
            if getattr(skill, 'skill_id', '') == '110204':
                resurgence_skill = skill
                break
        
        if resurgence_skill and hasattr(resurgence_skill, 'create_resurgence_buff'):
            # 直接使用天赋的Buff，持续时间为1回合
            enhanced_buff = resurgence_skill.create_resurgence_buff(user, level)
            enhanced_buff.duration = 1  # 终极技持续1回合
            enhanced_buff.source = "ultimate"  # 标记来源为终极技
        else:
            # 备用方案：创建基础Buff
            enhanced_buff = Buff.create_skill_buff(
                name="Resurgence Enhanced State",
                duration=1,
                stat_bonus={},
                damage_bonus=0.25,
                element_penetration=0.2,
                source="ultimate",
                level=level
            )
        
        return {
            "type": "buff_before_damage",
            "element": "Quantum",
            "multiplier": damage_multiplier,
            "targets": targets,
            "buff": enhanced_buff,
            "buff_target": user,  # 强化状态给自己
            "skill_name": self.name,
            "desc": f"进入强化状态并造成{damage_multiplier*100:.0f}%攻击力的量子伤害，强化状态持续2回合"
        }

class SeeleTalent(BaseSkill):
    """希儿天赋：Resurgence (110204)"""
    def __init__(self, skill_data):
        super().__init__(skill_data)
        self.skill_data = skill_data

    def create_resurgence_buff(self, user, level=1):
        """
        创建Resurgence强化状态Buff，可被终极技调用
        """
        # 获取技能参数
        params = self.skill_data["params"][level-1]
        damage_bonus = params[0]  # 伤害增加百分比
        duration = params[1]  # 持续时间
        
        # 创建强化状态Buff（独立的增伤区 + 属性穿透）
        enhanced_buff = Buff.create_skill_buff(
            name="Resurgence Enhanced State",  # 使用专门的Buff名称
            duration=duration,  # 天赋持续时间
            stat_bonus={},  # 不增加属性伤害
            damage_bonus=damage_bonus,  # 独立的增伤区
            source="talent",
            level=level
        )
        
        # 添加属性穿透效果
        enhanced_buff.element_penetration = 0.2  # 20%属性穿透
        
        return enhanced_buff

    def use(self, user, targets, context, level=1):
        # 创建Resurgence Buff
        enhanced_buff = self.create_resurgence_buff(user, level)
        
        return {
            "type": "talent_enhance",
            "buff": enhanced_buff,
            "buff_target": user,  # 强化状态给自己
            "extra_turn": True,  # 标记需要额外回合
            "skill_name": self.name,
            "desc": f"进入强化状态，攻击伤害提升{enhanced_buff.damage_bonus*100:.0f}%，获得20%属性穿透，持续{enhanced_buff.duration}回合，并获得额外回合"
        }

class SeeleTechnique(BaseSkill):
    """希儿秘技：Attack (110206)"""
    def use(self, user, targets, context, level=1):
        return {"type": "skip", "skill_name": self.name}

class SeeleBonusSkill(BaseSkill):
    """希儿追加能力：Phantom Illusion (110207)"""
    def use(self, user, targets, context, level=1):
        return {"type": "skip", "skill_name": self.name} 