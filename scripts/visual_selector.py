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

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from starrail.utils.data_loader import load_characters, load_skills, load_light_cones, load_relics, load_processed_enemies
from starrail.core.equipment_manager import RelicManager

def create_relic_name_to_id_mapping():
    """创建仪器名称到ID的映射"""
    try:
        # 加载relic_skills.json
        relic_skills_path = os.path.join(os.path.dirname(__file__), '../data/relic_skills.json')
        with open(relic_skills_path, 'r', encoding='utf-8') as f:
            relic_skills_data = json.load(f)
        
        # 创建名称到ID的映射
        name_to_id = {}
        for relic in relic_skills_data:
            name_to_id[relic['name']] = relic['id']
        
        return name_to_id
    except Exception as e:
        print(f"加载仪器映射失败: {e}")
        return {}

# 全局变量存储映射
RELIC_NAME_TO_ID = create_relic_name_to_id_mapping()

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
            
            # 加载敌人数据
            self.enemies = load_processed_enemies(os.path.join(self.data_path, 'processed_enemies.json'))
            
            self.light_cones = light_cones_data
            self.relics = relics_data
            self.relic_manager = RelicManager(self.relics)
            
            print(f"✅ 数据加载成功:")
            print(f"   角色: {len(self.characters)} 个")
            print(f"   光锥: {len(self.light_cones)} 个")
            print(f"   仪器: {len(self.relics)} 个")
            print(f"   敌人: {len(self.enemies)} 个")
            
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
        # 创建左右分栏
        left_frame = ttk.Frame(self.enemy_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        right_frame = ttk.Frame(self.enemy_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # 左侧：敌人选择
        ttk.Label(left_frame, text="敌人选择", font=("Arial", 14, "bold")).pack(pady=5)
        
        # 敌人搜索框
        enemy_search_frame = ttk.Frame(left_frame)
        enemy_search_frame.pack(fill=tk.X, pady=5)
        ttk.Label(enemy_search_frame, text="搜索:").pack(side=tk.LEFT)
        self.enemy_search_var = tk.StringVar()
        self.enemy_search_var.trace('w', self.filter_enemies)
        ttk.Entry(enemy_search_frame, textvariable=self.enemy_search_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # 敌人列表框架
        enemy_list_frame = ttk.Frame(left_frame)
        enemy_list_frame.pack(fill=tk.BOTH, expand=True)
        
        # 敌人列表
        self.enemy_canvas = tk.Canvas(enemy_list_frame)
        enemy_scrollbar = ttk.Scrollbar(enemy_list_frame, orient="vertical", command=self.enemy_canvas.yview)
        self.enemy_canvas.configure(yscrollcommand=enemy_scrollbar.set)
        
        self.enemy_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        enemy_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.enemy_inner_frame = ttk.Frame(self.enemy_canvas)
        self.enemy_canvas.create_window((0, 0), window=self.enemy_inner_frame, anchor="nw")
        
        # 右侧：当前敌人
        ttk.Label(right_frame, text="当前敌人", font=("Arial", 14, "bold")).pack(pady=5)
        
        # 敌人列表
        self.enemy_listbox = tk.Listbox(right_frame, height=8)
        self.enemy_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 敌人操作按钮
        enemy_btn_frame = ttk.Frame(right_frame)
        enemy_btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(enemy_btn_frame, text="移除选中", command=self.remove_enemy).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(enemy_btn_frame, text="清空敌人", command=self.clear_enemies).pack(side=tk.LEFT)
        
        # 初始化敌人列表
        self.update_enemy_list()
        
        # 绑定事件
        self.enemy_inner_frame.bind("<Configure>", lambda e: self.enemy_canvas.configure(scrollregion=self.enemy_canvas.bbox("all")))
    
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
    
    def update_enemy_list(self):
        """更新敌人列表"""
        # 清空现有内容
        for widget in self.enemy_inner_frame.winfo_children():
            widget.destroy()
        
        # 获取搜索关键词
        search_term = self.enemy_search_var.get().lower()
        
        # 创建敌人卡片
        row = 0
        col = 0
        max_cols = 3
        
        for enemy in self.enemies:
            if search_term and search_term not in enemy.name.lower():
                continue
                
            # 创建敌人卡片框架
            card_frame = ttk.Frame(self.enemy_inner_frame)
            card_frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            
            # 敌人名称
            name_label = ttk.Label(card_frame, text=enemy.name, font=("Arial", 10, "bold"))
            name_label.pack()
            
            # 敌人信息
            info_text = f"ID: {enemy.id}\nRank: {getattr(enemy, 'rank', 'Unknown')}"
            info_label = ttk.Label(card_frame, text=info_text, font=("Arial", 8))
            info_label.pack()
            
            # 添加按钮
            add_btn = ttk.Button(card_frame, text="添加", 
                               command=lambda e=enemy: self.add_enemy_to_list(e))
            add_btn.pack(pady=2)
            
            # 更新行列位置
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        # 配置网格权重
        for i in range(max_cols):
            self.enemy_inner_frame.columnconfigure(i, weight=1)
    
    def filter_characters(self, *args):
        """过滤角色列表"""
        self.update_character_list()
    
    def filter_enemies(self, *args):
        """过滤敌人列表"""
        self.update_enemy_list()
    
    def add_to_team(self, character):
        """添加角色到队伍"""
        if len(self.current_team) >= 4:
            messagebox.showwarning("警告", "队伍最多只能有4个角色")
            return
        
        # 检查是否已经在队伍中
        if any(char.id == character.id for char in self.current_team):
            messagebox.showwarning("警告", f"{character.name} 已经在队伍中")
            return
        
        # 打开装备选择窗口，不立即添加到队伍
        self.open_equipment_selector(character)
    
    def add_enemy_to_list(self, enemy):
        """添加敌人到列表"""
        # 检查是否已经在列表中
        if any(e.id == enemy.id for e in self.current_enemies):
            messagebox.showwarning("警告", f"{enemy.name} 已经在敌人列表中")
            return
        
        # 添加到敌人列表
        self.current_enemies.append(enemy)
        self.update_enemy_display()
        self.update_config_preview()
        
        messagebox.showinfo("成功", f"已添加敌人: {enemy.name}")
    
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
        
        EquipmentSelector(equipment_window, character, self.light_cones, self.relic_manager, self)
    
    def remove_enemy(self):
        """移除敌人"""
        selection = self.enemy_listbox.curselection()
        if selection:
            index = selection[0]
            if 0 <= index < len(self.current_enemies):
                removed_enemy = self.current_enemies.pop(index)
                self.update_enemy_display()
                self.update_config_preview()
                messagebox.showinfo("信息", f"已移除敌人: {removed_enemy.name}")
    
    def clear_enemies(self):
        """清空敌人"""
        self.current_enemies.clear()
        self.update_enemy_display()
        self.update_config_preview()
        messagebox.showinfo("信息", "敌人列表已清空")
    
    def update_enemy_display(self):
        """更新敌人显示"""
        self.enemy_listbox.delete(0, tk.END)
        for enemy in self.current_enemies:
            rank_info = f" ({getattr(enemy, 'rank', 'Unknown')})" if hasattr(enemy, 'rank') else ""
            self.enemy_listbox.insert(tk.END, f"{enemy.name} (ID: {enemy.id}){rank_info}")
    
    def update_config_preview(self):
        """更新配置预览"""
        config = {
            "team": [],
            "enemies": [],
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
        
        # 添加敌人信息
        for enemy in self.current_enemies:
            enemy_info = {
                "id": enemy.id,
                "name": enemy.name,
                "rank": getattr(enemy, 'rank', 'Unknown'),
                "stats": enemy.stats,
                "skills": getattr(enemy, 'skills', []),
                "weaknesses": getattr(enemy, 'weaknesses', []),
                "resistances": getattr(enemy, 'resistances', {}),
                "toughness": getattr(enemy, 'toughness', 100),
                "max_toughness": getattr(enemy, 'max_toughness', 100),
                "ai_type": getattr(enemy, 'ai_type', 'default'),
                "elite_group": getattr(enemy, 'elite_group', 1)
            }
            config["enemies"].append(enemy_info)
        
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
            "enemies": [],
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
        
        # 添加敌人信息
        for enemy in self.current_enemies:
            enemy_info = {
                "id": enemy.id,
                "name": enemy.name,
                "rank": getattr(enemy, 'rank', 'Unknown'),
                "stats": enemy.stats,
                "skills": getattr(enemy, 'skills', []),
                "weaknesses": getattr(enemy, 'weaknesses', []),
                "resistances": getattr(enemy, 'resistances', {}),
                "toughness": getattr(enemy, 'toughness', 100),
                "max_toughness": getattr(enemy, 'max_toughness', 100),
                "ai_type": getattr(enemy, 'ai_type', 'default'),
                "elite_group": getattr(enemy, 'elite_group', 1)
            }
            config["enemies"].append(enemy_info)
        
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
                for enemy_data in config.get('enemies', []):
                    enemy_id = enemy_data.get('id')
                    enemy = next((e for e in self.enemies if e.id == enemy_id), None)
                    if enemy:
                        # 更新敌人属性（如果需要）
                        if 'stats' in enemy_data:
                            enemy.stats.update(enemy_data['stats'])
                        if 'weaknesses' in enemy_data:
                            enemy.weaknesses = enemy_data['weaknesses']
                        if 'resistances' in enemy_data:
                            enemy.resistances = enemy_data['resistances']
                        if 'toughness' in enemy_data:
                            enemy.toughness = enemy_data['toughness']
                        if 'max_toughness' in enemy_data:
                            enemy.max_toughness = enemy_data['max_toughness']
                        if 'ai_type' in enemy_data:
                            enemy.ai_type = enemy_data['ai_type']
                        if 'elite_group' in enemy_data:
                            enemy.elite_group = enemy_data['elite_group']
                        
                        self.current_enemies.append(enemy)
                
                # 更新显示
                self.update_team_display()
                self.update_enemy_display()
                self.update_config_preview()
                
                messagebox.showinfo("成功", f"配置已从 {config_path} 加载")
                
            except Exception as e:
                messagebox.showerror("错误", f"加载失败: {e}")


class EquipmentSelector:
    def __init__(self, parent, character, light_cones, relic_manager, visual_selector=None):
        self.parent = parent
        self.character = character
        self.light_cones = light_cones
        self.relic_manager = relic_manager
        self.visual_selector = visual_selector  # 添加对主选择器的引用
        
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
        
        # 光锥列表框架（使用Canvas和Scrollbar）
        lc_list_frame = ttk.Frame(light_cone_frame)
        lc_list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 光锥Canvas
        self.lc_canvas = tk.Canvas(lc_list_frame, height=200)
        lc_scrollbar = ttk.Scrollbar(lc_list_frame, orient="vertical", command=self.lc_canvas.yview)
        self.lc_canvas.configure(yscrollcommand=lc_scrollbar.set)
        
        self.lc_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        lc_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.lc_inner_frame = ttk.Frame(self.lc_canvas)
        self.lc_canvas.create_window((0, 0), window=self.lc_inner_frame, anchor="nw")
        
        # 更新光锥列表
        self.update_light_cone_list()
        
        # 绑定事件
        self.lc_inner_frame.bind("<Configure>", lambda e: self.lc_canvas.configure(scrollregion=self.lc_canvas.bbox("all")))
        
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
        # 清空现有内容
        for widget in self.lc_inner_frame.winfo_children():
            widget.destroy()
        
        # 获取搜索关键词
        search_term = self.lc_search_var.get().lower()
        
        # 创建光锥卡片
        row = 0
        col = 0
        max_cols = 6  # 每行显示6个光锥
        
        for lc_id, lc in self.light_cones.items():
            if search_term and search_term not in lc.name.lower():
                continue
                
            # 创建光锥卡片框架
            card_frame = ttk.Frame(self.lc_inner_frame)
            card_frame.grid(row=row, column=col, padx=3, pady=3, sticky="nsew")
            
            # 尝试加载光锥图标
            try:
                icon_path = os.path.join(os.path.dirname(__file__), '../icon/light_cone', f"{lc_id}.webp")
                if os.path.exists(icon_path):
                    image = Image.open(icon_path)
                    image = image.resize((48, 48), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(image)
                    
                    # 创建图标标签
                    icon_label = ttk.Label(card_frame, image=photo)
                    icon_label.image = photo  # 保持引用
                    icon_label.pack()
                else:
                    # 如果没有图标，显示ID
                    ttk.Label(card_frame, text=lc_id, font=("Arial", 8)).pack()
            except Exception as e:
                # 如果加载失败，显示ID
                ttk.Label(card_frame, text=lc_id, font=("Arial", 8)).pack()
            
            # 光锥名称（缩短显示）
            name = lc.name
            if len(name) > 12:
                name = name[:10] + "..."
            name_label = ttk.Label(card_frame, text=name, font=("Arial", 8), wraplength=60)
            name_label.pack()
            
            # 选择按钮
            select_btn = ttk.Button(card_frame, text="选择", 
                                  command=lambda lc_id=lc_id: self.select_light_cone(lc_id))
            select_btn.pack(pady=1)
            
            # 更新行列位置
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        # 配置网格权重
        for i in range(max_cols):
            self.lc_inner_frame.columnconfigure(i, weight=1)
    
    def filter_light_cones(self, *args):
        """过滤光锥列表"""
        self.update_light_cone_list()
    
    def select_light_cone(self, lc_id):
        """选择光锥"""
        # 设置光锥
        self.character.light_cone_id = lc_id
        self.update_current_equipment()
        
        # 显示选择确认
        lc_name = self.light_cones[lc_id].name if lc_id in self.light_cones else lc_id
        messagebox.showinfo("选择成功", f"已为 {self.character.name} 选择光锥: {lc_name}")
    
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
        # 打开详细的仪器选择窗口
        relic_window = tk.Toplevel(self.parent)
        relic_window.title(f"为 {self.character.name} 手动选择仪器")
        relic_window.geometry("1000x700")
        
        RelicSelector(relic_window, self.character, self.relic_manager, self)
    
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
        # 检查是否已经在队伍中
        if self.visual_selector and any(char.id == self.character.id for char in self.visual_selector.current_team):
            messagebox.showwarning("警告", f"{self.character.name} 已经在队伍中")
            return
        
        # 添加到队伍
        if self.visual_selector:
            self.visual_selector.current_team.append(self.character)
            self.visual_selector.update_team_display()
            self.visual_selector.update_config_preview()
            messagebox.showinfo("成功", f"已为 {self.character.name} 配置装备并添加到队伍")
        else:
            messagebox.showinfo("成功", f"已为 {self.character.name} 配置装备")
        
        self.parent.destroy()


class RelicSelector:
    def __init__(self, parent, character, relic_manager, equipment_selector):
        self.parent = parent
        self.character = character
        self.relic_manager = relic_manager
        self.equipment_selector = equipment_selector
        
        # 当前选择的仪器配置
        self.current_relics = getattr(character, 'relics_config', {}).copy()
        
        # 仪器部位映射
        self.slot_names = {
            "Head": "头部",
            "Hands": "手部", 
            "Body": "身体",
            "Feet": "脚部",
            "PlanarSphere": "位面球",
            "LinkRope": "连接绳"
        }
        
        self.create_widgets()
    
    def create_widgets(self):
        """创建仪器选择界面"""
        # 标题
        ttk.Label(self.parent, text=f"为 {self.character.name} 选择仪器", 
                 font=("Arial", 14, "bold")).pack(pady=10)
        
        # 创建主框架
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 左侧：仪器选择
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # 仪器搜索
        search_frame = ttk.Frame(left_frame)
        search_frame.pack(fill=tk.X, pady=5)
        ttk.Label(search_frame, text="搜索仪器:").pack(side=tk.LEFT)
        self.relic_search_var = tk.StringVar()
        self.relic_search_var.trace('w', self.filter_relics)
        ttk.Entry(search_frame, textvariable=self.relic_search_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # 仪器列表框架
        relic_list_frame = ttk.Frame(left_frame)
        relic_list_frame.pack(fill=tk.BOTH, expand=True)
        
        # 仪器列表
        self.relic_canvas = tk.Canvas(relic_list_frame)
        relic_scrollbar = ttk.Scrollbar(relic_list_frame, orient="vertical", command=self.relic_canvas.yview)
        self.relic_canvas.configure(yscrollcommand=relic_scrollbar.set)
        
        self.relic_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        relic_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.relic_inner_frame = ttk.Frame(self.relic_canvas)
        self.relic_canvas.create_window((0, 0), window=self.relic_inner_frame, anchor="nw")
        
        # 右侧：当前配置
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        ttk.Label(right_frame, text="当前仪器配置", font=("Arial", 12, "bold")).pack(pady=5)
        
        # 当前配置显示
        self.config_text = tk.Text(right_frame, height=20, width=40)
        self.config_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 按钮框架
        btn_frame = ttk.Frame(right_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="清空配置", command=self.clear_relics).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="确认", command=self.confirm_relics).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(btn_frame, text="取消", command=self.parent.destroy).pack(side=tk.RIGHT)
        
        # 初始化仪器列表
        self.update_relic_list()
        self.update_config_display()
        
        # 绑定事件
        self.relic_inner_frame.bind("<Configure>", lambda e: self.relic_canvas.configure(scrollregion=self.relic_canvas.bbox("all")))
    
    def update_relic_list(self):
        """更新仪器列表"""
        # 清空现有内容
        for widget in self.relic_inner_frame.winfo_children():
            widget.destroy()
        
        # 获取搜索关键词
        search_term = self.relic_search_var.get().lower()
        
        # 按套装分组仪器
        relic_sets = {}
        for relic_id, relic in self.relic_manager.relics.items():
            if search_term and search_term not in relic.name.lower():
                continue
            
            set_name = relic.set_name if relic.set_name else "未知套装"
            if set_name not in relic_sets:
                relic_sets[set_name] = []
            relic_sets[set_name].append((relic_id, relic))
        
        # 创建套装分组显示
        current_row = 0
        max_cols = 4
        
        for set_name, relics in relic_sets.items():
            # 创建套装标题
            set_frame = ttk.Frame(self.relic_inner_frame)
            set_frame.grid(row=current_row, column=0, columnspan=max_cols, sticky="ew", padx=5, pady=5)
            
            # 套装名称标签
            set_label = ttk.Label(set_frame, text=f"📦 {set_name} ({len(relics)}件)", 
                                font=("Arial", 10, "bold"), foreground="purple")
            set_label.pack(anchor="w")
            
            current_row += 1
            
            # 创建该套装下的仪器卡片
            row = current_row
            col = 0
            
            for relic_id, relic in relics:
                # 创建仪器卡片框架
                card_frame = ttk.Frame(self.relic_inner_frame)
                card_frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
                
                # 尝试加载仪器图标
                try:
                    # 使用名称到ID的映射
                    icon_id = RELIC_NAME_TO_ID.get(relic.name, relic_id)
                    icon_path = os.path.join(os.path.dirname(__file__), '../icon/relic', f"{icon_id}.webp")
                    if os.path.exists(icon_path):
                        image = Image.open(icon_path)
                        image = image.resize((48, 48), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(image)
                        
                        # 创建图标标签
                        icon_label = ttk.Label(card_frame, image=photo)
                        icon_label.image = photo
                        icon_label.pack()
                    else:
                        # 如果没有图标，显示名称
                        ttk.Label(card_frame, text=relic.name[:8], font=("Arial", 8)).pack()
                except Exception as e:
                    # 如果加载失败，显示名称
                    ttk.Label(card_frame, text=relic.name[:8], font=("Arial", 8)).pack()
                
                # 仪器名称
                name = relic.name
                if len(name) > 15:
                    name = name[:12] + "..."
                name_label = ttk.Label(card_frame, text=name, font=("Arial", 8), wraplength=80)
                name_label.pack()
                
                # 仪器部位
                if relic.slot:
                    slot_name = self.slot_names.get(relic.slot, relic.slot)
                    slot_label = ttk.Label(card_frame, text=slot_name, font=("Arial", 7), foreground="blue")
                    slot_label.pack()
                
                # 主属性
                if relic.main_stat:
                    main_stat_text = ""
                    for stat, value in relic.main_stat.items():
                        if stat in ["CRIT Rate", "CRIT DMG", "Effect Hit Rate", "Effect RES"]:
                            main_stat_text += f"{stat}: {value:.1%}\n"
                        else:
                            main_stat_text += f"{stat}: {value:.0f}\n"
                    main_label = ttk.Label(card_frame, text=main_stat_text.strip(), font=("Arial", 7), foreground="green")
                    main_label.pack()
                
                # 选择按钮
                select_btn = ttk.Button(card_frame, text="选择", 
                                      command=lambda r=relic: self.select_relic(r))
                select_btn.pack(pady=2)
                
                # 更新行列位置
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
            
            # 更新当前行位置
            current_row = row + 1
        
        # 配置网格权重
        for i in range(max_cols):
            self.relic_inner_frame.columnconfigure(i, weight=1)
    
    def filter_relics(self, *args):
        """过滤仪器列表"""
        self.update_relic_list()
    
    def select_relic(self, relic):
        """选择仪器"""
        # 自动根据仪器的slot属性分配部位
        if relic.slot:
            slot = relic.slot
        else:
            # 如果没有slot属性，显示错误信息
            messagebox.showerror("错误", f"仪器 {relic.name} 没有部位信息")
            return
        
        # 直接分配仪器到对应部位
        self.assign_relic_to_slot(relic, slot, None)
    
    def assign_relic_to_slot(self, relic, slot, slot_window):
        """将仪器分配到指定部位"""
        # 检查该部位是否已有仪器
        if slot in self.current_relics:
            old_relic_id = self.current_relics[slot]
            result = messagebox.askyesno("确认替换", 
                                       f"部位 {self.slot_names[slot]} 已有仪器 {old_relic_id}，是否替换为 {relic.name}？")
            if not result:
                return
        
        # 分配仪器
        self.current_relics[slot] = relic.id
        self.update_config_display()
        
        # 如果slot_window存在，则关闭它
        if slot_window:
            slot_window.destroy()
        
        messagebox.showinfo("成功", f"已将 {relic.name} 分配到 {self.slot_names[slot]} 部位")
    
    def clear_relics(self):
        """清空仪器配置"""
        self.current_relics.clear()
        self.update_config_display()
        messagebox.showinfo("成功", "已清空仪器配置")
    
    def update_config_display(self):
        """更新配置显示"""
        self.config_text.delete(1.0, tk.END)
        
        if not self.current_relics:
            self.config_text.insert(tk.END, "未配置任何仪器\n")
            return
        
        self.config_text.insert(tk.END, "当前仪器配置:\n\n")
        
        for slot, relic_id in self.current_relics.items():
            slot_name = self.slot_names.get(slot, slot)
            relic = self.relic_manager.relics.get(relic_id)
            
            if relic:
                self.config_text.insert(tk.END, f"{slot_name}:\n")
                self.config_text.insert(tk.END, f"  {relic.name} (ID: {relic_id})\n")
                
                # 显示主属性
                if relic.main_stat:
                    self.config_text.insert(tk.END, "  主属性:\n")
                    for stat, value in relic.main_stat.items():
                        if stat in ["CRIT Rate", "CRIT DMG", "Effect Hit Rate", "Effect RES"]:
                            self.config_text.insert(tk.END, f"    {stat}: {value:.1%}\n")
                        else:
                            self.config_text.insert(tk.END, f"    {stat}: {value:.0f}\n")
                
                # 显示副属性
                if relic.sub_stats:
                    self.config_text.insert(tk.END, "  副属性:\n")
                    for sub in relic.sub_stats[:3]:  # 只显示前3个副属性
                        stat = sub.get("stat", "")
                        value = sub.get("value", 0)
                        if stat in ["CRIT Rate", "CRIT DMG", "Effect Hit Rate", "Effect RES"]:
                            self.config_text.insert(tk.END, f"    {stat}: {value:.1%}\n")
                        else:
                            self.config_text.insert(tk.END, f"    {stat}: {value:.0f}\n")
                
                self.config_text.insert(tk.END, "\n")
            else:
                self.config_text.insert(tk.END, f"{slot_name}: 未知仪器 (ID: {relic_id})\n\n")
    
    def confirm_relics(self):
        """确认仪器配置"""
        # 更新角色的仪器配置
        self.character.relics_config = self.current_relics.copy()
        
        # 更新装备选择器的显示
        if self.equipment_selector:
            self.equipment_selector.update_current_equipment()
        
        messagebox.showinfo("成功", f"已为 {self.character.name} 配置仪器")
        self.parent.destroy()


def main():
    """主函数"""
    root = tk.Tk()
    app = VisualSelector(root)
    root.mainloop()


if __name__ == "__main__":
    main() 