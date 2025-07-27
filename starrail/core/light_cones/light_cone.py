# light_cone.py
from typing import Optional, Dict, Any
from .light_cone_skill import LightConeSkillFactory

class LightCone:
    def __init__(self, id, name, stats, skill=None, path=None, skill_data=None):
        self.id = id
        self.name = name
        self.stats = stats  # 属性加成，如{"HP":100, "ATK":50}
        self.skill = skill  # 光锥技能描述或ID 
        self.path = path
        self.skill_data = skill_data  # 技能数据
        self.skill_instance = None  # 技能实例
        
        # 如果有技能数据，创建技能实例
        if skill_data and skill_data.get('id'):
            self.skill_instance = LightConeSkillFactory.create_skill(
                skill_data['id'], 
                skill_data, 
                level=1  # 默认1级
            )
    
    def get_skill_instance(self) -> Optional[Any]:
        """获取技能实例"""
        return self.skill_instance