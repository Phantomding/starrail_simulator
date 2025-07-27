# character.py
from typing import List, Dict, Any, Optional, Callable, Union
from starrail.core.skills.buff import Buff
from starrail.core.light_cones.light_cone import LightCone
from starrail.core.skills.base_skill import BaseSkill

class Character:
    def __init__(self, name: str, stats: Dict[str, Any], skills: List[BaseSkill], id: str, traces: Dict[str, Any], side: str = "player", light_cone: Optional[LightCone] = None, path: Optional[str] = None, relics: Optional[list] = None, level: int = 80, skill_manager: Optional[Any] = None, ai_strategy: Optional[Union[str, Callable[["Character"], Optional[BaseSkill]]]] = None, max_sp: Optional[int] = None):
        self.name = name
        self.id = id
        self.stats = stats
        self.skills: List[BaseSkill] = skills  # 明确类型注解
        self.buffs = []
        self.hp = self.get_current_stats().get("HP", 100)
        self.side = side
        self.light_cone = light_cone
        self.path = path
        self.relics = relics or []
        self.traces = traces
        self.level = level
        self.skill_manager = skill_manager
        self.ai_strategy = ai_strategy  # 新增
        self.relic_set_skills = []  # 修复linter错误，保证属性存在
        # 能量系统
        if max_sp is not None:
            self.max_sp = max_sp  # 优先使用传入的max_sp
        else:
            self.max_sp = stats.get("max_sp", 100)  # 最大能量
        self.current_sp = 0  # 当前能量
        self.energy_gain_multiplier = 1.0  # 能量回复倍率（用于特殊效果）
        self.can_instant_ultimate = False  # 能量满时可立即释放终极技

    def gain_energy(self, amount: float, source: str = "skill"):
        """
        获得能量
        amount: 基础能量量
        source: 能量来源（"skill", "damage", "kill"等）
        """
        # 应用能量回复速率加成
        energy_regen_rate = self.get_current_stats().get("Energy Regeneration Rate", 0)
        final_amount = amount * (1 + energy_regen_rate) * self.energy_gain_multiplier
        
        old_sp = self.current_sp
        self.current_sp = min(self.current_sp + final_amount, self.max_sp)
        gained = self.current_sp - old_sp
        
        if gained > 0:
            print(f"[能量] {self.name} 从{source}获得{gained:.1f}能量 (基础{amount:.1f} + 回复速率加成{amount * energy_regen_rate:.1f} + 特殊倍率{amount * (self.energy_gain_multiplier - 1):.1f})")
            print(f"[能量] {self.name} 当前能量: {self.current_sp:.1f}/{self.max_sp}")
        # 检查能量是否满
        if self.current_sp >= self.max_sp:
            self.can_instant_ultimate = True
        return gained

    def consume_energy(self, amount: float):
        """
        消耗能量
        """
        if self.current_sp >= amount:
            self.current_sp -= amount
            print(f"[能量] {self.name} 消耗{amount:.1f}能量，剩余{self.current_sp:.1f}/{self.max_sp}")
            # 能量消耗后不可立即释放终极技
            self.can_instant_ultimate = False
            return True
        else:
            print(f"[能量] {self.name} 能量不足，需要{amount:.1f}，当前{self.current_sp:.1f}/{self.max_sp}")
            return False

    def can_use_ultimate(self) -> bool:
        """
        检查是否可以使用终极技
        """
        return self.current_sp >= self.max_sp

    def get_energy_ratio(self) -> float:
        """
        获取能量比例
        """
        return self.current_sp / self.max_sp if self.max_sp > 0 else 0

    def on_skill_used(self, skill_type: str):
        """
        技能使用后的能量回复
        """
        energy_gain_map = {
            "Normal": 20,
            "BPSkill": 30,
            "Ultra": 5,
            "Talent": 0,
            "Technique": 0,
            "MazeNormal": 20,
            "Maze": 0
        }
        
        base_energy = energy_gain_map.get(skill_type, 0)
        if base_energy > 0:
            self.gain_energy(base_energy, f"{skill_type}技能")

    def on_damage_received(self, damage_hits: int = 1, skill_type: str = "Normal"):
        """
        受到攻击时的能量回复
        """
        energy_per_hit_map = {
            "Normal": 10,
            "BPSkill": 15,
            "Ultra": 20,
            "Talent": 0,
            "Technique": 0,
            "MazeNormal": 10,
            "Maze": 0
        }
        
        base_energy_per_hit = energy_per_hit_map.get(skill_type, 0)
        if base_energy_per_hit > 0:
            # 多段伤害每段回复5能量
            total_energy = base_energy_per_hit + (damage_hits - 1) * 5
            self.gain_energy(total_energy, f"受到{skill_type}攻击")

    def on_enemy_killed(self):
        """
        击杀敌人时的能量回复和天赋触发
        """
        self.gain_energy(10, "击杀敌人")
        
        # 检查是否触发Resurgence天赋
        self.check_resurgence_talent()
    
    def check_resurgence_talent(self):
        """
        检查是否触发Resurgence天赋
        """
        # 检查是否是希儿（ID: 1102）
        if self.id == "1102":
            # 检查是否在额外回合中，如果是则不触发（防循环机制）
            if self.is_in_extra_turn():
                print(f"[天赋限制] {self.name} 在额外回合中击杀敌人，Resurgence天赋不会触发")
                return
            
            # 查找Resurgence天赋技能
            resurgence_skill = None
            for skill in self.skills:
                if getattr(skill, 'skill_id', '') == '110204':
                    resurgence_skill = skill
                    break
            
            if resurgence_skill:
                # 检查当前使用的技能类型是否满足条件
                # Resurgence触发条件：普通攻击、战技或终极技击杀敌人
                current_skill_type = getattr(self, '_last_skill_type', 'Normal')
                
                if current_skill_type in ['Normal', 'BPSkill', 'Ultra']:
                    print(f"[天赋触发] {self.name} 的Resurgence天赋被触发！")
                    
                    # 使用天赋技能
                    if hasattr(self, 'skill_manager') and self.skill_manager is not None:
                        self.skill_manager.use_skill('110204', self, [self], self._battle_context, level=1)
                    else:
                        resurgence_skill.use(self, [self], self._battle_context, level=1)
    
    def set_last_skill_type(self, skill_type: str):
        """
        设置最后使用的技能类型，用于天赋触发判断
        """
        self._last_skill_type = skill_type
    
    def set_extra_turn(self, has_extra_turn: bool):
        """
        设置是否有额外回合
        """
        self._has_extra_turn = has_extra_turn
    
    def is_in_extra_turn(self) -> bool:
        """
        检查是否在额外回合中
        """
        return getattr(self, '_has_extra_turn', False)

    def take_turn(self, battle_context):
        import random
        skill: Optional[BaseSkill] = None
        
        # 将战斗上下文传递给角色，供AI策略使用
        self._battle_context = battle_context
        
        # 光锥技能回合开始效果
        if hasattr(self, 'light_cone') and self.light_cone and hasattr(self.light_cone, 'skill_instance') and self.light_cone.skill_instance:
            self.light_cone.skill_instance.on_turn_start(self)
        
        # 检查是否可以使用终极技（额外回合中不能使用终极技）
        if self.can_use_ultimate() and not self.is_in_extra_turn():
            # 优先使用终极技
            ultimate_skill = None
            for s in self.skills:
                if getattr(s, 'type', '') == 'Ultra':
                    ultimate_skill = s
                    break
            
            if ultimate_skill:
                enemies = [c for c in battle_context.characters if c.side != self.side and c.is_alive()]
                if enemies:
                    target = random.choice(enemies)
                    max_level = getattr(ultimate_skill, 'max_level', 1)
                    print(f"{self.name} 使用终极技 [{getattr(ultimate_skill, 'name', str(ultimate_skill))}] 攻击 {target.name}")
                    
                    # 记录技能类型
                    self.set_last_skill_type("Ultra")
                    
                    # 消耗能量
                    self.consume_energy(self.max_sp)
                    
                    # 触发光锥技能效果（在伤害结算前）
                    if hasattr(self, 'light_cone') and self.light_cone and hasattr(self.light_cone, 'skill_instance') and self.light_cone.skill_instance:
                        self.light_cone.skill_instance.on_skill_used(self, "Ultra")
                    
                    # 触发遗器套装技能效果（在伤害结算前）
                    if hasattr(self, 'relic_set_skills') and self.relic_set_skills:
                        for skill_instance in self.relic_set_skills:
                            skill_instance.on_skill_used(self, "Ultra")
                    
                    # 使用技能（Buff会在技能内部应用）
                    if hasattr(self, 'skill_manager') and self.skill_manager is not None:
                        self.skill_manager.use_skill(getattr(ultimate_skill, 'skill_id', ''), self, [target], battle_context, level=max_level)
                    else:
                        ultimate_skill.use(self, [target], battle_context, level=max_level)
                    
                    # 终极技回复能量
                    self.on_skill_used("Ultra")
                    return
        elif self.can_use_ultimate() and self.is_in_extra_turn():
            # 在额外回合中，即使能量足够也不能使用终极技
            print(f"[额外回合限制] {self.name} 在额外回合中不能使用终极技")
        
        # AI策略选择技能
        if callable(self.ai_strategy):
            s = self.ai_strategy(self)
            skill = s if isinstance(s, BaseSkill) or s is None else None
        elif self.ai_strategy == "first_skill":
            skill = self.skills[0] if self.skills else None
        else:  # 默认随机
            s = random.choice(self.skills) if self.skills else None
            skill = s if isinstance(s, BaseSkill) or s is None else None
        
        # 检查技能类型和战技点
        if skill:
            # 检查技能类型
            skill_type = getattr(skill, 'type', 'Normal')
            skill_id = getattr(skill, 'skill_id', '')
            
            # 判断是否为战技
            is_skill = (skill_type == 'BPSkill' or 
                       skill_id in ['110202'] or  # 希儿的战技（终极技单独处理）
                       'Skill' in skill.name)
            
            if is_skill:
                # 战技需要消耗战技点
                if hasattr(battle_context, 'can_use_skill') and battle_context.can_use_skill(self):
                    # 可以使用战技
                    # 检查是否为治疗技能
                    from starrail.core.ai_strategies import select_heal_targets
                    intent = None
                    max_level = getattr(skill, 'max_level', 1)
                    if hasattr(self, 'skill_manager') and self.skill_manager is not None:
                        # 先用空目标获取intent
                        intent = self.skill_manager.skill_data_dict.get(getattr(skill, 'skill_id', ''), None)
                        if intent is not None:
                            intent = skill.use(self, [], battle_context, level=max_level)
                    if intent and intent.get('type') == 'heal_only':
                        # 选择治疗目标
                        heal_targets = select_heal_targets(self, battle_context, skill)
                        print(f"{self.name} 使用战技 [{getattr(skill, 'name', str(skill))}] 治疗 {heal_targets[0].name}")
                        self.set_last_skill_type("BPSkill")
                        battle_context.use_skill_point(self)
                        if hasattr(self, 'light_cone') and self.light_cone and hasattr(self.light_cone, 'skill_instance') and self.light_cone.skill_instance:
                            self.light_cone.skill_instance.on_skill_used(self, "BPSkill")
                        if hasattr(self, 'relic_set_skills') and self.relic_set_skills:
                            for skill_instance in self.relic_set_skills:
                                skill_instance.on_skill_used(self, "BPSkill")
                        if hasattr(self, 'skill_manager') and self.skill_manager is not None:
                            self.skill_manager.use_skill(getattr(skill, 'skill_id', ''), self, heal_targets, battle_context, level=max_level)
                        else:
                            skill.use(self, heal_targets, battle_context, level=max_level)
                        self.on_skill_used("BPSkill")
                    else:
                        enemies = [c for c in battle_context.characters if c.side != self.side and c.is_alive()]
                        if enemies:
                            target = random.choice(enemies)
                            print(f"{self.name} 使用战技 [{getattr(skill, 'name', str(skill))}] 攻击 {target.name}")
                            self.set_last_skill_type("BPSkill")
                            battle_context.use_skill_point(self)
                            if hasattr(self, 'light_cone') and self.light_cone and hasattr(self.light_cone, 'skill_instance') and self.light_cone.skill_instance:
                                self.light_cone.skill_instance.on_skill_used(self, "BPSkill")
                            if hasattr(self, 'relic_set_skills') and self.relic_set_skills:
                                for skill_instance in self.relic_set_skills:
                                    skill_instance.on_skill_used(self, "BPSkill")
                            if hasattr(self, 'skill_manager') and self.skill_manager is not None:
                                self.skill_manager.use_skill(getattr(skill, 'skill_id', ''), self, [target], battle_context, level=max_level)
                            else:
                                skill.use(self, [target], battle_context, level=max_level)
                            self.on_skill_used("BPSkill")
                        else:
                            print(f"{self.name} 没有可攻击的目标。")
                else:
                    # 战技点不足，改为普通攻击
                    print(f"{self.name} 战技点不足，改为普通攻击")
                    enemies = [c for c in battle_context.characters if c.side != self.side and c.is_alive()]
                    if enemies:
                        target = random.choice(enemies)
                        damage = self.get_current_stats().get("ATK", 10)
                        print(f"{self.name} 对 {target.name} 进行普通攻击，造成 {damage:.1f} 点伤害！")
                        if hasattr(target, 'receive_damage'):
                            from starrail.core.skills.skill_manager import damage_calc
                            dmg = damage_calc(self, target, 1.0, None)
                            target.receive_damage(dmg)
                        # 普通攻击回复战技点
                        battle_context.gain_skill_point(self)
                        # 普通攻击回复能量
                        self.on_skill_used("Normal")
                    else:
                        print(f"{self.name} 没有可攻击的目标。")
            else:
                # 普通攻击
                enemies = [c for c in battle_context.characters if c.side != self.side and c.is_alive()]
                if enemies:
                    target = random.choice(enemies)
                    max_level = getattr(skill, 'max_level', 1)
                    print(f"{self.name} 使用普通攻击 [{getattr(skill, 'name', str(skill))}] 攻击 {target.name}")
                    # 记录技能类型
                    self.set_last_skill_type("Normal")
                    
                    # 触发光锥技能效果（在伤害结算前）
                    if hasattr(self, 'light_cone') and self.light_cone and hasattr(self.light_cone, 'skill_instance') and self.light_cone.skill_instance:
                        self.light_cone.skill_instance.on_skill_used(self, "Normal")
                    
                    # 触发遗器套装技能效果（在伤害结算前）
                    if hasattr(self, 'relic_set_skills') and self.relic_set_skills:
                        for skill_instance in self.relic_set_skills:
                            skill_instance.on_skill_used(self, "Normal")
                    
                    # 使用技能（Buff会在技能内部应用）
                    if hasattr(self, 'skill_manager') and self.skill_manager is not None:
                        self.skill_manager.use_skill(getattr(skill, 'skill_id', ''), self, [target], battle_context, level=max_level)
                    else:
                        skill.use(self, [target], battle_context, level=max_level)
                    # 普通攻击回复战技点
                    battle_context.gain_skill_point(self)
                    # 普通攻击回复能量
                    self.on_skill_used("Normal")
                else:
                    print(f"{self.name} 没有可攻击的目标。")
        else:
            # 没有技能，进行基础普通攻击
            enemies = [c for c in battle_context.characters if c.side != self.side and c.is_alive()]
            if enemies:
                target = random.choice(enemies)
                damage = self.get_current_stats().get("ATK", 10)
                print(f"{self.name} 对 {target.name} 进行普通攻击，造成 {damage:.1f} 点伤害！")
                # 记录技能类型
                self.set_last_skill_type("Normal")
                
                # 触发光锥技能效果（在伤害结算前）
                if hasattr(self, 'light_cone') and self.light_cone and hasattr(self.light_cone, 'skill_instance') and self.light_cone.skill_instance:
                    self.light_cone.skill_instance.on_skill_used(self, "Normal")
                
                # 触发遗器套装技能效果（在伤害结算前）
                if hasattr(self, 'relic_set_skills') and self.relic_set_skills:
                    for skill_instance in self.relic_set_skills:
                        skill_instance.on_skill_used(self, "Normal")
                
                # 造成伤害（Buff已生效）
                if hasattr(target, 'receive_damage'):
                    from starrail.core.skills.skill_manager import damage_calc
                    dmg = damage_calc(self, target, 1.0, None)
                    target.receive_damage(dmg)
                # 普通攻击回复战技点
                battle_context.gain_skill_point(self)
                # 普通攻击回复能量
                self.on_skill_used("Normal")
            else:
                print(f"{self.name} 没有可攻击的目标。")
        
        # 行动后处理Buff持续时间
        expired_buffs = []
        is_extra_turn = self.is_in_extra_turn()
        
        for buff in self.buffs:
            if hasattr(buff, 'freshly_added') and buff.freshly_added:
                buff.freshly_added = False
                continue
            
            # 在额外回合中，Resurgence Enhanced State Buff的回合数不减少
            if is_extra_turn and buff.name == "Resurgence Enhanced State":
                print(f"[特殊回合] {self.name} 在额外回合中，{buff.name} 回合数不减少 (剩余{buff.duration}回合)")
                continue
                
            if buff.duration > 0:
                buff.duration -= 1
                if buff.duration == 0:
                    expired_buffs.append(buff)
        
        for buff in expired_buffs:
            if hasattr(buff, 'on_remove'):
                buff.on_remove(self)
            self.remove_buff(buff)
            print(f"{self.name} 的Buff {buff.name} 已失效并被移除")
        
        # 显示当前Buff状态
        self.show_buffs()

    def get_max_hp(self):
        return self.get_current_stats().get("HP", 0)

    def get_hp_ratio(self):
        max_hp = self.get_max_hp()
        return self.hp / max_hp if max_hp > 0 else 0

    def show_hp(self):
        return f"{self.hp:.0f}/{self.get_max_hp():.0f}"

    def heal(self, amount: float, source=None):
        max_hp = self.get_max_hp()
        old_hp = self.hp
        self.hp = min(self.hp + amount, max_hp)
        healed = self.hp - old_hp
        # 优化来源显示
        if hasattr(source, 'name'):
            source_str = source.name
        elif isinstance(source, str):
            source_str = source
        else:
            source_str = '未知'
        print(f"[治疗] {self.name} 回复了 {healed:.1f} 点生命值（来源: {source_str})，当前HP: {self.show_hp()}")
        # 可扩展：被治疗加成、触发被动等

    @staticmethod
    def defense_reduction(damage, attacker, defender, ignore_def_pct=0, reduce_def_pct=0, flat_reduce_def=0):
        def_val = defender.get_current_stats().get("DEF", 0)
        def_val *= (1 - reduce_def_pct)
        def_val += flat_reduce_def
        def_val *= (1 - ignore_def_pct)
        def_val = max(def_val, 0)
        level = getattr(attacker, 'level', 80)
        reduction = def_val / (def_val + level * 10 + 200)
        final_damage = damage * (1 - reduction)
        print(f"  -> 防御减伤系数: {reduction:.4f}，计算防御后伤害: {final_damage:.1f}（无视防御:{ignore_def_pct*100:.0f}% ，百分比减防:{reduce_def_pct*100:.0f}% ，固定减防:{flat_reduce_def}）")
        return final_damage

    def receive_damage(self, amount: float, attacker=None, **kwargs):
        self.hp -= amount
        if self.hp < 0:
            self.hp = 0
        print(f"  -> {self.name} 剩余HP: {self.show_hp()}")
        # 新增：打印韧性状态
        if hasattr(self, 'toughness') and self.toughness is not None:
            print(f"  -> {self.name} 当前韧性: {self.toughness}")
        
        # 受到攻击时回复能量
        skill_type = kwargs.get('skill_type', 'Normal')
        damage_hits = kwargs.get('damage_hits', 1)
        self.on_damage_received(damage_hits, skill_type)
        # 死亡后立即判定战斗是否结束
        if self.hp <= 0 and hasattr(self, '_battle_context'):
            self._battle_context.check_battle_end()

    def add_buff(self, buff: Buff):
        stackable = getattr(buff, 'stackable', False)
        buff.freshly_added = True
        if not stackable:
            for b in self.buffs:
                if b.name == buff.name:
                    b.duration = buff.duration
                    b.freshly_added = True
                    print(f"[Buff刷新] {self.name} 的Buff {b.name} 持续时间刷新为 {b.duration} 回合")
                    return
        self.buffs.append(buff)

    def remove_buff(self, buff: Buff):
        if buff in self.buffs:
            self.buffs.remove(buff)
    
    def show_buffs(self):
        """显示角色当前拥有的Buff信息"""
        if not self.buffs:
            print(f"[Buff状态] {self.name}: 无Buff")
            return
        
        print(f"[Buff状态] {self.name} 当前Buff:")
        for buff in self.buffs:
            # 显示Buff详细信息
            buff_info = [f"  - {buff.name} (剩余{buff.duration}回合)"]
            
            # 显示属性加成
            if hasattr(buff, 'stat_bonus') and buff.stat_bonus:
                stat_info = []
                for stat, value in buff.stat_bonus.items():
                    if isinstance(value, float):
                        stat_info.append(f"{stat}: {value*100:.0f}%")
                    else:
                        stat_info.append(f"{stat}: {value}")
                if stat_info:
                    buff_info.append(f"    属性加成: {', '.join(stat_info)}")
            
            # 显示独立增伤
            if hasattr(buff, 'damage_bonus') and buff.damage_bonus:
                buff_info.append(f"    独立增伤: {buff.damage_bonus*100:.0f}%")
            
            # 显示属性穿透
            if hasattr(buff, 'element_penetration') and buff.element_penetration:
                buff_info.append(f"    属性穿透: {buff.element_penetration*100:.0f}%")
            
            # 显示来源
            if hasattr(buff, 'source') and buff.source:
                buff_info.append(f"    来源: {buff.source}")
            
            print('\n'.join(buff_info))

    def is_alive(self) -> bool:
        return self.hp > 0

    def get_current_stats(self):
        from starrail.core.equipment_manager import calc_total_stats
        from starrail.core.skills.buff import Buff
        base_stats, percent_stats, flat_bonus, active_sets, complex_effects = calc_total_stats(self)
        flat_bonus = {k: float(v) for k, v in flat_bonus.items()}
        # relic_buffs = Buff.apply_relic_set_buffs(getattr(self, 'relics', []), active_sets)  # 删除重复加成
        all_buffs = getattr(self, 'buffs', [])  # 只保留角色自身的buff
        final_stats = Buff.finalize_stats(base_stats, percent_stats, flat_bonus, buffs=all_buffs)
        return final_stats

    @property
    def atk(self):
        return self.get_current_stats().get("ATK", 0)

    @property
    def def_(self):
        return self.get_current_stats().get("DEF", 0)

    @property
    def spd(self):
        return self.get_current_stats().get("SPD", 0)

    @property
    def crit_rate(self):
        return self.get_current_stats().get("CRIT Rate", 0)

    @property
    def crit_dmg(self):
        return self.get_current_stats().get("CRIT DMG", 0)

    @property
    def effect_res(self):
        return self.get_current_stats().get("Effect RES", 0)

    @property
    def break_effect(self):
        return self.get_current_stats().get("Break Effect", 0)

    @property
    def energy_regen(self):
        return self.get_current_stats().get("Energy Regeneration Rate", 0)

    @property
    def max_hp(self):
        return self.get_current_stats().get("HP", 0) 