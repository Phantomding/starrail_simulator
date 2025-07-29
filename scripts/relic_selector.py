#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
遗器选择工具 - 提供清晰的遗器选择界面和推荐功能
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from starrail.utils.data_loader import load_relics
from starrail.core.equipment_manager import RelicManager
from starrail.core.character import Character

class RelicSelector:
    """遗器选择器 - 提供交互式遗器选择界面"""
    
    def __init__(self, relics_path):
        self.relics_data = load_relics(relics_path)
        self.relic_manager = RelicManager(self.relics_data)
    
    def show_character_relic_recommendations(self, character):
        """显示角色的遗器推荐"""
        print(f"\n=== {character.name} 的遗器推荐 ===")
        print(f"角色类型: {getattr(character, 'path', 'Unknown')}")
        
        # 显示套装推荐
        set_recommendations = self.relic_manager.get_set_recommendations(character)
        print("\n📦 推荐套装:")
        for set_name, description in set_recommendations:
            print(f"  • {set_name}: {description}")
        
        # 显示各部位推荐
        slots = ["Head", "Hands", "Body", "Feet", "PlanarSphere", "LinkRope"]
        print("\n🔧 各部位推荐:")
        for slot in slots:
            best_relics = self.relic_manager.get_best_relics_for_character(character, slot)
            if best_relics:
                best_relic = best_relics[0]
                print(f"  {slot}: {getattr(best_relic, 'name', 'Unknown')}")
                if hasattr(best_relic, 'main_stat'):
                    main_stat = best_relic.main_stat.get('stat', 'Unknown')
                    main_value = best_relic.main_stat.get('value', 0)
                    print(f"    主属性: {main_stat} +{main_value}")
                if hasattr(best_relic, 'sub_stats'):
                    sub_stats = []
                    for sub in best_relic.sub_stats:
                        stat_name = sub.get('stat', 'Unknown')
                        stat_value = sub.get('value', 0)
                        sub_stats.append(f"{stat_name} +{stat_value}")
                    if sub_stats:
                        print(f"    副属性: {', '.join(sub_stats)}")
    
    def show_relic_inventory(self, filters=None):
        """显示遗器库存"""
        print("\n=== 遗器库存 ===")
        
        if filters is None:
            filters = {}
        
        # 按套装分组显示
        sets = self.relic_manager.relics_by_set
        for set_name, relics in sets.items():
            if 'set_name' in filters and filters['set_name'] != set_name:
                continue
                
            print(f"\n📦 {set_name} ({len(relics)}件):")
            for relic in relics:
                if self._matches_filters(relic, filters):
                    self._print_relic_info(relic)
    
    def _matches_filters(self, relic, filters):
        """检查遗器是否匹配过滤器"""
        for key, value in filters.items():
            if key == 'slot' and getattr(relic, 'slot', None) != value:
                return False
            elif key == 'main_stat' and hasattr(relic, 'main_stat'):
                if relic.main_stat.get('stat') != value:
                    return False
            elif key == 'set_name' and getattr(relic, 'set_name', None) != value:
                return False
        return True
    
    def _print_relic_info(self, relic):
        """打印遗器信息"""
        slot = getattr(relic, 'slot', 'Unknown')
        set_name = getattr(relic, 'set_name', 'Unknown')
        
        print(f"  {slot} - {set_name}")
        
        # 主属性
        if hasattr(relic, 'main_stat'):
            main_stat = relic.main_stat.get('stat', 'Unknown')
            main_value = relic.main_stat.get('value', 0)
            print(f"    主属性: {main_stat} +{main_value}")
        
        # 副属性
        if hasattr(relic, 'sub_stats'):
            sub_stats = []
            for sub in relic.sub_stats:
                stat_name = sub.get('stat', 'Unknown')
                stat_value = sub.get('value', 0)
                sub_stats.append(f"{stat_name} +{stat_value}")
            if sub_stats:
                print(f"    副属性: {', '.join(sub_stats)}")
        
        # 评分信息
        if hasattr(relic, 'scoringResult'):
            score = relic.scoringResult.get('score', 'Unknown')
            rating = relic.scoringResult.get('rating', 'Unknown')
            print(f"    评分: {score} ({rating})")
    
    def create_character_build(self, character):
        """为角色创建遗器配置"""
        print(f"\n=== 为 {character.name} 创建遗器配置 ===")
        
        # 显示推荐
        self.show_character_relic_recommendations(character)
        
        # 创建配置
        build = {
            "character_id": getattr(character, 'id', character.name),
            "character_name": character.name,
            "relics": {}
        }
        
        slots = ["Head", "Hands", "Body", "Feet", "PlanarSphere", "LinkRope"]
        for slot in slots:
            best_relics = self.relic_manager.get_best_relics_for_character(character, slot)
            if best_relics:
                best_relic = best_relics[0]
                build["relics"][slot] = {
                    "id": getattr(best_relic, 'id', f"{slot}_best"),
                    "name": getattr(best_relic, 'name', f"Best {slot}"),
                    "set_name": getattr(best_relic, 'set_name', 'Unknown'),
                    "main_stat": getattr(best_relic, 'main_stat', {}),
                    "sub_stats": getattr(best_relic, 'sub_stats', [])
                }
        
        return build
    
    def save_build_to_file(self, build, filename):
        """保存配置到文件"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(build, f, ensure_ascii=False, indent=2)
        print(f"\n✅ 配置已保存到 {filename}")

def main():
    """主函数 - 演示遗器选择器功能"""
    # 初始化遗器选择器
    relics_path = os.path.join(os.path.dirname(__file__), '../data/fribbels-optimizer-save.json')
    selector = RelicSelector(relics_path)
    
    # 创建示例角色
    seele = Character(
        id="1102",
        name="Seele",
        stats={"HP": 931, "ATK": 640, "DEF": 364, "SPD": 115, "CRIT Rate": 0.05, "CRIT DMG": 0.5},
        skills=[],
        traces={},
        path="Hunt"
    )
    
    natasha = Character(
        id="1105", 
        name="Natasha",
        stats={"HP": 1164, "ATK": 476, "DEF": 507, "SPD": 98, "CRIT Rate": 0.05, "CRIT DMG": 0.5},
        skills=[],
        traces={},
        path="Abundance"
    )
    
    # 显示遗器库存概览
    print("=== 遗器库存概览 ===")
    sets = selector.relic_manager.relics_by_set
    for set_name, relics in sets.items():
        print(f"{set_name}: {len(relics)}件")
    
    # 为角色创建配置
    seele_build = selector.create_character_build(seele)
    natasha_build = selector.create_character_build(natasha)
    
    # 保存配置
    selector.save_build_to_file(seele_build, "seele_relic_build.json")
    selector.save_build_to_file(natasha_build, "natasha_relic_build.json")
    
    # 显示特定过滤器的遗器
    print("\n=== 头部遗器 (按套装过滤) ===")
    selector.show_relic_inventory({"slot": "Head"})

if __name__ == "__main__":
    main() 