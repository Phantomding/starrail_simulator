# equipment_manager.py
import os
import json
from starrail.core.relics.relic_set_skill import RelicSetSkillFactory

class RelicManager:
    """遗器管理器 - 提供遗器筛选、套装管理、推荐等功能"""
    
    def __init__(self, relics_data):
        self.relics = relics_data
        self.relics_by_slot = self._organize_relics_by_slot()
        self.relics_by_set = self._organize_relics_by_set()
    
    def _organize_relics_by_slot(self):
        """按部位组织遗器"""
        organized = {
            "Head": [],
            "Hands": [],
            "Body": [],
            "Feet": [],
            "PlanarSphere": [],
            "LinkRope": []
        }
        for relic in self.relics.values():
            if hasattr(relic, 'slot') and relic.slot in organized:
                organized[relic.slot].append(relic)
        return organized
    
    def _organize_relics_by_set(self):
        """按套装组织遗器"""
        organized = {}
        for relic in self.relics.values():
            if hasattr(relic, 'set_name') and relic.set_name:
                if relic.set_name not in organized:
                    organized[relic.set_name] = []
                organized[relic.set_name].append(relic)
        return organized
    
    def get_relics_by_slot(self, slot):
        """获取指定部位的所有遗器"""
        return self.relics_by_slot.get(slot, [])
    
    def get_relics_by_set(self, set_name):
        """获取指定套装的所有遗器"""
        return self.relics_by_set.get(set_name, [])
    
    def get_relics_by_main_stat(self, slot, main_stat):
        """获取指定部位和主属性的遗器"""
        relics = self.get_relics_by_slot(slot)
        return [r for r in relics if hasattr(r, 'main_stat') and r.main_stat.get('stat') == main_stat]
    
    def get_relics_by_sub_stats(self, slot, sub_stats):
        """获取指定部位和副属性的遗器"""
        relics = self.get_relics_by_slot(slot)
        matching_relics = []
        for relic in relics:
            if hasattr(relic, 'sub_stats'):
                relic_sub_stats = [sub.get('stat') for sub in relic.sub_stats if sub.get('stat')]
                if all(stat in relic_sub_stats for stat in sub_stats):
                    matching_relics.append(relic)
        return matching_relics
    
    def get_best_relics_for_character(self, character, slot, priority_stats=None):
        """为角色推荐指定部位的最佳遗器"""
        if priority_stats is None:
            # 根据角色类型设置默认优先级
            if hasattr(character, 'path'):
                if character.path == "Hunt":
                    priority_stats = ["CRIT DMG", "CRIT Rate", "ATK%", "SPD"]
                elif character.path == "Destruction":
                    priority_stats = ["CRIT DMG", "CRIT Rate", "ATK%", "HP%"]
                elif character.path == "Harmony":
                    priority_stats = ["SPD", "Effect Hit Rate", "HP%", "DEF%"]
                elif character.path == "Nihility":
                    priority_stats = ["Effect Hit Rate", "SPD", "ATK%", "HP%"]
                elif character.path == "Preservation":
                    priority_stats = ["DEF%", "HP%", "Effect RES", "SPD"]
                elif character.path == "Abundance":
                    priority_stats = ["HP%", "Outgoing Healing Boost", "SPD", "Effect RES"]
                else:
                    priority_stats = ["ATK%", "CRIT DMG", "CRIT Rate", "SPD"]
            else:
                priority_stats = ["ATK%", "CRIT DMG", "CRIT Rate", "SPD"]
        
        relics = self.get_relics_by_slot(slot)
        scored_relics = []
        
        for relic in relics:
            score = 0
            # 主属性评分
            if hasattr(relic, 'main_stat'):
                main_stat = relic.main_stat.get('stat')
                if main_stat in priority_stats:
                    score += priority_stats.index(main_stat) * 10
            
            # 副属性评分
            if hasattr(relic, 'sub_stats'):
                for sub_stat in relic.sub_stats:
                    stat_name = sub_stat.get('stat')
                    if stat_name in priority_stats:
                        score += (len(priority_stats) - priority_stats.index(stat_name)) * 2
            
            scored_relics.append((relic, score))
        
        # 按评分排序
        scored_relics.sort(key=lambda x: x[1], reverse=True)
        return [relic for relic, score in scored_relics]
    
    def get_set_recommendations(self, character):
        """为角色推荐遗器套装"""
        recommendations = []
        
        if hasattr(character, 'path'):
            if character.path == "Hunt":
                recommendations.extend([
                    ("Eagle of Twilight Line", "暴击和速度加成，适合输出角色"),
                    ("Inert Salsotto", "暴击和暴击伤害加成"),
                    ("Rutilant Arena", "暴击和技能伤害加成")
                ])
            elif character.path == "Destruction":
                recommendations.extend([
                    ("The Ashblazing Grand Duke", "暴击和暴击伤害加成"),
                    ("Inert Salsotto", "暴击和暴击伤害加成"),
                    ("Rutilant Arena", "暴击和技能伤害加成")
                ])
            elif character.path == "Harmony":
                recommendations.extend([
                    ("Messenger Traversing Hackerspace", "速度和团队增益"),
                    ("Fleet of the Ageless", "速度和团队增益"),
                    ("Broken Keel", "效果抵抗和团队增益")
                ])
            elif character.path == "Nihility":
                recommendations.extend([
                    ("Pioneer Diver of Dead Waters", "效果命中和伤害加成"),
                    ("Thief of Shooting Meteor", "效果命中和击破效率"),
                    ("Pan-Cosmic Commercial Enterprise", "效果命中和团队增益")
                ])
            elif character.path == "Preservation":
                recommendations.extend([
                    ("Guard of Wuthering Snow", "防御和护盾加成"),
                    ("Belobog of the Architects", "防御和护盾加成"),
                    ("Broken Keel", "效果抵抗和团队增益")
                ])
            elif character.path == "Abundance":
                recommendations.extend([
                    ("Passerby of Wandering Cloud", "治疗效果加成"),
                    ("Fleet of the Ageless", "速度和团队增益"),
                    ("Broken Keel", "效果抵抗和团队增益")
                ])
        
        return recommendations

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
            if k in percent_fields or k.endswith("%") or k.endswith("DMG") or k.endswith("DMG Boost"):
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
                elif k in percent_fields or k.endswith("%") or k.endswith("DMG") or k.endswith("DMG Boost"):
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
                        elif subk in percent_fields or subk.endswith("%") or subk.endswith("DMG") or subk.endswith("DMG Boost"):
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