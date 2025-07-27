import sys
import os
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from starrail.core.battle import Battle
from scripts.selection_loader import load_selection
from starrail.core.equipment_manager import calc_total_stats
from starrail.core.skills.buff import Buff
from starrail.core.skills.skill_manager import SkillManager
from starrail.core.ai_strategies import seele_smart_ai, seele_balanced_ai, seele_buff_focused_ai, natasha_smart_ai

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
    # 为希儿和娜塔莎设置AI策略
    for c in team:
        if c.name.lower() in ["seele", "希儿"]:
            # 可以选择不同的AI策略：
            # c.ai_strategy = seele_smart_ai  # 智能策略：优先战技
            c.ai_strategy = seele_balanced_ai  # 平衡策略：70%战技，30%普攻
            # c.ai_strategy = seele_buff_focused_ai  # Buff专注策略：根据Buff状态选择
            print(f"为 {c.name} 设置了智能AI策略")
        elif c.name.lower() in ["natasha", "娜塔莎"]:
            c.ai_strategy = natasha_smart_ai
            print(f"为 {c.name} 设置了奶妈AI策略")
    print('===== 战斗队伍 =====')
    for c in team:
        print(f"{c.name} (SPD={c.stats.get('SPD', 100)})")
        print(f"  属性: {c.stats}")
        print(f"  技能: {[getattr(s, 'name', str(s)) for s in getattr(c, 'skills', [])]}")
        print(f"  光锥: {getattr(getattr(c, 'light_cone', None), 'name', None)}")
        print(f"  遗器: {[getattr(r, 'name', str(r)) for r in getattr(c, 'relics', [])]}")
        print(f"  行迹: {getattr(c, 'traces', {})}")
        print(f"  能量: {getattr(c, 'current_sp', 0):.1f}/{getattr(c, 'max_sp', 100)}")
        # 使用角色的get_current_stats方法，避免重复计算
        final_stats = c.get_current_stats()
        print(f"  最终属性(结算后): {final_stats}")
    print('===== 敌人 =====')
    for e in enemies:
        print(f"{e.name} (SPD={e.stats.get('SPD', 100)})")
        print(f"  属性: {e.stats}")
        print(f"  技能: {[getattr(s, 'name', str(s)) for s in getattr(e, 'skills', [])]}")
        print(f"  能量: {getattr(e, 'current_sp', 0):.1f}/{getattr(e, 'max_sp', 100)}")
        # 使用角色的get_current_stats方法，避免重复计算
        final_stats = e.get_current_stats()
        print(f"  最终属性(结算后): {final_stats}")
    print('===== 自动战斗模拟开始 =====')
    # 合并角色和敌人
    all_chars = team + enemies
    # 初始化SkillManager并注入到每个角色
    with open(os.path.join(base, '../data/skills.json'), 'r', encoding='utf-8') as f:
        skills_data = json.load(f)
    skill_data_dict = {entry['id']: entry for entry in skills_data}
    manager = SkillManager(skill_data_dict)
    for c in all_chars:
        c.skill_manager = manager
    # 初始化血量
    for c in all_chars:
        c.hp = c.get_max_hp()
    battle = Battle(all_chars)
    battle.run(max_turns=8)  # 增加回合数以观察Buff效果
    
    # 战斗结束后显示角色当前属性
    print('\n===== 战斗结束后的角色属性 =====')
    for c in all_chars:
        if c.is_alive():
            current_stats = c.get_current_stats()
            print(f"{c.name} 当前属性:")
            print(f"  HP: {c.hp:.0f}/{current_stats.get('HP', 0):.0f}")
            print(f"  ATK: {current_stats.get('ATK', 0):.0f}")
            print(f"  DEF: {current_stats.get('DEF', 0):.0f}")
            print(f"  SPD: {current_stats.get('SPD', 0):.0f}")
            print(f"  CRIT Rate: {current_stats.get('CRIT Rate', 0):.1%}")
            print(f"  CRIT DMG: {current_stats.get('CRIT DMG', 0):.1%}")
            if c.buffs:
                print(f"  当前Buff: {[b.name for b in c.buffs]}")
            print()
