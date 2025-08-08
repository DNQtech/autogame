# -*- coding: utf-8 -*-
"""
v2多开智能游戏系统配置文件
"""

# 窗口扫描配置
WINDOW_SCAN_CONFIG = {
    'scan_interval': 5.0,           # 窗口扫描间隔（秒）
    'min_window_width': 120,        # 最小窗口宽度 (临时降低以检测微信)
    'min_window_height': 15,        # 最小窗口高度 (临时降低以检测微信)
}

# 目标游戏进程配置
TARGET_PROCESSES = [
    # 常见游戏进程名
    'Weixin.exe',


]

# 游戏窗口标题关键词
GAME_WINDOW_KEYWORDS = [
    # 中文关键词
    '钉钉', 
]

# 控制器配置
CONTROLLER_CONFIG = {
    'auto_start': True,             # 自动启动新发现的控制器
    
    # 战斗和移动范围配置
    'combat_area_ratio': {
        'min_x': 0.2,               # 战斗区域左边界（窗口宽度比例）
        'max_x': 0.8,               # 战斗区域右边界（窗口宽度比例）
        'min_y': 0.2,               # 战斗区域上边界（窗口高度比例）
        'max_y': 0.8,               # 战斗区域下边界（窗口高度比例）
    },
    
    'movement_config': {
        'movement_radius': 150,     # 移动半径（像素）- 基于v1版本优化
        'max_random_moves': 30,     # 最大随机移动次数 - 基于v1版本优化
        'move_interval': 2.0,       # 移动间隔（秒）
        'movement_mode': 'around_center',  # 移动模式：围绕屏幕中心移动（v1版本逻辑）
    },
    
    'attack_config': {
        'attack_interval': 1.5,     # 攻击间隔（秒）
        # 移除技能键系统 - 游戏没有技能攻击，只使用右键攻击
        # 'skill_keys': [],  # 不使用技能键
    },
    
    # 兼容旧配置（将被上面的新配置覆盖）
    'check_interval': 3.0,          # 控制器检查间隔（秒）
    'equipment_check_interval': 0.5, # 装备检测间隔（秒）
}

# 装备检测配置
EQUIPMENT_CONFIG = {
    'templates_folder': '../templates',  # 装备模板文件夹
    'detection_threshold': 0.8,          # 检测阈值
    'pickup_attempts': 5,                # 拾取尝试次数
    'pickup_interval': 0.1,              # 拾取间隔（秒）
    'pickup_timeout': 3.0,               # 拾取超时（秒）
}

# 截图配置
SCREENSHOT_CONFIG = {
    'cache_timeout': 0.1,           # 截图缓存超时（秒）
    'max_cache_size': 10,           # 最大缓存数量
    'screenshot_quality': 95,       # 截图质量 (1-100)
}

# 分辨率适配配置
RESOLUTION_CONFIG = {
    'base_width': 1920,             # 基准宽度
    'base_height': 1080,            # 基准高度
    'combat_area_ratio': {          # 战斗区域比例
        'min_x': 0.3,
        'max_x': 0.7,
        'min_y': 0.3,
        'max_y': 0.7,
    }
}

# 日志配置
LOGGING_CONFIG = {
    'level': 'INFO',                # 日志级别: DEBUG, INFO, WARNING, ERROR
    'console_output': True,         # 控制台输出
    'file_output': False,           # 文件输出
    'log_file': 'v2_system.log',    # 日志文件名
    'max_file_size': 10,            # 最大文件大小（MB）
    'backup_count': 5,              # 备份文件数量
}

# 性能配置
PERFORMANCE_CONFIG = {
    'max_threads': 20,              # 最大线程数
    'thread_pool_size': 10,         # 线程池大小
    'memory_limit': 512,            # 内存限制（MB）
    'cpu_usage_limit': 80,          # CPU使用率限制（%）
}

# 安全配置
SECURITY_CONFIG = {
    'enable_window_validation': True,    # 启用窗口验证
    'max_controllers': 10,               # 最大控制器数量
    'operation_timeout': 5.0,            # 操作超时（秒）
    'safe_mode': False,                  # 安全模式（仅检测不操作）
}

# 调试配置
DEBUG_CONFIG = {
    'save_screenshots': False,      # 保存调试截图
    'screenshot_folder': 'debug_screenshots',
    'verbose_logging': False,       # 详细日志
    'show_detection_boxes': False,  # 显示检测框
    'performance_monitoring': True, # 性能监控
}

# 快捷键配置
HOTKEY_CONFIG = {
    'pause_all': 'F9',              # 暂停所有控制器
    'resume_all': 'F10',            # 恢复所有控制器
    'emergency_stop': 'F12',        # 紧急停止
    'show_status': 'F8',            # 显示状态
}

# 获取配置函数
def get_config(config_name: str = None):
    """获取配置"""
    configs = {
        'window_scan': WINDOW_SCAN_CONFIG,
        'target_processes': TARGET_PROCESSES,
        'game_keywords': GAME_WINDOW_KEYWORDS,
        'controller': CONTROLLER_CONFIG,
        'equipment': EQUIPMENT_CONFIG,
        'screenshot': SCREENSHOT_CONFIG,
        'resolution': RESOLUTION_CONFIG,
        'logging': LOGGING_CONFIG,
        'performance': PERFORMANCE_CONFIG,
        'security': SECURITY_CONFIG,
        'debug': DEBUG_CONFIG,
        'hotkey': HOTKEY_CONFIG,
    }
    
    if config_name:
        return configs.get(config_name, {})
    
    return configs

# 验证配置
def validate_config():
    """验证配置有效性"""
    errors = []
    
    # 验证基本数值
    if CONTROLLER_CONFIG['fight_interval'] <= 0:
        errors.append("fight_interval 必须大于 0")
    
    if CONTROLLER_CONFIG['move_interval'] <= 0:
        errors.append("move_interval 必须大于 0")
    
    if EQUIPMENT_CONFIG['detection_threshold'] < 0 or EQUIPMENT_CONFIG['detection_threshold'] > 1:
        errors.append("detection_threshold 必须在 0-1 之间")
    
    if WINDOW_SCAN_CONFIG['min_window_width'] < 100:
        errors.append("min_window_width 不能小于 100")
    
    if WINDOW_SCAN_CONFIG['min_window_height'] < 100:
        errors.append("min_window_height 不能小于 100")
    
    # 验证路径
    import os
    template_path = EQUIPMENT_CONFIG['templates_folder']
    if not os.path.exists(template_path) and not os.path.isabs(template_path):
        # 相对路径，检查是否存在
        from pathlib import Path
        abs_path = Path(__file__).parent / template_path
        if not abs_path.exists():
            errors.append(f"装备模板文件夹不存在: {template_path}")
    
    return errors

if __name__ == "__main__":
    # 配置验证测试
    print("🔧 v2系统配置验证")
    
    errors = validate_config()
    if errors:
        print("❌ 配置验证失败:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✅ 配置验证通过")
    
    # 显示主要配置
    print(f"\n📋 主要配置:")
    print(f"目标进程: {len(TARGET_PROCESSES)} 个")
    print(f"窗口关键词: {len(GAME_WINDOW_KEYWORDS)} 个")
    print(f"自动启动控制器: {CONTROLLER_CONFIG['auto_start']}")
    print(f"装备检测阈值: {EQUIPMENT_CONFIG['detection_threshold']}")
    print(f"基准分辨率: {RESOLUTION_CONFIG['base_width']}x{RESOLUTION_CONFIG['base_height']}")

