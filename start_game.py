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
from hero_detector import HeroDetector


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
        
        # 游戏参数
        self.screen_width = 1920
        self.screen_height = 1080
        self.fight_interval = 1.5  # 打怪间隔（秒）
        self.move_interval = 3.0   # 移动间隔（秒）
        
    def equipment_detected_callback(self, match):
        """装备检测回调函数"""
        try:
            print(f"\n[EQUIPMENT] 发现装备！暂停打怪...")
            
            # 从 position元组中获取坐标和尺寸
            x, y, w, h = match.position
            
            # 计算装备中心坐标
            center_x = x + w // 2
            center_y = y + h // 2
            
            # 设置装备位置信息
            self.equipment_found = True
            self.equipment_position = (center_x, center_y)
            
            print(f"[EQUIPMENT] 装备名称: {match.equipment_name}")
            
            # 使用智能拾取方法
            self.smart_pickup_equipment(center_x, center_y)
            
        except Exception as e:
            print(f"[ERROR] 装备检测回调异常: {e}")
            import traceback
            traceback.print_exc()
        
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
        
        # 初始化装备检测器
        self.detector = TemplateEquipmentDetector()
        self.detector.load_templates_from_folder("D:/ggc/projects/only/equipment")
        
        # 初始化人物检测器
        self.hero_detector = HeroDetector()
        
        # 加载装备模板
        template_dir = project_root / "templates"
        if template_dir.exists():
            loaded_count = self.detector.load_templates_from_folder(str(template_dir))
            print(f"[INFO] 成功加载 {loaded_count} 个装备模板")
        else:
            print(f"[WARNING] 模板目录不存在: {template_dir}")
        
        # 启动监控线程
        self.monitor_thread = threading.Thread(
            target=self._equipment_monitor_loop,
            daemon=True
        )
        self.monitor_thread.start()
        
    def _equipment_monitor_loop(self):
        """装备监控循环（后台线程）"""
        try:
            print(f"[MONITOR] 启动装备检测线程...")
            print(f"[MONITOR] 检测器初始状态: is_running={self.detector.is_running}")
            print(f"[MONITOR] 游戏控制器状态: is_running={self.is_running}")
            
            # start_realtime_detection是阻塞调用，会持续运行直到被停止
            print(f"[MONITOR] 正在调用 start_realtime_detection...")
            self.detector.start_realtime_detection(
                callback=self.equipment_detected_callback,
                fps=20  # 20FPS高频检测
            )
            print(f"[MONITOR] start_realtime_detection 返回，装备检测线程已退出")
            print(f"[MONITOR] 检测器最终状态: is_running={self.detector.is_running}")
                
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
                    monitor_status = self.detector.is_running if self.detector else False
                    thread_alive = self.monitor_thread.is_alive() if self.monitor_thread else False
                    print(f"[COMBAT] 监控状态检查: 检测器={monitor_status}, 线程={thread_alive}")
                    last_monitor_check = current_time
                        
                # 检查是否需要暂停打怪（发现装备）
                if self.equipment_found:
                    print(f"[COMBAT] 暂停打怪，去捡装备...")
                    print(f"[COMBAT] 捡装备前检测器状态: {self.detector.is_running if self.detector else 'None'}")
                    self._handle_equipment_pickup()
                    print(f"[COMBAT] 捡装备后检测器状态: {self.detector.is_running if self.detector else 'None'}")
                    continue
                    
                current_time = time.time()
                
                # 移动角色（每3秒移动一次）
                if current_time - last_move_time >= self.move_interval:
                    move_pos = self.controller.get_random_move_position(
                        self.screen_width, self.screen_height
                    )
                    
                    print(f"[MOVE] 移动到: ({move_pos[0]}, {move_pos[1]})")
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
                    attack_pos = self.controller.get_random_move_position(
                        self.screen_width, self.screen_height
                    )
                    
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
                
    def _handle_equipment_pickup(self):
        """处理装备拾取"""
        if not self.equipment_position:
            print(f"[ERROR] 装备位置信息丢失")
            self.equipment_found = False
            return
            
        try:
            center_x, center_y = self.equipment_position
            
            print(f"[PICKUP] 开始捡装备: ({center_x}, {center_y})")
            
            # 执行智能捡装备
            pickup_result = self.controller.pickup_equipment(
                center_x, center_y, pickup_duration=2.0
            )
            
            if pickup_result.success:
                print(f"[PICKUP] 装备拾取成功! 耗时: {pickup_result.click_time:.2f}ms")
            else:
                print(f"[PICKUP] 装备拾取失败: {pickup_result.error_message}")
                
        except Exception as e:
            print(f"[ERROR] 装备拾取异常: {e}")
            
        finally:
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
                    print(f"[MONITOR] 新监控线程已启动")
                    
                    # 等待一下让新线程初始化
                    time.sleep(0.5)
                    print(f"[MONITOR] 新线程初始化后检测器状态: {self.detector.is_running}")
                    
                except Exception as e:
                    print(f"[ERROR] 重新启动装备监控失败: {e}")
                    import traceback
                    traceback.print_exc()
            elif detector_running:
                print(f"[MONITOR] 检测器仍在运行，无需重启")
            else:
                print(f"[MONITOR] 游戏已停止，不重启检测器")
            
            print(f"[COMBAT] 恢复打怪模式...")
            print(f"[DEBUG] 装备检测器状态: {self.detector.is_running if self.detector else 'None'}")
            
    def smart_pickup_equipment(self, initial_equipment_x, initial_equipment_y):
        """
        智能装备拾取：循环检测人物和装备位置，动态调整移动目标
        
        Args:
            initial_equipment_x: 装备初始 X坐标
            initial_equipment_y: 装备初始 Y坐标
        """
        print(f"[SMART_PICKUP] 开始智能拾取装备，初始位置: ({initial_equipment_x}, {initial_equipment_y})")
        
        # 暂停打怪
        self.is_fighting = False
        print(f"[SMART_PICKUP] 暂停打怪")
        
        try:
            max_attempts = 5  # 最大尝试次数
            pickup_threshold = 25  # 拾取距离阈值
            
            for attempt in range(max_attempts):
                print(f"[SMART_PICKUP] === 第 {attempt + 1} 次尝试 ===")
                
                # 检查停止信号
                if self.should_stop:
                    print(f"[SMART_PICKUP] 接收到停止信号，中断拾取")
                    return
                
                # 1. 检测人物位置
                hero_pos = self.hero_detector.detect_hero(threshold=0.6)
                if not hero_pos:
                    print(f"[SMART_PICKUP] 未检测到人物，尝试 {attempt + 1}/{max_attempts}")
                    if attempt == max_attempts - 1:
                        print(f"[SMART_PICKUP] 人物检测失败，强制拾取")
                        get_controller().left_click(initial_equipment_x, initial_equipment_y)
                        time.sleep(1.5)
                        break
                    time.sleep(0.5)
                    continue
                
                hero_x, hero_y = hero_pos.x, hero_pos.y
                print(f"[SMART_PICKUP] 人物位置: ({hero_x}, {hero_y}), 置信度: {hero_pos.confidence:.3f}")
                
                # 2. 重新检测装备位置（可能已移动）
                current_equipment_matches = self.detector.single_detection()[0]
                current_equipment_x, current_equipment_y = initial_equipment_x, initial_equipment_y
                
                if current_equipment_matches:
                    # 找到最近的装备
                    closest_match = None
                    min_distance = float('inf')
                    
                    for match in current_equipment_matches:
                        ex, ey, ew, eh = match.position
                        equipment_center_x = ex + ew // 2
                        equipment_center_y = ey + eh // 2
                        
                        distance_to_initial = self.hero_detector.calculate_distance(
                            (equipment_center_x, equipment_center_y), 
                            (initial_equipment_x, initial_equipment_y)
                        )
                        
                        if distance_to_initial < min_distance:
                            min_distance = distance_to_initial
                            closest_match = match
                            current_equipment_x = equipment_center_x
                            current_equipment_y = equipment_center_y
                    
                    if closest_match:
                        print(f"[SMART_PICKUP] 更新装备位置: ({current_equipment_x}, {current_equipment_y})")
                    else:
                        print(f"[SMART_PICKUP] 未找到装备，使用初始位置")
                else:
                    print(f"[SMART_PICKUP] 未检测到装备，使用初始位置")
                
                # 3. 计算人物与装备的距离
                distance = self.hero_detector.calculate_distance(
                    (hero_x, hero_y), (current_equipment_x, current_equipment_y)
                )
                print(f"[SMART_PICKUP] 人物距离装备: {distance:.1f} 像素")
                
                # 4. 判断是否在拾取范围内
                if distance <= pickup_threshold:
                    print(f"[SMART_PICKUP] ✅ 人物在装备附近，执行拾取")
                    get_controller().left_click(current_equipment_x, current_equipment_y)
                    time.sleep(1.5)
                    print(f"[SMART_PICKUP] ✅ 装备拾取完成")
                    break
                else:
                    # 5. 计算新的移动目标位置
                    target_x, target_y = self.hero_detector.get_move_position_near_equipment(
                        (hero_x, hero_y), (current_equipment_x, current_equipment_y), distance=20
                    )
                    print(f"[SMART_PICKUP] 计算新目标: ({target_x}, {target_y})")
                    
                    # 6. 移动到新目标位置
                    print(f"[SMART_PICKUP] 移动到新目标位置...")
                    move_result = get_controller().move_character(target_x, target_y, duration=1.0)
                    print(f"[SMART_PICKUP] 移动完成")
                    
                    # 7. 等待移动完成
                    time.sleep(1.2)
                    
                    # 继续下一次循环检测
                    if attempt < max_attempts - 1:
                        print(f"[SMART_PICKUP] 继续下一次检测...")
                    else:
                        print(f"[SMART_PICKUP] 达到最大尝试次数，强制拾取")
                        get_controller().left_click(current_equipment_x, current_equipment_y)
                        time.sleep(1.5)
                
        except Exception as e:
            print(f"[SMART_PICKUP] ⚠️ 智能拾取异常: {e}")
            import traceback
            traceback.print_exc()
            print(f"[SMART_PICKUP] 异常情况下强制拾取")
            try:
                get_controller().left_click(initial_equipment_x, initial_equipment_y)
                time.sleep(1.5)
            except:
                print(f"[SMART_PICKUP] 强制拾取也失败")
        
        # 8. 恢复打怪状态
        time.sleep(1.0)
        self.is_fighting = True
        self.equipment_found = False
        print(f"[SMART_PICKUP] ✅ 智能拾取流程完成，恢复打怪状态")
        
        # 9. 检查并重启装备检测
        self._check_and_restart_equipment_monitor()
    

    
    def _check_and_restart_equipment_monitor(self):
        """检查并重启装备监控线程"""
        if hasattr(self, 'equipment_monitor_thread'):
            print(f"[MONITOR] 装备监控线程状态: alive={self.equipment_monitor_thread.is_alive()}")
            print(f"[MONITOR] 检测器状态: is_running={self.detector.is_running}")
            
            # 如果检测线程停止了，重新启动
            if not self.equipment_monitor_thread.is_alive() or not self.detector.is_running:
                print(f"[MONITOR] 检测线程已停止，重新启动...")
                time.sleep(0.5)  # 等待一下
                self._restart_equipment_monitor()
            else:
                print(f"[MONITOR] 检测线程正常运行，无需重启")
            
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
            self.start_equipment_monitor()
            time.sleep(2)  # 等待监控启动
            
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
    print(f"[MAIN] 游戏自动化控制系统")
    print(f"[MAIN] 版本: 1.0")
    print(f"[MAIN] 功能: 自动打怪 + 装备监控 + 智能拾取")
    
    # 检查模板目录
    template_dir = project_root / "templates"
    if not template_dir.exists():
        print(f"[ERROR] 模板目录不存在: {template_dir}")
        print(f"[ERROR] 请确保 templates 目录存在并包含装备模板图片")
        return
        
    # 创建并启动游戏控制器
    game_controller = GameController()
    game_controller.start()


if __name__ == "__main__":
    main()
