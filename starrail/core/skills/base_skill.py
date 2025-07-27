class BaseSkill:
    def __init__(self, skill_data):
        self.skill_id = skill_data.get("id")
        self.name = skill_data.get("name")
        self.type = skill_data.get("type")
        self.description = skill_data.get("description")
        # 可以根据需要添加更多通用属性

    def use(self, user, targets, context, level=1):
        """
        技能释放的主入口，需在子类中实现。
        user: 施放技能的角色对象
        targets: 技能目标对象列表
        context: 当前战斗上下文（如回合、环境等）
        level: 技能等级
        """
        # 未实装技能，返回skip类型，表示跳过本回合
        return {"type": "skip", "skill_name": self.name} 