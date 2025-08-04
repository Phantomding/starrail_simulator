# skill.py
from .base_skill import BaseSkill
from .seele_skills import SeeleBasicSkill, SeeleSkill, SeeleUltimateSkill, SeeleTalent, SeeleTechnique, SeeleBonusSkill
from .natasha_skills import NatashaBasicSkill, NatashaSkill, NatashaUltimateSkill, NatashaTalent
from .bronya_skills import BronyaBasicSkill, BronyaSkill, BronyaUltimateSkill, BronyaTalent, BronyaTechnique, BronyaMazeNormal


SKILL_REGISTRY = {
    "110201": SeeleBasicSkill,
    "110202": SeeleSkill,
    "110203": SeeleUltimateSkill,
    "110204": SeeleTalent,
    "110206": SeeleTechnique,
    "110207": SeeleBonusSkill,
    "110501": NatashaBasicSkill,
    "110502": NatashaSkill,
    "110503": NatashaUltimateSkill,
    "110504": NatashaTalent,
    "110101": BronyaBasicSkill,
    "110102": BronyaSkill,
    "110103": BronyaUltimateSkill,
    "110104": BronyaTalent,
    "110107": BronyaTechnique,
    "110106": BronyaMazeNormal,
}

def get_skill_instance(skill_id, skill_data):
    skill_cls = SKILL_REGISTRY.get(skill_id, BaseSkill)
    return skill_cls(skill_data)