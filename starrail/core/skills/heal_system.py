# heal_system.py - 新的治疗系统
from typing import List, Callable, Optional
from enum import Enum

class HealTargetStrategy(Enum):
    """治疗目标选择策略"""
    LOWEST_HP_RATIO = "lowest_hp_ratio"      # 血量百分比最低
    LOWEST_HP_ABSOLUTE = "lowest_hp_absolute"  # 绝对血量最低
    SELF_ONLY = "self_only"                   # 只治疗自己
    ALL_ALLIES = "all_allies"                 # 所有队友
    MANUAL_TARGET = "manual_target"           # 手动指定目标
    CUSTOM = "custom"                         # 自定义策略

class HealCalculator:
    """治疗量计算器"""
    
    @staticmethod
    def calculate_heal_amount(healer, target, base_heal, heal_ratio=0, stat_scaling=None):
        """
        计算治疗量
        base_heal: 固定治疗量
        heal_ratio: 基于目标最大生命值的治疗比例
        stat_scaling: 基于施法者属性的缩放 {"ATK": 0.5, "HP": 0.3}
        """
        heal_amount = base_heal
        
        # 基于目标最大生命值的治疗
        if heal_ratio > 0:
            target_max_hp = target.get_max_hp() if hasattr(target, 'get_max_hp') else 0
            heal_amount += heal_ratio * target_max_hp
        
        # 基于施法者属性的缩放
        if stat_scaling:
            healer_stats = healer.get_current_stats()
            for stat, ratio in stat_scaling.items():
                heal_amount += healer_stats.get(stat, 0) * ratio
        
        # 应用治疗加成
        outgoing_healing_boost = healer.get_current_stats().get("Outgoing Healing Boost", 0)
        heal_amount *= (1 + outgoing_healing_boost)
        
        # 应用接受治疗加成（如果目标有的话）
        if hasattr(target, 'get_current_stats'):
            incoming_healing_boost = target.get_current_stats().get("Incoming Healing Boost", 0)
            heal_amount *= (1 + incoming_healing_boost)
        
        return heal_amount

class HealTargetSelector:
    """治疗目标选择器"""
    
    @staticmethod
    def select_targets(healer, available_targets, strategy: HealTargetStrategy, 
                      max_targets=1, custom_filter: Optional[Callable]=None):
        """
        选择治疗目标
        healer: 施法者
        available_targets: 可选目标列表
        strategy: 选择策略
        max_targets: 最大目标数量
        custom_filter: 自定义过滤函数
        """
        # 过滤掉死亡的目标
        alive_targets = [t for t in available_targets if t.is_alive()]
        
        # 应用自定义过滤器
        if custom_filter:
            alive_targets = [t for t in alive_targets if custom_filter(t)]
        
        if strategy == HealTargetStrategy.SELF_ONLY:
            return [healer] if healer in alive_targets else []
        
        elif strategy == HealTargetStrategy.ALL_ALLIES:
            return alive_targets[:max_targets]
        
        elif strategy == HealTargetStrategy.LOWEST_HP_RATIO:
            # 按血量百分比升序排序
            alive_targets.sort(key=lambda t: t.hp / max(1, t.get_max_hp()))
            return alive_targets[:max_targets]
        
        elif strategy == HealTargetStrategy.LOWEST_HP_ABSOLUTE:
            # 按绝对血量升序排序
            alive_targets.sort(key=lambda t: t.hp)
            return alive_targets[:max_targets]
        
        elif strategy == HealTargetStrategy.MANUAL_TARGET:
            # 手动目标应该在调用时已经指定
            return available_targets[:max_targets]
        
        else:
            # 默认策略：血量百分比最低
            return HealTargetSelector.select_targets(
                healer, available_targets, HealTargetStrategy.LOWEST_HP_RATIO, max_targets
            )

class HealSkillIntent:
    """治疗技能意图"""
    
    def __init__(self, skill_name, base_heal=0, heal_ratio=0, stat_scaling=None,
                 target_strategy=HealTargetStrategy.LOWEST_HP_RATIO, max_targets=1,
                 additional_effects=None):
        self.skill_name = skill_name
        self.base_heal = base_heal
        self.heal_ratio = heal_ratio
        self.stat_scaling = stat_scaling or {}
        self.target_strategy = target_strategy
        self.max_targets = max_targets
        self.additional_effects = additional_effects or []  # 额外效果如Buff
    
    def to_dict(self):
        return {
            "type": "heal_advanced",
            "skill_name": self.skill_name,
            "base_heal": self.base_heal,
            "heal_ratio": self.heal_ratio,
            "stat_scaling": self.stat_scaling,
            "target_strategy": self.target_strategy,
            "max_targets": self.max_targets,
            "additional_effects": self.additional_effects
        }

# 在SkillManager中添加新的处理函数
def _handle_heal_advanced(self, user, targets, intent, skill_type):
    """处理高级治疗技能"""
    # 重新选择目标（如果需要）
    if intent.get("target_strategy") != HealTargetStrategy.MANUAL_TARGET:
        # 获取所有己方目标
        all_allies = [c for c in getattr(user, '_battle_context', {}).get('characters', []) 
                     if c.side == user.side and c.is_alive()]
        
        # 根据策略选择目标
        targets = HealTargetSelector.select_targets(
            user, all_allies, 
            intent.get("target_strategy", HealTargetStrategy.LOWEST_HP_RATIO),
            intent.get("max_targets", 1)
        )
    
    results = []
    for target in targets:
        # 计算治疗量
        heal_amount = HealCalculator.calculate_heal_amount(
            user, target,
            intent.get("base_heal", 0),
            intent.get("heal_ratio", 0),
            intent.get("stat_scaling")
        )
        
        # 执行治疗
        result = self._apply_heal_to_target(target, heal_amount, intent["skill_name"])
        if result:
            results.append(result)
        
        # 应用额外效果
        for effect in intent.get("additional_effects", []):
            if effect.get("type") == "buff":
                self._apply_buff_to_target(target, effect.get("buff"), intent["skill_name"])
    
    return results

