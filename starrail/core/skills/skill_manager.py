# skill_manager.py - 重构版本
from .skill import get_skill_instance
from .buff import Buff
import random
from starrail.core.enemy import Enemy
from starrail.core.skills.damage_system import DamageCalculator, DamageType
from typing import Dict

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
        # 技能类型对应的削韧值
        self.toughness_damage_map = {"Normal": 10, "BPSkill": 20, "Ultra": 30}

    def use_skill(self, skill_id, user, targets, context, level=1):
        skill_data = self.skill_data_dict[skill_id]
        skill = get_skill_instance(skill_id, skill_data)
        intent = skill.use(user, targets, context, level)
        
        # 获取技能类型用于能量回复
        skill_type = skill_data.get("type", "Normal")
        
        # 记录技能类型，用于天赋触发判断
        if hasattr(user, 'set_last_skill_type'):
            user.set_last_skill_type(skill_type)
        
        # 统一的处理分发
        handler_map = {
            "damage_only": self._handle_damage_only,
            "buff_only": self._handle_buff_only,
            "damage_before_buff": self._handle_damage_before_buff,
            "buff_before_damage": self._handle_buff_before_damage,
            "talent_enhance": self._handle_talent_enhance,
            "damage_with_progress_boost": self._handle_damage_with_progress_boost,
            "heal_only": self._handle_heal_only,
            "skip": self._handle_skip
        }
        
        handler = handler_map.get(intent["type"])
        if handler:
            return handler(user, targets, intent, skill_type)
        else:
            print(f"[警告] 未知的技能类型: {intent['type']}")
            return []

    # ===== 公共逻辑提取 =====
    
    def _apply_damage_to_target(self, user, target, multiplier, element, skill_type, skill_name="Unknown"):
        """统一的伤害处理逻辑"""
        dmg = damage_calc(user, target, multiplier, element)
        target_was_alive = target.is_alive()
        
        # 造成伤害
        if hasattr(target, "receive_damage"):
            target.receive_damage(dmg, attacker=user, skill_type=skill_type)
        
        # 削韧（仅对Enemy）
        if isinstance(target, Enemy):
            toughness_amount = self.toughness_damage_map.get(skill_type, 0)
            if toughness_amount > 0:
                target.reduce_toughness(toughness_amount, element=element, attacker=user)
        
        # 击杀检查
        if target_was_alive and not target.is_alive():
            user.on_enemy_killed()
        
        return {
            "target": target,
            "damage": dmg,
            "element": element,
            "skill_name": skill_name,
            "result_type": "damage"
        }
    
    def _apply_buff_to_target(self, target, buff, skill_name="Unknown"):
        """统一的Buff应用逻辑"""
        if not buff or not hasattr(target, "add_buff"):
            return None
            
        target.add_buff(buff)
        print(f"[Buff应用] {target.name} 获得Buff: {buff.name} (持续{buff.duration}回合)")
        
        return {
            "target": target,
            "buff": buff,
            "skill_name": skill_name,
            "result_type": "buff"
        }
    
    def _apply_heal_to_target(self, target, heal_amount, skill_name="Unknown"):
        """统一的治疗逻辑"""
        if not hasattr(target, "heal"):
            return None
            
        target.heal(heal_amount, source=skill_name)
        
        return {
            "target": target,
            "heal": heal_amount,
            "skill_name": skill_name,
            "result_type": "heal"
        }
    
    def _handle_action_progress_boost(self, user, intent):
        """统一的行动进度提升处理"""
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
    
    def _handle_extra_turn(self, user, intent):
        """处理额外回合逻辑"""
        if intent.get("extra_turn", False):
            print(f"[额外回合] {user.name} 获得额外回合！")
            if hasattr(user, 'set_extra_turn'):
                user.set_extra_turn(True)

    # ===== 简化后的处理函数 =====
    
    def _handle_damage_only(self, user, targets, intent, skill_type):
        """处理纯伤害技能"""
        results = []
        multiplier = intent.get("multiplier", 1.0)
        element = intent.get("element")
        skill_name = intent.get("skill_name", "Unknown")
        
        for target in targets:
            result = self._apply_damage_to_target(user, target, multiplier, element, skill_type, skill_name)
            results.append(result)
        
        return results

    def _handle_buff_only(self, user, targets, intent, skill_type):
        """处理纯Buff技能"""
        results = []
        buff = intent.get("buff")
        skill_name = intent.get("skill_name", "Unknown")
        
        for target in targets:
            result = self._apply_buff_to_target(target, buff, skill_name)
            if result:
                results.append(result)
        
        return results

    def _handle_buff_before_damage(self, user, targets, intent, skill_type):
        """处理先Buff后伤害的技能"""
        results = []
        
        # 先应用Buff
        buff_target = intent.get("buff_target", user)
        buff = intent.get("buff")
        skill_name = intent.get("skill_name", "Unknown")
        
        if buff:
            buff_result = self._apply_buff_to_target(buff_target, buff, skill_name)
            if buff_result:
                results.append(buff_result)
        
        # 再造成伤害
        multiplier = intent.get("multiplier", 1.0)
        element = intent.get("element")
        
        for target in targets:
            damage_result = self._apply_damage_to_target(user, target, multiplier, element, skill_type, skill_name)
            results.append(damage_result)
        
        return results

    def _handle_damage_before_buff(self, user, targets, intent, skill_type):
        """处理先伤害后Buff的技能"""
        results = []
        multiplier = intent.get("multiplier", 1.0)
        element = intent.get("element")
        buff = intent.get("buff")
        skill_name = intent.get("skill_name", "Unknown")
        
        for target in targets:
            # 先造成伤害
            damage_result = self._apply_damage_to_target(user, target, multiplier, element, skill_type, skill_name)
            results.append(damage_result)
            
            # 再应用Buff（如果有）
            if buff:
                buff_result = self._apply_buff_to_target(target, buff, skill_name)
                if buff_result:
                    results.append(buff_result)
        
        return results

    def _handle_heal_only(self, user, targets, intent, skill_type):
        """处理纯治疗技能"""
        # 治疗技能强制只能选择己方目标
        valid_targets = [t for t in targets if t.side == user.side]
        if not valid_targets:
            valid_targets = [user]  # 至少治疗自己
        
        results = []
        heal_amount = intent.get("heal_amount", 0)
        skill_name = intent.get("skill_name", "Unknown")
        
        for target in valid_targets:
            result = self._apply_heal_to_target(target, heal_amount, skill_name)
            if result:
                results.append(result)
        
        return results

    def _handle_damage_with_progress_boost(self, user, targets, intent, skill_type):
        """处理伤害+行动进度提升技能"""
        # 先造成伤害
        damage_results = self._handle_damage_only(user, targets, intent, skill_type)
        
        # 再处理行动进度提升
        self._handle_action_progress_boost(user, intent)
        
        return damage_results

    def _handle_talent_enhance(self, user, targets, intent, skill_type):
        """处理天赋强化效果"""
        results = []
        
        # 应用Buff
        buff_target = intent.get("buff_target", user)
        buff = intent.get("buff")
        skill_name = intent.get("skill_name", "Unknown")
        
        if buff:
            buff_result = self._apply_buff_to_target(buff_target, buff, skill_name)
            if buff_result:
                results.append(buff_result)
        
        # 处理额外回合
        self._handle_extra_turn(user, intent)
        
        return results

    def _handle_skip(self, user, targets, intent, skill_type):
        """处理跳过技能"""
        skill_name = intent.get("skill_name", "Unknown")
        print(f"[技能跳过] {user.name} 使用了未实装技能 [{skill_name}]，本回合跳过。")
        return []

# 在SkillManager中集成新的伤害系统
class SkillManagerWithNewDamage(SkillManager):
    """集成新伤害系统的SkillManager"""
    
    def __init__(self, skill_data_dict):
        super().__init__(skill_data_dict)
        self.damage_calculator = DamageCalculator()
    
    def _apply_damage_to_target(self, user, target, intent, skill_type):
        """使用新伤害系统的伤害处理"""
        # 确定伤害类型
        damage_type_map = {
            "Normal": DamageType.NORMAL,
            "BPSkill": DamageType.NORMAL,
            "Ultra": DamageType.ULTIMATE,
            "Talent": DamageType.FOLLOW_UP,
            "Break": DamageType.BREAK
        }
        damage_type = damage_type_map.get(skill_type, DamageType.NORMAL)
        
        # 计算伤害
        damage_instance = self.damage_calculator.calculate_damage(
            user, target, intent["multiplier"], intent["element"], damage_type
        )
        
        target_was_alive = target.is_alive()
        
        # 造成伤害
        if hasattr(target, "receive_damage"):
            target.receive_damage(
                damage_instance.final_damage, 
                attacker=user, 
                skill_type=skill_type,
                damage_instance=damage_instance
            )
        
        # 削韧（仅对Enemy）
        if isinstance(target, Enemy):
            toughness_amount = self.toughness_map.get(skill_type, 0)
            target.reduce_toughness(toughness_amount, element=intent.get("element"), attacker=user)
        
        # 击杀检查
        if target_was_alive and not target.is_alive():
            user.on_enemy_killed()
        
        return {
            "target": target,
            "damage": damage_instance.final_damage,
            "damage_instance": damage_instance,
            "element": intent["element"],
            "skill_name": intent["skill_name"],
            "desc": intent.get("desc", "")
        }
    
    def get_battle_damage_report(self) -> Dict:
        """获取战斗伤害报告"""
        return self.damage_calculator.get_damage_statistics()