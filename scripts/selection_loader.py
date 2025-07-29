import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import json
from starrail.utils.data_loader import load_skills, load_characters, load_light_cones, load_relics
from starrail.core.enemy import Enemy
from starrail.core.equipment_manager import calc_total_stats
from starrail.core.skills.buff import Buff
from starrail.core.skills.skill import get_skill_instance

# 新增：加载skills.json为字典
with open(os.path.join(os.path.dirname(__file__), '../data/skills.json'), encoding='utf-8') as f:
    skills_json_data = json.load(f)
skill_data_dict = {entry['id']: entry for entry in skills_json_data}

def load_selection(selection_path, characters_path, skills_path, light_cones_path, light_cone_skills_path, relics_path):
    """
    加载选择文件，返回（角色对象列表, 敌人对象列表）
    只支持新的字典格式遗器配置
    """
    with open(selection_path, encoding='utf-8') as f:
        selection = json.load(f)
    # 加载数据
    skills = load_skills(skills_path)
    light_cones = load_light_cones(light_cones_path, light_cone_skills_path)
    relics = load_relics(relics_path)
    characters = load_characters(characters_path, skills, light_cones)
    # 角色选择
    team_objs = []
    for member in selection.get('team', []):
        char = next((c for c in characters if c.id == member.get('id') or c.name == member.get('name')), None)
        if char:
            # 装备光锥
            if 'light_cone' in member:
                lc = light_cones.get(member['light_cone'])
                if lc:
                    char.light_cone = lc
            # 装备遗器 - 只支持新格式（字典格式）
            if 'relics' in member:
                relics_config = member['relics']
                mapped_relics = []
                
                # 检查是否为字典格式
                if isinstance(relics_config, dict):
                    slot_map = {
                        "Head": 0, "Hands": 1, "Body": 2, 
                        "Feet": 3, "PlanarSphere": 4, "LinkRope": 5
                    }
                    
                    for slot, relic_id in relics_config.items():
                        if relic_id.startswith('r') and relic_id[1:].isdigit():
                            slot_idx = int(relic_id[1:]) - 1
                            if 0 <= slot_idx < 6:
                                # 查找对应部位的遗器
                                relic = next((r for r in relics.values() if getattr(r, 'slot', None) == slot), None)
                                if relic:
                                    mapped_relics.append(relic)
                        elif relic_id in relics:
                            mapped_relics.append(relics[relic_id])
                
                # 如果不是字典格式，给出错误提示
                else:
                    print(f"⚠️  警告: {char.name} 的遗器配置格式不正确，应为字典格式")
                    print(f"   当前格式: {type(relics_config)}")
                    print(f"   正确格式示例:")
                    print(f"   'relics': {{")
                    print(f"     'Head': 'r1',")
                    print(f"     'Hands': 'r2',")
                    print(f"     'Body': 'r3',")
                    print(f"     'Feet': 'r4',")
                    print(f"     'PlanarSphere': 'r5',")
                    print(f"     'LinkRope': 'r6'")
                    print(f"   }}")
                    mapped_relics = []
                
                char.relics = mapped_relics
                
                # 显示遗器装备信息
                if mapped_relics:
                    print(f"为 {char.name} 装备了 {len(mapped_relics)} 件遗器:")
                    for relic in mapped_relics:
                        slot = getattr(relic, 'slot', 'Unknown')
                        set_name = getattr(relic, 'set_name', 'Unknown')
                        print(f"  {slot}: {set_name}")
                else:
                    print(f"⚠️  {char.name} 没有装备任何遗器")
            
            # 新增：将技能ID映射为新技能实例
            if hasattr(char, 'skills') and isinstance(char.skills, list):
                new_skills = []
                for skill_id in char.skills:
                    skill_data = skill_data_dict.get(skill_id)
                    if skill_data:
                        new_skills.append(get_skill_instance(skill_id, skill_data))
                char.skills = new_skills
            
            # 显示角色配置信息
            if 'notes' in member:
                print(f"角色配置说明: {member['notes']}")
            
            team_objs.append(char)
    # 敌人选择
    enemy_objs = []
    for enemy in selection.get('enemies', []):
        enemy_obj = Enemy(
            id=enemy.get('id', ''),
            name=enemy['name'],
            stats=enemy['stats'],
            skills=[],
            traces=enemy.get('traces', {}),
            weaknesses=enemy.get('weaknesses', []),
            resistances=enemy.get('resistances', {}),
            toughness=enemy.get('toughness', 100),
            max_toughness=enemy.get('max_toughness', 100)
        )
        enemy_objs.append(enemy_obj)
    
    # 显示全局配置信息
    if 'notes' in selection:
        print("\n=== 配置信息 ===")
        notes = selection['notes']
        if 'team_composition' in notes:
            print(f"队伍组成: {notes['team_composition']}")
        if 'strategy' in notes:
            print(f"战斗策略: {notes['strategy']}")
        if 'relic_mapping' in notes:
            print("\n遗器映射:")
            for relic_id, description in notes['relic_mapping'].items():
                print(f"  {relic_id}: {description}")
    
    return team_objs, enemy_objs

# 用法示例（可注释掉）
if __name__ == '__main__':
    base = os.path.dirname(__file__)
    team, enemies = load_selection(
        selection_path=os.path.join(base, 'selection_template.json'),
        characters_path=os.path.join(base, '../data/characters.json'),
        skills_path=os.path.join(base, '../data/skills.json'),
        light_cones_path=os.path.join(base, '../data/light_cones.json'),
        light_cone_skills_path=os.path.join(base, '../data/light_cone_skills.json'),
        relics_path=os.path.join(base, '../data/fribbels-optimizer-save.json'),
    )
    print('===== 角色详细信息 =====')
    for c in team:
        print(f"ID: {getattr(c, 'id', None)}  Name: {c.name}")
        print(f"  Stats: {c.stats}")
        print(f"  Light Cone: {getattr(c.light_cone, 'name', None) if getattr(c, 'light_cone', None) else None}")
        print(f"  Relics: {[getattr(r, 'name', str(r)) for r in getattr(c, 'relics', [])]}")
        print(f"  Traces: {getattr(c, 'traces', {})}")
        # 计算并展示面板属性（包含遗器/光锥/套装加成）
        base_stats, percent_stats, flat_bonus, active_sets, complex_effects = calc_total_stats(c)
        flat_bonus = {k: float(v) for k, v in flat_bonus.items()}  # 修复类型
        relic_buffs = Buff.apply_relic_set_buffs(getattr(c, 'relics', []), active_sets)
        final_stats = Buff.finalize_stats(base_stats, percent_stats, flat_bonus, buffs=relic_buffs)
        print(f"  面板属性(结算后): {final_stats}")
        print()
    print('===== 敌人详细信息 =====')
    for e in enemies:
        print(f"ID: {getattr(e, 'id', None)}  Name: {e.name}")
        print(f"  Stats: {e.stats}")
        print(f"  Weaknesses: {getattr(e, 'weaknesses', [])}")
        print(f"  Resistances: {getattr(e, 'resistances', {})}")
        print(f"  Toughness: {getattr(e, 'toughness', 100)}/{getattr(e, 'max_toughness', 100)}")
        if hasattr(e, 'notes'):
            print(f"  Notes: {e.notes}")
        print() 