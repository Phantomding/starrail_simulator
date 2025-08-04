# main_simulator.py
import os
import json
import copy

# 确保项目根目录在sys.path中，以便正确导入
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from starrail.utils.data_loader import load_all_game_data
from starrail.core.character import Character
from starrail.core.enemy import Enemy
from starrail.core.battle import Battle
from starrail.core.skills.skill_manager import SkillManager
from starrail.core.skills.skill import get_skill_instance
from starrail.core.ai_strategies import seele_smart_ai, natasha_smart_ai, bronya_simple_ai # 引入AI策略

def setup_battle_from_config(config_path: str, game_data: dict) -> Battle:
    """
    根据配置文件和游戏数据，创建并配置一个完整的战斗实例。
    """
    print("🚀 开始根据配置设置战斗...")

    # 1. 加载战斗配置
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # 2. 初始化技能管理器 (全局唯一)
    skill_manager = SkillManager(game_data['skills'])
    
    # AI策略映射
    ai_strategy_map = {
        "1102": seele_smart_ai,   # 希儿
        "1105": natasha_smart_ai, # 娜塔莎
        "1101": bronya_simple_ai, # 布洛妮娅
        # 可以为其他角色添加更多AI
    }

    participants = []
    
    # 3. 创建我方队伍
    print("\n assembling player team...")
    for member_config in config.get('team', []):
        char_id = member_config['id']
        
        # 从游戏数据中找到角色模板
        char_template = next((c for c in game_data['characters'] if c.id == char_id), None)
        if not char_template:
            print(f"⚠️  警告: 在角色数据库中未找到ID为 {char_id} 的角色，已跳过。")
            continue
        
        # 使用深拷贝创建独立的角色实例
        character = copy.deepcopy(char_template)
        
        # 装备光锥
        lc_id = member_config.get('light_cone')
        if lc_id:
            light_cone = game_data['light_cones'].get(lc_id)
            if light_cone:
                character.light_cone = copy.deepcopy(light_cone)
                print(f"  - 为 {character.name} 装备了光锥: {light_cone.name}")

        # 装备遗器
        relic_ids = member_config.get('relics', {}).values()
        character.relics = [copy.deepcopy(game_data['relics'][rid]) for rid in relic_ids if rid in game_data['relics']]
        if character.relics:
            print(f"  - 为 {character.name} 装备了 {len(character.relics)} 件遗器。")

        # 实例化角色的技能
        skill_instances = [get_skill_instance(sid, game_data['skills'][sid]) for sid in character.skills if sid in game_data['skills']]
        character.skills = skill_instances
        
        # 绑定技能管理器和AI
        character.skill_manager = skill_manager
        character.ai_strategy = ai_strategy_map.get(char_id, lambda c: random.choice(c.skills)) # 分配AI，若无特定AI则随机
        
        # 初始化HP
        character.hp = character.get_max_hp()
        
        participants.append(character)
        print(f"  👍 角色 '{character.name}' 配置完成。")

    # 4. 创建敌方队伍
    print("\n assembling enemy team...")
    for enemy_config in config.get('enemies', []):
        # 敌人数据直接来自配置文件
        enemy = Enemy(
            id=enemy_config['id'],
            name=enemy_config['name'],
            stats=enemy_config['stats'],
            skills=[], # 稍后实例化
            side='enemy',
            weaknesses=enemy_config.get('weaknesses', []),
            resistances=enemy_config.get('resistances', {}),
            toughness=enemy_config.get('toughness', 100),
            max_toughness=enemy_config.get('max_toughness', 100),
            ai_type=enemy_config.get('ai_type', 'default')
        )
        # 实例化敌人的技能
        enemy_skill_ids = [s['id'] for s in enemy_config.get('skills', [])]
        enemy.skills = [get_skill_instance(sid, game_data['skills'][str(sid)]) for sid in enemy_skill_ids if str(sid) in game_data['skills']]
        
        # 敌人也需要技能管理器和AI
        enemy.skill_manager = skill_manager
        from starrail.core.ai_strategies import enemy_default_ai
        enemy.ai_strategy = enemy_default_ai  # 敌人使用默认AI策略
        
        enemy.hp = enemy.get_max_hp()
        participants.append(enemy)
        print(f"  👾 敌人 '{enemy.name}' 配置完成。")

    # 5. 创建战斗实例
    print("\n✅ 所有单位配置完成，正在创建战斗...")
    battle = Battle(participants)
    return battle

if __name__ == '__main__':
    try:
        # 定义数据文件路径
        data_folder = os.path.join(os.path.dirname(__file__), 'data')
        config_file = os.path.join(data_folder, 'visual_config.json')

        # 检查配置文件是否存在
        if not os.path.exists(config_file):
            print(f"❌ 错误: 配置文件 '{config_file}' 不存在。")
            print("请先运行 visual_selector.py 生成配置文件。")
        else:
            # 加载所有游戏数据
            all_game_data = load_all_game_data(data_folder)
            
            # 从配置创建战斗
            battle_instance = setup_battle_from_config(config_file, all_game_data)
            
            # 运行战斗模拟
            print("\n" + "="*50)
            print("⚔️ 战斗模拟开始！")
            print("="*50 + "\n")
            battle_instance.run()

    except Exception as e:
        print(f"\n❌ 模拟器运行时发生严重错误: {e}")
        import traceback
        traceback.print_exc()