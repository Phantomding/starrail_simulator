# relic.py
class Relic:
    def __init__(self, id, name, main_stat, sub_stats=None, set_name=None, slot=None):
        self.id = id
        self.name = name
        self.main_stat = main_stat
        self.sub_stats = sub_stats or []
        self.set_name = set_name
        self.slot = slot  # 新增，部位 