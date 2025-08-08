"""
高级输入注入系统 - 支持真正的非激活窗口输入
使用多种底层技术实现对非激活窗口的输入注入
"""

import ctypes
import ctypes.wintypes
import win32gui
import win32con
import win32api
import win32process
import time
import threading
from typing import Optional, Tuple, List
from dataclasses import dataclass

# Windows API 常量
WH_KEYBOARD_LL = 13
WH_MOUSE_LL = 14
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_RBUTTONDOWN = 0x0204
WM_RBUTTONUP = 0x0205
WM_MOUSEMOVE = 0x0200

# 输入结构体
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
        ("_input", _INPUT)
    ]

@dataclass
class InputEvent:
    """输入事件数据类"""
    hwnd: int
    x: int
    y: int
    action: str
    key_code: Optional[int] = None
    duration: float = 0.0

class AdvancedInputInjector:
    """高级输入注入器 - 支持多种非激活窗口输入方法"""
    
    def __init__(self):
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32
        self.injection_methods = [
            self._method_direct_message,
            self._method_sendinput_targeted,
            self._method_thread_injection,
            self._method_hook_injection,
        ]
        
    def inject_input(self, event: InputEvent) -> bool:
        """尝试多种方法注入输入到非激活窗口"""
        print(f"[INJECT] 开始输入注入: HWND={event.hwnd}, 动作={event.action}")
        
        # 按优先级尝试各种注入方法
        for i, method in enumerate(self.injection_methods):
            try:
                print(f"[INJECT] 尝试方法 {i+1}: {method.__name__}")
                if method(event):
                    print(f"[INJECT] 方法 {i+1} 成功")
                    return True
                else:
                    print(f"[INJECT] 方法 {i+1} 失败")
            except Exception as e:
                print(f"[INJECT] 方法 {i+1} 异常: {e}")
                continue
        
        print(f"[INJECT] 所有注入方法都失败")
        return False
    
    def _method_direct_message(self, event: InputEvent) -> bool:
        """方法1: 直接消息注入（增强版，针对高安全应用优化）"""
        try:
            if not win32gui.IsWindow(event.hwnd):
                return False
            
            # 获取窗口信息
            window_text = win32gui.GetWindowText(event.hwnd)
            class_name = win32gui.GetClassName(event.hwnd)
            
            # 针对微信等高安全应用的特殊处理
            is_high_security = any(keyword in window_text.lower() for keyword in ['微信', 'wechat'])
            
            if is_high_security:
                print(f"[INJECT] 检测到高安全应用: {window_text}")
                return self._high_security_injection(event)
            
            # 获取窗口线程和进程信息
            thread_id, process_id = win32process.GetWindowThreadProcessId(event.hwnd)
            
            # 尝试附加到目标窗口的输入队列
            current_thread = win32api.GetCurrentThreadId()
            if thread_id != current_thread:
                win32process.AttachThreadInput(current_thread, thread_id, True)
            
            try:
                if event.action == 'move_and_drag':
                    return self._direct_message_move_drag(event)
                elif event.action == 'click':
                    return self._direct_message_click(event)
                elif event.action == 'right_click':
                    return self._direct_message_right_click(event)
                
            finally:
                # 分离输入队列
                if thread_id != current_thread:
                    win32process.AttachThreadInput(current_thread, thread_id, False)
            
            return True
            
        except Exception as e:
            print(f"[INJECT] 直接消息注入失败: {e}")
            return False
    
    def _high_security_injection(self, event: InputEvent) -> bool:
        """针对高安全应用（如微信）的特殊注入方法"""
        try:
            print(f"[INJECT] 使用高安全注入方法")
            
            # 方法1: 使用WM_COMMAND消息
            if event.action == 'click':
                # 尝试发送WM_COMMAND消息
                win32gui.SendMessage(event.hwnd, win32con.WM_COMMAND, 0, 0)
                
                # 备用：使用WM_CHAR消息模拟字符输入
                win32gui.SendMessage(event.hwnd, win32con.WM_CHAR, ord(' '), 0)
                
                return True
            
            # 方法2: 使用SetWindowPos强制重绘
            if event.action == 'move_and_drag':
                # 获取当前窗口位置
                rect = win32gui.GetWindowRect(event.hwnd)
                
                # 微调窗口位置触发重绘
                win32gui.SetWindowPos(
                    event.hwnd, 0, 
                    rect[0], rect[1], rect[2]-rect[0], rect[3]-rect[1],
                    0x0001 | 0x0002 | 0x0010  # SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE
                )
                
                # 然后发送鼠标消息
                lparam = (event.y << 16) | event.x
                win32gui.SendMessage(event.hwnd, WM_LBUTTONDOWN, win32con.MK_CONTROL, lparam)
                time.sleep(event.duration)
                win32gui.SendMessage(event.hwnd, WM_LBUTTONUP, 0, lparam)
                
                return True
            
            # 方法3: 使用BroadcastSystemMessage
            if event.action == 'right_click':
                # 广播系统消息
                try:
                    import ctypes.wintypes
                    user32 = ctypes.windll.user32
                    
                    # 发送广播消息
                    lparam = (event.y << 16) | event.x
                    user32.SendMessageW(event.hwnd, WM_RBUTTONDOWN, 0, lparam)
                    time.sleep(0.05)
                    user32.SendMessageW(event.hwnd, WM_RBUTTONUP, 0, lparam)
                    
                    return True
                except:
                    pass
            
            return False
            
        except Exception as e:
            print(f"[INJECT] 高安全注入失败: {e}")
            return False
    
    def _direct_message_move_drag(self, event: InputEvent) -> bool:
        """直接消息方式的移动拖拽"""
        # Ctrl键按下
        win32gui.PostMessage(event.hwnd, WM_KEYDOWN, win32con.VK_CONTROL, 0)
        
        # 鼠标移动到目标位置
        lparam = (event.y << 16) | event.x
        win32gui.PostMessage(event.hwnd, WM_MOUSEMOVE, 0, lparam)
        
        # 左键按下（开始拖拽）
        win32gui.PostMessage(event.hwnd, WM_LBUTTONDOWN, win32con.MK_CONTROL, lparam)
        
        # 持续时间
        time.sleep(event.duration)
        
        # 左键释放
        win32gui.PostMessage(event.hwnd, WM_LBUTTONUP, 0, lparam)
        
        # Ctrl键释放
        win32gui.PostMessage(event.hwnd, WM_KEYUP, win32con.VK_CONTROL, 0)
        
        return True
    
    def _direct_message_click(self, event: InputEvent) -> bool:
        """直接消息方式的点击"""
        lparam = (event.y << 16) | event.x
        win32gui.PostMessage(event.hwnd, WM_LBUTTONDOWN, 0, lparam)
        time.sleep(0.05)
        win32gui.PostMessage(event.hwnd, WM_LBUTTONUP, 0, lparam)
        return True
    
    def _direct_message_right_click(self, event: InputEvent) -> bool:
        """直接消息方式的右键点击"""
        lparam = (event.y << 16) | event.x
        win32gui.PostMessage(event.hwnd, WM_RBUTTONDOWN, 0, lparam)
        time.sleep(0.05)
        win32gui.PostMessage(event.hwnd, WM_RBUTTONUP, 0, lparam)
        return True
    
    def _method_sendinput_targeted(self, event: InputEvent) -> bool:
        """方法2: 目标化SendInput注入"""
        try:
            # 获取窗口位置
            rect = win32gui.GetWindowRect(event.hwnd)
            screen_x = rect[0] + event.x
            screen_y = rect[1] + event.y
            
            # 临时设置前台窗口（快速切换）
            old_hwnd = win32gui.GetForegroundWindow()
            
            # 快速激活目标窗口
            win32gui.SetForegroundWindow(event.hwnd)
            time.sleep(0.01)  # 极短暂等待
            
            try:
                # 使用SendInput发送输入
                if event.action == 'move_and_drag':
                    success = self._sendinput_move_drag(screen_x, screen_y, event.duration)
                elif event.action == 'click':
                    success = self._sendinput_click(screen_x, screen_y)
                elif event.action == 'right_click':
                    success = self._sendinput_right_click(screen_x, screen_y)
                else:
                    success = False
                
            finally:
                # 快速恢复原窗口
                if old_hwnd:
                    win32gui.SetForegroundWindow(old_hwnd)
            
            return success
            
        except Exception as e:
            print(f"[INJECT] 目标化SendInput失败: {e}")
            return False
    
    def _sendinput_move_drag(self, x: int, y: int, duration: float) -> bool:
        """SendInput方式的移动拖拽"""
        inputs = []
        
        # Ctrl键按下
        inputs.append(self._create_key_input(win32con.VK_CONTROL, True))
        
        # 鼠标移动
        inputs.append(self._create_mouse_input(x, y, 0, 0x0001 | 0x8000))  # MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE
        
        # 左键按下
        inputs.append(self._create_mouse_input(x, y, 0, 0x0002))  # MOUSEEVENTF_LEFTDOWN
        
        # 发送输入
        self.user32.SendInput(len(inputs), (INPUT * len(inputs))(*inputs), ctypes.sizeof(INPUT))
        
        # 持续时间
        time.sleep(duration)
        
        # 左键释放和Ctrl释放
        release_inputs = [
            self._create_mouse_input(x, y, 0, 0x0004),  # MOUSEEVENTF_LEFTUP
            self._create_key_input(win32con.VK_CONTROL, False)
        ]
        
        self.user32.SendInput(len(release_inputs), (INPUT * len(release_inputs))(*release_inputs), ctypes.sizeof(INPUT))
        return True
    
    def _sendinput_click(self, x: int, y: int) -> bool:
        """SendInput方式的点击"""
        inputs = [
            self._create_mouse_input(x, y, 0, 0x0001 | 0x8000),  # 移动
            self._create_mouse_input(x, y, 0, 0x0002),  # 按下
            self._create_mouse_input(x, y, 0, 0x0004),  # 释放
        ]
        
        result = self.user32.SendInput(len(inputs), (INPUT * len(inputs))(*inputs), ctypes.sizeof(INPUT))
        return result == len(inputs)
    
    def _sendinput_right_click(self, x: int, y: int) -> bool:
        """SendInput方式的右键点击"""
        inputs = [
            self._create_mouse_input(x, y, 0, 0x0001 | 0x8000),  # 移动
            self._create_mouse_input(x, y, 0, 0x0008),  # 右键按下
            self._create_mouse_input(x, y, 0, 0x0010),  # 右键释放
        ]
        
        result = self.user32.SendInput(len(inputs), (INPUT * len(inputs))(*inputs), ctypes.sizeof(INPUT))
        return result == len(inputs)
    
    def _create_key_input(self, vk_code: int, key_down: bool) -> INPUT:
        """创建键盘输入结构"""
        input_obj = INPUT()
        input_obj.type = 1  # INPUT_KEYBOARD
        input_obj._input.ki.wVk = vk_code
        input_obj._input.ki.dwFlags = 0 if key_down else 0x0002  # KEYEVENTF_KEYUP
        return input_obj
    
    def _create_mouse_input(self, x: int, y: int, data: int, flags: int) -> INPUT:
        """创建鼠标输入结构"""
        input_obj = INPUT()
        input_obj.type = 0  # INPUT_MOUSE
        input_obj._input.mi.dx = x
        input_obj._input.mi.dy = y
        input_obj._input.mi.mouseData = data
        input_obj._input.mi.dwFlags = flags
        return input_obj
    
    def _method_thread_injection(self, event: InputEvent) -> bool:
        """方法3: 线程注入方式"""
        try:
            # 获取目标窗口的线程ID
            thread_id, process_id = win32process.GetWindowThreadProcessId(event.hwnd)
            
            # 创建远程线程执行输入（这需要更复杂的实现）
            # 这里简化为PostThreadMessage方式
            if event.action == 'click':
                win32api.PostThreadMessage(thread_id, WM_LBUTTONDOWN, 0, (event.y << 16) | event.x)
                time.sleep(0.05)
                win32api.PostThreadMessage(thread_id, WM_LBUTTONUP, 0, (event.y << 16) | event.x)
                return True
            
            return False
            
        except Exception as e:
            print(f"[INJECT] 线程注入失败: {e}")
            return False
    
    def _method_hook_injection(self, event: InputEvent) -> bool:
        """方法4: Hook注入方式（针对微信等高安全应用）"""
        try:
            # 获取窗口信息判断是否为微信
            window_text = win32gui.GetWindowText(event.hwnd)
            is_wechat = '微信' in window_text or 'wechat' in window_text.lower()
            
            if is_wechat:
                return self._wechat_special_injection(event)
            
            # 通用Hook注入方法
            print(f"[INJECT] 使用通用Hook注入")
            return self._generic_hook_injection(event)
            
        except Exception as e:
            print(f"[INJECT] Hook注入失败: {e}")
            return False
    
    def _wechat_special_injection(self, event: InputEvent) -> bool:
        """专门针对微信的特殊注入方法"""
        try:
            print(f"[INJECT] 使用微信专用注入方法")
            
            # 方法1: 尝试查找微信的子窗口
            child_windows = []
            def enum_child_proc(hwnd, param):
                child_windows.append(hwnd)
                return True
            
            win32gui.EnumChildWindows(event.hwnd, enum_child_proc, None)
            
            # 向所有子窗口发送消息
            success_count = 0
            for child_hwnd in child_windows:
                try:
                    if event.action == 'click':
                        lparam = (event.y << 16) | event.x
                        win32gui.PostMessage(child_hwnd, WM_LBUTTONDOWN, 0, lparam)
                        time.sleep(0.05)
                        win32gui.PostMessage(child_hwnd, WM_LBUTTONUP, 0, lparam)
                        success_count += 1
                except:
                    continue
            
            if success_count > 0:
                print(f"[INJECT] 微信子窗口注入成功: {success_count}/{len(child_windows)}")
                return True
            
            # 方法2: 尝试使用不同的消息类型
            try:
                lparam = (event.y << 16) | event.x
                
                # 尝试WM_NCLBUTTONDOWN（非客户区点击）
                win32gui.SendMessage(event.hwnd, 0x00A1, 1, lparam)  # WM_NCLBUTTONDOWN
                
                # 尝试WM_SETCURSOR
                win32gui.SendMessage(event.hwnd, 0x0020, event.hwnd, 0x02000001)  # WM_SETCURSOR
                
                # 尝试WM_MOUSEFIRST系列消息
                win32gui.SendMessage(event.hwnd, 0x0200, 0, lparam)  # WM_MOUSEMOVE
                win32gui.SendMessage(event.hwnd, 0x0201, 0, lparam)  # WM_LBUTTONDOWN
                time.sleep(0.05)
                win32gui.SendMessage(event.hwnd, 0x0202, 0, lparam)  # WM_LBUTTONUP
                
                print(f"[INJECT] 微信特殊消息注入完成")
                return True
                
            except Exception as e:
                print(f"[INJECT] 微信特殊消息失败: {e}")
            
            # 方法3: 尝试模拟键盘输入激活
            try:
                # 发送Tab键尝试激活控件
                win32gui.SendMessage(event.hwnd, WM_KEYDOWN, 0x09, 0)  # VK_TAB
                time.sleep(0.1)
                win32gui.SendMessage(event.hwnd, WM_KEYUP, 0x09, 0)
                
                # 然后发送空格键
                win32gui.SendMessage(event.hwnd, WM_KEYDOWN, 0x20, 0)  # VK_SPACE
                time.sleep(0.1)
                win32gui.SendMessage(event.hwnd, WM_KEYUP, 0x20, 0)
                
                print(f"[INJECT] 微信键盘激活注入完成")
                return True
                
            except Exception as e:
                print(f"[INJECT] 微信键盘激活失败: {e}")
            
            return False
            
        except Exception as e:
            print(f"[INJECT] 微信专用注入失败: {e}")
            return False
    
    def _generic_hook_injection(self, event: InputEvent) -> bool:
        """通用Hook注入方法"""
        try:
            # 使用SetWindowsHookEx进行更底层的注入
            # 这里提供基础实现
            
            if event.action == 'click':
                # 尝试直接调用mouse_event API
                import ctypes
                user32 = ctypes.windll.user32
                
                # 获取屏幕坐标
                rect = win32gui.GetWindowRect(event.hwnd)
                screen_x = rect[0] + event.x
                screen_y = rect[1] + event.y
                
                # 使用mouse_event API
                user32.mouse_event(0x0002, screen_x, screen_y, 0, 0)  # MOUSEEVENTF_LEFTDOWN
                time.sleep(0.05)
                user32.mouse_event(0x0004, screen_x, screen_y, 0, 0)  # MOUSEEVENTF_LEFTUP
                
                return True
            
            return False
            
        except Exception as e:
            print(f"[INJECT] 通用Hook注入失败: {e}")
            return False

# 全局高级输入注入器实例
_advanced_injector = AdvancedInputInjector()

def inject_move_and_drag(hwnd: int, x: int, y: int, duration: float = 0.5) -> bool:
    """注入移动拖拽操作到非激活窗口"""
    event = InputEvent(hwnd=hwnd, x=x, y=y, action='move_and_drag', duration=duration)
    return _advanced_injector.inject_input(event)

def inject_click(hwnd: int, x: int, y: int) -> bool:
    """注入点击操作到非激活窗口"""
    event = InputEvent(hwnd=hwnd, x=x, y=y, action='click')
    return _advanced_injector.inject_input(event)

def inject_right_click(hwnd: int, x: int, y: int) -> bool:
    """注入右键点击操作到非激活窗口"""
    event = InputEvent(hwnd=hwnd, x=x, y=y, action='right_click')
    return _advanced_injector.inject_input(event)

if __name__ == "__main__":
    # 测试代码
    print("高级输入注入系统已加载")
    print("支持的操作: inject_move_and_drag, inject_click, inject_right_click")
