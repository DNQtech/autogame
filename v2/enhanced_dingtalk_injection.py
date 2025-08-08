"""
增强版钉钉输入注入
专门针对钉钉等高安全应用的输入注入方法
"""

import ctypes
import ctypes.wintypes
import win32gui
import win32con
import win32api
import time
from typing import Optional

# 更多Windows API常量
WM_ACTIVATE = 0x0006
WM_SETFOCUS = 0x0007
WM_KILLFOCUS = 0x0008
WM_COMMAND = 0x0111
WM_SYSCOMMAND = 0x0112
WM_NCHITTEST = 0x0084
WM_NCLBUTTONDOWN = 0x00A1
WM_NCMOUSEMOVE = 0x00A0

# 系统级输入结构
class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        class _ki(ctypes.Structure):
            _fields_ = [
                ("wVk", ctypes.wintypes.WORD),
                ("wScan", ctypes.wintypes.WORD),
                ("dwFlags", ctypes.wintypes.DWORD),
                ("time", ctypes.wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.wintypes.ULONG))
            ]
        
        class _mi(ctypes.Structure):
            _fields_ = [
                ("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.wintypes.DWORD),
                ("dwFlags", ctypes.wintypes.DWORD),
                ("time", ctypes.wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.wintypes.ULONG))
            ]
        
        _fields_ = [("ki", _ki), ("mi", _mi)]
    
    _fields_ = [
        ("type", ctypes.wintypes.DWORD),
        ("ii", _INPUT)
    ]

# 输入类型常量
INPUT_MOUSE = 0
INPUT_KEYBOARD = 1

# 鼠标事件标志
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_ABSOLUTE = 0x8000

class EnhancedDingTalkInjector:
    """增强版钉钉输入注入器"""
    
    def __init__(self):
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32
    
    def inject_with_system_cursor(self, hwnd: int, x: int, y: int, action: str = 'click') -> bool:
        """使用系统光标进行注入（最接近真实用户操作）"""
        try:
            print(f"[ENHANCED] 开始系统光标注入: HWND={hwnd}, 坐标=({x},{y}), 动作={action}")
            
            # 1. 验证窗口和坐标
            if not self._validate_window_and_coordinates(hwnd, x, y):
                return False
            
            # 获取正确的客户区坐标
            client_left, client_top = win32gui.ClientToScreen(hwnd, (0, 0))
            screen_x = client_left + x
            screen_y = client_top + y
            
            print(f"[ENHANCED] 客户区屏幕坐标: ({screen_x}, {screen_y})")
            
            # 2. 温和激活窗口
            self._gentle_activate_window(hwnd)
            time.sleep(0.05)
            
            # 3. 保存当前光标位置
            current_pos = win32gui.GetCursorPos()
            print(f"[ENHANCED] 当前光标位置: {current_pos}")
            
            # 4. 移动系统光标到目标位置
            win32api.SetCursorPos((screen_x, screen_y))
            time.sleep(0.05)
            
            # 5. 执行真实的鼠标操作
            if action == 'click':
                # 左键按下和释放
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, screen_x, screen_y, 0, 0)
                time.sleep(0.02)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, screen_x, screen_y, 0, 0)
                print(f"[ENHANCED] 执行了真实左键点击")
                
            elif action == 'right_click':
                # 右键按下和释放
                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, screen_x, screen_y, 0, 0)
                time.sleep(0.02)
                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, screen_x, screen_y, 0, 0)
                print(f"[ENHANCED] 执行了真实右键点击")
                
            elif action == 'move_and_drag':
                # 移动并拖拽
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, screen_x, screen_y, 0, 0)
                time.sleep(0.3)  # 持续按住
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, screen_x, screen_y, 0, 0)
                print(f"[ENHANCED] 执行了真实拖拽操作")
            
            # 6. 恢复光标位置
            time.sleep(0.05)
            win32api.SetCursorPos(current_pos)
            
            print(f"[ENHANCED] 系统光标注入完成")
            return True
            
        except Exception as e:
            print(f"[ENHANCED] 系统光标注入失败: {e}")
            return False
    
    def _force_activate_window(self, hwnd: int):
        """强制激活窗口"""
        try:
            # 方法1: 标准激活
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
            win32gui.SetForegroundWindow(hwnd)
            
            # 方法2: 如果失败，尝试更强制的方法
            foreground_hwnd = win32gui.GetForegroundWindow()
            if foreground_hwnd != hwnd:
                # 模拟Alt+Tab切换
                win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)  # Alt按下
                win32api.keybd_event(win32con.VK_TAB, 0, 0, 0)   # Tab按下
                time.sleep(0.05)
                win32api.keybd_event(win32con.VK_TAB, 0, win32con.KEYEVENTF_KEYUP, 0)  # Tab释放
                win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0) # Alt释放
                
                time.sleep(0.1)
                win32gui.SetForegroundWindow(hwnd)
            
        except Exception as e:
            print(f"[ENHANCED] 窗口激活异常: {e}")
    
    def inject_with_sendinput(self, hwnd: int, x: int, y: int, action: str = 'click') -> bool:
        """使用SendInput API进行更底层的注入"""
        try:
            print(f"[ENHANCED] 开始SendInput注入: HWND={hwnd}, 坐标=({x},{y})")
            
            # 获取窗口屏幕坐标
            rect = win32gui.GetWindowRect(hwnd)
            screen_x = rect[0] + x
            screen_y = rect[1] + y
            
            # 转换为绝对坐标（0-65535范围）
            screen_width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
            screen_height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
            
            abs_x = int((screen_x * 65535) / screen_width)
            abs_y = int((screen_y * 65535) / screen_height)
            
            print(f"[ENHANCED] 绝对坐标: ({abs_x}, {abs_y})")
            
            # 激活窗口
            self._force_activate_window(hwnd)
            time.sleep(0.1)
            
            if action == 'click':
                # 创建鼠标输入事件
                inputs = []
                
                # 移动到目标位置
                move_input = INPUT()
                move_input.type = INPUT_MOUSE
                move_input.ii.mi.dx = abs_x
                move_input.ii.mi.dy = abs_y
                move_input.ii.mi.dwFlags = MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE
                inputs.append(move_input)
                
                # 左键按下
                down_input = INPUT()
                down_input.type = INPUT_MOUSE
                down_input.ii.mi.dx = abs_x
                down_input.ii.mi.dy = abs_y
                down_input.ii.mi.dwFlags = MOUSEEVENTF_LEFTDOWN | MOUSEEVENTF_ABSOLUTE
                inputs.append(down_input)
                
                # 左键释放
                up_input = INPUT()
                up_input.type = INPUT_MOUSE
                up_input.ii.mi.dx = abs_x
                up_input.ii.mi.dy = abs_y
                up_input.ii.mi.dwFlags = MOUSEEVENTF_LEFTUP | MOUSEEVENTF_ABSOLUTE
                inputs.append(up_input)
                
                # 发送输入事件
                input_array = (INPUT * len(inputs))(*inputs)
                result = self.user32.SendInput(len(inputs), input_array, ctypes.sizeof(INPUT))
                
                print(f"[ENHANCED] SendInput结果: {result}/{len(inputs)}")
                return result == len(inputs)
            
            return False
            
        except Exception as e:
            print(f"[ENHANCED] SendInput注入失败: {e}")
            return False
    
    def inject_game_move_character(self, hwnd: int, x: int, y: int, duration: float = 0.5) -> bool:
        """游戏角色移动注入 - Ctrl+左键长按操作"""
        try:
            print(f"[ENHANCED] 开始游戏角色移动注入: HWND={hwnd}, 坐标=({x},{y}), 持续时间={duration}s")
            
            # 1. 获取窗口信息和边界检查
            if not self._validate_window_and_coordinates(hwnd, x, y):
                return False
            
            rect = win32gui.GetWindowRect(hwnd)
            client_rect = win32gui.GetClientRect(hwnd)
            
            # 计算客户区偏移（排除标题栏和边框）
            client_left, client_top = win32gui.ClientToScreen(hwnd, (0, 0))
            offset_x = client_left - rect[0]
            offset_y = client_top - rect[1]
            
            # 使用客户区坐标计算屏幕坐标
            screen_x = client_left + x
            screen_y = client_top + y
            
            print(f"[ENHANCED] 窗口边界: {rect}")
            print(f"[ENHANCED] 客户区: {client_rect}, 偏移: ({offset_x}, {offset_y})")
            print(f"[ENHANCED] 最终屏幕坐标: ({screen_x}, {screen_y})")
            
            # 2. 减少闪烁的温和激活（不强制前台）
            self._gentle_activate_window(hwnd)
            time.sleep(0.05)  # 减少等待时间
            
            # 3. 保存当前光标位置
            current_pos = win32gui.GetCursorPos()
            
            # 4. 移动系统光标到目标位置
            win32api.SetCursorPos((screen_x, screen_y))
            time.sleep(0.05)
            
            # 5. 执行游戏角色移动操作：Ctrl+左键长按
            # 按下Ctrl键
            win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
            time.sleep(0.02)
            
            # 按下左键
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, screen_x, screen_y, 0, 0)
            print(f"[ENHANCED] 开始Ctrl+左键长按移动，持续{duration}秒")
            
            # 持续按住指定时间
            time.sleep(duration)
            
            # 释放左键
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, screen_x, screen_y, 0, 0)
            
            # 释放Ctrl键
            win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
            
            print(f"[ENHANCED] 游戏角色移动完成")
            
            # 6. 恢复光标位置
            time.sleep(0.05)
            win32api.SetCursorPos(current_pos)
            
            return True
            
        except Exception as e:
            print(f"[ENHANCED] 游戏角色移动注入失败: {e}")
            # 确保释放所有按键
            try:
                win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            except:
                pass
            return False
    
    def _validate_window_and_coordinates(self, hwnd: int, x: int, y: int) -> bool:
        """验证窗口和坐标的有效性"""
        try:
            # 检查窗口是否有效
            if not win32gui.IsWindow(hwnd):
                print(f"[ENHANCED] 错误：窗口句柄无效 HWND={hwnd}")
                return False
            
            # 获取窗口客户区大小
            client_rect = win32gui.GetClientRect(hwnd)
            client_width = client_rect[2] - client_rect[0]
            client_height = client_rect[3] - client_rect[1]
            
            # 检查坐标是否在客户区内
            if x < 0 or y < 0 or x >= client_width or y >= client_height:
                print(f"[ENHANCED] 警告：坐标({x},{y})超出客户区范围({client_width}x{client_height})")
                # 自动修正坐标到安全范围
                x = max(10, min(x, client_width - 10))
                y = max(10, min(y, client_height - 10))
                print(f"[ENHANCED] 坐标已修正为: ({x},{y})")
            
            return True
            
        except Exception as e:
            print(f"[ENHANCED] 窗口验证失败: {e}")
            return False
    
    def _gentle_activate_window(self, hwnd: int):
        """温和的窗口激活（减少闪烁）"""
        try:
            # 检查窗口是否已经是前台窗口
            foreground_hwnd = win32gui.GetForegroundWindow()
            if foreground_hwnd == hwnd:
                print(f"[ENHANCED] 窗口已在前台，无需激活")
                return
            
            # 温和激活：只显示窗口，不强制前台
            try:
                if win32gui.IsIconic(hwnd):  # 如果窗口最小化
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                else:
                    win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
            except Exception as show_error:
                # 如果显示窗口失败，尝试基本的显示
                try:
                    win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                except:
                    print(f"[ENHANCED] 显示窗口失败: {show_error}")
            
            # 尝试设置前台，但不强制
            try:
                win32gui.SetForegroundWindow(hwnd)
            except:
                # 如果设置前台失败，继续执行（某些情况下Windows不允许设置前台）
                print(f"[ENHANCED] 无法设置前台窗口，继续执行")
                pass
            
        except Exception as e:
            print(f"[ENHANCED] 温和激活异常: {e}")

# 全局增强注入器实例
_enhanced_injector = EnhancedDingTalkInjector()

def enhanced_inject_click(hwnd: int, x: int, y: int) -> bool:
    """增强版点击注入"""
    # 先尝试系统光标方法
    if _enhanced_injector.inject_with_system_cursor(hwnd, x, y, 'click'):
        return True
    
    # 如果失败，尝试SendInput方法
    print("[ENHANCED] 系统光标方法失败，尝试SendInput...")
    return _enhanced_injector.inject_with_sendinput(hwnd, x, y, 'click')

def enhanced_inject_move_character(hwnd: int, x: int, y: int, duration: float = 0.5):
    """增强版角色移动注入 - 游戏专用Ctrl+左键长按操作"""
    return _enhanced_injector.inject_game_move_character(hwnd, x, y, duration)

def enhanced_inject_drag(hwnd: int, x: int, y: int, duration: float = 0.5):
    """增强版拖拽注入 - 已弃用，请使用enhanced_inject_move_character进行游戏角色移动"""
    print("[WARNING] enhanced_inject_drag已弃用，建议使用enhanced_inject_move_character进行游戏角色移动")
    return enhanced_inject_move_character(hwnd, x, y, duration)

def enhanced_inject_right_click(hwnd: int, x: int, y: int) -> bool:
    """增强版右键点击注入"""
    return _enhanced_injector.inject_with_system_cursor(hwnd, x, y, 'right_click')

if __name__ == "__main__":
    print("增强版钉钉输入注入系统已加载")
    print("支持的操作: enhanced_inject_click, enhanced_inject_drag, enhanced_inject_right_click")
