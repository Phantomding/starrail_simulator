#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可视化选择器 - 提供图形界面来选择角色、光锥和仪器
"""

import sys
import os
import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import threading

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from starrail.utils.data_loader import load_characters, load_skills, load_light_cones, load_relics
from starrail.core.equipment_manager import RelicManager

class VisualSelector:
    def __init__(self, root):
        self.root = root
        self.root.title("星穹铁道模拟器 - 可视化选择器")
        self.root.geometry("1200x800")
        
        # 数据路径
        self.data_path = os.path.join(os.path.dirname(__file__), '../data')
        self.icon_path = os.path.join(os.path.dirname(__file__), '../icon')
        
        # 加载数据
        self.load_data()
        
        # 当前选择
        self.current_team = []
        self.current_enemies = []
        
        # 创建界面
        self.create_widgets()
        
    def load_data(self):
        """加载所有数据"""
        try:
            # 加载基础数据
            skills_data = load_skills(os.path.join(self.data_path, 'skills.json'))
            light_cones_data = load_light_cones(
                os.path.join(self.data_path, 'light_cones.json'),
                os.path.join(self.data_path, 'light_cone_skills.json')
            )
            relics_data = load_relics(os.path.join(self.data_path, 'fribbels-optimizer-save.json'))
            
            # 加载角色数据
            self.characters = load_characters(
                os.path.join(self.data_path, 'characters.json'),
                skills_data,
                light_cones_data
            )
            
            self.light_cones = light_cones_data
            self.relics = relics_data
            self.relic_manager = RelicManager(self.relics)
            
            print(f"✅ 数据加载成功:")
            print(f"   角色: {len(self.characters)} 个")
            print(f"   光锥: {len(self.light_cones)} 个")
            print(f"   仪器: {len(self.relics)} 个")
            
        except Exception as e:
            print(f"❌ 数据加载失败: {e}")
            messagebox.showerror("错误", f"数据加载失败: {e}")
    
    def create_widgets(self):
        """创建界面组件"""
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建选项卡
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # 队伍配置选项卡
        self.team_frame = ttk.Frame(notebook)
        notebook.add(self.team_frame, text="队伍配置")
        self.create_team_tab()
        
        # 敌人配置选项卡
        self.enemy_frame = ttk.Frame(notebook)
        notebook.add(self.enemy_frame, text="敌人配置")
        self.create_enemy_tab()
        
        # 保存/加载选项卡
        self.save_frame = ttk.Frame(notebook)
        notebook.add(self.save_frame, text="保存/加载")
        self.create_save_tab()
    
    def create_team_tab(self):
        """创建队伍配置选项卡"""
        # 左侧：角色选择
        left_frame = ttk.Frame(self.team_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        ttk.Label(left_frame, text="角色选择", font=("Arial", 14, "bold")).pack(pady=5)
        
        # 角色搜索框
        search_frame = ttk.Frame(left_frame)
        search_frame.pack(fill=tk.X, pady=5)
        ttk.Label(search_frame, text="搜索:").pack(side=tk.LEFT)
        self.char_search_var = tk.StringVar()
        self.char_search_var.trace('w', self.filter_characters)
        ttk.Entry(search_frame, textvariable=self.char_search_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # 角色列表框架
        char_list_frame = ttk.Frame(left_frame)
        char_list_frame.pack(fill=tk.BOTH, expand=True)
        
        # 角色列表
        self.char_canvas = tk.Canvas(char_list_frame)
        char_scrollbar = ttk.Scrollbar(char_list_frame, orient="vertical", command=self.char_canvas.yview)
        self.char_canvas.configure(yscrollcommand=char_scrollbar.set)
        
        self.char_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        char_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.char_inner_frame = ttk.Frame(self.char_canvas)
        self.char_canvas.create_window((0, 0), window=self.char_inner_frame, anchor="nw")
        
        # 右侧：当前队伍
        right_frame = ttk.Frame(self.team_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        ttk.Label(right_frame, text="当前队伍", font=("Arial", 14, "bold")).pack(pady=5)
        
        # 队伍列表
        self.team_listbox = tk.Listbox(right_frame, height=10)
        self.team_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 队伍操作按钮
        team_btn_frame = ttk.Frame(right_frame)
        team_btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(team_btn_frame, text="移除选中", command=self.remove_from_team).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(team_btn_frame, text="清空队伍", command=self.clear_team).pack(side=tk.LEFT)
        
        # 初始化角色列表
        self.update_character_list()
        
        # 绑定事件
        self.char_inner_frame.bind("<Configure>", lambda e: self.char_canvas.configure(scrollregion=self.char_canvas.bbox("all")))
    
    def create_enemy_tab(self):
        """创建敌人配置选项卡"""
        # 敌人配置框架
        enemy_config_frame = ttk.Frame(self.enemy_frame)
        enemy_config_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(enemy_config_frame, text="敌人配置", font=("Arial", 14, "bold")).pack(pady=5)
        
        # 敌人列表
        self.enemy_listbox = tk.Listbox(enemy_config_frame, height=8)
        self.enemy_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 敌人操作按钮
        enemy_btn_frame = ttk.Frame(enemy_config_frame)
        enemy_btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(enemy_btn_frame, text="添加敌人", command=self.add_enemy).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(enemy_btn_frame, text="移除选中", command=self.remove_enemy).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(enemy_btn_frame, text="清空敌人", command=self.clear_enemies).pack(side=tk.LEFT)
    
    def create_save_tab(self):
        """创建保存/加载选项卡"""
        save_frame = ttk.Frame(self.save_frame)
        save_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(save_frame, text="配置管理", font=("Arial", 14, "bold")).pack(pady=5)
        
        # 保存配置
        save_btn_frame = ttk.Frame(save_frame)
        save_btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(save_btn_frame, text="保存配置到 data/", command=self.save_config).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(save_btn_frame, text="加载配置", command=self.load_config).pack(side=tk.LEFT)
        
        # 配置预览
        ttk.Label(save_frame, text="当前配置预览:", font=("Arial", 12, "bold")).pack(pady=(20, 5))
        
        self.config_text = tk.Text(save_frame, height=15, width=80)
        self.config_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 更新配置预览
        self.update_config_preview()
    
    def update_character_list(self):
        """更新角色列表"""
        # 清空现有内容
        for widget in self.char_inner_frame.winfo_children():
            widget.destroy()
        
        # 获取搜索关键词
        search_term = self.char_search_var.get().lower()
        
        # 创建角色卡片
        row = 0
        col = 0
        max_cols = 4
        
        for char in self.characters:
            if search_term and search_term not in char.name.lower():
                continue
                
            # 创建角色卡片框架
            card_frame = ttk.Frame(self.char_inner_frame)
            card_frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            
            # 尝试加载角色头像
            try:
                avatar_path = os.path.join(self.icon_path, 'avatar', f"{char.id}.webp")
                if os.path.exists(avatar_path):
                    image = Image.open(avatar_path)
                    image = image.resize((64, 64), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(image)
                    
                    # 创建头像标签
                    avatar_label = ttk.Label(card_frame, image=photo)
                    avatar_label.image = photo  # 保持引用
                    avatar_label.pack()
                else:
                    # 如果没有头像，显示ID
                    ttk.Label(card_frame, text=char.id, font=("Arial", 10)).pack()
            except Exception as e:
                # 如果加载失败，显示ID
                ttk.Label(card_frame, text=char.id, font=("Arial", 10)).pack()
            
            # 角色名称
            name_label = ttk.Label(card_frame, text=char.name, font=("Arial", 10, "bold"))
            name_label.pack()
            
            # 添加按钮
            add_btn = ttk.Button(card_frame, text="添加", 
                               command=lambda c=char: self.add_to_team(c))
            add_btn.pack(pady=2)
            
            # 更新行列位置
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        # 配置网格权重
        for i in range(max_cols):
            self.char_inner_frame.columnconfigure(i, weight=1)
    
    def filter_characters(self, *args):
        """过滤角色列表"""
        self.update_character_list()
    
    def add_to_team(self, character):
        """添加角色到队伍"""
        if len(self.current_team) >= 4:
            messagebox.showwarning("警告", "队伍最多只能有4个角色")
            return
        
        # 检查是否已经在队伍中
        if any(char.id == character.id for char in self.current_team):
            messagebox.showwarning("警告", f"{character.name} 已经在队伍中")
            return
        
        # 添加到队伍
        self.current_team.append(character)
        self.update_team_display()
        self.update_config_preview()
        
        # 打开装备选择窗口
        self.open_equipment_selector(character)
    
    def remove_from_team(self):
        """从队伍中移除选中的角色"""
        selection = self.team_listbox.curselection()
        if selection:
            index = selection[0]
            if 0 <= index < len(self.current_team):
                removed_char = self.current_team.pop(index)
                self.update_team_display()
                self.update_config_preview()
                messagebox.showinfo("信息", f"已移除 {removed_char.name}")
    
    def clear_team(self):
        """清空队伍"""
        if self.current_team:
            self.current_team.clear()
            self.update_team_display()
            self.update_config_preview()
            messagebox.showinfo("信息", "队伍已清空")
    
    def update_team_display(self):
        """更新队伍显示"""
        self.team_listbox.delete(0, tk.END)
        for char in self.current_team:
            self.team_listbox.insert(tk.END, f"{char.name} (ID: {char.id})")
    
    def open_equipment_selector(self, character):
        """打开装备选择窗口"""
        equipment_window = tk.Toplevel(self.root)
        equipment_window.title(f"为 {character.name} 选择装备")
        equipment_window.geometry("800x600")
        
        EquipmentSelector(equipment_window, character, self.light_cones, self.relic_manager)
    
    def add_enemy(self):
        """添加敌人"""
        # 简化的敌人添加，实际可以扩展为更复杂的界面
        enemy_id = "8000001"
        enemy_name = "Test Enemy"
        enemy_stats = {"HP": 20000, "ATK": 800, "DEF": 200, "SPD": 100, "CRIT Rate": 0, "CRIT DMG": 0}
        
        enemy = {
            "id": enemy_id,
            "name": enemy_name,
            "stats": enemy_stats,
            "weaknesses": ["Fire", "Ice"],
            "resistances": {},
            "toughness": 100,
            "max_toughness": 100
        }
        
        self.current_enemies.append(enemy)
        self.update_enemy_display()
        self.update_config_preview()
    
    def remove_enemy(self):
        """移除敌人"""
        selection = self.enemy_listbox.curselection()
        if selection:
            index = selection[0]
            if 0 <= index < len(self.current_enemies):
                removed_enemy = self.current_enemies.pop(index)
                self.update_enemy_display()
                self.update_config_preview()
    
    def clear_enemies(self):
        """清空敌人"""
        self.current_enemies.clear()
        self.update_enemy_display()
        self.update_config_preview()
    
    def update_enemy_display(self):
        """更新敌人显示"""
        self.enemy_listbox.delete(0, tk.END)
        for enemy in self.current_enemies:
            self.enemy_listbox.insert(tk.END, f"{enemy['name']} (ID: {enemy['id']})")
    
    def update_config_preview(self):
        """更新配置预览"""
        config = {
            "team": [],
            "enemies": self.current_enemies,
            "notes": {
                "team_composition": "可视化选择器生成的配置",
                "strategy": "自动生成的战斗策略"
            }
        }
        
        # 添加队伍信息
        for char in self.current_team:
            team_member = {
                "id": char.id,
                "name": char.name,
                "light_cone": getattr(char, 'light_cone_id', None),
                "relics": getattr(char, 'relics_config', {}),
                "notes": f"由可视化选择器添加"
            }
            config["team"].append(team_member)
        
        # 更新预览文本
        self.config_text.delete(1.0, tk.END)
        self.config_text.insert(1.0, json.dumps(config, ensure_ascii=False, indent=2))
    
    def save_config(self):
        """保存配置到data文件夹"""
        if not self.current_team:
            messagebox.showwarning("警告", "请先添加角色到队伍")
            return
        
        config = {
            "team": [],
            "enemies": self.current_enemies,
            "notes": {
                "team_composition": "可视化选择器生成的配置",
                "strategy": "自动生成的战斗策略"
            }
        }
        
        # 添加队伍信息
        for char in self.current_team:
            team_member = {
                "id": char.id,
                "name": char.name,
                "light_cone": getattr(char, 'light_cone_id', None),
                "relics": getattr(char, 'relics_config', {}),
                "notes": f"由可视化选择器添加"
            }
            config["team"].append(team_member)
        
        # 保存到文件
        config_path = os.path.join(self.data_path, 'visual_config.json')
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("成功", f"配置已保存到 {config_path}")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {e}")
    
    def load_config(self):
        """加载配置"""
        config_path = filedialog.askopenfilename(
            title="选择配置文件",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir=self.data_path
        )
        
        if config_path:
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 清空当前配置
                self.current_team.clear()
                self.current_enemies.clear()
                
                # 加载队伍
                for member in config.get('team', []):
                    char_id = member.get('id')
                    char = next((c for c in self.characters if c.id == char_id), None)
                    if char:
                        # 设置装备信息
                        char.light_cone_id = member.get('light_cone')
                        char.relics_config = member.get('relics', {})
                        self.current_team.append(char)
                
                # 加载敌人
                self.current_enemies = config.get('enemies', [])
                
                # 更新显示
                self.update_team_display()
                self.update_enemy_display()
                self.update_config_preview()
                
                messagebox.showinfo("成功", f"配置已从 {config_path} 加载")
                
            except Exception as e:
                messagebox.showerror("错误", f"加载失败: {e}")


class EquipmentSelector:
    def __init__(self, parent, character, light_cones, relic_manager):
        self.parent = parent
        self.character = character
        self.light_cones = light_cones
        self.relic_manager = relic_manager
        
        self.create_widgets()
    
    def create_widgets(self):
        """创建装备选择界面"""
        # 标题
        ttk.Label(self.parent, text=f"为 {self.character.name} 选择装备", 
                 font=("Arial", 14, "bold")).pack(pady=10)
        
        # 光锥选择
        light_cone_frame = ttk.LabelFrame(self.parent, text="光锥选择")
        light_cone_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 光锥搜索
        lc_search_frame = ttk.Frame(light_cone_frame)
        lc_search_frame.pack(fill=tk.X, pady=5)
        ttk.Label(lc_search_frame, text="搜索光锥:").pack(side=tk.LEFT)
        self.lc_search_var = tk.StringVar()
        self.lc_search_var.trace('w', self.filter_light_cones)
        ttk.Entry(lc_search_frame, textvariable=self.lc_search_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # 光锥列表
        self.lc_listbox = tk.Listbox(light_cone_frame, height=6)
        self.lc_listbox.pack(fill=tk.X, pady=5)
        self.lc_listbox.bind('<<ListboxSelect>>', self.on_light_cone_select)
        
        # 更新光锥列表
        self.update_light_cone_list()
        
        # 仪器选择
        relic_frame = ttk.LabelFrame(self.parent, text="仪器选择")
        relic_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 仪器选择按钮
        relic_btn_frame = ttk.Frame(relic_frame)
        relic_btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(relic_btn_frame, text="自动推荐仪器", 
                  command=self.auto_recommend_relics).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(relic_btn_frame, text="手动选择仪器", 
                  command=self.manual_select_relics).pack(side=tk.LEFT)
        
        # 当前装备显示
        current_frame = ttk.LabelFrame(self.parent, text="当前装备")
        current_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.current_equipment_text = tk.Text(current_frame, height=8, width=60)
        self.current_equipment_text.pack(fill=tk.X, pady=5)
        
        # 确认按钮
        confirm_frame = ttk.Frame(self.parent)
        confirm_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(confirm_frame, text="确认", command=self.confirm_equipment).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(confirm_frame, text="取消", command=self.parent.destroy).pack(side=tk.RIGHT)
        
        # 更新当前装备显示
        self.update_current_equipment()
    
    def update_light_cone_list(self):
        """更新光锥列表"""
        self.lc_listbox.delete(0, tk.END)
        
        search_term = self.lc_search_var.get().lower()
        
        for lc_id, lc in self.light_cones.items():
            if search_term and search_term not in lc.name.lower():
                continue
            self.lc_listbox.insert(tk.END, f"{lc.name} (ID: {lc_id})")
    
    def filter_light_cones(self, *args):
        """过滤光锥列表"""
        self.update_light_cone_list()
    
    def on_light_cone_select(self, event):
        """光锥选择事件"""
        selection = self.lc_listbox.curselection()
        if selection:
            index = selection[0]
            # 获取选中的光锥ID
            lc_items = [item for item in self.lc_listbox.get(0, tk.END)]
            if 0 <= index < len(lc_items):
                lc_text = lc_items[index]
                lc_id = lc_text.split("(ID: ")[1].split(")")[0]
                
                # 设置光锥
                self.character.light_cone_id = lc_id
                self.update_current_equipment()
    
    def auto_recommend_relics(self):
        """自动推荐仪器"""
        # 根据角色路径推荐仪器
        path = getattr(self.character, 'path', 'Hunt')
        
        # 简化的推荐逻辑
        recommended_sets = {
            'Hunt': ['Eagle of Twilight Line'],
            'Abundance': ['Fleet of the Ageless'],
            'Destruction': ['Eagle of Twilight Line'],
            'Harmony': ['Fleet of the Ageless']
        }
        
        recommended = recommended_sets.get(path, ['Eagle of Twilight Line'])
        
        # 设置推荐仪器
        self.character.relics_config = {
            "Head": "r1",
            "Hands": "r2", 
            "Body": "r3",
            "Feet": "r4",
            "PlanarSphere": "r5",
            "LinkRope": "r6"
        }
        
        self.update_current_equipment()
        messagebox.showinfo("推荐完成", f"已为 {self.character.name} 推荐 {recommended[0]} 套装")
    
    def manual_select_relics(self):
        """手动选择仪器"""
        # 这里可以打开一个更详细的仪器选择窗口
        messagebox.showinfo("提示", "手动选择仪器功能正在开发中")
    
    def update_current_equipment(self):
        """更新当前装备显示"""
        self.current_equipment_text.delete(1.0, tk.END)
        
        # 显示光锥
        lc_id = getattr(self.character, 'light_cone_id', None)
        if lc_id and lc_id in self.light_cones:
            lc = self.light_cones[lc_id]
            self.current_equipment_text.insert(tk.END, f"光锥: {lc.name} (ID: {lc_id})\n")
        else:
            self.current_equipment_text.insert(tk.END, "光锥: 未选择\n")
        
        # 显示仪器
        relics_config = getattr(self.character, 'relics_config', {})
        if relics_config:
            self.current_equipment_text.insert(tk.END, "\n仪器配置:\n")
            for slot, relic_id in relics_config.items():
                self.current_equipment_text.insert(tk.END, f"  {slot}: {relic_id}\n")
        else:
            self.current_equipment_text.insert(tk.END, "\n仪器: 未配置\n")
    
    def confirm_equipment(self):
        """确认装备选择"""
        messagebox.showinfo("成功", f"已为 {self.character.name} 配置装备")
        self.parent.destroy()


def main():
    """主函数"""
    root = tk.Tk()
    app = VisualSelector(root)
    root.mainloop()


if __name__ == "__main__":
    main() 