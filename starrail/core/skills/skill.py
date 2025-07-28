# skill.py
import json
from typing import Any, Callable, Dict, List, Optional
import os
import random
from .base_skill import BaseSkill
from .seele_skills import SeeleBasicSkill, SeeleSkill, SeeleUltimateSkill, SeeleTalent, SeeleTechnique, SeeleBonusSkill
from .natasha_skills import NatashaBasicSkill, NatashaSkill
# 未来可导入更多角色技能

SKILL_REGISTRY = {
    "110201": SeeleBasicSkill,
    "110202": SeeleSkill,
    "110203": SeeleUltimateSkill,
    "110204": SeeleTalent,
    "110206": SeeleTechnique,
    "110207": SeeleBonusSkill,
    "110501": NatashaBasicSkill,  # Natasha 普攻
    "110502": NatashaSkill,       # Natasha 战技
    # 其他技能ID与类的映射
}

def get_skill_instance(skill_id, skill_data):
    skill_cls = SKILL_REGISTRY.get(skill_id, BaseSkill)
    return skill_cls(skill_data) 