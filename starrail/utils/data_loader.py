# updated_data_loader.py
import json
import os
from starrail.core.character import Character
from starrail.core.enemy import Enemy
from starrail.core.light_cones.light_cone import LightCone
from starrail.core.relics.relic import Relic

def load_json(path):
    """加载JSON文件"""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_skills(path):
    """加载技能数据"""
    data = load_json(path)
    return {item['id']: item for item in data}

def load_light_cones(light_cones_path, light_cone_skills_path=None):
    """加载光锥数据"""
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
            skill_data=skill_data
        )
    return light_cones

PERCENT_STATS = {
    "CRIT Rate", "CRIT DMG", "Effect Hit Rate", "Effect RES",
    "Break Effect", "Outgoing Healing Boost", "Energy Regeneration Rate"
}

def normalize_stat(stat, value):
    """标准化属性值"""
    if stat in PERCENT_STATS and value > 1:
        return value / 100
    return value

def load_relics(path):
    """加载遗器数据"""
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
    """加载角色数据"""
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
                max_sp=max_sp
            ))
    return characters

def load_processed_enemies(path):
    """加载处理后的敌人数据"""
    try:
        data = load_json(path)
        enemies = []
        
        for item in data:
            # 创建敌人对象
            enemy = Enemy(
                id=item['id'],
                name=item['name'],
                stats=item['stats'],
                skills=item.get('skills', []),
                side='enemy',
                weaknesses=item.get('weaknesses', []),
                resistances=item.get('resistances', {}),
                toughness=item.get('toughness', 100),
                max_toughness=item.get('max_toughness', 100),
                ai_type=item.get('ai_info', {}).get('path', 'default')
            )
            
            # 设置额外的属性
            enemy.rank = item.get('rank', 'Unknown')
            enemy.elite_group = item.get('elite_group', 1)
            
            # 设置AI相关信息
            if 'ai_info' in item:
                enemy.ai_info = item['ai_info']
            
            enemies.append(enemy)
            
        print(f"✅ 成功加载 {len(enemies)} 个敌人")
        return enemies
        
    except Exception as e:
        print(f"❌ 加载敌人数据失败: {e}")
        return []

def load_enemy_templates(path):
    """加载敌人模板数据（用于创建新的敌人实例）"""
    try:
        data = load_json(path)
        templates = {}
        
        for item in data:
            template_id = item.get('template_id') or item.get('id')
            if template_id:
                templates[template_id] = item
        
        print(f"✅ 成功加载 {len(templates)} 个敌人模板")
        return templates
        
    except Exception as e:
        print(f"❌ 加载敌人模板失败: {e}")
        return {}

def create_enemy_from_template(template_data, custom_stats=None, custom_name=None):
    """从模板创建敌人实例"""
    if not template_data:
        return None
    
    # 使用自定义属性或模板默认属性
    stats = custom_stats if custom_stats else template_data.get('stats', {})
    name = custom_name if custom_name else template_data.get('name', 'Unknown Enemy')
    
    enemy = Enemy(
        id=template_data['id'],
        name=name,
        stats=stats,
        skills=template_data.get('skills', []),
        side='enemy',
        weaknesses=template_data.get('weaknesses', []),
        resistances=template_data.get('resistances', {}),
        toughness=template_data.get('toughness', 100),
        max_toughness=template_data.get('max_toughness', 100),
        ai_type=template_data.get('ai_info', {}).get('path', 'default')
    )
    
    # 设置额外的属性
    enemy.rank = template_data.get('rank', 'Unknown')
    enemy.elite_group = template_data.get('elite_group', 1)
    
    return enemy

def load_all_game_data(data_path):
    """加载所有游戏数据的便捷函数"""
    try:
        print("📂 开始加载游戏数据...")
        
        # 加载基础数据
        skills_data = load_skills(os.path.join(data_path, 'skills.json'))
        light_cones_data = load_light_cones(
            os.path.join(data_path, 'light_cones.json'),
            os.path.join(data_path, 'light_cone_skills.json')
        )
        relics_data = load_relics(os.path.join(data_path, 'fribbels-optimizer-save.json'))
        
        # 加载角色数据
        characters_data = load_characters(
            os.path.join(data_path, 'characters.json'),
            skills_data,
            light_cones_data
        )
        
        # 加载敌人数据（优先使用处理后的数据）
        processed_enemies_path = os.path.join(data_path, 'processed_enemies.json')
        enemies_data = []
        
        if os.path.exists(processed_enemies_path):
            enemies_data = load_processed_enemies(processed_enemies_path)
        else:
            print("⚠️  未找到处理后的敌人数据，使用默认敌人配置")
            # 可以在这里添加默认敌人或从其他源加载
        
        # 加载敌人模板（可选）
        enemy_templates_path = os.path.join(data_path, 'processed_enemies.json')
        enemy_templates = {}
        if os.path.exists(enemy_templates_path):
            enemy_templates = load_enemy_templates(enemy_templates_path)
        
        print(f"✅ 游戏数据加载完成:")
        print(f"   技能: {len(skills_data)} 个")
        print(f"   角色: {len(characters_data)} 个")
        print(f"   光锥: {len(light_cones_data)} 个")
        print(f"   遗器: {len(relics_data)} 个")
        print(f"   敌人: {len(enemies_data)} 个")
        print(f"   敌人模板: {len(enemy_templates)} 个")
        
        return {
            'skills': skills_data,
            'characters': characters_data,
            'light_cones': light_cones_data,
            'relics': relics_data,
            'enemies': enemies_data,
            'enemy_templates': enemy_templates
        }
        
    except Exception as e:
        print(f"❌ 游戏数据加载失败: {e}")
        raise