# ai_strategies.py
from typing import Optional, List
from .skills.base_skill import BaseSkill

def seele_smart_ai(character) -> Optional[BaseSkill]:
    """
    希儿的智能AI策略
    策略：
    1. 优先使用战技（如果有战技点的话）
    2. 如果没有战技点，使用普攻
    3. 如果战技在冷却中，使用普攻
    """
    if not character.skills:
        return None
    
    # 检查战技点（通过battle_context）
    battle_context = getattr(character, '_battle_context', None)
    can_use_skill = True
    if battle_context and hasattr(battle_context, 'can_use_skill'):
        can_use_skill = battle_context.can_use_skill(character)
    
    # 查找战技（通常是第二个技能）
    skill = None
    basic_skill = None
    
    for i, s in enumerate(character.skills):
        if hasattr(s, 'skill_id'):
            if s.skill_id == "110202":  # 希儿战技ID
                skill = s
            elif s.skill_id == "110201":  # 希儿普攻ID
                basic_skill = s
    
    # 如果有战技点，优先使用战技
    if can_use_skill and skill:
        return skill
    
    # 如果没有战技点或没有战技，使用普攻
    if basic_skill:
        return basic_skill
    
    # 如果都没有，使用第一个技能
    return character.skills[0] if character.skills else None

def seele_balanced_ai(character) -> Optional[BaseSkill]:
    """
    希儿的平衡AI策略
    策略：
    1. 70%概率使用战技（如果有战技点）
    2. 30%概率使用普攻
    """
    import random
    
    if not character.skills:
        return None
    
    # 检查战技点
    battle_context = getattr(character, '_battle_context', None)
    can_use_skill = True
    if battle_context and hasattr(battle_context, 'can_use_skill'):
        can_use_skill = battle_context.can_use_skill(character)
    
    # 查找战技和普攻
    skill = None
    basic_skill = None
    
    for s in character.skills:
        if hasattr(s, 'skill_id'):
            if s.skill_id == "110202":  # 希儿战技ID
                skill = s
            elif s.skill_id == "110201":  # 希儿普攻ID
                basic_skill = s
    
    # 70%概率使用战技，30%概率使用普攻（但需要战技点）
    if random.random() < 0.7 and can_use_skill and skill:
        return skill
    elif basic_skill:
        return basic_skill
    
    # 如果都没有，使用第一个技能
    return character.skills[0] if character.skills else None

def seele_buff_focused_ai(character) -> Optional[BaseSkill]:
    """
    希儿的Buff专注AI策略
    策略：
    1. 如果没有速度Buff且有战技点，优先使用战技
    2. 如果已有速度Buff，使用普攻
    3. 如果战技点不足，使用普攻
    """
    if not character.skills:
        return None
    
    # 检查战技点
    battle_context = getattr(character, '_battle_context', None)
    can_use_skill = True
    if battle_context and hasattr(battle_context, 'can_use_skill'):
        can_use_skill = battle_context.can_use_skill(character)
    
    # 检查是否有速度Buff
    has_spd_buff = False
    for buff in character.buffs:
        if "SPD" in buff.name or "Speed" in buff.name:
            has_spd_buff = True
            break
    
    # 查找战技和普攻
    skill = None
    basic_skill = None
    
    for s in character.skills:
        if hasattr(s, 'skill_id'):
            if s.skill_id == "110202":  # 希儿战技ID
                skill = s
            elif s.skill_id == "110201":  # 希儿普攻ID
                basic_skill = s
    
    # 如果没有速度Buff且有战技点，优先使用战技
    if not has_spd_buff and can_use_skill and skill:
        return skill
    
    # 如果有速度Buff或没有战技点，使用普攻
    if basic_skill:
        return basic_skill
    
    # 如果都没有，使用第一个技能
    return character.skills[0] if character.skills else None 

def seele_should_cast_ultimate(character, battle_context) -> bool:
    """
    希儿的终极技释放策略：能量满且不是额外回合就释放
    可根据需要扩展更复杂的条件
    """
    return character.can_use_ultimate() and not character.is_in_extra_turn()

# 可为其他角色/AI添加不同的should_cast_ultimate函数

def default_should_cast_ultimate(character, battle_context) -> bool:
    """
    默认终极技释放策略：能量满且不是额外回合就释放
    """
    return character.can_use_ultimate() and not character.is_in_extra_turn() 

def natasha_smart_ai(character) -> Optional[BaseSkill]:
    """
    娜塔莎的智能AI策略：
    1. 优先使用战技（如果有战技点且有队友受伤）
    2. 否则使用普攻
    """
    if not character.skills:
        return None
    battle_context = getattr(character, '_battle_context', None)
    can_use_skill = True
    if battle_context and hasattr(battle_context, 'can_use_skill'):
        can_use_skill = battle_context.can_use_skill(character)
    # 查找战技和普攻
    skill = None
    basic_skill = None
    for s in character.skills:
        if hasattr(s, 'skill_id'):
            if s.skill_id == "110502":  # Natasha战技ID
                skill = s
            elif s.skill_id == "110501":  # Natasha普攻ID
                basic_skill = s
    # 判断是否有队友需要治疗
    need_heal = False
    if battle_context:
        allies = [c for c in battle_context.characters if c.side == character.side and c.is_alive()]
        for ally in allies:
            if ally.hp < ally.get_max_hp():
                need_heal = True
                break
    # 优先使用战技（如果有战技点且有队友受伤）
    if can_use_skill and skill and need_heal:
        return skill
    # 否则使用普攻
    if basic_skill:
        return basic_skill
    return character.skills[0] if character.skills else None

def natasha_select_heal_targets(character, battle_context, skill) -> list:
    """
    选择治疗目标：优先选择我方血量最低且未满的队友
    """
    if not battle_context:
        return [character]
    allies = [c for c in battle_context.characters if c.side == character.side and c.is_alive() and c.hp < c.get_max_hp()]
    if not allies:
        return [character]  # 没有队友受伤则给自己
    # 按血量百分比升序排序
    allies.sort(key=lambda c: c.hp / max(1, c.get_max_hp()))
    return [allies[0]] 