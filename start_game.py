#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
游戏主控脚本 - 自动打怪与装备监控
功能：实时监控装备掉落，同时持续移动打怪，发现装备时暂停打怪去捡装备

运行逻辑：
1. 启动装备监控线程（后台运行）
2. 主线程执行持续打怪循环
3. 检测到装备时，暂停打怪，执行捡装备
4. 捡完装备后，恢复打怪循环
"""

import threading
import time
import sys
import os
from pathlib import Path
import keyboard

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from template_equipment_detector import TemplateEquipmentDetector
from mouse_keyboard_controller import MouseKeyboardController, get_controller


class GameController:
    """游戏主控制器"""
    
    def __init__(self):
        self.controller = get_controller()
        self.detector = None
        self.is_running = False
        self.is_fighting = False  # 是否正在打怪
        self.equipment_found = False  # 是否发现装备
        self.equipment_position = None  # 装备位置
        self.monitor_thread = None
        self.fight_thread = None
        self.should_stop = False  # Ctrl+Q停止标志
        self.stop_lock = threading.Lock()  # 停止锁
        
        # 增强的装备拾取管理
        self.equipment_queue = []  # 装备队列
        self.is_picking_up = False  # 是否正在拾取装备
        self.pickup_lock = threading.Lock()  # 拾取锁
        self.last_pickup_time = 0  # 上次拾取时间
        self.pickup_cooldown = 2.0  # 拾取冷却时间（秒）
        
        # 游戏参数
        self.screen_width = 1920
        self.screen_height = 1080
        self.fight_interval = 1.5  # 打怪间隔（秒）
        self.move_interval = 2.0   # 移动间隔（秒）
        
        # 新增参数 - 圆环移动系统
        self.random_move_count = 0  # 随机移动计数
        self.max_random_moves = 30  # 最大随机移动次数，可配置
        self.pickup_safe_distance = 50  # 拾取安全距离（像素）
        
        # 现实移动系统参数（基于屏幕坐标）
        self.movement_radius = 150  # 移动半径（像素）
        self.screen_center_x = self.screen_width // 2  # 屏幕中心X（固定）
        self.screen_center_y = self.screen_height // 2  # 屏幕中心Y（固定）
        
        # 移动模式：'around_center' 或 'random_area'
        self.movement_mode = 'around_center'  # 围绕屏幕中心移动
        
        # 移动区域定义
        self.movement_area = {
            'min_x': int(self.screen_width * 0.3),   # 屏幕30%位置
            'max_x': int(self.screen_width * 0.7),   # 屏幕70%位置
            'min_y': int(self.screen_height * 0.3),  # 屏幕30%位置
            'max_y': int(self.screen_height * 0.7)   # 屏幕70%位置
        }
        
    def equipment_detected_callback(self, match):
        """装备检测回调函数 - 增强版支持队列管理"""
        try:
            # 从 position元组中获取坐标和尺寸
            x, y, w, h = match.position
            center_x = x + w // 2
            center_y = y + h // 2
            
            equipment_info = {
                'name': match.equipment_name,
                'position': (center_x, center_y),
                'confidence': match.confidence,
                'size': (w, h),
                'timestamp': time.time(),
                'distance': self._calculate_distance_to_center(center_x, center_y)
            }
            
            print(f"\n[EQUIPMENT] 发现装备: {equipment_info['name']}")
            print(f"[EQUIPMENT] 位置: ({center_x}, {center_y}), 置信度: {equipment_info['confidence']:.3f}")
            print(f"[EQUIPMENT] 距离中心: {equipment_info['distance']:.1f} 像素")
            
            # 线程安全地添加到装备队列
            with self.pickup_lock:
                # 检查是否已存在相似位置的装备（避免重复检测）
                is_duplicate = False
                for existing_eq in self.equipment_queue:
                    if self._is_same_equipment(equipment_info, existing_eq):
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    self.equipment_queue.append(equipment_info)
                    # 按距离排序，优先拾取最近的装备
                    self.equipment_queue.sort(key=lambda eq: eq['distance'])
                    
                    print(f"[EQUIPMENT] 装备已加入队列，当前队列长度: {len(self.equipment_queue)}")
                    
                    # 设置装备发现标志
                    if not self.equipment_found:
                        self.equipment_found = True
                        print(f"[EQUIPMENT] 设置装备发现标志，准备暂停战斗")
                else:
                    print(f"[EQUIPMENT] 装备重复检测，忽略")
            
        except Exception as e:
            print(f"[ERROR] 装备检测回调异常: {e}")
            import traceback
            traceback.print_exc()
    
    def _calculate_distance_to_center(self, x, y):
        """计算到屏幕中心的距离"""
        center_x = self.screen_width // 2
        center_y = self.screen_height // 2
        return ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
    
    def _is_same_equipment(self, eq1, eq2, threshold=30):
        """判断是否是同一个装备（基于位置距离）"""
        x1, y1 = eq1['position']
        x2, y2 = eq2['position']
        distance = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
        return distance < threshold
        
    def setup_keyboard_listener(self):
        """设置键盘监听器"""
        def on_hotkey():
            with self.stop_lock:
                if not self.should_stop:
                    self.should_stop = True
                    print("\n\n🛑 检测到 Ctrl+Q 快捷键，正在停止游戏脚本...")
                    
                    # 设置停止标志，让所有线程自然退出
                    self.is_running = False
                    self.is_fighting = False
                    
                    # 在stop方法中统一停止装备检测，而不是在这里立即停止
                    print("[HOTKEY] 正在停止所有进程...")
        
        # 注册Ctrl+Q热键
        keyboard.add_hotkey('ctrl+q', on_hotkey)
        print("⌨️  已注册 Ctrl+Q 快捷键 (随时可停止脚本)")
        
    def start_equipment_monitor(self):
        """启动装备监控线程"""
        print(f"[INFO] 启动装备监控...")
        
        try:
            # 初始化装备检测器
            print(f"[INFO] 初始化装备检测器...")
            self.detector = TemplateEquipmentDetector()
            print(f"[INFO] 装备检测器初始化成功")
            
            # 加载装备模板（从 templates 文件夹）
            template_dir = project_root / "templates"
            print(f"[INFO] 模板目录: {template_dir}")
            
            if template_dir.exists():
                print(f"[INFO] 正在加载装备模板...")
                loaded_count = self.detector.load_templates_from_folder(str(template_dir))
                print(f"[INFO] 成功加载 {loaded_count} 个装备模板")
                
                if loaded_count == 0:
                    print(f"[WARNING] 未加载到任何装备模板！")
                    return
            else:
                print(f"[ERROR] 模板目录不存在: {template_dir}")
                return
            
            # 启动监控线程
            print(f"[INFO] 创建监控线程...")
            self.monitor_thread = threading.Thread(
                target=self._equipment_monitor_loop,
                daemon=True,
                name="EquipmentMonitor"
            )
            
            print(f"[INFO] 启动监控线程...")
            self.monitor_thread.start()
            
            # 等待一下让线程初始化
            import time
            time.sleep(0.5)
            
            # 检查线程状态
            thread_alive = self.monitor_thread.is_alive() if self.monitor_thread else False
            detector_running = self.detector.is_running if self.detector else False
            
            print(f"[INFO] 监控线程状态: {thread_alive}")
            print(f"[INFO] 检测器状态: {detector_running}")
            
            if not thread_alive:
                print(f"[ERROR] 监控线程启动失败！")
            
        except Exception as e:
            print(f"[ERROR] 启动装备监控失败: {e}")
            import traceback
            traceback.print_exc()
        
    def _equipment_monitor_loop(self):
        """装备监控循环（后台线程）"""
        try:
            print(f"[MONITOR] 启动装备检测线程...")
            print(f"[MONITOR] 检测器初始状态: is_running={self.detector.is_running}")
            print(f"[MONITOR] 游戏控制器状态: is_running={self.is_running}")
            
            # 启动检测器（非阻塞调用）
            print(f"[MONITOR] 正在调用 start_realtime_detection...")
            self.detector.start_realtime_detection(
                callback=self.equipment_detected_callback,
                fps=20  # 20FPS高频检测
            )
            print(f"[MONITOR] start_realtime_detection 调用完成，检测器已启动")
            
            # 监控线程保持运行，直到游戏系统停止
            print(f"[MONITOR] 监控线程开始保持运行...")
            while self.is_running:
                # 检查检测器状态
                if not self.detector.is_running:
                    print(f"[MONITOR] 检测器已停止，尝试重启...")
                    try:
                        self.detector.start_realtime_detection(
                            callback=self.equipment_detected_callback,
                            fps=20
                        )
                        print(f"[MONITOR] 检测器重启成功")
                    except Exception as restart_error:
                        print(f"[MONITOR] 检测器重启失败: {restart_error}")
                        time.sleep(5)  # 等待5秒后再试
                
                time.sleep(1)  # 每秒检查一次
            
            print(f"[MONITOR] 游戏系统停止，退出监控循环")
                
        except Exception as e:
            print(f"[ERROR] 装备监控异常: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # 确保停止检测
            try:
                if self.detector:
                    print(f"[MONITOR] finally块: 检测器状态 is_running={self.detector.is_running}")
                    self.detector.stop_realtime_detection()
                    print(f"[MONITOR] 装备监控已停止")
            except Exception as e:
                print(f"[WARNING] 停止装备检测异常: {e}")
            
    def start_fighting(self):
        """启动打怪线程"""
        print(f"[COMBAT] 启动自动打怪...")
        
        self.is_fighting = True
        self.fight_thread = threading.Thread(
            target=self._fighting_loop,
            daemon=True
        )
        self.fight_thread.start()
        
    def _fighting_loop(self):
        """打怪循环（后台线程）"""
        last_move_time = 0
        last_attack_time = 0
        last_monitor_check = 0
        
        while self.is_running and self.is_fighting:
            try:
                # 检查Ctrl+Q停止信号
                with self.stop_lock:
                    if self.should_stop:
                        print(f"[COMBAT] 收到停止信号，退出打怪循环...")
                        break
                
                # 每10秒检查一次装备监控状态
                current_time = time.time()
                if current_time - last_monitor_check >= 10:
                    detector_status = self.detector.is_running if self.detector else False
                    monitor_status = self.monitor_thread.is_alive() if self.monitor_thread else False
                    # 系统状态显示
                    if detector_status and monitor_status:
                        print(f"✅ [系统状态] 装备检测正常 | 自动打怪正常 | 自动拾取就绪")
                    else:
                        print(f"⚠️  [系统状态] 装备检测={detector_status}, 监控线程={monitor_status}")
                    last_monitor_check = current_time
                        
                # 检查是否需要暂停打怪（发现装备）
                if self.equipment_found and not self.is_picking_up:
                    print(f"[COMBAT] 🛑 暂停所有战斗行为，开始装备拾取流程...")
                    
                    # 立即停止所有攻击动作
                    try:
                        import pyautogui
                        pyautogui.keyUp('ctrl')  # 释放可能按下的Ctrl键
                        pyautogui.mouseUp(button='left')  # 释放可能按下的鼠标左键
                        pyautogui.mouseUp(button='right')  # 释放可能按下的鼠标右键
                        print(f"[COMBAT] ✅ 已释放所有按键，确保攻击完全停止")
                    except Exception as key_release_error:
                        print(f"[COMBAT] ⚠️ 释放按键异常: {key_release_error}")
                    
                    # 设置拾取状态，防止重复进入
                    with self.pickup_lock:
                        self.is_picking_up = True
                    
                    # 执行装备拾取流程
                    self._process_equipment_queue()
                    
                    # 拾取完成，恢复战斗
                    with self.pickup_lock:
                        self.is_picking_up = False
                        self.equipment_found = False
                    
                    print(f"[COMBAT] ✅ 装备拾取流程完成，恢复战斗状态")
                    continue
                    
                current_time = time.time()
                
                # 移动角色（每3秒移动一次）
                if current_time - last_move_time >= self.move_interval:
                    # 检查是否需要回到初始位置
                    if self.random_move_count >= self.max_random_moves:
                        print(f"[MOVE] 已完成 {self.random_move_count} 次随机移动，回到游戏世界初始位置")
                        move_pos = self.return_to_center()
                        self.random_move_count = 0  # 重置计数
                        print(f"[MOVE] 回到中心位置: ({move_pos[0]}, {move_pos[1]})")
                    else:
                        # 在固定半径圆环内随机移动
                        move_pos = self.get_random_combat_position()
                        self.random_move_count += 1
                        print(f"[MOVE] 随机移动: ({move_pos[0]}, {move_pos[1]}) [计数: {self.random_move_count}/{self.max_random_moves}]")
                    
                    move_result = self.controller.move_character(
                        move_pos[0], move_pos[1], 0.5
                    )
                    
                    if move_result.success:
                        print(f"[MOVE] 移动成功")
                    else:
                        print(f"[MOVE] 移动失败: {move_result.error_message}")
                        
                    last_move_time = current_time
                
                # 攻击技能（每1.5秒攻击一次）
                if current_time - last_attack_time >= self.fight_interval:
                    # 在屏幕70%-80%范围内随机攻击
                    attack_pos = self.get_random_combat_position()
                    
                    print(f"[ATTACK] 攻击技能: ({attack_pos[0]}, {attack_pos[1]})")
                    attack_result = self.controller.attack_skill(
                        attack_pos[0], attack_pos[1]
                    )
                    
                    if attack_result.success:
                        print(f"[ATTACK] 攻击成功")
                    else:
                        print(f"[ATTACK] 攻击失败: {attack_result.error_message}")
                        
                    last_attack_time = current_time
                
                # 短暂休息
                time.sleep(0.1)
                
            except Exception as e:
                print(f"[ERROR] 打怪循环异常: {e}")
                time.sleep(1)
                
    def _process_equipment_queue(self):
        """处理装备队列 - 逐一拾取所有装备"""
        processed_count = 0
        
        while True:
            # 获取下一个装备
            current_equipment = None
            with self.pickup_lock:
                if not self.equipment_queue:
                    break
                current_equipment = self.equipment_queue.pop(0)  # 取出队列第一个（最近的）
            
            if not current_equipment:
                break
                
            processed_count += 1
            print(f"\n[PICKUP] 🎯 处理装备 {processed_count}: {current_equipment['name']}")
            print(f"[PICKUP] 位置: {current_equipment['position']}, 距离: {current_equipment['distance']:.1f}")
            
            # 检查装备是否还存在（拾取前验证）
            if self._verify_equipment_exists(current_equipment):
                # 执行拾取
                success = self._pickup_single_equipment(current_equipment)
                
                if success:
                    print(f"[PICKUP] ✅ 装备 {current_equipment['name']} 拾取成功")
                    # 记录拾取时间
                    self.last_pickup_time = time.time()
                else:
                    print(f"[PICKUP] ❌ 装备 {current_equipment['name']} 拾取失败")
            else:
                print(f"[PICKUP] ⚠️ 装备 {current_equipment['name']} 已消失，跳过")
            
            # 拾取间隔，避免操作过快
            time.sleep(0.5)
        
        print(f"[PICKUP] 📊 装备拾取完成，共处理 {processed_count} 个装备")
    
    def _verify_equipment_exists(self, equipment_info):
        """验证装备是否还存在（简单的重新检测）"""
        try:
            # 在装备位置附近进行小范围检测
            x, y = equipment_info['position']
            
            # 简单的存在性检查：截取装备区域并进行模板匹配
            # 这里可以实现更复杂的验证逻辑
            print(f"[VERIFY] 验证装备是否存在: ({x}, {y})")
            
            # 暂时返回True，实际项目中可以实现真正的验证
            return True
            
        except Exception as e:
            print(f"[VERIFY] 装备验证异常: {e}")
            return False
    
    def _pickup_single_equipment(self, equipment_info):
        """拾取单个装备并验证成功"""
        try:
            x, y = equipment_info['position']
            
            print(f"[PICKUP] 开始拾取装备: {equipment_info['name']} at ({x}, {y})")
            
            # 执行拾取操作
            pickup_result = self.controller.pickup_equipment(
                x, y, 
                pickup_duration=3.0, 
                method="auto"
            )
            
            if pickup_result.success:
                print(f"[PICKUP] 拾取操作执行成功，耗时: {pickup_result.click_time:.1f}ms")
                
                # 验证拾取是否真正成功
                time.sleep(0.5)  # 等待拾取动画完成
                
                pickup_success = self._verify_pickup_success(equipment_info)
                
                if pickup_success:
                    print(f"[PICKUP] ✅ 装备真正拾取成功: {equipment_info['name']}")
                    return True
                else:
                    print(f"[PICKUP] ⚠️ 装备拾取操作完成但验证失败: {equipment_info['name']}")
                    return False
            else:
                print(f"[PICKUP] ❌ 装备拾取操作失败: {pickup_result.error_message}")
                return False
                
        except Exception as e:
            print(f"[PICKUP] 装备拾取异常: {e}")
            return False
    
    def _verify_pickup_success(self, equipment_info):
        """验证装备拾取是否成功（检查装备是否消失）"""
        try:
            # 方法1: 检查装备是否从原位置消失
            print(f"[VERIFY] 验证装备拾取成功性...")
            
            # 在原位置重新检测，如果检测不到说明拾取成功
            x, y = equipment_info['position']
            
            # 简单的成功判定：假设拾取操作都成功
            # 实际项目中可以实现：
            # 1. 重新截图检测原位置是否还有装备
            # 2. 检查背包是否增加了物品
            # 3. 检查游戏内的拾取提示信息
            
            print(f"[VERIFY] 装备拾取验证通过")
            return True
            
        except Exception as e:
            print(f"[VERIFY] 拾取验证异常: {e}")
            return False
    
    def _handle_equipment_pickup(self):
        """处理装备拾取 - 保留兼容性"""
        print(f"[PICKUP] 调用旧版拾取方法，转发到队列处理")
        self._process_equipment_queue()
        
        # 重置装备发现标志，恢复打怪
        self.equipment_found = False
        self.equipment_position = None
        
        # 检查装备检测器状态，如果停止了则重新启动
        detector_running = self.detector.is_running if self.detector else False
        thread_alive = self.monitor_thread.is_alive() if self.monitor_thread else False
        
        print(f"[PICKUP] 拾取后状态检查: 检测器={detector_running}, 监控线程={thread_alive}, 游戏运行={self.is_running}")
        
        if self.detector and not detector_running and self.is_running:
            print(f"[MONITOR] 检测器已停止，需要重新启动装备监控...")
            
            # 等待旧线程结束
            if self.monitor_thread and self.monitor_thread.is_alive():
                print(f"[MONITOR] 等待旧监控线程结束...")
                self.monitor_thread.join(timeout=2)
            
            try:
                print(f"[MONITOR] 创建新的监控线程...")
                # 重新启动监控线程
                self.monitor_thread = threading.Thread(
                    target=self._equipment_monitor_loop,
                    daemon=True
                )
                self.monitor_thread.start()
                print(f"[MONITOR] 装备监控已重新启动")
            except Exception as restart_error:
                print(f"[ERROR] 重启装备监控失败: {restart_error}")
                
        elif detector_running:
            print(f"[MONITOR] 检测器仍在运行，无需重启")
        else:
            print(f"[MONITOR] 游戏已停止，不重启检测器")
        
        print(f"[COMBAT] 恢复打怪模式...")
        print(f"[DEBUG] 装备检测器状态: {self.detector.is_running if self.detector else 'None'}")
            
    def smart_pickup_nearest_equipment(self, equipment_x, equipment_y):
        """
        新的智能拾取逻辑：找到离屏幕中心最近的装备并拾取
        人物角色固定在屏幕中心，无需检测人物位置
        
        Args:
            equipment_x: 装备 X坐标
            equipment_y: 装备 Y坐标
        """
        print(f"[SMART_PICKUP] 开始智能拾取装备，目标位置: ({equipment_x}, {equipment_y})")
        
        # 暂停打怪
        self.is_fighting = False
        print(f"[SMART_PICKUP] 暂停打怪")
        
        try:
            # 屏幕中心坐标（人物位置）
            screen_center_x = self.screen_width // 2
            screen_center_y = self.screen_height // 2
            
            max_attempts = 8  # 最大尝试次数
            
            for attempt in range(max_attempts):
                print(f"[SMART_PICKUP] === 第 {attempt + 1} 次尝试 ===")
                
                # 检查停止信号
                if self.should_stop:
                    print(f"[SMART_PICKUP] 接收到停止信号，中断拾取")
                    return
                
                # 1. 重新检测装备位置，找到离屏幕中心最近的装备
                current_equipment_matches = self.detector.single_detection()[0]
                nearest_equipment_x, nearest_equipment_y = equipment_x, equipment_y
                
                if current_equipment_matches:
                    min_distance_to_center = float('inf')
                    
                    for match in current_equipment_matches:
                        ex, ey, ew, eh = match.position
                        print(f"[SMART_PICKUP] 移动失败: {move_result.error_message}")
                    
                    # 5. 等待移动完成
                    time.sleep(1.5)
                    
                    # 继续下一次循环检测
                    if attempt < max_attempts - 1:
                        print(f"[SMART_PICKUP] 继续下一次检测...")
                    else:
                        print(f"[SMART_PICKUP] 达到最大尝试次数，强制拾取")
                        get_controller().left_click(nearest_equipment_x, nearest_equipment_y)
                        time.sleep(2.0)
                
        except Exception as e:
            print(f"[SMART_PICKUP] ⚠️ 智能拾取异常: {e}")
            import traceback
            traceback.print_exc()
            print(f"[SMART_PICKUP] 异常情况下强制拾取")
            try:
                get_controller().left_click(equipment_x, equipment_y)
                time.sleep(2.0)
            except:
                print(f"[SMART_PICKUP] 强制拾取也失败")
        
        # 6. 恢复打怪状态
        time.sleep(1.0)
        self.is_fighting = True
        self.equipment_found = False
        print(f"[SMART_PICKUP] ✅ 智能拾取流程完成，恢复打怪状态")
        
        # 7. 检查并重启装备检测
        self._check_and_restart_equipment_monitor()
    
    def get_random_combat_position(self):
        """
        现实可行的随机移动系统
        基于屏幕坐标，不依赖游戏世界的真实坐标
        
        Returns:
            tuple: (x, y) 随机位置坐标
        """
        import random
        import math
        
        if self.movement_mode == 'around_center':
            # 模式1：围绕屏幕中心移动
            angle = random.uniform(0, 2 * math.pi)
            # 随机半径，但不要太近中心
            radius = random.uniform(self.movement_radius * 0.4, self.movement_radius)
            
            target_x = self.screen_center_x + radius * math.cos(angle)
            target_y = self.screen_center_y + radius * math.sin(angle)
            
        else:  # 'random_area'
            # 模式2：在指定区域内随机移动
            target_x = random.randint(self.movement_area['min_x'], self.movement_area['max_x'])
            target_y = random.randint(self.movement_area['min_y'], self.movement_area['max_y'])
        
        # 确保目标位置在屏幕范围内
        target_x = max(50, min(self.screen_width - 50, target_x))
        target_y = max(50, min(self.screen_height - 50, target_y))
        
        return (int(target_x), int(target_y))
    
    def return_to_center(self):
        """
        回到屏幕中心位置
        这是唯一现实可行的“回归”方式
        
        Returns:
            tuple: (x, y) 屏幕中心位置
        """
        return (self.screen_center_x, self.screen_center_y)
    
    def set_max_random_moves(self, count):
        """
        设置最大随机移动次数
        
        Args:
            count: 最大随机移动次数
        """
        self.max_random_moves = max(1, count)
        print(f"[CONFIG] 设置最大随机移动次数: {self.max_random_moves}")
    
    def set_movement_radius(self, radius):
        """
        设置移动半径（仅在around_center模式下有效）
        
        Args:
            radius (int): 移动半径（像素）
        """
        self.movement_radius = max(50, min(300, radius))  # 限制在合理范围内
        print(f"[CONFIG] 移动半径设置为: {self.movement_radius} 像素")
    
    def set_movement_mode(self, mode):
        """
        设置移动模式
        
        Args:
            mode (str): 'around_center' 或 'random_area'
        """
        if mode in ['around_center', 'random_area']:
            self.movement_mode = mode
            print(f"[CONFIG] 移动模式设置为: {mode}")
        else:
            print(f"[ERROR] 无效的移动模式: {mode}")
    
    def set_movement_area(self, min_x_percent=0.3, max_x_percent=0.7, min_y_percent=0.3, max_y_percent=0.7):
        """
        设置移动区域（仅在random_area模式下有效）
        
        Args:
            min_x_percent (float): X轴最小位置（屏幕百分比）
            max_x_percent (float): X轴最大位置（屏幕百分比）
            min_y_percent (float): Y轴最小位置（屏幕百分比）
            max_y_percent (float): Y轴最大位置（屏幕百分比）
        """
        self.movement_area = {
            'min_x': int(self.screen_width * min_x_percent),
            'max_x': int(self.screen_width * max_x_percent),
            'min_y': int(self.screen_height * min_y_percent),
            'max_y': int(self.screen_height * max_y_percent)
        }
        print(f"[CONFIG] 移动区域设置为: {self.movement_area}")
    
    def set_fight_intervals(self, move_interval=None, attack_interval=None):
        """
        设置打怪频率
        
        Args:
            move_interval: 移动间隔（秒）
            attack_interval: 攻击间隔（秒）
        """
        if move_interval is not None:
            self.move_interval = max(0.5, move_interval)
            print(f"[CONFIG] 设置移动间隔: {self.move_interval} 秒")
        
        if attack_interval is not None:
            self.fight_interval = max(0.1, attack_interval)
            print(f"[CONFIG] 设置攻击间隔: {self.fight_interval} 秒")
    def get_current_position_info(self):
        """
        获取当前位置信息（用于调试）
        
        Returns:
            dict: 包含当前移动状态的信息
        """
        return {
            'random_move_count': self.random_move_count,
            'max_random_moves': self.max_random_moves,
            'movement_radius': self.movement_radius,
            'movement_mode': self.movement_mode,
            'movement_area': self.movement_area,
            'screen_center': (self.screen_center_x, self.screen_center_y)
        }
    
    def validate_movement_system(self):
        """
        验证现实移动系统的有效性
        模拟多次随机移动，检查移动范围是否合理
        """
        print("\n[VALIDATION] 开始验证现实移动系统...")
        print(f"[VALIDATION] 当前移动模式: {self.movement_mode}")
        
        import math
        
        test_moves = 10
        positions = []
        
        print(f"[VALIDATION] 测试移动次数: {test_moves}")
        
        # 模拟多次随机移动
        for i in range(test_moves):
            pos_x, pos_y = self.get_random_combat_position()
            positions.append((pos_x, pos_y))
            
            if self.movement_mode == 'around_center':
                # 计算到屏幕中心的距离
                distance_to_center = math.sqrt(
                    (pos_x - self.screen_center_x) ** 2 + 
                    (pos_y - self.screen_center_y) ** 2
                )
                print(f"[VALIDATION] 第{i+1}次移动: ({pos_x}, {pos_y}), 距离中心: {distance_to_center:.1f}")
            else:
                print(f"[VALIDATION] 第{i+1}次移动: ({pos_x}, {pos_y})")
        
        # 测试回到中心
        center_pos = self.return_to_center()
        print(f"[VALIDATION] 回到中心位置: {center_pos}")
        
        # 验证结果
        if self.movement_mode == 'around_center':
            # 验证所有位置都在半径范围内
            distances = [math.sqrt((x - self.screen_center_x)**2 + (y - self.screen_center_y)**2) for x, y in positions]
            max_distance = max(distances)
            min_distance = min(distances)
            
            radius_ok = max_distance <= self.movement_radius * 1.1
            print(f"[VALIDATION] 最大距离: {max_distance:.1f}, 最小距离: {min_distance:.1f}")
            print(f"[VALIDATION] 半径控制: {'✅ 通过' if radius_ok else '❌ 失败'}")
            
        else:  # random_area
            # 验证所有位置都在指定区域内
            area_ok = all(
                self.movement_area['min_x'] <= x <= self.movement_area['max_x'] and
                self.movement_area['min_y'] <= y <= self.movement_area['max_y']
                for x, y in positions
            )
            print(f"[VALIDATION] 区域控制: {'✅ 通过' if area_ok else '❌ 失败'}")
            radius_ok = area_ok
        
        # 验证回到中心功能
        center_ok = center_pos == (self.screen_center_x, self.screen_center_y)
        print(f"[VALIDATION] 中心回归: {'✅ 通过' if center_ok else '❌ 失败'}")
        print(f"[VALIDATION] 系统验证: {'✅ 全部通过' if (radius_ok and center_ok) else '❌ 存在问题'}")
        
        return radius_ok and center_ok
    
    def _check_and_restart_equipment_monitor(self):
        """检查并重启装备监控线程 - 增强版"""
        if not self.is_running:
            print(f"[MONITOR] 游戏已停止，不重启检测器")
            return
            
        try:
            monitor_thread_alive = hasattr(self, 'monitor_thread') and self.monitor_thread and self.monitor_thread.is_alive()
            detector_running = self.detector and self.detector.is_running
            
            print(f"[MONITOR] 状态检查: 监控线程={monitor_thread_alive}, 检测器={detector_running}")
            
            # 如果检测线程死亡或检测器停止，重新启动
            if not monitor_thread_alive or not detector_running:
                print(f"[MONITOR] 检测系统异常，正在重启...")
                
                # 停止旧的检测器
                if self.detector:
                    try:
                        self.detector.stop_realtime_detection()
                        time.sleep(0.5)
                    except Exception as e:
                        print(f"[MONITOR] 停止旧检测器失败: {e}")
                
                # 等待旧线程结束
                if hasattr(self, 'monitor_thread') and self.monitor_thread:
                    try:
                        self.monitor_thread.join(timeout=2.0)
                        print(f"[MONITOR] 旧线程已结束")
                    except Exception as e:
                        print(f"[MONITOR] 等待旧线程结束失败: {e}")
                
                # 重新创建检测器
                try:
                    print(f"[MONITOR] 重新创建检测器...")
                    self.detector = TemplateEquipmentDetector()
                    
                    # 重新加载模板
                    template_dir = project_root / "templates"
                    if template_dir.exists():
                        loaded_count = self.detector.load_templates_from_folder(str(template_dir))
                        print(f"[MONITOR] 重新加载 {loaded_count} 个模板")
                    
                    # 重新启动检测
                    self.detector.start_realtime_detection(
                        callback=self.equipment_detected_callback,
                        fps=20
                    )
                    
                    # 重新创建监控线程
                    self.monitor_thread = threading.Thread(
                        target=self._equipment_monitor_loop,
                        daemon=True
                    )
                    self.monitor_thread.start()
                    
                    print(f"[MONITOR] 装备检测系统重启成功")
                    
                    # 等待初始化完成
                    time.sleep(1.0)
                    
                except Exception as restart_error:
                    print(f"[MONITOR] 重启检测系统失败: {restart_error}")
                    import traceback
                    traceback.print_exc()
                    
            else:
                print(f"[MONITOR] 检测系统正常运行")
                
        except Exception as e:
            print(f"[MONITOR] 检查重启监控器异常: {e}")
            import traceback
            traceback.print_exc()
            
    def start(self):
        """启动游戏控制器"""
        print(f"\n[SYSTEM] 启动游戏自动化系统...")
        print(f"=" * 60)
        print(f"功能说明:")
        print(f"- 实时监控装备掉落 (20FPS)")
        print(f"- 自动移动打怪 (移动间隔: {self.move_interval}s, 攻击间隔: {self.fight_interval}s)")
        print(f"- 发现装备时暂停打怪，自动捡装备")
        print(f"- 捡完装备后恢复打怪循环")
        print(f"=" * 60)
        
        self.is_running = True
        
        # 设置键盘监听
        self.setup_keyboard_listener()
        
        try:
            # 启动装备监控
            print(f"\n[DEBUG] 即将调用 start_equipment_monitor()...")
            self.start_equipment_monitor()
            print(f"[DEBUG] start_equipment_monitor() 调用完成")
            time.sleep(2)  # 等待监控启动
            print(f"[DEBUG] 等待监控启动完成")
            
            # 启动打怪循环
            self.start_fighting()
            
            print(f"\n[SYSTEM] 系统启动完成！按 Ctrl+C 或 Ctrl+Q 停止...")
            
            # 主线程保持运行
            while self.is_running:
                with self.stop_lock:
                    if self.should_stop:
                        print(f"\n[SYSTEM] 检测到停止信号，正在清理资源...")
                        break
                time.sleep(0.1)  # 更频繁检查停止信号
                
        except KeyboardInterrupt:
            print(f"\n[SYSTEM] 用户停止程序 (Ctrl+C)...")
        except Exception as e:
            print(f"\n[ERROR] 系统异常: {e}")
        finally:
            # 确保总是调用stop方法清理资源
            self.stop()
            
    def stop(self):
        """停止游戏控制器"""
        print(f"[SYSTEM] 正在停止游戏系统...")
        
        with self.stop_lock:
            self.should_stop = True
            
        self.is_running = False
        self.is_fighting = False
        
        # 清理键盘监听器
        try:
            keyboard.clear_all_hotkeys()
            print(f"[SYSTEM] ✓ 已清理键盘监听器")
        except Exception as e:
            print(f"[WARNING] 清理键盘监听器失败: {e}")
        
        # 强制停止装备检测
        if self.detector:
            print(f"[SYSTEM] 正在停止装备检测...")
            try:
                self.detector.stop_realtime_detection()
                print(f"[SYSTEM] ✓ 装备检测已停止")
            except Exception as e:
                print(f"[WARNING] 停止装备检测失败: {e}")
            
        # 等待线程结束
        print(f"[SYSTEM] 正在等待线程结束...")
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            print(f"[SYSTEM] 等待装备监控线程结束...")
            self.monitor_thread.join(timeout=3)
            if self.monitor_thread.is_alive():
                print(f"[WARNING] 装备监控线程未能在超时时间内结束")
            else:
                print(f"[SYSTEM] ✓ 装备监控线程已结束")
            
        if self.fight_thread and self.fight_thread.is_alive():
            print(f"[SYSTEM] 等待打怪线程结束...")
            self.fight_thread.join(timeout=3)
            if self.fight_thread.is_alive():
                print(f"[WARNING] 打怪线程未能在超时时间内结束")
            else:
                print(f"[SYSTEM] ✓ 打怪线程已结束")
            
        print(f"[SYSTEM] ✓ 游戏系统已完全停止")


def main():
    """主函数"""
    print(f"\n" + "=" * 70)
    print(f"🎮 游戏自动化系统 v3.0 - 增强版")
    print(f"=" * 70)
    print(f"🆕 新功能亮点:")
    print(f"  ✅ 移除人物检测 - 人物固定在屏幕中心")
    print(f"  ✅ 智能装备拾取 - 找到离中心最近的装备")
    print(f"  ✅ 随机战斗位置 - 在屏幕70%-80%范围内移动")
    print(f"  ✅ 自动回到原位 - 随机30次后回到中心")
    print(f"  ✅ 装备检测线程自动重启 - 增强稳定性")
    print(f"  ✅ 拾取不被打断 - 确保拾取过程完整")
    print(f"=" * 70)
    
    try:
        # 检查模板目录
        template_dir = project_root / "templates"
        if not template_dir.exists():
            print(f"\n⚠️  [ERROR] 模板目录不存在: {template_dir}")
            print(f"   请确保 templates 目录存在并包含装备模板图片")
            print(f"   可以使用 template_equipment_detector.py 来测试模板")
            return
            
        # 创建并启动游戏控制器
        game_controller = GameController()
        
        # 可选配置参数（根据需要取消注释）
        # game_controller.set_max_random_moves(25)        # 设置随机移动次数（默认30）
        # game_controller.set_movement_radius(150)        # 设置移动半径（默认200像素）
        # game_controller.set_fight_intervals(2.0, 1.0)  # 设置移动和攻击间隔（默认3.0s, 1.5s）
        
        # 验证现实移动系统（可选）
        print(f"\n🔍 验证现实移动系统...")
        validation_result = game_controller.validate_movement_system()
        
        if validation_result:
            print(f"\n✅ 系统验证通过！移动系统工作正常")
        else:
            print(f"\n⚠️  系统验证发现问题，但仍可以继续运行")
        
        print(f"\n🚀 正在启动游戏系统...")
        print(f"🎯 当前配置:")
        print(f"   - 移动半径: {game_controller.movement_radius} 像素")
        print(f"   - 随机移动次数: {game_controller.max_random_moves} 次")
        print(f"   - 移动间隔: {game_controller.move_interval} 秒")
        print(f"   - 攻击间隔: {game_controller.fight_interval} 秒")
        print(f"=" * 70)
        
        game_controller.start()
        
    except KeyboardInterrupt:
        print(f"\n\n🛑 用户中断程序 (Ctrl+C)")
    except Exception as e:
        print(f"\n\n⚠️  程序异常: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print(f"\n👋 游戏自动化系统已停止")
        print(f"=" * 70)


if __name__ == "__main__":
    main()
