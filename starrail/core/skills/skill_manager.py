from .skill import get_skill_instance
from .buff import Buff
import random
from starrail.core.enemy import Enemy

def damage_calc_attack_side(user, target, multiplier, element):
    """攻击方修正：返回理论伤害和暴击信息"""
    atk = getattr(user, "atk", 0)
    base_damage = atk * multiplier

    # 增益修正
    damage_bonus = 0
    element_penetration = 0
    if element:
        damage_bonus += user.get_current_stats().get(f"{element} DMG", 0)
    for buff in getattr(user, 'buffs', []):
        damage_bonus += getattr(buff, 'damage_bonus', 0)
        element_penetration += getattr(buff, 'element_penetration', 0)

    damage_modifier = 1 + damage_bonus

    # 暴击
    crit_rate = user.get_current_stats().get("CRIT Rate", 0.05)
    crit_dmg = user.get_current_stats().get("CRIT DMG", 0.5)
    is_crit = random.random() < crit_rate
    crit_modifier = 1 + crit_dmg if is_crit else 1

    # 输出理论伤害
    theory_damage = base_damage * damage_modifier * crit_modifier
    return {
        "theory_damage": theory_damage,
        "element": element,
        "element_penetration": element_penetration,
        "is_crit": is_crit,
        "crit_modifier": crit_modifier,
        "base_damage": base_damage,
        "damage_modifier": damage_modifier,
    }

def damage_calc_defense_side(theory_damage, user, target, element, element_penetration):
    """防御方修正：输入理论伤害，输出最终伤害"""
    # 1. 属性抗性
    element_resistance = 0
    if hasattr(target, 'resistances') and target.resistances:
        element_resistance = target.resistances.get(element, 0)
    # 穿透修正
    resistance_modifier = 1 - (element_resistance - element_penetration)
    if element is not None:
        penetration_info = f", 穿透:{element_penetration:.1%}" if element_penetration > 0 else ""
        print(f"  -> 属性抗性修正: {resistance_modifier:.3f} (属性:{element}, 抗性:{element_resistance:.1%}{penetration_info})")

    # 2. 防御修正
    if hasattr(target, 'defense_reduction'):
        after_def = target.defense_reduction(theory_damage, user, target)
    else:
        after_def = theory_damage

    # 3. 独立减伤区间
    independent_reduction = 1.0
    for buff in getattr(target, 'buffs', []):
        independent_reduction *= (1 - getattr(buff, 'independent_damage_reduction', 0))
    # 新增：韧性独立减伤
    if hasattr(target, 'toughness') and target.toughness is not None and target.toughness > 0:
        print(f"  -> [韧性减伤] {target.name} 韧性>0，额外10%独立减伤")
        independent_reduction *= 0.9
    # 4. 受到伤害增加区间
    damage_taken_bonus = 1.0
    for buff in getattr(target, 'buffs', []):
        damage_taken_bonus *= (1 + getattr(buff, 'damage_taken_increase', 0))

    # 5. 合并
    final_damage = after_def * resistance_modifier * independent_reduction * damage_taken_bonus
    return final_damage

def damage_calc(user, target, multiplier, element):
    """主伤害结算函数"""
    attack_result = damage_calc_attack_side(user, target, multiplier, element)
    final_damage = damage_calc_defense_side(
        attack_result["theory_damage"],
        user, target, element,
        attack_result["element_penetration"]
    )
    # 可在此输出详细log
    print(f"[伤害计算] {user.name} -> {target.name}")
    print(f"  基础伤害: {attack_result['base_damage']:.1f}")
    print(f"  增益修正: {attack_result['damage_modifier']:.3f}")
    print(f"  暴击修正: {attack_result['crit_modifier']:.3f} ({'暴击' if attack_result['is_crit'] else '非暴击'})")
    print(f"  理论伤害: {attack_result['theory_damage']:.1f}")
    print(f"  最终伤害: {final_damage:.1f}")
    return final_damage

def break_damage_calc(attacker, target, break_damage, element):
    # 只走防御方修正，不做攻击方增益和暴击
    return damage_calc_defense_side(
        break_damage, attacker, target, element, element_penetration=0
    )

class SkillManager:
    def __init__(self, skill_data_dict):
        self.skill_data_dict = skill_data_dict

    def use_skill(self, skill_id, user, targets, context, level=1):
        skill_data = self.skill_data_dict[skill_id]
        skill = get_skill_instance(skill_id, skill_data)
        intent = skill.use(user, targets, context, level)
        results = []
        
        # 获取技能类型用于能量回复
        skill_type = skill_data.get("type", "Normal")
        
        # 记录技能类型，用于天赋触发判断
        if hasattr(user, 'set_last_skill_type'):
            user.set_last_skill_type(skill_type)
        
        # 处理不同类型的技能
        if intent["type"] == "damage_only":
            # 纯伤害技能
            results = self._handle_damage_only(user, targets, intent, skill_type)
            
        elif intent["type"] == "buff_only":
            # 纯Buff技能
            results = self._handle_buff_only(user, targets, intent)
            
        elif intent["type"] == "damage_before_buff":
            # 先伤害后Buff（适用于需要先造成伤害再提供Buff的技能）
            results = self._handle_damage_before_buff(user, targets, intent, skill_type)
            
        elif intent["type"] == "buff_before_damage":
            # 先Buff后伤害（适用于需要先提供Buff再造成伤害的技能）
            results = self._handle_buff_before_damage(user, targets, intent, skill_type)
            
        elif intent["type"] == "talent_enhance":
            # 天赋强化效果
            results = self._handle_talent_enhance(user, intent)
            
        elif intent["type"] == "damage_with_progress_boost":
            # 伤害+行动进度提升技能
            results = self._handle_damage_with_progress_boost(user, targets, intent, skill_type)
            
        elif intent["type"] == "heal_only":
            # 强制治疗类技能只能选择己方目标
            targets = [t for t in targets if t.side == user.side]
            if not targets:
                targets = [user]  # 至少治疗自己
            results = self._handle_heal_only(user, targets, intent)
            
        elif intent["type"] == "heal_before_buff":
            # 先治疗后Buff的混合技能，只能选择己方目标
            targets = [t for t in targets if t.side == user.side]
            if not targets:
                targets = [user]  # 至少治疗自己
            results = self._handle_heal_before_buff(user, targets, intent)
            
        elif intent["type"] == "skip":
            print(f"[技能跳过] {user.name} 使用了未实装技能 [{intent.get('skill_name', skill_id)}]，本回合跳过。")
            
        # 其他类型如治疗等可扩展
        return results

    def _handle_damage_only(self, user, targets, intent, skill_type):
        """处理纯伤害技能"""
        results = []
        # 削韧值设定
        toughness_map = {"Normal": 10, "BPSkill": 20, "Ultra": 30}
        for target in targets:
            dmg = damage_calc(user, target, intent["multiplier"], intent["element"])
            target_was_alive = target.is_alive()
            if hasattr(target, "receive_damage"):
                target.receive_damage(dmg, attacker=user, skill_type=skill_type)
            # 仅对Enemy削韧
            if isinstance(target, Enemy):
                toughness_amount = toughness_map.get(skill_type, 0)
                target.reduce_toughness(toughness_amount, element=intent.get("element"), attacker=user)
            # 检查是否击杀
            if target_was_alive and not target.is_alive():
                user.on_enemy_killed()
            results.append({
                "target": target,
                "damage": dmg,
                "element": intent["element"],
                "skill_name": intent["skill_name"],
                "desc": intent["desc"]
            })
        return results

    def _handle_buff_only(self, user, targets, intent):
        """处理纯Buff技能"""
        results = []
        for target in targets:
            if hasattr(target, "add_buff") and intent.get("buff"):
                buff = intent["buff"]
                # 设置Buff的self_buff属性
                buff.self_buff = (target == user)  # 只有目标是自己时才设为self_buff
                target.add_buff(buff)
                print(f"[Buff应用] {target.name} 获得Buff: {buff.name} (持续{buff.duration}回合)")
            
            results.append({
                "target": target,
                "buff": intent.get("buff"),
                "skill_name": intent["skill_name"],
                "desc": intent["desc"]
            })
        return results

    def _handle_damage_before_buff(self, user, targets, intent, skill_type):
        """处理先伤害后Buff的技能（适用于需要先造成伤害再提供Buff的技能）"""
        results = []
        # 削韧值设定
        toughness_map = {"Normal": 10, "BPSkill": 20, "Ultra": 30}
        for target in targets:
            dmg = damage_calc(user, target, intent["multiplier"], intent["element"])
            target_was_alive = target.is_alive()
            if hasattr(target, "receive_damage"):
                target.receive_damage(dmg, attacker=user, skill_type=skill_type)
            if isinstance(target, Enemy):
                toughness_amount = toughness_map.get(skill_type, 0)
                target.reduce_toughness(toughness_amount, element=intent.get("element"), attacker=user)
            # 检查是否击杀
            if target_was_alive and not target.is_alive():
                user.on_enemy_killed()
            # 再应用Buff
            if hasattr(target, "add_buff") and intent.get("buff"):
                buff = intent["buff"]
                # 设置Buff的self_buff属性
                buff.self_buff = (target == user)  # 只有目标是自己时才设为self_buff
                target.add_buff(buff)
                print(f"[Buff应用] {target.name} 获得Buff: {buff.name} (持续{buff.duration}回合)")
            results.append({
                "target": target,
                "damage": dmg,
                "element": intent["element"],
                "buff": intent.get("buff"),
                "skill_name": intent["skill_name"],
                "desc": intent["desc"]
            })
        return results

    def _handle_buff_before_damage(self, user, targets, intent, skill_type):
        """处理先Buff后伤害的技能（适用于需要先提供Buff再造成伤害的技能）"""
        results = []
        # 削韧值设定
        toughness_map = {"Normal": 10, "BPSkill": 20, "Ultra": 30}
        buff_target = intent.get("buff_target", user)
        if hasattr(buff_target, "add_buff") and intent.get("buff"):
            buff = intent["buff"]
            # 设置Buff的self_buff属性
            buff.self_buff = (buff_target == user)  # 只有目标是自己时才设为self_buff
            buff_target.add_buff(buff)
            print(f"[Buff应用] {buff_target.name} 获得Buff: {buff.name} (持续{buff.duration}回合)")
        for target in targets:
            dmg = damage_calc(user, target, intent["multiplier"], intent["element"])
            target_was_alive = target.is_alive()
            if hasattr(target, "receive_damage"):
                target.receive_damage(dmg, attacker=user, skill_type=skill_type)
            if isinstance(target, Enemy):
                toughness_amount = toughness_map.get(skill_type, 0)
                target.reduce_toughness(toughness_amount, element=intent.get("element"), attacker=user)
            # 检查是否击杀
            if target_was_alive and not target.is_alive():
                user.on_enemy_killed()
            results.append({
                "target": target,
                "damage": dmg,
                "element": intent["element"],
                "skill_name": intent["skill_name"],
                "desc": intent["desc"]
            })
        return results

    def _handle_talent_enhance(self, user, intent):
        """处理天赋强化效果"""
        results = []
        buff_target = intent.get("buff_target", user)
        if hasattr(buff_target, "add_buff") and intent.get("buff"):
            buff = intent["buff"]
            # 设置Buff的self_buff属性
            buff.self_buff = (buff_target == user)  # 只有目标是自己时才设为self_buff
            buff_target.add_buff(buff)
            print(f"[天赋触发] {buff_target.name} 获得Buff: {buff.name} (持续{buff.duration}回合)")
        
        # 检查是否需要额外回合
        if intent.get("extra_turn", False):
            print(f"[额外回合] {user.name} 获得额外回合！")
            # 标记需要额外回合
            if hasattr(user, 'set_extra_turn'):
                user.set_extra_turn(True)
        
        results.append({
            "target": buff_target,
            "buff": intent.get("buff"),
            "extra_turn": intent.get("extra_turn", False),
            "skill_name": intent["skill_name"],
            "desc": intent["desc"]
        })
        return results

    def _handle_damage_with_progress_boost(self, user, targets, intent, skill_type):
        """处理伤害+行动进度提升技能"""
        results = []
        # 削韧值设定
        toughness_map = {"Normal": 10, "BPSkill": 20, "Ultra": 30}
        for target in targets:
            dmg = damage_calc(user, target, intent["multiplier"], intent["element"])
            target_was_alive = target.is_alive()
            if hasattr(target, "receive_damage"):
                target.receive_damage(dmg, attacker=user, skill_type=skill_type)
            if isinstance(target, Enemy):
                toughness_amount = toughness_map.get(skill_type, 0)
                target.reduce_toughness(toughness_amount, element=intent.get("element"), attacker=user)
            # 检查是否击杀
            if target_was_alive and not target.is_alive():
                user.on_enemy_killed()
            results.append({
                "target": target,
                "damage": dmg,
                "element": intent["element"],
                "skill_name": intent["skill_name"],
                "desc": intent["desc"]
            })
        # 再处理行动进度提升
        progress_target = intent.get("progress_target", user)
        progress_boost = intent.get("action_progress_boost", 0)
        boost_timing = intent.get("boost_timing", "current_turn")
        if progress_boost > 0 and hasattr(progress_target, '_battle_context'):
            battle_context = progress_target._battle_context
            if hasattr(battle_context, 'boost_action_progress'):
                if boost_timing == "next_turn":
                    battle_context.delayed_boost_next_turn_progress(progress_target, progress_boost)
                    print(f"[行动进度] {progress_target.name} 的下一回合行动进度提前了 {progress_boost*100:.0f}%")
                else:
                    battle_context.boost_action_progress(progress_target, progress_boost)
                    print(f"[行动进度] {progress_target.name} 的行动进度提前了 {progress_boost*100:.0f}%")
        return results 

    def _handle_heal_only(self, user, targets, intent):
        """处理纯治疗技能"""
        results = []
        for target in targets:
            heal_amount = intent["heal_amount"]
            if hasattr(target, "heal"):
                # 传递治疗者的名称而不是对象引用
                target.heal(heal_amount, source=user.name)
            results.append({
                "target": target,
                "heal": heal_amount,
                "skill_name": intent["skill_name"],
                "desc": intent["desc"]
            })
        return results

    def _handle_heal_before_buff(self, user, targets, intent):
        """处理先治疗后Buff的混合技能"""
        results = []
        for target in targets:
            # 先进行治疗
            heal_amount = intent["heal_amount"]
            if hasattr(target, "heal"):
                # 传递治疗者的名称而不是对象引用
                target.heal(heal_amount, source=user.name)
            
            # 再应用Buff
            if hasattr(target, "add_buff") and intent.get("buff"):
                buff = intent["buff"]
                # 设置Buff的self_buff属性
                buff.self_buff = (target == user)  # 只有目标是自己时才设为self_buff
                target.add_buff(buff)
                print(f"[Buff应用] {target.name} 获得Buff: {buff.name} (持续{buff.duration}回合)")
            
            results.append({
                "target": target,
                "heal": heal_amount,
                "buff": intent.get("buff"),
                "skill_name": intent["skill_name"],
                "desc": intent["desc"]
            })
        return results 