#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
敌人配置处理器 - 从游戏原始配置文件生成简化的敌人数据
"""

import json
import os
from typing import Dict, List, Optional, Any


class EnemyConfigProcessor:
    """敌人配置处理器"""
    
    def __init__(self):
        self.monster_configs = {}
        self.monster_skills = {}
        self.monster_templates = {}
        
    def load_config_files(self, monster_config_path: str, skill_config_path: str, template_config_path: str):
        """加载配置文件"""
        try:
            # 加载怪物配置
            with open(monster_config_path, 'r', encoding='utf-8') as f:
                monster_data = json.load(f)
                if isinstance(monster_data, list):
                    for monster in monster_data:
                        self.monster_configs[monster['MonsterID']] = monster
                else:
                    self.monster_configs = monster_data
            
            # 加载技能配置
            with open(skill_config_path, 'r', encoding='utf-8') as f:
                skill_data = json.load(f)
                if isinstance(skill_data, list):
                    for skill in skill_data:
                        self.monster_skills[skill['SkillID']] = skill
                else:
                    self.monster_skills = skill_data
            
            # 加载模板配置
            with open(template_config_path, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
                if isinstance(template_data, list):
                    for template in template_data:
                        self.monster_templates[template['MonsterTemplateID']] = template
                else:
                    self.monster_templates = template_data
            
            print(f"✅ 配置文件加载成功:")
            print(f"   怪物配置: {len(self.monster_configs)} 个")
            print(f"   技能配置: {len(self.monster_skills)} 个")
            print(f"   模板配置: {len(self.monster_templates)} 个")
            
        except Exception as e:
            print(f"❌ 配置文件加载失败: {e}")
            raise
    
    def extract_value(self, obj: Any) -> Any:
        """提取Value字段的值，如果存在的话"""
        if isinstance(obj, dict) and 'Value' in obj:
            return obj['Value']
        return obj
    
    def process_damage_resistances(self, resistances: List[Dict]) -> Dict[str, float]:
        """处理伤害抗性"""
        result = {}
        for resistance in resistances:
            damage_type = resistance.get('DamageType')
            value = self.extract_value(resistance.get('Value', 0))
            if damage_type:
                result[damage_type] = float(value)
        return result
    
    def process_skills(self, skill_ids: List[int]) -> List[Dict]:
        """处理技能列表"""
        skills = []
        for skill_id in skill_ids:
            if skill_id in self.monster_skills:
                skill_data = self.monster_skills[skill_id]
                skill = {
                    'id': skill_id,
                    'name': f"Skill_{skill_id}",  # 可以后续从Hash映射获取真实名称
                    'damage_type': skill_data.get('DamageType', 'Physical'),
                    'attack_type': skill_data.get('AttackType', 'Normal'),
                    'sp_cost': self.extract_value(skill_data.get('SPHitBase', 0)),
                    'delay_ratio': self.extract_value(skill_data.get('DelayRatio', 1)),
                    'params': [self.extract_value(param) for param in skill_data.get('ParamList', [])]
                }
                skills.append(skill)
        return skills
    
    def calculate_final_stats(self, template_id: int, monster_config: Dict) -> Dict[str, float]:
        """计算最终属性"""
        if template_id not in self.monster_templates:
            return {}
        
        template = self.monster_templates[template_id]
        
        # 基础属性
        base_stats = {
            'ATK': self.extract_value(template.get('AttackBase', 0)),
            'DEF': self.extract_value(template.get('DefenceBase', 0)),
            'HP': self.extract_value(template.get('HPBase', 0)),
            'SPD': self.extract_value(template.get('SpeedBase', 0)),
            'Stance': self.extract_value(template.get('StanceBase', 0)),
            'CRIT_DMG': self.extract_value(template.get('CriticalDamageBase', 0.2)),
            'Status_RES': self.extract_value(template.get('StatusResistanceBase', 0.1))
        }
        
        # 应用修正系数
        modifiers = {
            'ATK': self.extract_value(monster_config.get('AttackModifyRatio', 1)),
            'DEF': self.extract_value(monster_config.get('DefenceModifyRatio', 1)),
            'HP': self.extract_value(monster_config.get('HPModifyRatio', 1)),
            'SPD': self.extract_value(monster_config.get('SpeedModifyRatio', 1)),
            'Stance': self.extract_value(monster_config.get('StanceModifyRatio', 1))
        }
        
        # 计算最终属性
        final_stats = {}
        for stat, base_value in base_stats.items():
            modifier = modifiers.get(stat, 1)
            final_stats[stat] = float(base_value * modifier)
        
        # 处理速度修正值
        if 'SpeedModifyValue' in monster_config:
            speed_modify = self.extract_value(monster_config['SpeedModifyValue'])
            final_stats['SPD'] += speed_modify
        
        return final_stats
    
    def process_single_enemy(self, monster_id: int) -> Optional[Dict]:
        """处理单个敌人"""
        if monster_id not in self.monster_configs:
            print(f"⚠️  警告: 未找到怪物ID {monster_id} 的配置")
            return None
        
        monster_config = self.monster_configs[monster_id]
        template_id = monster_config.get('MonsterTemplateID')
        
        if not template_id or template_id not in self.monster_templates:
            print(f"⚠️  警告: 怪物 {monster_id} 的模板ID {template_id} 不存在")
            return None
        
        template = self.monster_templates[template_id]
        
        # 计算最终属性
        final_stats = self.calculate_final_stats(template_id, monster_config)
        
        # 处理弱点
        weaknesses = monster_config.get('StanceWeakList', [])
        
        # 处理抗性
        resistances = self.process_damage_resistances(
            monster_config.get('DamageTypeResistance', [])
        )
        
        # 处理技能
        skill_ids = monster_config.get('SkillList', [])
        skills = self.process_skills(skill_ids)
        
        # 获取AI相关信息
        ai_path = template.get('AIPath', '')
        ai_skill_sequence = template.get('AISkillSequence', [])
        
        # 构建敌人数据
        enemy_data = {
            'id': str(monster_id),
            'name': f"Enemy_{monster_id}",  # 可以后续从Hash映射获取真实名称
            'template_id': template_id,
            'rank': template.get('Rank', 'Unknown'),
            'elite_group': monster_config.get('EliteGroup', 1),
            'stats': final_stats,
            'weaknesses': weaknesses,
            'resistances': resistances,
            'skills': skills,
            'ai_info': {
                'path': ai_path,
                'skill_sequence': ai_skill_sequence
            },
            'toughness': final_stats.get('Stance', 100),
            'max_toughness': final_stats.get('Stance', 100),
            'side': 'enemy'
        }
        
        return enemy_data
    
    def process_all_enemies(self) -> List[Dict]:
        """处理所有敌人"""
        enemies = []
        
        print("🔄 开始处理敌人配置...")
        
        for monster_id in self.monster_configs.keys():
            enemy_data = self.process_single_enemy(monster_id)
            if enemy_data:
                enemies.append(enemy_data)
                print(f"✅ 处理完成: {enemy_data['name']} (ID: {monster_id})")
        
        print(f"🎯 处理完成，共生成 {len(enemies)} 个敌人")
        return enemies
    
    def save_processed_enemies(self, enemies: List[Dict], output_path: str):
        """保存处理后的敌人数据"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(enemies, f, ensure_ascii=False, indent=2)
            print(f"💾 敌人数据已保存到: {output_path}")
        except Exception as e:
            print(f"❌ 保存失败: {e}")
    
    def generate_enemy_summary(self, enemies: List[Dict]) -> Dict:
        """生成敌人统计摘要"""
        summary = {
            'total_count': len(enemies),
            'by_rank': {},
            'by_elite_group': {},
            'damage_types': set(),
            'weaknesses': set(),
            'resistances': set()
        }
        
        for enemy in enemies:
            # 按等级统计
            rank = enemy.get('rank', 'Unknown')
            summary['by_rank'][rank] = summary['by_rank'].get(rank, 0) + 1
            
            # 按精英组统计
            elite_group = enemy.get('elite_group', 1)
            summary['by_elite_group'][elite_group] = summary['by_elite_group'].get(elite_group, 0) + 1
            
            # 收集伤害类型
            for skill in enemy.get('skills', []):
                summary['damage_types'].add(skill.get('damage_type', 'Physical'))
            
            # 收集弱点和抗性
            summary['weaknesses'].update(enemy.get('weaknesses', []))
            summary['resistances'].update(enemy.get('resistances', {}).keys())
        
        # 转换set为list以便JSON序列化
        summary['damage_types'] = list(summary['damage_types'])
        summary['weaknesses'] = list(summary['weaknesses'])
        summary['resistances'] = list(summary['resistances'])
        
        return summary


def main():
    """主函数"""
    print("🎮 星穹铁道敌人配置处理器")
    print("=" * 50)
    
    # 配置文件路径（请根据实际情况修改）
    base_path = os.path.dirname(__file__)
    config_paths = {
        'monster_config': os.path.join(base_path, 'data/MonsterConfig.json'),
        'skill_config': os.path.join(base_path, 'data/MonsterSkillConfig.json'),
        'template_config': os.path.join(base_path, 'data/MonsterTemplateConfig.json')
    }
    
    # 检查文件是否存在
    missing_files = []
    for name, path in config_paths.items():
        if not os.path.exists(path):
            missing_files.append(f"{name}: {path}")
    
    if missing_files:
        print("❌ 以下配置文件不存在:")
        for file in missing_files:
            print(f"   {file}")
        print("\n请确保配置文件存在并修改路径配置")
        return
    
    # 创建处理器
    processor = EnemyConfigProcessor()
    
    try:
        # 加载配置文件
        processor.load_config_files(
            config_paths['monster_config'],
            config_paths['skill_config'],
            config_paths['template_config']
        )
        
        # 处理所有敌人
        enemies = processor.process_all_enemies()
        
        if not enemies:
            print("❌ 没有成功处理任何敌人数据")
            return
        
        # 生成统计摘要
        summary = processor.generate_enemy_summary(enemies)
        
        print(f"\n📊 敌人数据统计:")
        print(f"   总数量: {summary['total_count']}")
        print(f"   等级分布: {summary['by_rank']}")
        print(f"   精英组分布: {summary['by_elite_group']}")
        print(f"   伤害类型: {summary['damage_types']}")
        print(f"   弱点类型: {summary['weaknesses']}")
        print(f"   抗性类型: {summary['resistances']}")
        
        # 保存处理后的数据
        output_path = os.path.join(base_path, 'data/processed_enemies.json')
        processor.save_processed_enemies(enemies, output_path)
        
        # 保存统计摘要
        summary_path = os.path.join(base_path, 'data/enemy_summary.json')
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print(f"📈 统计摘要已保存到: {summary_path}")
        
        # 显示一些示例敌人
        print(f"\n🔍 示例敌人数据 (前3个):")
        for i, enemy in enumerate(enemies[:3]):
            print(f"\n--- 敌人 {i+1} ---")
            print(f"ID: {enemy['id']}")
            print(f"名称: {enemy['name']}")
            print(f"等级: {enemy['rank']}")
            print(f"属性: HP={enemy['stats'].get('HP', 0):.1f}, ATK={enemy['stats'].get('ATK', 0):.1f}, SPD={enemy['stats'].get('SPD', 0):.1f}")
            print(f"弱点: {enemy['weaknesses']}")
            print(f"技能数量: {len(enemy['skills'])}")
        
        print(f"\n✅ 处理完成！生成了 {len(enemies)} 个敌人数据")
        
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()