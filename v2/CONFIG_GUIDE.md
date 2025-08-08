# v2多窗口游戏自动化系统 - 配置指南

## 🎮 控制说明

### 停止脚本
- **Ctrl+Q**: 随时一键停止所有脚本，安全退出程序
- **Ctrl+C**: 在控制台中中断程序（传统方式）

## ⚙️ 配置参数说明

### 1. 战斗和点击范围配置

在 `config.py` 文件中的 `CONTROLLER_CONFIG['combat_area_ratio']` 部分：

```python
'combat_area_ratio': {
    'min_x': 0.2,               # 战斗区域左边界（窗口宽度比例）
    'max_x': 0.8,               # 战斗区域右边界（窗口宽度比例）
    'min_y': 0.2,               # 战斗区域上边界（窗口高度比例）
    'max_y': 0.8,               # 战斗区域下边界（窗口高度比例）
},
```

**说明：**
- 数值范围：0.0 - 1.0（代表窗口的百分比）
- `min_x: 0.2` = 从窗口左边20%的位置开始
- `max_x: 0.8` = 到窗口右边80%的位置结束
- 实际点击区域 = 窗口中间60%的区域

**示例配置：**
```python
# 更小的战斗区域（窗口中心40%区域）
'combat_area_ratio': {
    'min_x': 0.3, 'max_x': 0.7,
    'min_y': 0.3, 'max_y': 0.7,
},

# 更大的战斗区域（窗口90%区域）
'combat_area_ratio': {
    'min_x': 0.05, 'max_x': 0.95,
    'min_y': 0.05, 'max_y': 0.95,
},
```

### 2. 移动范围配置

在 `config.py` 文件中的 `CONTROLLER_CONFIG['movement_config']` 部分：

```python
'movement_config': {
    'movement_radius': 120,     # 移动半径（像素）
    'max_random_moves': 15,     # 最大随机移动次数
    'move_interval': 2.0,       # 移动间隔（秒）
},
```

**参数说明：**
- `movement_radius`: 角色移动的最大半径（像素单位）
  - 值越大，移动范围越大
  - 推荐范围：80-200像素
- `max_random_moves`: 随机移动多少次后回到中心
  - 防止角色走得太远
  - 推荐范围：10-30次
- `move_interval`: 移动操作的时间间隔
  - 值越小，移动越频繁
  - 推荐范围：1.5-3.0秒

**示例配置：**
```python
# 小范围移动（适合小地图）
'movement_config': {
    'movement_radius': 80,
    'max_random_moves': 10,
    'move_interval': 1.5,
},

# 大范围移动（适合大地图）
'movement_config': {
    'movement_radius': 200,
    'max_random_moves': 25,
    'move_interval': 2.5,
},
```

### 3. 攻击配置

```python
'attack_config': {
    'attack_interval': 1.2,     # 攻击间隔（秒）
    'skill_keys': ['Q', 'W', 'E', 'R'],  # 技能键
},
```

**参数说明：**
- `attack_interval`: 攻击频率控制
  - 值越小，攻击越频繁
  - 推荐范围：0.8-2.0秒
- `skill_keys`: 自动释放的技能键
  - 可以添加或删除技能键
  - 支持字母和数字键

## 🔧 实际应用示例

### 场景1：小窗口游戏（800x600）
```python
'combat_area_ratio': {
    'min_x': 0.25, 'max_x': 0.75,  # 中间50%区域
    'min_y': 0.25, 'max_y': 0.75,
},
'movement_config': {
    'movement_radius': 60,          # 小半径移动
    'max_random_moves': 8,
    'move_interval': 1.8,
},
```

### 场景2：全屏游戏（1920x1080）
```python
'combat_area_ratio': {
    'min_x': 0.15, 'max_x': 0.85,  # 大范围战斗区域
    'min_y': 0.15, 'max_y': 0.85,
},
'movement_config': {
    'movement_radius': 150,         # 大半径移动
    'max_random_moves': 20,
    'move_interval': 2.2,
},
```

### 场景3：保守模式（避免误操作）
```python
'combat_area_ratio': {
    'min_x': 0.4, 'max_x': 0.6,    # 仅窗口中心20%区域
    'min_y': 0.4, 'max_y': 0.6,
},
'movement_config': {
    'movement_radius': 40,          # 极小移动范围
    'max_random_moves': 5,
    'move_interval': 3.0,           # 较慢的移动频率
},
```

## 📝 配置修改步骤

1. **打开配置文件**：编辑 `v2/config.py`
2. **修改参数**：根据需要调整上述参数值
3. **保存文件**：保存配置文件
4. **重启程序**：重新运行多窗口管理器以应用新配置

## ⚠️ 注意事项

1. **范围比例**：combat_area_ratio的值必须在0.0-1.0之间
2. **移动半径**：movement_radius不要设置得过大，避免角色移动到危险区域
3. **攻击间隔**：attack_interval不要设置得过小，避免被游戏检测为外挂
4. **测试配置**：修改配置后建议先进行小范围测试

## 🚀 快速配置模板

复制以下代码到 `config.py` 中的 `CONTROLLER_CONFIG` 部分：

```python
CONTROLLER_CONFIG = {
    'auto_start': True,
    
    # 战斗区域（可根据需要调整）
    'combat_area_ratio': {
        'min_x': 0.2, 'max_x': 0.8,  # 左右各留20%边距
        'min_y': 0.2, 'max_y': 0.8,  # 上下各留20%边距
    },
    
    # 移动配置（可根据需要调整）
    'movement_config': {
        'movement_radius': 120,       # 移动半径120像素
        'max_random_moves': 15,       # 15次移动后回中心
        'move_interval': 2.0,         # 每2秒移动一次
    },
    
    # 攻击配置（可根据需要调整）
    'attack_config': {
        'attack_interval': 1.2,       # 每1.2秒攻击一次
        'skill_keys': ['Q', 'W', 'E', 'R'],  # 技能键
    },
    
    # 其他配置
    'check_interval': 3.0,
    'equipment_check_interval': 0.5,
}
```

现在你可以通过修改这些参数来精确控制脚本的行为范围！
