# -*- coding: utf-8 -*-
"""
鼠标键盘控制器
提供自动化的鼠标和键盘操作功能
"""

import pyautogui
import time
from typing import Tuple, Optional
from dataclasses import dataclass

@dataclass
class ClickResult:
    """点击操作结果"""
    success: bool
    x: int
    y: int
    error_message: Optional[str] = None
    click_time: float = 0.0  # 点击耗时（毫秒）

class MouseKeyboardController:
    """鼠标键盘控制器"""
    
    def __init__(self):
        # 设置pyautogui安全参数
        pyautogui.FAILSAFE = True  # 鼠标移到左上角时停止
        pyautogui.PAUSE = 0.01     # 每次操作间隔10ms
        
    def click_position(self, x: int, y: int, button: str = 'left', clicks: int = 1, 
                      interval: float = 0.0) -> ClickResult:
        """
        点击指定坐标位置
        
        Args:
            x: X坐标
            y: Y坐标  
            button: 鼠标按键 ('left', 'right', 'middle')
            clicks: 点击次数
            interval: 多次点击间隔时间（秒）
            
        Returns:
            ClickResult: 点击结果
        """
        start_time = time.time()
        
        try:
            pyautogui.click(x, y, clicks=clicks, interval=interval, button=button)
            
            click_time = (time.time() - start_time) * 1000  # 转换为毫秒
            
            return ClickResult(
                success=True,
                x=x,
                y=y,
                click_time=click_time
            )
            
        except Exception as e:
            click_time = (time.time() - start_time) * 1000
            return ClickResult(
                success=False,
                x=x,
                y=y,
                error_message=str(e),
                click_time=click_time
            )
    
    def left_click(self, x: int, y: int) -> ClickResult:
        """左键单击"""
        return self.click_position(x, y, button='left', clicks=1)
    
    def right_click(self, x: int, y: int) -> ClickResult:
        """右键单击"""
        return self.click_position(x, y, button='right', clicks=1)
    
    def double_click(self, x: int, y: int) -> ClickResult:
        """左键双击"""
        return self.click_position(x, y, button='left', clicks=2, interval=0.1)
    
    def drag_to(self, start_x: int, start_y: int, end_x: int, end_y: int, 
               duration: float = 0.5) -> ClickResult:
        """
        拖拽操作
        
        Args:
            start_x: 起始X坐标
            start_y: 起始Y坐标
            end_x: 结束X坐标
            end_y: 结束Y坐标
            duration: 拖拽持续时间（秒）
            
        Returns:
            ClickResult: 操作结果
        """
        start_time = time.time()
        
        try:
            pyautogui.drag(start_x, start_y, end_x - start_x, end_y - start_y, duration=duration)
            
            drag_time = (time.time() - start_time) * 1000
            
            return ClickResult(
                success=True,
                x=end_x,
                y=end_y,
                click_time=drag_time
            )
            
        except Exception as e:
            drag_time = (time.time() - start_time) * 1000
            return ClickResult(
                success=False,
                x=end_x,
                y=end_y,
                error_message=str(e),
                click_time=drag_time
            )
    
    def send_key(self, key: str, presses: int = 1, interval: float = 0.0) -> bool:
        """
        发送键盘按键
        
        Args:
            key: 按键名称 (如 'space', 'enter', 'f1', 'ctrl', 'alt' 等)
            presses: 按键次数
            interval: 多次按键间隔时间（秒）
            
        Returns:
            bool: 是否成功
        """
        try:
            pyautogui.press(key, presses=presses, interval=interval)
            return True
        except Exception as e:
            print(f"❌ 发送按键失败: {e}")
            return False
    
    def send_hotkey(self, *keys) -> bool:
        """
        发送组合键
        
        Args:
            *keys: 按键组合 (如 'ctrl', 'c' 或 'alt', 'tab')
            
        Returns:
            bool: 是否成功
        """
        try:
            pyautogui.hotkey(*keys)
            return True
        except Exception as e:
            print(f"❌ 发送组合键失败: {e}")
            return False
    
    def type_text(self, text: str, interval: float = 0.0) -> bool:
        """
        输入文本
        
        Args:
            text: 要输入的文本
            interval: 字符间隔时间（秒）
            
        Returns:
            bool: 是否成功
        """
        try:
            pyautogui.typewrite(text, interval=interval)
            return True
        except Exception as e:
            print(f"❌ 输入文本失败: {e}")
            return False
    
    def get_mouse_position(self) -> Tuple[int, int]:
        """获取当前鼠标位置"""
        return pyautogui.position()
    
    def move_mouse(self, x: int, y: int, duration: float = 0.0) -> bool:
        """
        移动鼠标到指定位置
        
        Args:
            x: X坐标
            y: Y坐标
            duration: 移动持续时间（秒）
            
        Returns:
            bool: 是否成功
        """
        try:
            pyautogui.moveTo(x, y, duration=duration)
            return True
        except Exception as e:
            print(f"❌ 移动鼠标失败: {e}")
            return False
    
    def scroll(self, clicks: int, x: Optional[int] = None, y: Optional[int] = None) -> bool:
        """
        滚轮滚动
        
        Args:
            clicks: 滚动次数（正数向上，负数向下）
            x: 滚动位置X坐标（可选）
            y: 滚动位置Y坐标（可选）
            
        Returns:
            bool: 是否成功
        """
        try:
            if x is not None and y is not None:
                pyautogui.scroll(clicks, x=x, y=y)
            else:
                pyautogui.scroll(clicks)
            return True
        except Exception as e:
            print(f"❌ 滚轮滚动失败: {e}")
            return False
    
    # ========== 游戏专用功能 ==========
    
    def move_character(self, x: int, y: int, duration: float = 0.5) -> ClickResult:
        """
        移动角色：长按Ctrl+左键
        
        Args:
            x: 移动目标X坐标
            y: 移动目标Y坐标
            duration: 移动持续时间（秒）
            
        Returns:
            ClickResult: 移动结果
        """
        start_time = time.time()
        
        try:
            # 按下Ctrl键
            pyautogui.keyDown('ctrl')
            
            # 移动到目标位置
            pyautogui.moveTo(x, y)
            
            # 按下左键并持续
            pyautogui.mouseDown(x, y, button='left')
            
            # 持续移动指定时间
            time.sleep(duration)
            
            # 释放左键
            pyautogui.mouseUp(x, y, button='left')
            
            # 释放Ctrl键
            pyautogui.keyUp('ctrl')
            
            move_time = (time.time() - start_time) * 1000
            
            return ClickResult(
                success=True,
                x=x,
                y=y,
                click_time=move_time
            )
            
        except Exception as e:
            # 确保释放所有按键
            try:
                pyautogui.keyUp('ctrl')
                pyautogui.mouseUp(button='left')
            except:
                pass
                
            move_time = (time.time() - start_time) * 1000
            return ClickResult(
                success=False,
                x=x,
                y=y,
                error_message=str(e),
                click_time=move_time
            )
    
    def attack_skill(self, x: int, y: int) -> ClickResult:
        """
        攻击技能：右键点击
        
        Args:
            x: 攻击目标X坐标
            y: 攻击目标Y坐标
            
        Returns:
            ClickResult: 攻击结果
        """
        start_time = time.time()
        
        try:
            # 右键点击放技能
            pyautogui.click(x, y, button='right')
            
            attack_time = (time.time() - start_time) * 1000
            
            return ClickResult(
                success=True,
                x=x,
                y=y,
                click_time=attack_time
            )
            
        except Exception as e:
            attack_time = (time.time() - start_time) * 1000
            return ClickResult(
                success=False,
                x=x,
                y=y,
                error_message=str(e),
                click_time=attack_time
            )
    
    def pickup_equipment(self, x: int, y: int, pickup_duration: float = 2.0) -> ClickResult:
        """
        捡装备功能：先移动到装备位置，然后持续左键点击
        
        Args:
            x: 装备中心X坐标
            y: 装备中心Y坐标
            pickup_duration: 持续点击时间（秒）
            
        Returns:
            ClickResult: 拾取结果
        """
        start_time = time.time()
        
        try:
            # 第一步：移动到装备位置
            move_result = self.move_character(x, y, 0.3)  # 0.3秒移动
            if not move_result.success:
                return move_result
            
            # 等待移动完成
            time.sleep(0.2)
            
            # 第二步：持续左键点击拾取装备
            end_time = time.time() + pickup_duration
            click_count = 0
            
            while time.time() < end_time:
                pyautogui.click(x, y, button='left')
                click_count += 1
                time.sleep(0.1)  # 每100ms点击一次
            
            pickup_time = (time.time() - start_time) * 1000
            
            return ClickResult(
                success=True,
                x=x,
                y=y,
                click_time=pickup_time
            )
            
        except Exception as e:
            # 确保释放所有按键
            try:
                pyautogui.keyUp('ctrl')
                pyautogui.mouseUp(button='left')
            except:
                pass
                
            pickup_time = (time.time() - start_time) * 1000
            return ClickResult(
                success=False,
                x=x,
                y=y,
                error_message=str(e),
                click_time=pickup_time
            )
    
    def get_random_move_position(self, screen_width: int = 1920, screen_height: int = 1080) -> Tuple[int, int]:
        """
        获取屏幕中心70%内的随机位置
        
        Args:
            screen_width: 屏幕宽度
            screen_height: 屏幕高度
            
        Returns:
            Tuple[int, int]: 随机位置(x, y)
        """
        import random
        
        # 计算屏幕中心区域（70%范围）
        center_x = screen_width // 2
        center_y = screen_height // 2
        
        # 70%范围的半径
        radius_x = int(screen_width * 0.35)  # 70% / 2 = 35%
        radius_y = int(screen_height * 0.35)
        
        # 随机生成位置
        random_x = random.randint(center_x - radius_x, center_x + radius_x)
        random_y = random.randint(center_y - radius_y, center_y + radius_y)
        
        return random_x, random_y
    
    def combat_mode(self, duration: float = 5.0, screen_width: int = 1920, screen_height: int = 1080) -> ClickResult:
        """
        战斗模式：一边随机移动一边攻击
        
        Args:
            duration: 战斗持续时间（秒）
            screen_width: 屏幕宽度
            screen_height: 屏幕高度
            
        Returns:
            ClickResult: 战斗结果
        """
        start_time = time.time()
        end_time = start_time + duration
        
        try:
            while time.time() < end_time:
                # 获取随机移动位置
                move_x, move_y = self.get_random_move_position(screen_width, screen_height)
                
                # 移动角色（0.3秒）
                self.move_character(move_x, move_y, 0.3)
                
                # 攻击技能（右键）
                self.attack_skill(move_x, move_y)
                
                # 等待一下再继续
                time.sleep(0.2)
            
            combat_time = (time.time() - start_time) * 1000
            
            return ClickResult(
                success=True,
                x=0,
                y=0,
                click_time=combat_time
            )
            
        except Exception as e:
            # 确保释放所有按键
            try:
                pyautogui.keyUp('ctrl')
                pyautogui.mouseUp(button='left')
                pyautogui.mouseUp(button='right')
            except:
                pass
                
            combat_time = (time.time() - start_time) * 1000
            return ClickResult(
                success=False,
                x=0,
                y=0,
                error_message=str(e),
                click_time=combat_time
            )
    
    def start_continuous_attack(self, x: int, y: int) -> bool:
        """
        开始持续攻击（非阻塞）
        长按Ctrl+右键，需要手动调用stop_continuous_attack停止
        
        Args:
            x: 攻击目标X坐标
            y: 攻击目标Y坐标
            
        Returns:
            bool: 是否成功开始
        """
        try:
            # 移动到目标位置
            pyautogui.moveTo(x, y)
            
            # 按下Ctrl键
            pyautogui.keyDown('ctrl')
            
            # 按下右键
            pyautogui.mouseDown(x, y, button='right')
            
            return True
            
        except Exception as e:
            print(f"❌ 开始持续攻击失败: {e}")
            return False
    
    def stop_continuous_attack(self) -> bool:
        """
        停止持续攻击
        
        Returns:
            bool: 是否成功停止
        """
        try:
            # 释放右键
            pyautogui.mouseUp(button='right')
            
            # 释放Ctrl键
            pyautogui.keyUp('ctrl')
            
            return True
            
        except Exception as e:
            print(f"❌ 停止持续攻击失败: {e}")
            return False

# 全局控制器实例
_controller_instance = None

def get_controller() -> MouseKeyboardController:
    """获取全局控制器实例（单例模式）"""
    global _controller_instance
    if _controller_instance is None:
        _controller_instance = MouseKeyboardController()
    return _controller_instance

# 便捷函数
def auto_click(x: int, y: int, button: str = 'left') -> ClickResult:
    """便捷的自动点击函数"""
    controller = get_controller()
    return controller.click_position(x, y, button=button)

def auto_left_click(x: int, y: int) -> ClickResult:
    """便捷的左键点击函数"""
    controller = get_controller()
    return controller.left_click(x, y)

def auto_right_click(x: int, y: int) -> ClickResult:
    """便捷的右键点击函数"""
    controller = get_controller()
    return controller.right_click(x, y)

def send_key_shortcut(key: str) -> bool:
    """便捷的发送按键函数"""
    controller = get_controller()
    return controller.send_key(key)

# 游戏专用便捷函数
def game_move_character(x: int, y: int, duration: float = 0.5) -> ClickResult:
    """便捷的移动函数：长按Ctrl+左键移动"""
    controller = get_controller()
    return controller.move_character(x, y, duration)

def game_attack_skill(x: int, y: int) -> ClickResult:
    """便捷的攻击技能函数：右键点击"""
    controller = get_controller()
    return controller.attack_skill(x, y)

def game_pickup_equipment(x: int, y: int, pickup_duration: float = 2.0) -> ClickResult:
    """便捷的捡装备函数：移动+持续左键点击"""
    controller = get_controller()
    return controller.pickup_equipment(x, y, pickup_duration)

def game_combat_mode(duration: float = 5.0, screen_width: int = 1920, screen_height: int = 1080) -> ClickResult:
    """便捷的战斗模式函数：随机移动+攻击"""
    controller = get_controller()
    return controller.combat_mode(duration, screen_width, screen_height)

def game_get_random_position(screen_width: int = 1920, screen_height: int = 1080) -> Tuple[int, int]:
    """便捷的随机位置函数：获取屏幕中心70%内随机位置"""
    controller = get_controller()
    return controller.get_random_move_position(screen_width, screen_height)

def main():
    """测试函数"""
    print("🖱️ 鼠标键盘控制器测试")
    print("=" * 50)
    
    controller = MouseKeyboardController()
    
    # 获取当前鼠标位置
    x, y = controller.get_mouse_position()
    print(f"当前鼠标位置: ({x}, {y})")
    
    # 测试基础点击
    print(f"\n测试基础点击: ({x}, {y})")
    result = controller.left_click(x, y)
    
    if result.success:
        print(f"✅ 左键点击成功! 耗时: {result.click_time:.2f}ms")
    else:
        print(f"❌ 左键点击失败: {result.error_message}")
    
    # 测试游戏功能
    print(f"\n🎮 游戏功能测试:")
    
    # 测试移动功能
    print(f"测试移动功能: ({x}, {y}) - 0.3秒移动")
    move_result = controller.move_character(x, y, 0.3)
    
    if move_result.success:
        print(f"✅ 移动成功! 耗时: {move_result.click_time:.2f}ms")
    else:
        print(f"❌ 移动失败: {move_result.error_message}")
    
    # 测试攻击技能
    print(f"\n测试攻击技能: ({x}, {y})")
    attack_result = controller.attack_skill(x, y)
    
    if attack_result.success:
        print(f"✅ 攻击技能成功! 耗时: {attack_result.click_time:.2f}ms")
    else:
        print(f"❌ 攻击技能失败: {attack_result.error_message}")
    
    # 测试捡装备功能
    print(f"\n测试捡装备功能: ({x}, {y}) - 移动+2秒持续点击")
    pickup_result = controller.pickup_equipment(x, y, 1.0)  # 测试时用1秒
    
    if pickup_result.success:
        print(f"✅ 捡装备成功! 耗时: {pickup_result.click_time:.2f}ms")
    else:
        print(f"❌ 捡装备失败: {pickup_result.error_message}")
    
    # 测试随机位置
    print(f"\n测试随机位置生成:")
    random_x, random_y = controller.get_random_move_position(1920, 1080)
    print(f"随机位置: ({random_x}, {random_y})")
    
    print("\n🎯 新游戏功能说明:")
    print("• move_character(x, y, duration) - 长按Ctrl+左键移动")
    print("• attack_skill(x, y) - 右键点击攻击技能")
    print("• pickup_equipment(x, y, duration) - 移动+持续左键捡装备")
    print("• combat_mode(duration) - 随机移动+攻击组合")
    print("• get_random_move_position() - 获取屏幕中心70%内随机位置")
    
    print("\n⌨️ 可用的按键示例:")
    print("- 方向键: 'up', 'down', 'left', 'right'")
    print("- 功能键: 'f1', 'f2', ..., 'f12'")
    print("- 修饰键: 'ctrl', 'alt', 'shift', 'win'")
    print("- 其他键: 'space', 'enter', 'esc', 'tab', 'backspace'")

if __name__ == "__main__":
    main()
