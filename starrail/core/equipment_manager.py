# equipment_manager.py
import os
import json
from starrail.core.relics.relic_set_skill import RelicSetSkillFactory

def equip_light_cone(character, light_cone):
    character.light_cone = light_cone

def unequip_light_cone(character):
    character.light_cone = None

def equip_relic(character, relic):
    if not hasattr(character, 'relics') or character.relics is None:
        character.relics = []
    # 检查是否已有同部位遗器
    for r in character.relics:
        if r.slot == relic.slot:
            print(f"角色已装备{relic.slot}部位的遗器，不能重复装备。")
            return False
    if len(character.relics) >= 6:
        print("角色最多只能装备6个遗器。")
        return False
    character.relics.append(relic)
    return True

def unequip_relic_by_slot(character, slot):
    if hasattr(character, 'relics') and character.relics:
        character.relics = [r for r in character.relics if r.slot != slot]

def normalize_path(p):
    # 规范化命途名称，用于比较
    return str(p).strip().lower() if p else ""

def calc_total_stats(character):
    """
    重新设计的属性计算逻辑：
    1. 基础属性 = 角色基础属性 + 光锥基础属性
    2. 百分比加成只作用于基础属性
    3. 遗器固定加成不参与百分比计算，最后直接加算
    4. 行迹固定加成也不参与百分比计算
    """
    # 1. 基础属性（只包含角色本身和光锥的基础属性）
    base_stats = character.stats.copy()
    if hasattr(character, 'light_cone') and character.light_cone and hasattr(character.light_cone, 'stats'):
        for k, v in character.light_cone.stats.items():
            if k in ["HP", "ATK", "DEF", "SPD"]:
                base_stats[k] = base_stats.get(k, 0) + v
            else:
                base_stats[k] = base_stats.get(k, 0) + v
    
    # 2. 百分比加成（只作用于基础属性）
    percent_stats = {}
    percent_fields = ["HP%", "ATK%", "DEF%", "SPD%"]
    
    # 光锥百分比属性
    if hasattr(character, 'light_cone') and character.light_cone and hasattr(character.light_cone, 'stats'):
        for k, v in character.light_cone.stats.items():
            if k in percent_fields or k.endswith("%"):
                percent_stats[k] = percent_stats.get(k, 0) + (v / 100 if v > 1 else v)
    
    # 光锥技能效果（需要命途匹配）
    if hasattr(character, 'light_cone') and character.light_cone and hasattr(character.light_cone, 'skill'):
        light_cone = character.light_cone
        if light_cone.skill and normalize_path(character.path) == normalize_path(light_cone.path):
            # 命途匹配，应用光锥技能效果
            if hasattr(light_cone, 'skill_instance') and light_cone.skill_instance:
                # 获取基础属性加成
                base_skill_stats = light_cone.skill_instance.get_base_stats()
                for k, v in base_skill_stats.items():
                    if k in percent_fields or k.endswith("%"):
                        percent_stats[k] = percent_stats.get(k, 0) + v
                    else:
                        base_stats[k] = base_stats.get(k, 0) + v
    
    # 3. 遗器固定加成（不参与百分比计算）
    flat_bonus = {"HP": 0, "ATK": 0, "DEF": 0, "SPD": 0}
    relics = getattr(character, 'relics', [])
    if relics:
        for relic in relics:
            # 主属性
            for k, v in relic.main_stat.items():
                if k in ["HP", "ATK", "DEF", "SPD"]:
                    flat_bonus[k] = flat_bonus.get(k, 0) + v
                elif k in percent_fields or k.endswith("%"):
                    percent_stats[k] = percent_stats.get(k, 0) + (v / 100 if v > 1 else v)
                else:
                    base_stats[k] = base_stats.get(k, 0) + v
            # 副属性
            for sub in getattr(relic, 'sub_stats', []):
                if isinstance(sub, dict):
                    subk = sub.get('stat')
                    subv = sub.get('value')
                    if subk and subv is not None:
                        if subk in ["HP", "ATK", "DEF", "SPD"]:
                            flat_bonus[subk] = flat_bonus.get(subk, 0) + subv
                        elif subk in percent_fields or subk.endswith("%"):
                            percent_stats[subk] = percent_stats.get(subk, 0) + (subv / 100 if subv > 1 else subv)
                        else:
                            base_stats[subk] = base_stats.get(subk, 0) + subv
    
    # 4. 行迹固定加成（不参与百分比计算）
    trace_flat_bonus = {"HP": 0, "ATK": 0, "DEF": 0, "SPD": 0}
    if hasattr(character, 'traces') and character.traces:
        for k, v in character.traces.items():
            if k in ["HP", "ATK", "DEF", "SPD"]:
                trace_flat_bonus[k] = trace_flat_bonus.get(k, 0) + v
            elif k in percent_fields or k.endswith("%"):
                percent_stats[k] = percent_stats.get(k, 0) + v
            else:
                base_stats[k] = base_stats.get(k, 0) + v
    
    # 5. 遗器套装效果
    set_counter = {}
    for relic in relics:
        if relic.set_name:
            set_counter[relic.set_name] = set_counter.get(relic.set_name, 0) + 1
    
    # 激活套装效果（只考虑2件/4件套）
    relic_skills_path = os.path.join(os.path.dirname(__file__), '../../data/relic_skills.json')
    active_sets = {}
    complex_effects = {}  # 复杂效果，用于战斗内结算
    relic_set_skills = []  # 遗器套装技能实例
    
    # 创建临时角色对象用于检查战斗效果
    class TempCharacter:
        def __init__(self):
            self.spd = 0
    
    # 加载遗器套装数据
    if os.path.exists(relic_skills_path):
        with open(relic_skills_path, encoding='utf-8') as f:
            relic_data = json.load(f)
        
        for set_name, count in set_counter.items():
            # 查找套装数据
            set_data = None
            for entry in relic_data:
                if entry.get('name') == set_name:
                    set_data = entry
                    break
            
            if set_data:
                description = set_data.get('skills', '')
                skill_instance = RelicSetSkillFactory.create_skill(set_name, description, level=1)
                
                if count >= 4:
                    if skill_instance:
                        # 获取基础属性加成
                        base_skill_stats = skill_instance.get_base_stats()
                        if base_skill_stats:
                            active_sets[f'{set_name} (4)'] = base_skill_stats
                            # 应用套装加成到percent_stats
                            for k, v in base_skill_stats.items():
                                if k in percent_fields or k.endswith("%"):
                                    percent_stats[k] = percent_stats.get(k, 0) + v
                                else:
                                    base_stats[k] = base_stats.get(k, 0) + v
                        relic_set_skills.append(skill_instance)
                        # 检查是否有复杂效果（通过技能实例判断）
                        if hasattr(skill_instance, 'get_battle_effects'):
                            temp_char = TempCharacter()
                            battle_effects = skill_instance.get_battle_effects(temp_char)
                            if battle_effects:
                                complex_effects[f'{set_name} (4)'] = description
                elif count >= 2:
                    if skill_instance:
                        # 获取基础属性加成
                        base_skill_stats = skill_instance.get_base_stats()
                        if base_skill_stats:
                            active_sets[f'{set_name} (2)'] = base_skill_stats
                            # 应用套装加成到percent_stats
                            for k, v in base_skill_stats.items():
                                if k in percent_fields or k.endswith("%"):
                                    percent_stats[k] = percent_stats.get(k, 0) + v
                                else:
                                    base_stats[k] = base_stats.get(k, 0) + v
                        relic_set_skills.append(skill_instance)
                        # 检查是否有复杂效果（通过技能实例判断）
                        if hasattr(skill_instance, 'get_battle_effects'):
                            temp_char = TempCharacter()
                            battle_effects = skill_instance.get_battle_effects(temp_char)
                            if battle_effects:
                                complex_effects[f'{set_name} (2)'] = description
    
    # 将遗器套装技能实例保存到角色身上
    if relic_set_skills:
        character.relic_set_skills = relic_set_skills
    
    # 合并所有固定加成
    total_flat_bonus = {}
    for k in ["HP", "ATK", "DEF", "SPD"]:
        total_flat_bonus[k] = flat_bonus.get(k, 0) + trace_flat_bonus.get(k, 0)
    
    return base_stats, percent_stats, total_flat_bonus, active_sets, complex_effects 