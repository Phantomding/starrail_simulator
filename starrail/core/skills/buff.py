# buff.py
from typing import Callable, Any, Optional, Dict, List

class Buff:
    def __init__(self, name: str, duration: int, apply_effect: Optional[Callable] = None, remove_effect: Optional[Callable] = None, stat_bonus: Optional[Dict[str, float]] = None, damage_bonus: float = 0, element_penetration: float = 0, stackable: bool = False):
        self.name = name
        self.duration = duration  # 持续回合数
        self.apply_effect = apply_effect  # 可选，应用时触发
        self.remove_effect = remove_effect  # 可选，移除时触发
        self.stat_bonus = stat_bonus or {}  # 直接加成属性
        self.damage_bonus = damage_bonus  # 独立的增伤区
        self.element_penetration = element_penetration  # 属性穿透
        self.stackable = stackable  # 是否可叠加
        self.freshly_added = False  # 新增，首回合不扣减
        self.source = None  # 来源（技能、天赋等）
        self.level = 1  # 技能等级

    def on_apply(self, character):
        if self.apply_effect:
            self.apply_effect(character)

    def on_remove(self, character):
        if self.remove_effect:
            self.remove_effect(character)

    def on_turn_start(self, character):
        # 每回合开始时触发，可扩展
        pass

    def on_turn_end(self, character):
        # 每回合结束时触发，可扩展
        pass

    def modify_stats(self, stats: dict) -> dict:
        """
        默认实现：不修改属性。子类可重写此方法。
        例如提升20%最大生命的Buff应累加HP%字段。
        """
        for k, v in self.stat_bonus.items():
            stats[k] = stats.get(k, 0) + v
        return stats

    # 属性名统一映射（如有新属性可补充）
    STAT_NAME_UNIFY_MAP = {
        'BREAK_EFFECT': 'Break Effect',
        'Break Effect': 'Break Effect',
        'Effect RES': 'Effect RES',
        'EFFECT_RES': 'Effect RES',
        'CRIT_RATE': 'CRIT Rate',
        'CRIT Rate': 'CRIT Rate',
        'CRIT_DMG': 'CRIT DMG',
        'CRIT DMG': 'CRIT DMG',
        'ENERGY_REGEN_RATE': 'Energy Regeneration Rate',
        'Energy Regeneration Rate': 'Energy Regeneration Rate',
        'EFFECT_HIT_RATE': 'Effect Hit Rate',
        'Effect Hit Rate': 'Effect Hit Rate',
        'OUTGOING_HEALING': 'Outgoing Healing Boost',
        'Outgoing Healing Boost': 'Outgoing Healing Boost',
        'WIND_DMG': 'Wind DMG',
        'Wind DMG': 'Wind DMG',
        'LIGHTNING_DMG': 'Lightning DMG',
        'Lightning DMG': 'Lightning DMG',
        'FIRE_DMG': 'Fire DMG',
        'Fire DMG': 'Fire DMG',
        'ICE_DMG': 'Ice DMG',
        'Ice DMG': 'Ice DMG',
        'PHYSICAL_DMG': 'Physical DMG',
        'Physical DMG': 'Physical DMG',
        'QUANTUM_DMG': 'Quantum DMG',
        'Quantum DMG': 'Quantum DMG',
        'IMAGINARY_DMG': 'Imaginary DMG',
        'Imaginary DMG': 'Imaginary DMG',
        # 其它属性可补充
    }

    @staticmethod
    def finalize_stats(base_stats: dict, percent_stats: dict, flat_bonus: Optional[Dict[str, float]] = None, buffs: Optional[List['Buff']] = None) -> dict:
        """
        统一结算所有百分比加成，返回最终属性。
        百分比加成只作用于base_stats，flat_bonus为装备/遗器主副属性的平A加成，最后加算。
        buffs: 额外的Buff列表（如套装Buff），会统一叠加到percent_stats。
        """
        final_stats = base_stats.copy()
        flat_bonus = flat_bonus or {}
        percent_stats = percent_stats.copy()
        # 先应用所有buff的stat_bonus到percent_stats
        if buffs:
            for buff in buffs:
                for k, v in buff.stat_bonus.items():
                    percent_stats[k] = percent_stats.get(k, 0) + v
        # 支持HP/DEF/ATK/SPD等所有主属性的百分比加成
        for base, percent in [("HP", "HP%"), ("DEF", "DEF%"), ("ATK", "ATK%"), ("SPD", "SPD%")]:
            base_val = base_stats.get(base, 0)
            percent_val = percent_stats.get(percent, 0)
            flat_val = flat_bonus.get(base, 0)
            final_stats[base] = base_val * (1 + percent_val) + flat_val
        # 处理其它百分比属性
        for k, v in percent_stats.items():
            if k not in ["HP%", "DEF%", "ATK%", "SPD%"]:
                final_stats[k] = final_stats.get(k, 0) + v
        # 属性名统一
        unified_stats = {}
        for k, v in final_stats.items():
            unified_key = Buff.STAT_NAME_UNIFY_MAP.get(k, k)
            if unified_key in unified_stats:
                unified_stats[unified_key] += v
            else:
                unified_stats[unified_key] = v
        return unified_stats

    @staticmethod
    def apply_relic_set_buffs(relics: List[Any], active_sets: Dict[str, Dict[str, float]]) -> List['Buff']:
        """
        根据active_sets生成对应的Buff对象列表。
        """
        buffs = []
        for set_name, effects in active_sets.items():
            buffs.append(Buff(name=f"套装：{set_name}", duration=-1, stat_bonus=effects))
        return buffs

    @staticmethod
    def create_skill_buff(name: str, duration: int, stat_bonus: Dict[str, float], source: str = "skill", level: int = 1, damage_bonus: float = 0, element_penetration: float = 0) -> 'Buff':
        """
        创建技能Buff的便捷方法
        """
        buff = Buff(name=name, duration=duration, stat_bonus=stat_bonus, damage_bonus=damage_bonus, element_penetration=element_penetration)
        buff.source = source
        buff.level = level
        return buff 