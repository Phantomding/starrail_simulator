# data_loader.py
import json
import os
from starrail.core.character import Character
from starrail.core.light_cones.light_cone import LightCone
from starrail.core.relics.relic import Relic

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_skills(path):
    data = load_json(path)
    return {item['id']: item for item in data}

def load_light_cones(light_cones_path, light_cone_skills_path=None):
    data = load_json(light_cones_path)
    skills = {}
    if light_cone_skills_path:
        skill_data = load_json(light_cone_skills_path)
        for item in skill_data:
            skills[item['id']] = item
    light_cones = {}
    for item in data:
        skill_data = skills.get(item.get('skill_id')) if skills else None
        light_cones[item['id']] = LightCone(
            id=item['id'],
            name=item['name'],
            stats=item.get('stats', {}),
            skill=skill_data,
            path=item.get('path'),
            skill_data=skill_data  # 传递技能数据
        )
    return light_cones

PERCENT_STATS = {
    "CRIT Rate", "CRIT DMG", "Effect Hit Rate", "Effect RES",
    "Break Effect", "Outgoing Healing Boost", "Energy Regeneration Rate"
}

def normalize_stat(stat, value):
    if stat in PERCENT_STATS and value > 1:
        return value / 100
    return value

def load_relics(path):
    data = load_json(path)
    if isinstance(data, dict) and "relics" in data:
        data = data["relics"]
    relics = {}
    for item in data:
        # 兼容主属性格式
        main_stat = {}
        if "main" in item and "stat" in item["main"] and "value" in item["main"]:
            stat = item["main"]["stat"]
            value = item["main"]["value"]
            main_stat[stat] = normalize_stat(stat, value)
        # 兼容副属性格式
        sub_stats = []
        if "substats" in item:
            for sub in item["substats"]:
                if isinstance(sub, dict) and "stat" in sub and "value" in sub:
                    stat = sub["stat"]
                    value = sub["value"]
                    sub_stats.append({"stat": stat, "value": normalize_stat(stat, value)})
        elif "sub_stats" in item:
            for sub in item["sub_stats"]:
                if isinstance(sub, dict) and "stat" in sub and "value" in sub:
                    stat = sub["stat"]
                    value = sub["value"]
                    sub_stats.append({"stat": stat, "value": normalize_stat(stat, value)})
        relics[item['id']] = Relic(
            id=item['id'],
            name=item.get('name', item.get('set', '')),
            main_stat=main_stat,
            sub_stats=sub_stats,
            set_name=item.get('set'),
            slot=item.get('part')
        )
    return relics

def load_characters(path, skills_dict, light_cones_dict=None):
    from starrail.core.enemy import Enemy
    data = load_json(path)
    characters = []
    for item in data:
        # 只保留技能ID列表
        char_skills = item['skills']
        side = item.get('side', 'player')
        light_cone = None
        if light_cones_dict and item.get('light_cone'):
            light_cone = light_cones_dict.get(item['light_cone'])
        
        # 处理stats，max_sp现在在根级别
        stats = item['stats'].copy()
        max_sp = item.get('max_sp', 100)  # 从根级别获取max_sp，默认100
        
        if side == 'enemy':
            characters.append(Enemy(
                id=item['id'],
                name=item['name'],
                stats=stats,
                skills=char_skills,
                side=side,
                drop=item.get('drop'),
                ai_type=item.get('ai_type', 'default'),
                light_cone=light_cone,
                weaknesses=item.get('weaknesses', []),
                resistances=item.get('resistances', {}),
            ))
        else:
            characters.append(Character(
                id=item['id'],
                name=item['name'],
                stats=stats,
                skills=char_skills,
                side=side,
                light_cone=light_cone,
                path=item.get('path'),
                traces=item['traces'],
                max_sp=max_sp  # 传递max_sp参数
            ))
    return characters 