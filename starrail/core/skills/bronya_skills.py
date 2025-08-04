# starrail/core/skills/bronya_skills.py
from typing import List
from ...utils.logger import logger
from .base_skill import BaseSkill
from .buff import Buff
from .effects import DamageEffect, BuffEffect, ProgressBoostEffect

# 前向声明以支持类型提示
if False:
    from ..character import Character

class BronyaBasicSkill(BaseSkill):
    """布洛妮娅普攻 (110101) - 附带天赋效果"""
    def use(self, user: 'Character', targets: List['Character'], context, level=1) -> List:
        # 普攻伤害效果
        multiplier = self.skill_data["params"][level-1][0]
        effects = [
            DamageEffect(user, targets, context, "Wind", multiplier, self.type)
        ]
        
        # 天赋 (110104) 效果: 使用普攻后，自身行动提前
        talent_skill_data = user.skill_manager.skill_data_dict.get("110104")
        if talent_skill_data:
            # 假设天赋等级与角色等级或某个设定挂钩，这里用 level 1
            talent_level = 1 
            advance_forward_pct = talent_skill_data["params"][talent_level-1][0]
            logger.log(f"[天赋] {user.name} 的 '先行' 天赋触发，下次行动提前 {advance_forward_pct:.0%}", color="green")
            effects.append(
                ProgressBoostEffect(user, [user], context, boost_amount=advance_forward_pct, timing="next_turn")
            )
            
        return effects

class BronyaSkill(BaseSkill):
    """布洛妮娅战技 (110102) - 作战再部署"""
    def use(self, user: 'Character', targets: List['Character'], context, level=1) -> List:
        if not targets:
            return []
            
        target_ally = targets[0]
        params = self.skill_data["params"][level-1]
        dmg_boost, _, buff_duration, _ = params

        effects = []
        
        # 效果1: 驱散一个负面效果 (当前框架未实现debuff，仅打印日志)
        logger.log(f"[技能效果] {user.name} 对 {target_ally.name} 尝试驱散一个负面效果。", color="cyan")
        # 在未来的实现中，这里可以添加 DebuffRemovalEffect

        # 效果2: 使目标队友立即行动 (如果目标不是自己)
        if target_ally.id != user.id:
            logger.log(f"[技能效果] {target_ally.name} 获得立即行动机会！", color="blue")
            effects.append(ProgressBoostEffect(target_ally, [target_ally], context, boost_amount=1.0, timing="immediate"))
        else:
            logger.log(f"[技能效果] {user.name} 对自己使用了战技，无法立即行动。", color="yellow")

        # 效果3: 为目标队友提供伤害加成
        dmg_buff = Buff(
            name=f"作战再部署 (来自{user.name})",
            duration=buff_duration,
            damage_bonus=dmg_boost
        )
        effects.append(BuffEffect(user, [target_ally], context, dmg_buff))
        
        return effects

class BronyaUltimateSkill(BaseSkill):
    """布洛妮娅终结技 (110103) - 贝洛伯格进行曲"""
    def use(self, user: 'Character', targets: List['Character'], context, level=1) -> List:
        params = self.skill_data["params"][level-1]
        atk_boost, crit_dmg_from_bronya, crit_dmg_flat, buff_duration = params
        
        all_allies = [c for c in context.characters if c.side == user.side and c.is_alive()]
        
        # 定义一个动态计算暴伤加成的函数
        def dynamic_crit_dmg_bonus(character: 'Character') -> dict:
            # [关键修正] 调用 get_current_stats 时传入 recursive_guard=True
            # 这会获取布洛妮娅未应用动态Buff的基础面板，从而避免无限递归
            bronya_current_stats = user.get_current_stats(recursive_guard=True)
            bronya_crit_dmg = bronya_current_stats.get("CRIT DMG", 0.5)
            
            # 计算最终的暴伤加成
            total_crit_dmg_bonus = (bronya_crit_dmg * crit_dmg_from_bronya) + crit_dmg_flat
            
            return {"CRIT DMG": total_crit_dmg_bonus}

        # 创建包含固定攻击力加成和动态暴伤加成的Buff
        ultimate_buff = Buff(
            name="贝洛伯格进行曲",
            duration=buff_duration,
            stat_bonus={"ATK%": atk_boost},
            dynamic_stat_bonus_func=dynamic_crit_dmg_bonus
        )
        
        return [BuffEffect(user, all_allies, context, ultimate_buff)]

class BronyaTalent(BaseSkill):
    """布洛妮娅天赋 (110104) - 先行"""
    # 天赋的逻辑已在 BronyaBasicSkill 中实现，此处作为占位符
    def use(self, user, targets, context, level=1):
        logger.log_verbose(f"[天赋占位] {self.name} 被动触发。")
        return []

class BronyaTechnique(BaseSkill):
    """布洛妮娅秘技 (110107) - 号令的旗帜"""
    def use(self, user: 'Character', targets: List['Character'], context, level=1) -> List:
        # 在当前战斗框架下，秘技模拟为战斗开始时给全体队友施加的buff
        params = self.skill_data["params"][level-1]
        atk_boost, buff_duration = params
        
        all_allies = [c for c in context.characters if c.side == user.side and c.is_alive()]

        technique_buff = Buff(
            name="号令的旗帜",
            duration=buff_duration,
            stat_bonus={"ATK%": atk_boost}
        )
        
        logger.log(f"[秘技] {user.name} 使用秘技，全体队友攻击力提升！", color="purple")
        return [BuffEffect(user, all_allies, context, technique_buff)]

class BronyaMazeNormal(BaseSkill):
    """布洛妮娅地图攻击 (110106)"""
    # 地图技能，在战斗中无效果，作为占位符
    def use(self, user, targets, context, level=1):
        return []
