# Star Rail Simulator

一个可扩展的星穹铁道战斗模拟器，基于 Python 实现。

## 目录结构

```
starrail_simulator/
├── data/                    # 静态数据（角色、技能、装备等，json/yaml/csv）
├── starrail/                # 主包，核心代码
│   ├── core/                # 战斗核心（角色、技能、Buff、回合等）
│   ├── engine/              # 战斗引擎（流程控制、事件系统等）
│   ├── plugins/             # 插件/扩展（新角色、AI、特殊机制等）
│   ├── utils/               # 工具函数
│   └── config.py            # 配置与常量
├── tests/                   # 单元测试
├── scripts/                 # 命令行脚本/批量模拟
├── requirements.txt         # 依赖
└── README.md
```

## 主要特性
- 数据驱动，易于扩展
- 面向对象设计，便于维护
- 插件机制，支持新角色/技能/AI扩展
- 单元测试，保证模拟器正确性

## 快速开始
1. 安装依赖：`pip install -r requirements.txt`
2. 运行模拟脚本：`python scripts/run_simulation.py` 