# starrail/core/skills/buff.py (已修正)
from typing import Optional, Dict, Any, List, Callable

# 为了类型提示
if False:
    from starrail.core.character import Character

class Buff:
    # 静态变量控制动态属性日志输出
    _show_dynamic_stats_log = True
    _dynamic_stats_logged = set()  # 记录已输出的Buff名称
    
    def __init__(self, name: str, duration: int, stat_bonus: Optional[Dict[str, float]] = None, damage_bonus: float = 0, element_penetration: float = 0, stackable: bool = False, dynamic_stat_bonus_func: Optional[Callable[['Character'], Dict[str, float]]] = None, dynamic_damage_bonus_func: Optional[Callable[['Character'], float]] = None):
        self.name = name
        self.duration = duration
        self.stat_bonus = stat_bonus or {}
        self.damage_bonus = damage_bonus
        self.element_penetration = element_penetration
        self.stackable = stackable
        
        self.dynamic_stat_bonus_func = dynamic_stat_bonus_func
        self.dynamic_damage_bonus_func = dynamic_damage_bonus_func
        
        self.freshly_added = False
        self.self_buff = False
        self.source: Optional[str] = None
        self.level = 1
        
        self.on_turn_start_data: Optional[Dict] = None
        self.on_turn_end_data: Optional[Dict] = None
        
    def get_damage_bonus(self, character: 'Character') -> float:
        if self.dynamic_damage_bonus_func:
            return self.dynamic_damage_bonus_func(character)
        return self.damage_bonus

    def modify_stats(self, stats: dict) -> dict:
        for k, v in self.stat_bonus.items():
            stats[k] = stats.get(k, 0) + v
        return stats

    STAT_NAME_UNIFY_MAP = {
        'BREAK_EFFECT': 'Break Effect', 'Break Effect': 'Break Effect', 'Effect RES': 'Effect RES',
        'EFFECT_RES': 'Effect RES', 'CRIT_RATE': 'CRIT Rate', 'CRIT Rate': 'CRIT Rate',
        'CRIT_DMG': 'CRIT DMG', 'CRIT DMG': 'CRIT DMG', 'ENERGY_REGEN_RATE': 'Energy Regeneration Rate',
        'Energy Regeneration Rate': 'Energy Regeneration Rate', 'EFFECT_HIT_RATE': 'Effect Hit Rate',
        'Effect Hit Rate': 'Effect Hit Rate', 'OUTGOING_HEALING': 'Outgoing Healing Boost',
        'Outgoing Healing Boost': 'Outgoing Healing Boost', 'WIND_DMG': 'Wind DMG', 'Wind DMG': 'Wind DMG',
        'LIGHTNING_DMG': 'Lightning DMG', 'Lightning DMG': 'Lightning DMG', 'FIRE_DMG': 'Fire DMG',
        'Fire DMG': 'Fire DMG', 'ICE_DMG': 'Ice DMG', 'Ice DMG': 'Ice DMG', 'PHYSICAL_DMG': 'Physical DMG',
        'Physical DMG': 'Physical DMG', 'QUANTUM_DMG': 'Quantum DMG', 'Quantum DMG': 'Quantum DMG',
        'IMAGINARY_DMG': 'Imaginary DMG', 'Imaginary DMG': 'Imaginary DMG',
    }

    @staticmethod
    def finalize_stats(base_stats: dict, percent_stats: dict, flat_bonus: Optional[Dict[str, float]] = None, buffs: Optional[List['Buff']] = None, character: Optional['Character'] = None, recursive_guard: bool = False) -> dict:
        final_stats = base_stats.copy()
        flat_bonus = flat_bonus or {}
        percent_stats = percent_stats.copy()
        
        # 【关键修正】添加了 recursive_guard 来防止无限循环
        if buffs and character:
            for buff in buffs:
                for k, v in buff.stat_bonus.items():
                    percent_stats[k] = percent_stats.get(k, 0) + v
                
                # 只有在非递归调用时，才执行动态属性计算
                if not recursive_guard and buff.dynamic_stat_bonus_func:
                    dynamic_bonuses = buff.dynamic_stat_bonus_func(character)
                    for k, v in dynamic_bonuses.items():
                        # 只在需要时输出动态属性日志
                        if (Buff._show_dynamic_stats_log and 
                            buff.name not in Buff._dynamic_stats_logged):
                            print(f"    [属性计算] {buff.name} 动态属性: {k} +{v*100:.1f}%")
                            Buff._dynamic_stats_logged.add(buff.name)
                        percent_stats[k] = percent_stats.get(k, 0) + v

        for base, percent in [("HP", "HP%"), ("DEF", "DEF%"), ("ATK", "ATK%"), ("SPD", "SPD%")]:
            base_val = base_stats.get(base, 0)
            percent_val = percent_stats.get(percent, 0)
            flat_val = flat_bonus.get(base, 0)
            final_stats[base] = base_val * (1 + percent_val) + flat_val

        for k, v in percent_stats.items():
            if k not in ["HP%", "DEF%", "ATK%", "SPD%"]:
                final_stats[k] = final_stats.get(k, 0) + v
        
        for k, v in list(final_stats.items()):
            if k.endswith("DMG%"):
                base_key = k[:-1]
                final_stats[base_key] = final_stats.get(base_key, 0) + v
        
        for k, v in list(final_stats.items()):
            if k.endswith("DMG Boost"):
                base_key = k[:-6]
                final_stats[base_key] = final_stats.get(base_key, 0) + v

        unified_stats = {}
        for k, v in final_stats.items():
            unified_key = Buff.STAT_NAME_UNIFY_MAP.get(k, k)
            if unified_key in unified_stats:
                unified_stats[unified_key] += v
            else:
                unified_stats[unified_key] = v
        return unified_stats

    @staticmethod
    def create_skill_buff(name: str, duration: int, stat_bonus: Dict[str, float], source: str = "skill", level: int = 1, damage_bonus: float = 0, element_penetration: float = 0) -> 'Buff':
        if duration is None or duration == 0:
            duration = -1
        
        buff = Buff(name=name, duration=duration, stat_bonus=stat_bonus, damage_bonus=damage_bonus, element_penetration=element_penetration)
        buff.source = source
        buff.level = level
        return buff
    
    @staticmethod
    def reset_dynamic_stats_log():
        """重置动态属性日志状态，允许重新输出日志"""
        Buff._dynamic_stats_logged.clear()
    
    @staticmethod
    def set_dynamic_stats_log_enabled(enabled: bool):
        """设置是否启用动态属性日志输出"""
        Buff._show_dynamic_stats_log = enabled