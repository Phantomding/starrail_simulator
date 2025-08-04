# skill_manager.py (已修正)
import random
from .skill import get_skill_instance
from .effects import DamageEffect, HealEffect, BaseEffect
from starrail.core.enemy import Enemy
if False:
    from starrail.core.character import Character

def damage_calc_attack_side(user: 'Character', target, multiplier, element):
    atk = user.get_current_stats().get("ATK", 0) # 确保获取最新属性
    base_damage = atk * multiplier
    
    print(f"    [伤害计算] 基础伤害: {base_damage:.1f} (攻击力: {atk:.1f} × 倍率: {multiplier:.2f})")

    damage_bonus = 0
    element_penetration = 0
    current_stats = user.get_current_stats()

    if element:
        element_dmg = current_stats.get(f"{element} DMG", 0)
        damage_bonus += element_dmg
        if element_dmg > 0:
            print(f"    [伤害计算] 元素伤害加成: {element_dmg*100:.1f}%")
    
    skill_type = getattr(user, '_last_skill_type', 'Normal')
    if skill_type == "Ultra":
        ultimate_dmg = current_stats.get("Ultimate DMG%", 0)
        damage_bonus += ultimate_dmg
        if ultimate_dmg > 0:
            print(f"    [伤害计算] 终极技伤害加成: {ultimate_dmg*100:.1f}%")
    elif skill_type == "Follow-up":
        followup_dmg = current_stats.get("Follow-up DMG%", 0)
        damage_bonus += followup_dmg
        if followup_dmg > 0:
            print(f"    [伤害计算] 追击伤害加成: {followup_dmg*100:.1f}%")
    
    # 【关键修正】调用 get_damage_bonus 方法，而不是直接访问属性
    for buff in getattr(user, 'buffs', []):
        # 通过调用方法来获取动态或静态的伤害加成
        buff_dmg_bonus = buff.get_damage_bonus(user)
        buff_penetration = getattr(buff, 'element_penetration', 0)
        
        damage_bonus += buff_dmg_bonus
        element_penetration += buff_penetration

        # 对于静态Buff，仍然打印其固定值
        if not buff.dynamic_damage_bonus_func and buff_dmg_bonus > 0:
            print(f"    [伤害计算] {buff.name} 伤害加成: {buff_dmg_bonus*100:.1f}%")
        if buff_penetration > 0:
            print(f"    [伤害计算] {buff.name} 穿透加成: {buff_penetration*100:.1f}%")

    damage_modifier = 1 + damage_bonus
    print(f"    [伤害计算] 总伤害修正: {damage_modifier:.3f} (1 + {damage_bonus*100:.1f}%)")

    crit_rate = current_stats.get("CRIT Rate", 0.05)
    crit_dmg = current_stats.get("CRIT DMG", 0.5)
    is_crit = random.random() < crit_rate
    crit_modifier = 1 + crit_dmg if is_crit else 1
    
    print(f"    [伤害计算] 暴击率: {crit_rate*100:.1f}%, 暴击伤害: {crit_dmg*100:.1f}%")
    print(f"    [伤害计算] 暴击判定: {'是' if is_crit else '否'} (修正系数: {crit_modifier:.3f})")

    theory_damage = base_damage * damage_modifier * crit_modifier
    print(f"    [伤害计算] 理论伤害: {theory_damage:.1f}")
    
    return {
        "theory_damage": theory_damage, "element": element,
        "element_penetration": element_penetration, "is_crit": is_crit,
    }

# ... (文件其余部分保持不变) ...
def damage_calc_defense_side(theory_damage, user, target, element, element_penetration, is_break_damage=False):
    print(f"    [防御计算] 理论伤害: {theory_damage:.1f}")
    
    element_resistance = getattr(target, 'resistances', {}).get(element, 0)
    resistance_modifier = 1 - (element_resistance - element_penetration)
    print(f"    [防御计算] 属性抗性: {element_resistance*100:.1f}%, 穿透: {element_penetration*100:.1f}%")
    print(f"    [防御计算] 抗性修正: {resistance_modifier:.3f} (1 - {element_resistance*100:.1f}% + {element_penetration*100:.1f}%)")

    # 击破伤害跳过无视防御效果，但仍进行正常防御计算
    if is_break_damage:
        if hasattr(target, 'defense_reduction'):
            after_def = target.defense_reduction(theory_damage, user, target, skip_ignore_def=True)
            print(f"    [防御计算] 击破伤害跳过无视防御效果: {after_def:.1f}")
        else:
            after_def = theory_damage
            print(f"    [防御计算] 击破伤害无防御修正: {after_def:.1f}")
    else:
        if hasattr(target, 'defense_reduction'):
            after_def = target.defense_reduction(theory_damage, user, target)
            print(f"    [防御计算] 防御修正后: {after_def:.1f}")
        else:
            after_def = theory_damage
            print(f"    [防御计算] 无防御修正: {after_def:.1f}")

    independent_reduction = 1.0
    for buff in getattr(target, 'buffs', []):
        buff_reduction = getattr(buff, 'independent_damage_reduction', 0)
        independent_reduction *= (1 - buff_reduction)
        if buff_reduction > 0:
            print(f"    [防御计算] {buff.name} 独立减伤: {buff_reduction*100:.1f}%")
    
    if hasattr(target, 'toughness') and target.toughness is not None and target.toughness > 0:
        toughness_reduction = 0.1
        independent_reduction *= (1 - toughness_reduction)
        print(f"    [防御计算] 韧性减伤: {toughness_reduction*100:.1f}%")
    
    print(f"    [防御计算] 独立减伤修正: {independent_reduction:.3f}")

    damage_taken_bonus = 1.0
    for buff in getattr(target, 'buffs', []):
        buff_taken_increase = getattr(buff, 'damage_taken_increase', 0)
        damage_taken_bonus *= (1 + buff_taken_increase)
        if buff_taken_increase > 0:
            print(f"    [防御计算] {buff.name} 受到伤害增加: {buff_taken_increase*100:.1f}%")
    
    print(f"    [防御计算] 受到伤害修正: {damage_taken_bonus:.3f}")

    final_damage = after_def * resistance_modifier * independent_reduction * damage_taken_bonus
    print(f"    [防御计算] 最终伤害: {final_damage:.1f}")
    
    return final_damage

def full_damage_calc(user, target, multiplier, element, skill_type):
    user._last_skill_type = skill_type
    
    print(f"  [伤害计算开始] {user.name} 对 {target.name} 使用 {skill_type} 技能")
    
    attack_result = damage_calc_attack_side(user, target, multiplier, element)
    final_damage = damage_calc_defense_side(
        attack_result["theory_damage"], user, target, element, attack_result["element_penetration"]
    )
    print(f"  -> [伤害结算] {user.name} 对 {target.name} 造成 {final_damage:.1f} 点伤害 ({'暴击' if attack_result['is_crit'] else '非暴击'})")
    
    target_was_alive = target.is_alive()
    if hasattr(target, "receive_damage"):
        target.receive_damage(final_damage, attacker=user, skill_type=skill_type)
        
    if hasattr(user, 'light_cone') and user.light_cone and user.light_cone.skill_instance:
        if hasattr(user.light_cone.skill_instance, 'on_damage_dealt'):
            user.light_cone.skill_instance.on_damage_dealt(user, final_damage, skill_type)
    
    if isinstance(target, Enemy):
        toughness_map = {"Normal": 10, "BPSkill": 20, "Ultra": 30}
        toughness_amount = toughness_map.get(skill_type, 0)
        target.reduce_toughness(toughness_amount, element=element, attacker=user)
        
    if target_was_alive and not target.is_alive():
        if hasattr(user, "on_enemy_killed"):
            user.on_enemy_killed()

    return final_damage

def calculate_final_heal(user, base_heal_amount, skill_type):
    healing_bonus = user.get_current_stats().get("Outgoing Healing Boost", 0)
    light_cone_healing_bonus = 0
    
    if hasattr(user, 'light_cone') and user.light_cone and user.light_cone.skill_instance:
        if hasattr(user.light_cone.skill_instance, 'get_healing_bonus'):
            light_cone_healing_bonus = user.light_cone.skill_instance.get_healing_bonus(skill_type)
    
    talent_bonus = 0

    final_bonus = 1 + healing_bonus + light_cone_healing_bonus + talent_bonus
    print(f"    [治疗计算] 基础治疗: {base_heal_amount:.1f}, 治疗加成: {final_bonus*100-100:.1f}% (角色加成: {healing_bonus*100:.1f}%, 光锥加成: {light_cone_healing_bonus*100:.1f}%)")
    
    return base_heal_amount * final_bonus

class SkillManager:
    def __init__(self, skill_data_dict):
        self.skill_data_dict = skill_data_dict

    def use_skill(self, skill_id, user, targets, context, level=1):
        skill_data = self.skill_data_dict.get(skill_id)
        
        if not skill_data and skill_id == "default_attack":
            from starrail.core.skills.base_skill import BaseSkill
            skill = BaseSkill.create_default_attack(user)
        elif not skill_data:
            print(f"[错误] 找不到技能ID: {skill_id}")
            return
        else:
            skill = get_skill_instance(skill_id, skill_data)
        
        if hasattr(user, 'set_last_skill_type'):
            user.set_last_skill_type(skill.type)
        
        print(f"\n[{user.name}] 使用技能: [{skill.name}]")
        
        effects = skill.use(user, targets, context, level)
        
        for effect in effects:
            if isinstance(effect, DamageEffect):
                effect.execute(damage_calc_func=full_damage_calc)
            elif isinstance(effect, HealEffect):
                effect.execute(calculate_final_heal_func=calculate_final_heal)
            else:
                effect.execute()

    def process_turn_start_buffs(self, character, context):
        if not hasattr(character, "buffs"):
            return

        for buff in character.buffs[:]: 
            if buff.on_turn_start_data:
                data = buff.on_turn_start_data
                
                if data.get("type") == "heal_from_caster":
                    caster = next((c for c in context.characters if c.id == data["caster_id"]), None)
                    if caster:
                        print(f"  -> [回合开始Buff] {character.name} 的持续治疗Buff '{buff.name}' 生效")
                        caster_max_hp = caster.get_max_hp()
                        base_heal = data["heal_ratio"] * caster_max_hp + data["heal_base"]
                        
                        heal_effect = HealEffect(caster, [character], context, base_heal)
                        # 为持续治疗传递特殊技能类型，避免享受终结技加成
                        heal_effect.execute(calculate_final_heal_func=lambda user, base_heal, skill_type: calculate_final_heal(user, base_heal, "HealOverTime"))

def break_damage_calc(attacker, target, break_damage, element):
    print(f"  -> [击破伤害结算] 基础击破伤害: {break_damage:.1f}")
    return damage_calc_defense_side(
        break_damage, attacker, target, element, element_penetration=0, is_break_damage=True
    )