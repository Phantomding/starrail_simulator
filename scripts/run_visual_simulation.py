#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可视化配置战斗模拟器 - 从可视化选择器生成的配置运行战斗模拟
"""

import sys
import os
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from starrail.core.battle import Battle
from starrail.core.character import Character
from starrail.core.enemy import Enemy
from starrail.utils.data_loader import load_skills, load_characters, load_light_cones, load_relics
from starrail.core.equipment_manager import calc_total_stats
from starrail.core.skills.buff import Buff
from starrail.core.skills.skill import get_skill_instance

def load_visual_config(config_path):
    """加载可视化配置"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return None

def create_characters_from_config(config, characters_data, skills_data, light_cones_data, relics_data):
    """从配置创建角色对象"""
    team = []
    
    for member in config.get('team', []):
        char_id = member.get('id')
        char_name = member.get('name', 'Unknown')
        
        # 查找角色数据
        char_data = next((c for c in characters_data if c.id == char_id), None)
        if not char_data:
            print(f"⚠️  警告: 未找到角色 {char_name} (ID: {char_id}) 的数据")
            continue
        
        # 创建角色对象
        char = Character(
            id=char_id,
            name=char_name,
            stats=char_data.stats,
            skills=char_data.skills,
            traces=char_data.traces,
            path=getattr(char_data, 'path', 'Hunt')
        )
        
        # 装备光锥
        light_cone_id = member.get('light_cone')
        if light_cone_id and light_cone_id in light_cones_data:
            char.light_cone = light_cones_data[light_cone_id]
            print(f"为 {char.name} 装备光锥: {char.light_cone.name}")
        
        # 装备仪器
        relics_config = member.get('relics', {})
        if relics_config:
            # 简化的仪器装备逻辑
            char.relics = []  # 这里可以扩展为实际的仪器对象
            print(f"为 {char.name} 配置仪器: {relics_config}")
        
        # 设置技能实例
        if hasattr(char, 'skills') and isinstance(char.skills, list):
            new_skills = []
            for skill_id in char.skills:
                skill_data = skills_data.get(skill_id)
                if skill_data:
                    new_skills.append(get_skill_instance(skill_id, skill_data))
            char.skills = new_skills
        
        team.append(char)
        print(f"✅ 成功创建角色: {char.name}")
    
    return team

def create_enemies_from_config(config):
    """从配置创建敌人对象"""
    enemies = []
    
    for enemy_data in config.get('enemies', []):
        enemy = Enemy(
            id=enemy_data.get('id', ''),
            name=enemy_data.get('name', 'Unknown'),
            stats=enemy_data.get('stats', {}),
            skills=enemy_data.get('skills', []),
            traces=enemy_data.get('traces', {}),
            weaknesses=enemy_data.get('weaknesses', []),
            resistances=enemy_data.get('resistances', {}),
            toughness=enemy_data.get('toughness', 100),
            max_toughness=enemy_data.get('max_toughness', 100)
        )
        enemies.append(enemy)
        print(f"✅ 成功创建敌人: {enemy.name}")
    
    return enemies

def main():
    """主函数"""
    print("🎮 星穹铁道模拟器 - 可视化配置版本")
    print("=" * 50)
    
    # 数据路径
    base_path = os.path.dirname(__file__)
    data_path = os.path.join(base_path, '../data')
    
    # 加载基础数据
    print("📂 加载数据...")
    try:
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
        
        print(f"✅ 数据加载成功:")
        print(f"   技能: {len(skills_data)} 个")
        print(f"   角色: {len(characters_data)} 个")
        print(f"   光锥: {len(light_cones_data)} 个")
        print(f"   仪器: {len(relics_data)} 个")
        
    except Exception as e:
        print(f"❌ 数据加载失败: {e}")
        return
    
    # 加载可视化配置
    config_path = os.path.join(data_path, 'visual_config.json')
    if not os.path.exists(config_path):
        print(f"❌ 未找到可视化配置文件: {config_path}")
        print("请先运行可视化选择器生成配置")
        return
    
    config = load_visual_config(config_path)
    if not config:
        return
    
    print(f"\n📋 加载配置: {config_path}")
    
    # 创建角色和敌人
    print("\n👥 创建角色...")
    team = create_characters_from_config(config, characters_data, skills_data, light_cones_data, relics_data)
    
    print("\n👹 创建敌人...")
    enemies = create_enemies_from_config(config)
    
    if not team:
        print("❌ 没有有效的角色，无法开始战斗")
        return
    
    if not enemies:
        print("❌ 没有有效的敌人，无法开始战斗")
        return
    
    print(f"\n🎯 战斗配置:")
    print(f"   队伍: {len(team)} 个角色")
    print(f"   敌人: {len(enemies)} 个")
    
    # 显示队伍信息
    print("\n===== 战斗队伍 =====")
    for char in team:
        print(f"{char.name} (SPD={char.stats.get('SPD', 0)})")
        print(f"  属性: {char.stats}")
        print(f"  技能: {[s.name for s in char.skills]}")
        print(f"  光锥: {getattr(char.light_cone, 'name', 'None')}")
        print(f"  行迹: {char.traces}")
        print(f"  能量: {getattr(char, 'energy', 0)}/{getattr(char, 'max_energy', 100)}")
        
        # 计算并展示面板属性
        base_stats, percent_stats, flat_bonus, active_sets, complex_effects = calc_total_stats(char)
        flat_bonus = {k: float(v) for k, v in flat_bonus.items()}
        relic_buffs = Buff.apply_relic_set_buffs(getattr(char, 'relics', []), active_sets)
        final_stats = Buff.finalize_stats(base_stats, percent_stats, flat_bonus, buffs=relic_buffs)
        print(f"  最终属性(结算后): {final_stats}")
        print()
    
    # 显示敌人信息
    print("===== 敌人 =====")
    for enemy in enemies:
        print(f"{enemy.name} (SPD={enemy.stats.get('SPD', 0)})")
        print(f"  属性: {enemy.stats}")
        print(f"  技能: {[s.name for s in enemy.skills]}")
        print(f"  能量: {getattr(enemy, 'energy', 0)}/{getattr(enemy, 'max_energy', 100)}")
        print(f"  最终属性(结算后): {enemy.stats}")
        print()
    
    # 开始战斗
    print("===== 自动战斗模拟开始 =====")
    
    # 设置AI策略
    for char in team:
        if char.name == "Seele":
            char.ai_strategy = "smart"
        elif char.name == "Natasha":
            char.ai_strategy = "healer"
        else:
            char.ai_strategy = "basic"
        print(f"为 {char.name} 设置了{char.ai_strategy}AI策略")
    
    # 创建战斗实例 - 将所有角色和敌人合并为一个列表
    all_characters = team + enemies
    battle = Battle(all_characters)
    
    # 运行战斗
    try:
        battle.run()
        print("\n战斗结束！")
    except Exception as e:
        print(f"❌ 战斗运行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 