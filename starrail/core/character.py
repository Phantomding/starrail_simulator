# starrail/core/character.py (日志优化和事件修正版)
import random
from typing import List, Dict, Any, Optional, Callable
from ..utils.logger import logger

# 前向声明以支持类型提示
if False:
    from .skills.buff import Buff
    from .light_cones.light_cone import LightCone
    from .skills.base_skill import BaseSkill
    from .battle import Battle
    from .skills.skill_manager import SkillManager

class Character:
    def __init__(self, name: str, stats: Dict[str, Any], skills: List['BaseSkill'], id: str, traces: Dict[str, Any], side: str = "player", light_cone: Optional['LightCone'] = None, path: Optional[str] = None, relics: Optional[list] = None, level: int = 80, skill_manager: Optional['SkillManager'] = None, ai_strategy: Optional[Callable[["Character"], Optional['BaseSkill']]] = None, max_sp: Optional[int] = None):
        self.name = name
        self.id = id
        self.stats = stats
        self.skills: List['BaseSkill'] = skills
        self.buffs: List['Buff'] = []
        self.hp = self.get_current_stats(recursive_guard=True).get("HP", 100)
        self.side = side
        self.light_cone = light_cone
        self.path = path
        self.relics = relics or []
        self.traces = traces
        self.level = level
        self.skill_manager = skill_manager
        self.ai_strategy = ai_strategy
        self.relic_set_skills: List[Any] = []
        
        self.max_sp = max_sp if max_sp is not None else stats.get("max_sp", 100)
        self.current_sp = 0
        self.can_instant_ultimate = False
        
        self._battle_context: Optional['Battle'] = None
        self._last_skill_type = 'Normal'
        self._has_extra_turn = False
        self._current_target: Optional['Character'] = None

    def get_current_stats(self, recursive_guard: bool = False) -> Dict[str, Any]:
        from .equipment_manager import calc_total_stats
        from .skills.buff import Buff
        base_stats, percent_stats, flat_bonus, _, _ = calc_total_stats(self)
        flat_bonus = {k: float(v) for k, v in flat_bonus.items()}
        all_buffs = getattr(self, 'buffs', [])
        final_stats = Buff.finalize_stats(base_stats, percent_stats, flat_bonus, buffs=all_buffs, character=self, recursive_guard=recursive_guard)
        return final_stats

    def on_battle_start(self, battle_context: 'Battle'):
        self._battle_context = battle_context
        if self.light_cone and self.light_cone.skill_instance:
            if hasattr(self.light_cone.skill_instance, 'on_battle_start'):
                self.light_cone.skill_instance.on_battle_start(self)

    def take_turn(self, battle_context: 'Battle'):
        self._battle_context = battle_context
        
        if self.skill_manager:
            self.skill_manager.process_turn_start_buffs(self, battle_context)

        if self.light_cone and self.light_cone.skill_instance:
            if hasattr(self.light_cone.skill_instance, 'on_turn_start'):
                self.light_cone.skill_instance.on_turn_start(self)

        skill_to_use = self.ai_strategy(self) if callable(self.ai_strategy) else random.choice(self.skills)
        if not skill_to_use:
            logger.log(f"{self.name} 没有可用的技能，跳过回合。", color="yellow")
            return
            
        skill_type = getattr(skill_to_use, 'type', 'Normal')
        skill_id = getattr(skill_to_use, 'skill_id', '')

        is_battle_skill = skill_type == 'BPSkill'
        if is_battle_skill and not battle_context.can_use_skill(self):
            logger.log(f"[资源检查] 战技点不足，改为使用普攻。", color="yellow")
            skill_to_use = next((s for s in self.skills if getattr(s, 'type', '') == 'Normal'), None)
            if not skill_to_use: return
            skill_type = 'Normal'
            skill_id = getattr(skill_to_use, 'skill_id', '')
            is_battle_skill = False

        # --- 关键修正: 调用更新后的目标选择函数 ---
        targets = self._select_targets(skill_to_use, battle_context)
        if not targets:
            logger.log(f"{self.name} 找不到合适的目标，跳过回合。", color="yellow")
            return

        if targets:
            self._current_target = targets[0]

        if self.skill_manager:
            if is_battle_skill:
                battle_context.use_skill_point(self)
            elif skill_type == 'Normal':
                battle_context.gain_skill_point(self)
            
            self.on_skill_used(skill_type)

            if self.light_cone and self.light_cone.skill_instance and hasattr(self.light_cone.skill_instance, 'on_skill_used'):
                self.light_cone.skill_instance.on_skill_used(self, skill_type)

            if hasattr(self, 'relic_set_skills'):
                for skill_instance in self.relic_set_skills:
                    if hasattr(skill_instance, 'on_skill_used'):
                        skill_instance.on_skill_used(self, skill_type)

            self.skill_manager.use_skill(skill_id, self, targets, battle_context, level=1)
        
        self._process_buff_duration()
        self._display_buff_status()
        self._current_target = None
        self._last_skill_type = "Idle"

    def _select_targets(self, skill: 'BaseSkill', battle_context: 'Battle') -> List['Character']:
        """
        [已更新] 扩展了目标选择逻辑以支持布洛妮娅
        """
        skill_id = getattr(skill, 'skill_id', '')
        targets = []

        # 娜塔莎战技: 选择血量百分比最低的队友
        if skill_id == "110502":
             allies = [c for c in battle_context.characters if c.side == self.side and c.is_alive()]
             if allies:
                allies.sort(key=lambda c: c.get_hp_ratio())
                targets = [allies[0]]
        # 布洛妮娅战技: 选择攻击力最高的队友 (非自己)
        elif skill_id == "110102":
            allies = [c for c in battle_context.characters if c.side == self.side and c.is_alive() and c.id != self.id]
            # 如果有其他队友，选择攻击力最高的
            if allies:
                allies.sort(key=lambda c: c.get_current_stats().get("ATK", 0), reverse=True)
                targets = [allies[0]]
            # 如果只有自己，就选择自己
            else:
                targets = [self]
        # 默认: 选择随机敌人
        else:
            enemies = [c for c in battle_context.characters if c.side != self.side and c.is_alive()]
            if enemies:
                targets = [random.choice(enemies)]
        return targets

    def _process_buff_duration(self):
        expired_buffs = []
        is_extra = self.is_in_extra_turn()
        
        for buff in self.buffs[:]:
            if buff.duration == -1: continue
            if hasattr(buff, 'freshly_added') and buff.freshly_added and getattr(buff, 'self_buff', False):
                buff.freshly_added = False
                continue
            if is_extra and self.id == "1102":
                logger.log_verbose(f"[特殊回合] 在额外回合中，{buff.name} 回合数不减少。")
                continue
            if buff.duration > 0:
                buff.duration -= 1
                if buff.duration == 0:
                    expired_buffs.append(buff)
        
        for buff in expired_buffs:
            self.remove_buff(buff)
            logger.log(f"[Buff结束] '{buff.name}' 已失效。", color="purple")

    def check_resurgence_talent(self):
        if self.id != "1102" or self.is_in_extra_turn(): return
        if self._last_skill_type in ['Normal', 'BPSkill', 'Ultra']:
            logger.log(f"[天赋] {self.name} 的 '复现' 天赋触发！", color="green")
            if self.skill_manager:
                self.skill_manager.use_skill('110204', self, [self], self._battle_context, level=1)

    def gain_energy(self, amount: float, source: str = "skill"):
        energy_regen_rate = self.get_current_stats().get("Energy Regeneration Rate", 0)
        final_amount = amount * (1 + energy_regen_rate)
        old_sp = self.current_sp
        self.current_sp = min(self.current_sp + final_amount, self.max_sp)
        gained = self.current_sp - old_sp
        if gained > 0:
            logger.log(f"[能量] 当前能量: {self.current_sp:.1f}/{self.max_sp} (+{gained:.1f} from {source})", color="blue")
        if self.current_sp >= self.max_sp:
            self.can_instant_ultimate = True

    def consume_energy(self, amount: float) -> bool:
        if self.current_sp >= amount:
            self.current_sp -= amount
            logger.log(f"[能量] 消耗{amount:.1f}能量，剩余{self.current_sp:.1f}/{self.max_sp}", color="blue")
            self.can_instant_ultimate = False
            return True
        return False
    
    def on_skill_used(self, skill_type: str):
        self.set_last_skill_type(skill_type)
        energy_gain_map = {"Normal": 20, "BPSkill": 30, "Ultra": 5}
        base_energy = energy_gain_map.get(skill_type, 0)
        if base_energy > 0:
            self.gain_energy(base_energy, f"{skill_type} 技能")

    def on_enemy_killed(self):
        self.gain_energy(10, "击杀敌人")
        self.check_resurgence_talent()
        if self.light_cone and self.light_cone.skill_instance and hasattr(self.light_cone.skill_instance, 'on_enemy_killed'):
            self.light_cone.skill_instance.on_enemy_killed(self)

    def set_last_skill_type(self, skill_type: str): self._last_skill_type = skill_type
    def set_extra_turn(self, has_extra_turn: bool): self._has_extra_turn = has_extra_turn
    def is_in_extra_turn(self) -> bool: return getattr(self, '_has_extra_turn', False)
    def get_max_hp(self) -> float: return self.get_current_stats().get("HP", 0)
    def get_hp_ratio(self) -> float: return self.hp / self.get_max_hp() if self.get_max_hp() > 0 else 0
    def show_hp(self) -> str: return f"{self.hp:.0f}/{self.get_max_hp():.0f}"
    def is_alive(self) -> bool: return self.hp > 0

    def heal(self, amount: float, source: Optional[str] = None):
        max_hp = self.get_max_hp()
        old_hp = self.hp
        self.hp = min(self.hp + amount, max_hp)
        healed = self.hp - old_hp
        logger.log(f"[治疗] {self.name} 回复了 {healed:.1f} HP (from: {source or '未知'})，当前HP: {self.show_hp()}", color="green")

    @staticmethod
    def defense_reduction(damage, attacker: 'Character', defender: 'Character', reduce_def_pct=0, flat_reduce_def=0, skip_ignore_def=False):
        attacker_stats = attacker.get_current_stats()
        ignore_def_pct = attacker_stats.get("DEF Ignore %", 0)
        def_val = defender.get_current_stats().get("DEF", 0)
        def_val *= (1 - reduce_def_pct)
        def_val += flat_reduce_def
        
        if skip_ignore_def:
            ignore_def_pct = 0
            logger.log(f"-> [击破伤害] 跳过无视防御效果", color="yellow")
        
        def_val *= (1 - ignore_def_pct)
        def_val = max(def_val, 0)
        level = getattr(attacker, 'level', 80)
        reduction = def_val / (def_val + level * 10 + 200)
        final_damage = damage * (1 - reduction)
        
        logger.log(f"-> 防御修正(系数: {reduction:.3f}):", color="red")
        logger.log(f"   (无视:{ignore_def_pct:.1%}, 减防:{reduce_def_pct:.1%}, 固减:{flat_reduce_def}) -> 最终伤害: {final_damage:.1f}")
        return final_damage

    def receive_damage(self, amount: float, attacker: Optional['Character'] = None, **kwargs):
        self.hp -= amount
        if self.hp < 0: self.hp = 0
        if self.light_cone and self.light_cone.skill_instance and hasattr(self.light_cone.skill_instance, 'on_damage_received'):
            self.light_cone.skill_instance.on_damage_received(self, amount)
        logger.log(f"-> {self.name} 剩余HP: {self.show_hp()}", color="red")
        if hasattr(self, 'toughness') and self.toughness is not None:
            logger.log_verbose(f"-> {self.name} 当前韧性: {self.toughness}")
        if self.hp <= 0 and self._battle_context:
            self._battle_context.check_battle_end()

    def add_buff(self, buff: 'Buff'):
        stackable = getattr(buff, 'stackable', False)
        buff.freshly_added = True
        if not stackable:
            for b in self.buffs:
                if b.name == buff.name:
                    b.duration = buff.duration
                    b.freshly_added = True
                    logger.log(f"[Buff刷新] {self.name} 的 '{b.name}' 刷新为 {b.duration} 回合", color="purple")
                    return
        self.buffs.append(buff)
        logger.log(f"[Buff获得] {self.name} 获得 '{buff.name}' (持续{buff.duration}回合)", color="purple")

    def remove_buff(self, buff_to_remove: 'Buff'):
        if buff_to_remove in self.buffs: self.buffs.remove(buff_to_remove)

    @property
    def atk(self): return self.get_current_stats().get("ATK", 0)
    @property
    def spd(self): return self.get_current_stats().get("SPD", 0)
    def can_use_ultimate(self) -> bool: return self.current_sp >= self.max_sp

    def _display_buff_status(self):
        if not self.buffs: return
        logger.start_block(f"Buff状态", color="cyan")
        for buff in self.buffs:
            duration_str = "永久" if buff.duration == -1 else f"剩余 {buff.duration} 回合"
            logger.log(f"- {buff.name}: {duration_str}")
        logger.end_block()
