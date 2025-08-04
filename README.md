
# Star Rail Simulator

一个可扩展的星穹铁道战斗模拟器，支持角色与敌方单位，基于 Python 实现。

## 目录结构

```
├── data/                # 静态数据（角色、敌人、技能、装备等，json）
│   ├── characters.json
│   ├── enemy_summary.json
│   ├── MonsterConfig.json
│   ├── MonsterSkillConfig.json
│   ├── MonsterTemplateConfig.json
│   └── ...
├── icon/                # 角色、光锥、遗器等图标资源
│   ├── avatar/
│   ├── light_cone/
│   └── relic/
├── starrail/            # 主包，核心代码
│   ├── core/            # 战斗核心（角色、敌人、技能、Buff、回合等）
│   ├── engine/          # 战斗引擎（流程控制、事件系统等）
│   ├── plugins/         # 插件/扩展（新角色、AI、特殊机制等）
│   ├── utils/           # 工具函数
│   └── config.py        # 配置与常量
├── scripts/             # 命令行脚本/批量模拟
│   └── visual_selector.py
├── create_enemy.py      # 敌方角色创建脚本
├── main_simulator.py    # 主模拟器入口
├── requirements.txt     # 依赖
└── README.md
```

## 主要特性
- 支持角色与敌方单位的完整模拟
- 数据驱动，易于扩展和自定义
- 插件机制，支持新角色/技能/AI/机制扩展
- 面向对象设计，便于维护
- 图标资源丰富，支持可视化
- 命令行脚本与批量模拟

## 快速开始
1. 安装依赖：
   ```powershell
   pip install -r requirements.txt
   ```
2. 运行主模拟器：
   ```powershell
   python main_simulator.py
   ```
3. 创建/编辑敌方角色：
   ```powershell
   python create_enemy.py
   ```
4. 可选：运行可视化选择脚本
   ```powershell
   python scripts/visual_selector.py
   ```

## 依赖
- Python 3.8+
- 详见 `requirements.txt`

## 扩展与自定义
- 新角色/敌人：编辑 `data/characters.json` 或相关敌人配置文件
- 新技能/机制：在 `starrail/core/` 或 `starrail/plugins/` 中添加模块
- 图标资源：放置于 `icon/` 目录下对应子文件夹

## 贡献与反馈
欢迎 issue、PR 或建议！