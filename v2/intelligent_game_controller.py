# -*- coding: utf-8 -*-
"""
v2智能游戏控制器
支持非激活窗口的智能自动化控制，自适应分辨率
"""

import sys
import time
import threading
import queue
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
import cv2
import numpy as np
import win32con
import win32gui

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from template_equipment_detector import TemplateEquipmentDetector, EquipmentMatch
from multi_window_manager import MultiWindowManager, WindowInfo, GameInstance
from v2.config import CONTROLLER_CONFIG
from hotkey_manager import global_stop_manager

@dataclass
class AdaptiveSettings:
    """自适应设置"""
    window_width: int
    window_height: int
    scale_factor_x: float
    scale_factor_y: float
    center_x: int
    center_y: int
    combat_area: Dict[str, int]  # 战斗区域
    
    @classmethod
    def from_window_size(cls, width: int, height: int, base_width: int = 1920, base_height: int = 1080):
        """根据窗口尺寸创建自适应设置"""
        scale_x = width / base_width
        scale_y = height / base_height
        
        # 从配置文件获取战斗区域比例
        combat_ratio = CONTROLLER_CONFIG.get('combat_area_ratio', {
            'min_x': 0.2, 'max_x': 0.8, 'min_y': 0.2, 'max_y': 0.8
        })
        
        return cls(
            window_width=width,
            window_height=height,
            scale_factor_x=scale_x,
            scale_factor_y=scale_y,
            center_x=width // 2,
            center_y=height // 2,
            combat_area={
                'min_x': int(width * combat_ratio['min_x']),
                'max_x': int(width * combat_ratio['max_x']),
                'min_y': int(height * combat_ratio['min_y']),
                'max_y': int(height * combat_ratio['max_y'])
            }
        )
    
    def scale_position(self, x: int, y: int) -> Tuple[int, int]:
        """缩放坐标位置"""
        return (int(x * self.scale_factor_x), int(y * self.scale_factor_y))

class IntelligentGameController:
    """智能游戏控制器 - v2版本"""
    
    def __init__(self, hwnd: int, window_manager: MultiWindowManager):
        self.hwnd = hwnd
        self.window_manager = window_manager
        self.window_info: Optional[WindowInfo] = None
        self.adaptive_settings: Optional[AdaptiveSettings] = None
        
        # 控制状态
        self.is_running = False
        self.is_fighting = False
        self.is_picking_up = False
        self.should_stop = False
        
        # 线程管理
        self.control_thread = None
        self.equipment_monitor_thread = None
        self.control_lock = threading.Lock()
        
        # 装备检测 - 升级为v1版本的智能管理系统
        self.equipment_detector = None
        self.equipment_queue = []  # 改为列表，支持更复杂的队列管理
        self.last_equipment_check = 0
        self.equipment_check_interval = CONTROLLER_CONFIG.get('equipment_check_interval', 0.5)
        self.last_pickup_time = 0  # 上次拾取时间
        self.pickup_cooldown = 2.0  # 拾取冷却时间（秒）
        self.pickup_safe_distance = 50  # 拾取安全距离（像素）
        
        # 战斗参数（从配置文件读取）
        attack_config = CONTROLLER_CONFIG.get('attack_config', {})
        self.fight_interval = attack_config.get('attack_interval', 1.2)
        # 移除技能键系统 - 游戏没有技能攻击
        # self.skill_keys = []  # 不使用技能键
        
        # 移动参数（从配置文件读取） - 升级为v1版本的智能移动系统
        movement_config = CONTROLLER_CONFIG.get('movement_config', {})
        self.move_interval = movement_config.get('move_interval', 2.0)
        self.movement_radius = movement_config.get('movement_radius', 150)  # 增加移动半径
        self.max_random_moves = movement_config.get('max_random_moves', 30)  # 增加随机移动次数
        
        # v1版本的屏幕中心移动系统
        self.screen_width = 1920
        self.screen_height = 1080
        self.screen_center_x = self.screen_width // 2
        self.screen_center_y = self.screen_height // 2
        self.movement_mode = 'around_center'  # 围绕屏幕中心移动
        
        # 时间跟踪
        self.last_attack_time = 0
        self.last_move_time = 0
        self.random_move_count = 0
        
        # 注册全局停止回调
        global_stop_manager.register_stop_callback(self.stop)
        
        print(f"[CONTROLLER] 智能控制器初始化: HWND={hwnd}")
    
    def initialize(self) -> bool:
        """初始化控制器"""
        try:
            # 获取窗口信息
            game_instance = self.window_manager.get_game_instance(self.hwnd)
            if not game_instance:
                print(f"[CONTROLLER] 找不到游戏实例: HWND={self.hwnd}")
                return False
            
            self.window_info = game_instance.window_info
            
            # 创建自适应设置
            self.adaptive_settings = AdaptiveSettings.from_window_size(
                self.window_info.width,
                self.window_info.height
            )
            
            print(f"[CONTROLLER] 自适应设置:")
            print(f"  窗口尺寸: {self.adaptive_settings.window_width}x{self.adaptive_settings.window_height}")
            print(f"  缩放因子: {self.adaptive_settings.scale_factor_x:.2f}x{self.adaptive_settings.scale_factor_y:.2f}")
            print(f"  战斗区域: {self.adaptive_settings.combat_area}")
            
            # 初始化装备检测器
            self.equipment_detector = TemplateEquipmentDetector()
            
            # 加载装备模板
            template_dir = project_root / "templates"
            if template_dir.exists():
                loaded_count = self.equipment_detector.load_templates_from_folder(str(template_dir))
                print(f"[CONTROLLER] 加载装备模板: {loaded_count} 个")
                
                if loaded_count == 0:
                    print(f"[CONTROLLER] 警告: 未加载到装备模板")
            else:
                print(f"[CONTROLLER] 警告: 模板目录不存在: {template_dir}")
            
            return True
            
        except Exception as e:
            print(f"[CONTROLLER] 初始化失败: {e}")
            return False
    
    def start(self):
        """启动智能控制"""
        if self.is_running:
            print(f"[CONTROLLER] 控制器已在运行: HWND={self.hwnd}")
            return
        
        if not self.initialize():
            print(f"[CONTROLLER] 初始化失败，无法启动: HWND={self.hwnd}")
            return
        
        self.is_running = True
        self.should_stop = False
        
        # 启动控制线程
        self.control_thread = threading.Thread(
            target=self._control_loop,
            daemon=True,
            name=f"Controller-{self.hwnd}"
        )
        self.control_thread.start()
        
        # 启动装备监控线程
        self.equipment_monitor_thread = threading.Thread(
            target=self._equipment_monitor_loop,
            daemon=True,
            name=f"EquipmentMonitor-{self.hwnd}"
        )
        self.equipment_monitor_thread.start()
        
        print(f"[CONTROLLER] 智能控制器已启动: HWND={self.hwnd}, 控制线程={self.control_thread.name}, 监控线程={self.equipment_monitor_thread.name}")
    
    def stop(self):
        """停止智能控制"""
        self.should_stop = True
        self.is_running = False
        self.is_fighting = False
        
        # 等待线程结束
        if self.control_thread and self.control_thread.is_alive():
            self.control_thread.join(timeout=2.0)
        
        if self.equipment_monitor_thread and self.equipment_monitor_thread.is_alive():
            self.equipment_monitor_thread.join(timeout=2.0)
        
        print(f"[CONTROLLER] 智能控制已停止: HWND={self.hwnd}")
    
    def _control_loop(self):
        """主控制循环"""
        print(f"[CONTROLLER] 控制循环开始: HWND={self.hwnd}")
        
        while self.is_running and not self.should_stop and not global_stop_manager.is_stop_requested():
            try:
                current_time = time.time()
                
                # 检查窗口是否仍然有效
                if not self.window_manager._is_window_valid(self.hwnd):
                    print(f"[CONTROLLER] 窗口已关闭，停止控制: HWND={self.hwnd}")
                    break
                
                # 处理装备拾取
                if self.equipment_queue and not self.is_picking_up:
                    self._handle_equipment_pickup()
                
                # 战斗控制
                if not self.is_picking_up:
                    self._combat_control(current_time)
                
                time.sleep(0.1)  # 控制循环频率
                
            except Exception as e:
                print(f"[CONTROLLER] 控制循环异常: {e}")
                time.sleep(1)
        
        # 检查停止原因
        if global_stop_manager.is_stop_requested():
            print(f"[CONTROLLER] 收到全局停止信号: HWND={self.hwnd}")
        
        print(f"[CONTROLLER] 控制循环结束: HWND={self.hwnd}")
    
    def _equipment_monitor_loop(self):
        """装备监控循环"""
        print(f"[CONTROLLER] 装备监控开始: HWND={self.hwnd}")
        
        while self.is_running and not self.should_stop:
            try:
                current_time = time.time()
                
                # 检查装备检测间隔
                if current_time - self.last_equipment_check >= self.equipment_check_interval:
                    self._detect_equipment()
                    self.last_equipment_check = current_time
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"[CONTROLLER] 装备监控异常: {e}")
                time.sleep(1)
        
        print(f"[CONTROLLER] 装备监控结束: HWND={self.hwnd}")
    
    def _detect_equipment(self):
        """检测装备"""
        try:
            # 获取窗口截图
            screenshot = self.window_manager.get_window_screenshot(self.hwnd)
            if screenshot is None:
                return
            
            # 使用装备检测器检测
            if self.equipment_detector and self.equipment_detector.templates:
                matches, detection_time = self.equipment_detector.detect_equipment_templates(screenshot)
                
                if matches:
                    print(f"[EQUIPMENT] 发现装备: {len(matches)} 个")
                    
                    for match in matches:
                        # 转换为适应窗口的坐标
                        equipment_info = {
                            'name': match.equipment_name,
                            'position': match.position,
                            'confidence': match.confidence,
                            'timestamp': time.time(),
                            'hwnd': self.hwnd
                        }
                        
                        # 添加到装备队列
                        self.equipment_queue.append(equipment_info)
            
        except Exception as e:
            print(f"[EQUIPMENT] 装备检测异常: {e}")
    
    def _handle_equipment_pickup(self):
        """处理装备拾取 - 就近顺序拾取（修正版）"""
        try:
            # 检查拾取冷却时间
            current_time = time.time()
            if current_time - self.last_pickup_time < self.pickup_cooldown:
                return
            
            # 处理装备队列（使用列表而不是Queue）
            if not self.equipment_queue:
                return
                
            print(f"[PICKUP] 开始处理装备队列，当前有 {len(self.equipment_queue)} 个装备")
            
            # 设置拾取状态
            with self.control_lock:
                self.is_picking_up = True
            
            # 按距离排序装备（就近拾取）
            sorted_equipment = self._sort_equipment_by_distance(self.equipment_queue)
            print(f"[PICKUP] 装备已按距离排序，准备逐个拾取")
            
            # 逐个拾取装备（重要：一个一个拾取，不并发）
            processed_equipment = []
            for i, equipment_info in enumerate(sorted_equipment):
                try:
                    equipment_name = equipment_info.get('name', 'Unknown')
                    print(f"[PICKUP] 正在拾取第{i+1}/{len(sorted_equipment)}个装备: {equipment_name}")
                    
                    # 验证装备是否还存在
                    if self._verify_equipment_exists(equipment_info):
                        # 拾取单个装备
                        pickup_success = self._pickup_single_equipment(equipment_info)
                        
                        if pickup_success:
                            print(f"[PICKUP] ✅ 装备拾取成功: {equipment_name}")
                        else:
                            print(f"[PICKUP] ❌ 装备拾取失败: {equipment_name}")
                        
                        processed_equipment.append(equipment_info)
                        
                        # 更新拾取时间
                        self.last_pickup_time = time.time()
                        
                        # 重要：等待拾取完成再处理下一个装备
                        time.sleep(1.5)  # 给足够时间让游戏处理拾取
                    else:
                        print(f"[PICKUP] 装备已消失，跳过: {equipment_name}")
                        processed_equipment.append(equipment_info)
                        
                except Exception as pickup_error:
                    print(f"[PICKUP] 单个装备拾取异常: {pickup_error}")
                    processed_equipment.append(equipment_info)
            
            # 清理已处理的装备
            for equipment in processed_equipment:
                if equipment in self.equipment_queue:
                    self.equipment_queue.remove(equipment)
                    
        except Exception as e:
            print(f"[PICKUP] 处理装备拾取异常: {e}")
        finally:
            # 清理拾取状态
            with self.control_lock:
                self.is_picking_up = False
            
            print(f"[PICKUP] 装备拾取处理完成，剩余 {len(self.equipment_queue)} 个装备")
    
    def _pickup_single_equipment(self, equipment_info: Dict) -> bool:
        """拾取单个装备 - 修正版（返回拾取结果）"""
        try:
            # 获取装备位置
            if 'position' in equipment_info:
                x, y = equipment_info['position']
            else:
                x = equipment_info.get('x', 0)
                y = equipment_info.get('y', 0)
            
            equipment_name = equipment_info.get('name', 'Unknown')
            print(f"[PICKUP] 开始拾取装备: {equipment_name}，位置: ({x}, {y})")
            
            # 执行拾取点击序列（移动+单次点击）
            pickup_result = self._pickup_click_sequence(x, y)
            
            if pickup_result:
                print(f"[PICKUP] 装备拾取操作完成: {equipment_name}")
                return True
            else:
                print(f"[PICKUP] 装备拾取操作失败: {equipment_name}")
                return False
            
        except Exception as e:
            print(f"[PICKUP] 单个装备拾取异常: {e}")
            return False
    
    def _sort_equipment_by_distance(self, equipment_list: List[Dict]) -> List[Dict]:
        """按距离排序装备（就近拾取）"""
        try:
            if not equipment_list:
                return []
            
            # 获取角色当前位置（假设在屏幕中心）
            center_x = self.screen_center_x
            center_y = self.screen_center_y
            
            def calculate_distance(equipment):
                """计算装备到角色的距离"""
                if 'position' in equipment:
                    x, y = equipment['position']
                else:
                    x = equipment.get('x', center_x)
                    y = equipment.get('y', center_y)
                
                import math
                return math.sqrt((x - center_x)**2 + (y - center_y)**2)
            
            # 按距离排序（最近的装备优先）
            sorted_equipment = sorted(equipment_list, key=calculate_distance)
            
            print(f"[PICKUP] 装备距离排序完成:")
            for i, equipment in enumerate(sorted_equipment):
                distance = calculate_distance(equipment)
                name = equipment.get('name', 'Unknown')
                print(f"  {i+1}. {name} - 距离: {distance:.1f}像素")
            
            return sorted_equipment
            
        except Exception as e:
            print(f"[PICKUP] 装备排序异常: {e}")
            return equipment_list
    
    def _pickup_click_sequence(self, x: int, y: int):
        """装备拾取点击序列 - 长按Ctrl+左键移动然后单次左键拾取（修正版）"""
        try:
            print(f"[PICKUP] 开始装备拾取序列，目标位置: ({x}, {y})")
            
            # 方法1: 使用增强版输入注入系统（真实游戏操作）
            try:
                from v2.enhanced_dingtalk_injection import enhanced_inject_move_character, enhanced_inject_click
                
                # 第一步：移动角色到装备位置（Ctrl+左键长按）
                if enhanced_inject_move_character(self.hwnd, x, y, 0.5):
                    print(f"[PICKUP] 角色移动到装备位置成功")
                    
                    # 等待移动完成
                    time.sleep(0.2)
                    
                    # 第二步：单次左键拾取（不连续点击）
                    if enhanced_inject_click(self.hwnd, x, y):
                        print(f"[PICKUP] 装备拾取点击成功")
                        
                        # 等待拾取动画完成（重要：给游戏足够时间处理拾取）
                        time.sleep(1.0)
                        
                        print(f"[PICKUP] 装备拾取完成")
                        return True
                    else:
                        print(f"[PICKUP] 装备拾取点击失败")
                else:
                    print(f"[PICKUP] 角色移动失败")
                    
            except Exception as e:
                print(f"[PICKUP] 增强注入异常: {e}")
            
            # 方法2: 备用方案 - 使用窗口管理器的输入方法
            print(f"[PICKUP] 增强注入失败，尝试备用方案")
            
            # 先移动到装备位置
            self._move_to_position(x, y, 0.5)
            time.sleep(0.2)
            
            # 单次点击拾取
            if self.window_manager.send_input_to_window(self.hwnd, x, y, 'click'):
                print(f"[PICKUP] 备用方案拾取点击成功")
                # 等待拾取完成
                time.sleep(1.0)
                return True
            else:
                print(f"[PICKUP] 备用方案拾取失败")
                return False
            
        except Exception as e:
            print(f"[PICKUP] 拾取异常: {e}")
            return False
    
    def _verify_equipment_exists(self, equipment_info: Dict) -> bool:
        """验证装备是否还存在（简单的重新检测）"""
        try:
            if not self.equipment_detector:
                return True  # 如果没有检测器，假设存在
            
            # 简单的存在性检查：检查时间戳
            current_time = time.time()
            equipment_time = equipment_info.get('timestamp', 0)
            
            # 如果装备检测时间超过5秒，认为可能已消失
            if current_time - equipment_time > 5.0:
                print(f"[VERIFY] 装备检测时间过久，可能已消失")
                return False
            
            return True
            
        except Exception as e:
            print(f"[VERIFY] 验证装备存在异常: {e}")
            return True  # 异常情况下假设存在
    
    def _verify_pickup_success(self, equipment_info: Dict) -> bool:
        """验证装备拾取是否成功（检查装备是否消失）"""
        try:
            # 简单的成功验证：等待一段时间后再检测
            time.sleep(0.5)
            
            # 这里可以添加更复杂的验证逻辑
            # 比如重新截屏检测装备是否还在原位置
            
            return True  # 暂时返回true，表示拾取成功
            
        except Exception as e:
            print(f"[VERIFY] 验证拾取成功异常: {e}")
            return True
    
    def _calculate_distance_to_center(self, x: int, y: int) -> float:
        """计算到屏幕中心的距离"""
        import math
        return math.sqrt((x - self.screen_center_x)**2 + (y - self.screen_center_y)**2)
    
    def _is_same_equipment(self, eq1: Dict, eq2: Dict, threshold: int = 30) -> bool:
        """判断是否是同一个装备（基于位置距离）"""
        try:
            pos1 = eq1.get('position', (0, 0))
            pos2 = eq2.get('position', (0, 0))
            
            distance = math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
            return distance < threshold
            
        except Exception as e:
            print(f"[VERIFY] 判断装备相同性异常: {e}")
            return False
    
    def return_to_center(self) -> Tuple[int, int]:
        """回到屏幕中心位置 - v1版本功能"""
        center_pos = (self.screen_center_x, self.screen_center_y)
        print(f"[MOVE] 回到中心位置: {center_pos}")
        self._move_to_position(center_pos[0], center_pos[1], 1.0)
        return center_pos
    
    def _combat_control(self, current_time: float):
        """战斗控制"""
        if not self.is_fighting:
            self.is_fighting = True
            print(f"[COMBAT] 开始战斗模式: HWND={self.hwnd}")
        
        # 移动控制
        if current_time - self.last_move_time >= self.move_interval:
            print(f"[COMBAT] 执行移动控制: HWND={self.hwnd}")
            self._combat_move()
            self.last_move_time = current_time
        
        # 攻击控制
        if current_time - self.last_attack_time >= self.fight_interval:
            print(f"[COMBAT] 执行攻击控制: HWND={self.hwnd}")
            self._combat_attack()
            self.last_attack_time = current_time
    
    def _combat_move(self):
        """战斗移动"""
        try:
            # 获取随机移动位置
            move_x, move_y = self._get_random_combat_position()
            
            self._move_to_position(move_x, move_y)
            
            self.random_move_count += 1
            if self.random_move_count >= self.max_random_moves:
                # 回到中心
                self._move_to_position(
                    self.adaptive_settings.center_x,
                    self.adaptive_settings.center_y
                )
                self.random_move_count = 0
                print(f"[COMBAT] 回到中心位置: HWND={self.hwnd}")
            
        except Exception as e:
            print(f"[COMBAT] 移动异常: {e}")
    
    def _combat_attack(self):
        """战斗攻击 - 长按Ctrl+左键移动然后右键攻击（高级非激活输入注入）"""
        try:
            # 获取攻击位置
            attack_x, attack_y = self._get_random_combat_position()
            
            print(f"[COMBAT] 开始高级注入攻击序列，目标位置: ({attack_x}, {attack_y})")
            
            # 方法1: 使用增强版输入注入系统（真实游戏操作）
            try:
                from v2.enhanced_dingtalk_injection import enhanced_inject_move_character, enhanced_inject_right_click
                
                # 第一步：移动角色到攻击位置（Ctrl+左键长按）
                if enhanced_inject_move_character(self.hwnd, attack_x, attack_y, 0.3):
                    print(f"[COMBAT] 增强注入角色移动成功")
                    
                    # 第二步：右键攻击
                    if enhanced_inject_right_click(self.hwnd, attack_x, attack_y):
                        print(f"[COMBAT] 增强注入攻击成功")
                        print(f"[COMBAT] 右键攻击完成 (HWND={self.hwnd})")
                        return
                    else:
                        print(f"[COMBAT] 增强注入右键失败")
                else:
                    print(f"[COMBAT] 增强注入角色移动失败")
                    
            except Exception as e:
                print(f"[COMBAT] 增强注入异常: {e}")
            
            # 方法2: 备用方案 - 使用窗口管理器的输入方法
            print(f"[COMBAT] 高级注入失败，尝试备用方案")
            
            # 先移动
            self._move_to_position(attack_x, attack_y, 0.3)
            
            # 再攻击
            success = self.window_manager.send_input_to_window(self.hwnd, attack_x, attack_y, 'right_click')
            if success:
                print(f"[COMBAT] 备用方案攻击成功")
                print(f"[COMBAT] 右键攻击完成 (HWND={self.hwnd})")
            else:
                print(f"[COMBAT] 所有攻击方案都失败")
            
        except Exception as e:
            print(f"[COMBAT] 攻击异常: {e}")
    
    def _move_to_position(self, x: int, y: int, duration: float = 0.5):
        """移动到指定位置 - 长按Ctrl+左键（高级非激活输入注入）"""
        try:
            print(f"[MOVE] 开始高级注入移动到位置 ({x}, {y}), 持续时间: {duration}s")
            
            # 方法1: 使用增强版输入注入系统（真实游戏操作）
            try:
                from v2.enhanced_dingtalk_injection import enhanced_inject_move_character
                if enhanced_inject_move_character(self.hwnd, x, y, duration):
                    print(f"[MOVE] 增强注入角色移动成功")
                    return
                else:
                    print(f"[MOVE] 增强注入角色移动失败，尝试备用方案")
            except Exception as e:
                print(f"[MOVE] 增强注入异常: {e}")
            
            # 方法2: 备用方案 - 使用窗口管理器的输入方法
            success = self.window_manager.send_input_to_window(self.hwnd, x, y, 'move_and_drag')
            if success:
                print(f"[MOVE] 备用方案移动成功")
            else:
                print(f"[MOVE] 所有移动方案都失败")
            
        except Exception as e:
            print(f"[MOVE] 移动异常: {e}")
    
    def _get_random_combat_position(self) -> Tuple[int, int]:
        """获取随机战斗位置 - 基于v1版本的屏幕中心移动系统"""
        import random
        import math
        
        if self.movement_mode == 'around_center':
            # 围绕屏幕中心移动（v1版本逻辑）
            angle = random.uniform(0, 2 * math.pi)
            # 随机半径，但不要太近中心
            radius = random.uniform(self.movement_radius * 0.4, self.movement_radius)
            
            target_x = self.screen_center_x + radius * math.cos(angle)
            target_y = self.screen_center_y + radius * math.sin(angle)
        else:
            # 备用：使用配置的战斗区域
            combat_area = self.adaptive_settings.combat_area if self.adaptive_settings else {
                'min_x': int(self.screen_width * 0.3),
                'max_x': int(self.screen_width * 0.7),
                'min_y': int(self.screen_height * 0.3),
                'max_y': int(self.screen_height * 0.7)
            }
            target_x = random.randint(combat_area['min_x'], combat_area['max_x'])
            target_y = random.randint(combat_area['min_y'], combat_area['max_y'])
        
        # 确保目标位置在屏幕范围内
        target_x = max(50, min(self.screen_width - 50, target_x))
        target_y = max(50, min(self.screen_height - 50, target_y))
        
        return (int(target_x), int(target_y))
    
    def get_status(self) -> Dict[str, Any]:
        """获取控制器状态"""
        return {
            'hwnd': self.hwnd,
            'is_running': self.is_running,
            'is_fighting': self.is_fighting,
            'is_picking_up': self.is_picking_up,
            'equipment_queue_size': len(self.equipment_queue),
            'window_size': (
                self.adaptive_settings.window_width,
                self.adaptive_settings.window_height
            ) if self.adaptive_settings else None,
            'random_move_count': self.random_move_count
        }
    
    def print_status(self):
        """打印控制器状态"""
        status = self.get_status()
        window_title = self.window_info.title if self.window_info else "Unknown"
        
        print(f"\n🎮 控制器状态 - {window_title}")
        print(f"HWND: {status['hwnd']}")
        print(f"运行状态: {'运行中' if status['is_running'] else '已停止'}")
        print(f"战斗状态: {'战斗中' if status['is_fighting'] else '待机'}")
        print(f"拾取状态: {'拾取中' if status['is_picking_up'] else '待机'}")
        print(f"装备队列: {status['equipment_queue_size']} 个")
        print(f"窗口尺寸: {status['window_size']}")
        print(f"移动计数: {status['random_move_count']}/{self.max_random_moves}")

def main():
    """测试主函数"""
    print("🧠 v2智能游戏控制器测试")
    
    # 这里需要配合MultiWindowManager使用
    print("请先运行MultiWindowManager来管理窗口")

if __name__ == "__main__":
    main()
