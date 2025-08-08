# -*- coding: utf-8 -*-
"""
v2多开智能自动化系统 - 多窗口管理器
支持同时控制多个游戏窗口，在非激活状态下进行自动化操作
"""

import sys
import os
import time
import threading
import queue
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
import win32gui
import win32con
import win32api
import win32process
import win32ui
import psutil
import cv2
import numpy as np
from PIL import Image
import mss

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# 全局输入互斥锁 - 解决多窗口鼠标键盘冲突
_global_input_lock = threading.Lock()

# 导入配置
from v2.config import TARGET_PROCESSES, GAME_WINDOW_KEYWORDS, WINDOW_SCAN_CONFIG
from hotkey_manager import global_stop_manager

@dataclass
class WindowInfo:
    """窗口信息"""
    hwnd: int                    # 窗口句柄
    title: str                   # 窗口标题
    process_id: int              # 进程ID
    process_name: str            # 进程名称
    rect: Tuple[int, int, int, int]  # 窗口位置和大小 (left, top, right, bottom)
    width: int                   # 窗口宽度
    height: int                  # 窗口高度
    is_visible: bool             # 是否可见
    is_minimized: bool           # 是否最小化
    client_rect: Tuple[int, int, int, int]  # 客户区域
    
    @property
    def size(self) -> Tuple[int, int]:
        """获取窗口尺寸"""
        return (self.width, self.height)
    
    @property
    def position(self) -> Tuple[int, int]:
        """获取窗口位置"""
        return (self.rect[0], self.rect[1])

@dataclass
class GameInstance:
    """游戏实例"""
    window_info: WindowInfo
    controller: Any              # 游戏控制器
    detector: Any                # 装备检测器
    is_running: bool = False     # 是否运行中
    last_screenshot: Optional[np.ndarray] = None  # 最后截图
    screenshot_time: float = 0   # 截图时间
    
class MultiWindowManager:
    """多窗口管理器 - v2智能版本"""
    
    def __init__(self):
        self.game_instances: Dict[int, GameInstance] = {}  # hwnd -> GameInstance
        
        # 从配置文件加载设置
        self.target_process_names = TARGET_PROCESSES
        self.game_keywords = GAME_WINDOW_KEYWORDS
        self.min_window_width = WINDOW_SCAN_CONFIG['min_window_width']
        self.min_window_height = WINDOW_SCAN_CONFIG['min_window_height']
        self.scan_interval = WINDOW_SCAN_CONFIG['scan_interval']
        
        self.is_scanning = False     # 是否正在扫描
        self.scan_thread = None      # 扫描线程
        self.management_lock = threading.Lock()  # 管理锁
        
        # 截图相关
        self.screenshot_cache = {}   # 截图缓存
        self.cache_timeout = 0.1     # 缓存超时时间（秒）
        
        # 注册全局停止回调
        global_stop_manager.register_stop_callback(self.stop_window_scanning)
        
        print(f"[MANAGER] 多窗口管理器初始化完成")
        print(f"[MANAGER] 目标进程: {len(self.target_process_names)} 个")
        print(f"[MANAGER] 关键词: {len(self.game_keywords)} 个")
        print(f"[MANAGER] 最小窗口尺寸: {self.min_window_width}x{self.min_window_height}")
        print(f"[MANAGER] 全局热键: Ctrl+Q 可随时停止所有脚本")
    
    def start_window_scanning(self):
        """启动窗口扫描"""
        if self.is_scanning:
            print(f"[MANAGER] 窗口扫描已在运行")
            return
        
        self.is_scanning = True
        self.scan_thread = threading.Thread(
            target=self._window_scan_loop,
            daemon=True,
            name="WindowScanner"
        )
        self.scan_thread.start()
        print(f"[MANAGER] 窗口扫描已启动")
    
    def stop_window_scanning(self):
        """停止窗口扫描"""
        self.is_scanning = False
        if self.scan_thread and self.scan_thread.is_alive():
            self.scan_thread.join(timeout=2.0)
        print(f"[MANAGER] 窗口扫描已停止")
    
    def _window_scan_loop(self):
        """窗口扫描循环"""
        while self.is_scanning:
            try:
                self._scan_and_update_windows()
                time.sleep(self.scan_interval)
            except Exception as e:
                print(f"[MANAGER] 窗口扫描异常: {e}")
                time.sleep(1)
    
    def _scan_and_update_windows(self):
        """扫描并更新窗口列表"""
        current_windows = self._find_game_windows()
        
        with self.management_lock:
            # 检查新窗口
            for window_info in current_windows:
                if window_info.hwnd not in self.game_instances:
                    self._add_game_instance(window_info)
            
            # 检查已关闭的窗口
            closed_hwnds = []
            for hwnd in self.game_instances.keys():
                if not self._is_window_valid(hwnd):
                    closed_hwnds.append(hwnd)
            
            for hwnd in closed_hwnds:
                self._remove_game_instance(hwnd)
    
    def _find_game_windows(self) -> List[WindowInfo]:
        """查找游戏窗口"""
        game_windows = []
        
        def enum_windows_callback(hwnd, windows):
            # 检查窗口是否有效，包括最小化的窗口
            if win32gui.IsWindow(hwnd) and (win32gui.IsWindowVisible(hwnd) or win32gui.IsIconic(hwnd)):
                try:
                    # 获取窗口信息
                    title = win32gui.GetWindowText(hwnd)
                    if not title:  # 跳过无标题窗口
                        return True
                    
                    # 获取进程信息
                    _, process_id = win32process.GetWindowThreadProcessId(hwnd)
                    try:
                        process = psutil.Process(process_id)
                        process_name = process.name()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        return True
                    
                    # 检查是否是目标游戏进程
                    if not self._is_target_process(process_name, title):
                        return True
                    
                    # 获取窗口位置和大小
                    rect = win32gui.GetWindowRect(hwnd)
                    client_rect = win32gui.GetClientRect(hwnd)
                    
                    width = rect[2] - rect[0]
                    height = rect[3] - rect[1]
                    
                    # 过滤太小的窗口
                    if width < self.min_window_width or height < self.min_window_height:
                        return True
                    
                    is_minimized = win32gui.IsIconic(hwnd)
                    
                    window_info = WindowInfo(
                        hwnd=hwnd,
                        title=title,
                        process_id=process_id,
                        process_name=process_name,
                        rect=rect,
                        width=width,
                        height=height,
                        is_visible=True,
                        is_minimized=is_minimized,
                        client_rect=client_rect
                    )
                    
                    windows.append(window_info)
                    
                except Exception as e:
                    print(f"[MANAGER] 获取窗口信息异常: {e}")
            
            return True
        
        win32gui.EnumWindows(enum_windows_callback, game_windows)
        return game_windows
    
    def _is_target_process(self, process_name: str, window_title: str) -> bool:
        """判断是否是目标游戏进程"""
        # 方法1: 通过进程名判断
        for target_name in self.target_process_names:
            if target_name.lower() in process_name.lower():
                return True
        
        # 方法2: 通过窗口标题判断（使用配置文件中的关键词）
        for keyword in self.game_keywords:
            if keyword.lower() in window_title.lower():
                return True
        
        return False
    
    def _is_window_valid(self, hwnd: int) -> bool:
        """检查窗口是否仍然有效"""
        try:
            return win32gui.IsWindow(hwnd) and win32gui.IsWindowVisible(hwnd)
        except:
            return False
    
    def _add_game_instance(self, window_info: WindowInfo):
        """添加游戏实例"""
        try:
            print(f"[MANAGER] 发现新游戏窗口: {window_info.title} ({window_info.width}x{window_info.height})")
            
            # 创建游戏实例（暂时为None，后续会创建具体的控制器）
            game_instance = GameInstance(
                window_info=window_info,
                controller=None,
                detector=None,
                is_running=False
            )
            
            self.game_instances[window_info.hwnd] = game_instance
            
            print(f"[MANAGER] 游戏实例已添加: HWND={window_info.hwnd}")
            
        except Exception as e:
            print(f"[MANAGER] 添加游戏实例失败: {e}")
    
    def _remove_game_instance(self, hwnd: int):
        """移除游戏实例"""
        try:
            if hwnd in self.game_instances:
                game_instance = self.game_instances[hwnd]
                
                # 停止游戏实例
                if game_instance.controller:
                    try:
                        game_instance.controller.stop()
                    except:
                        pass
                
                del self.game_instances[hwnd]
                print(f"[MANAGER] 游戏实例已移除: HWND={hwnd}")
                
        except Exception as e:
            print(f"[MANAGER] 移除游戏实例失败: {e}")
    
    def get_window_screenshot(self, hwnd: int, use_cache: bool = True) -> Optional[np.ndarray]:
        """获取窗口截图（非侵入式方法）"""
        try:
            # 检查缓存
            current_time = time.time()
            if use_cache and hwnd in self.screenshot_cache:
                cache_data = self.screenshot_cache[hwnd]
                if current_time - cache_data['timestamp'] < self.cache_timeout:
                    return cache_data['screenshot']
            
            # 直接使用非侵入式截图方法（假设窗口正常显示）
            screenshot = self._capture_window_non_intrusive(hwnd)
            
            if screenshot is not None:
                # 更新缓存
                if use_cache:
                    self.screenshot_cache[hwnd] = {
                        'screenshot': screenshot,
                        'timestamp': current_time
                    }
                return screenshot
            else:
                # 静默失败，不打印错误信息
                return None
                
        except Exception as e:
            # 静默处理异常
            return None
    
    def _capture_window_non_intrusive(self, hwnd: int) -> Optional[np.ndarray]:
        """非侵入式窗口截图 - 不激活窗口"""
        try:
            if not win32gui.IsWindow(hwnd):
                return None
            
            # 获取窗口尺寸
            rect = win32gui.GetWindowRect(hwnd)
            width = rect[2] - rect[0]
            height = rect[3] - rect[1]
            
            if width <= 0 or height <= 0:
                return None
            
            # 方法1: 使用GetWindowDC + PrintWindow
            image = self._try_getwindowdc_printwindow(hwnd, width, height)
            if image is not None and not self._is_blank_image(image):
                return image
            
            # 方法2: 使用BitBlt方法
            image = self._try_bitblt_method(hwnd, width, height)
            if image is not None and not self._is_blank_image(image):
                return image
            
            return None
            
        except Exception as e:
            print(f"[SCREENSHOT] 非侵入式截图异常: {e}")
            return None
    
    def _try_getwindowdc_printwindow(self, hwnd: int, width: int, height: int) -> Optional[np.ndarray]:
        """使用GetWindowDC + PrintWindow方法"""
        try:
            # 获取窗口DC
            hwndDC = win32gui.GetWindowDC(hwnd)
            if not hwndDC:
                return None
            
            try:
                # 创建内存DC
                memDC = win32gui.CreateCompatibleDC(hwndDC)
                if not memDC:
                    return None
                
                try:
                    # 创建位图
                    hBitmap = win32gui.CreateCompatibleBitmap(hwndDC, width, height)
                    if not hBitmap:
                        return None
                    
                    try:
                        # 选择位图到内存DC
                        win32gui.SelectObject(memDC, hBitmap)
                        
                        # 尝试PrintWindow
                        success = False
                        try:
                            # 方法1: 使用PrintWindow API
                            import ctypes
                            result = ctypes.windll.user32.PrintWindow(hwnd, memDC, 0x2)  # PW_CLIENTONLY
                            if result:
                                success = True
                        except:
                            pass
                        
                        if not success:
                            try:
                                # 方法2: 使用WM_PRINT消息
                                result = win32api.SendMessage(hwnd, win32con.WM_PRINT, memDC, 
                                                            win32con.PRF_CLIENT | win32con.PRF_CHILDREN | win32con.PRF_OWNED)
                                success = True
                            except:
                                pass
                        
                        if success:
                            # 获取位图数据
                            bmp_info = win32gui.GetObject(hBitmap)
                            bmp_str = win32gui.GetBitmapBits(hBitmap, bmp_info.bmWidthBytes * height)
                            
                            # 转换为numpy数组
                            img_array = np.frombuffer(bmp_str, dtype=np.uint8)
                            if bmp_info.bmBitsPixel == 32:
                                img_array = img_array.reshape((height, width, 4))
                                img_bgr = img_array[:, :, :3]  # 去掉alpha通道
                                img_bgr = cv2.flip(img_bgr, 0)  # 垂直翻转
                                return img_bgr
                            elif bmp_info.bmBitsPixel == 24:
                                img_array = img_array.reshape((height, width, 3))
                                img_bgr = cv2.flip(img_array, 0)  # 垂直翻转
                                return img_bgr
                        
                    finally:
                        win32gui.DeleteObject(hBitmap)
                finally:
                    win32gui.DeleteDC(memDC)
            finally:
                win32gui.ReleaseDC(hwnd, hwndDC)
                
        except Exception as e:
            pass
        
        return None
    
    def _try_bitblt_method(self, hwnd: int, width: int, height: int) -> Optional[np.ndarray]:
        """使用BitBlt方法截图"""
        try:
            # 获取窗口DC
            hwndDC = win32gui.GetWindowDC(hwnd)
            if not hwndDC:
                return None
            
            try:
                # 创建内存DC和位图
                memDC = win32gui.CreateCompatibleDC(hwndDC)
                hBitmap = win32gui.CreateCompatibleBitmap(hwndDC, width, height)
                win32gui.SelectObject(memDC, hBitmap)
                
                # 使用BitBlt复制窗口内容
                result = win32gui.BitBlt(memDC, 0, 0, width, height, hwndDC, 0, 0, win32con.SRCCOPY)
                if not result:
                    return None
                
                # 获取位图数据
                bmp_info = win32gui.GetObject(hBitmap)
                bmp_str = win32gui.GetBitmapBits(hBitmap, bmp_info.bmWidthBytes * height)
                
                # 转换为numpy数组
                img_array = np.frombuffer(bmp_str, dtype=np.uint8)
                if bmp_info.bmBitsPixel == 32:
                    img_array = img_array.reshape((height, width, 4))
                    img_bgr = img_array[:, :, :3]
                    img_bgr = cv2.flip(img_bgr, 0)
                    return img_bgr
                elif bmp_info.bmBitsPixel == 24:
                    img_array = img_array.reshape((height, width, 3))
                    img_bgr = cv2.flip(img_array, 0)
                    return img_bgr
                
                win32gui.DeleteObject(hBitmap)
                win32gui.DeleteDC(memDC)
                
            finally:
                win32gui.ReleaseDC(hwnd, hwndDC)
                
        except Exception as e:
            pass
        
        return None
    
    def _is_blank_image(self, image: np.ndarray, threshold: int = 10) -> bool:
        """检查图像是否为空白"""
        if image is None:
            return True
        
        std_dev = np.std(image)
        return std_dev < threshold
    
    def send_message_to_window(self, hwnd: int, msg: int, wparam: int = 0, lparam: int = 0):
        """向窗口发送消息（非激活状态）"""
        try:
            win32api.SendMessage(hwnd, msg, wparam, lparam)
        except Exception as e:
            print(f"[MESSAGE] 发送消息失败 HWND={hwnd}: {e}")
    
    def send_input_to_window_non_active(self, hwnd: int, x: int, y: int, action: str = 'click'):
        """向非激活窗口发送输入（多种方案尝试）"""
        
        # 方法1: 尝试UI自动化方案
        try:
            print(f"[INPUT] 尝试UI自动化方案...")
            success = self._try_ui_automation_input(hwnd, x, y, action)
            if success:
                return True
        except Exception as e:
            print(f"[INPUT] UI自动化方案失败: {e}")
        
        # 方法2: 尝试PostMessage方案
        try:
            print(f"[INPUT] 尝试PostMessage方案...")
            success = self._try_post_message_input(hwnd, x, y, action)
            if success:
                return True
        except Exception as e:
            print(f"[INPUT] PostMessage方案失败: {e}")
        
        # 方法3: 使用 SendInput 配合窗口消息
        try:
            print(f"[INPUT] 尝试SendInput方案...")
            import ctypes
            from ctypes import wintypes, windll
            
            # 获取窗口位置
            rect = win32gui.GetWindowRect(hwnd)
            abs_x = rect[0] + x
            abs_y = rect[1] + y
            
            # 定义 INPUT 结构
            class POINT(ctypes.Structure):
                _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
            
            class MOUSEINPUT(ctypes.Structure):
                _fields_ = [("dx", wintypes.LONG),
                           ("dy", wintypes.LONG),
                           ("mouseData", wintypes.DWORD),
                           ("dwFlags", wintypes.DWORD),
                           ("time", wintypes.DWORD),
                           ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]
            
            class INPUT(ctypes.Structure):
                class _INPUT(ctypes.Union):
                    _fields_ = [("mi", MOUSEINPUT)]
                _anonymous_ = ("_input",)
                _fields_ = [("type", wintypes.DWORD),
                           ("_input", _INPUT)]
            
            # 设置光标位置到目标窗口
            windll.user32.SetCursorPos(abs_x, abs_y)
            
            # 创建输入事件
            if action == 'click':
                # 左键按下
                input_down = INPUT()
                input_down.type = 0  # INPUT_MOUSE
                input_down.mi.dwFlags = 0x0002  # MOUSEEVENTF_LEFTDOWN
                
                # 左键释放
                input_up = INPUT()
                input_up.type = 0  # INPUT_MOUSE
                input_up.mi.dwFlags = 0x0004  # MOUSEEVENTF_LEFTUP
                
                # 发送输入事件
                windll.user32.SendInput(1, ctypes.byref(input_down), ctypes.sizeof(INPUT))
                time.sleep(0.01)
                windll.user32.SendInput(1, ctypes.byref(input_up), ctypes.sizeof(INPUT))
                
            elif action == 'right_click':
                # 右键按下
                input_down = INPUT()
                input_down.type = 0  # INPUT_MOUSE
                input_down.mi.dwFlags = 0x0008  # MOUSEEVENTF_RIGHTDOWN
                
                # 右键释放
                input_up = INPUT()
                input_up.type = 0  # INPUT_MOUSE
                input_up.mi.dwFlags = 0x0010  # MOUSEEVENTF_RIGHTUP
                
                # 发送输入事件
                windll.user32.SendInput(1, ctypes.byref(input_down), ctypes.sizeof(INPUT))
                time.sleep(0.01)
                windll.user32.SendInput(1, ctypes.byref(input_up), ctypes.sizeof(INPUT))
            
            print(f"[INPUT] 非激活窗口输入完成: HWND={hwnd}, 动作={action}, 位置=({abs_x}, {abs_y})")
            return True
                    
        except Exception as e:
            print(f"[INPUT] SendInput方案失败: {e}")
        
        # 所有方案都失败
        print(f"[INPUT] 所有非激活窗口输入方案都失败 HWND={hwnd}")
        return False
    
    def _try_ui_automation_input(self, hwnd: int, x: int, y: int, action: str) -> bool:
        """尝试使用UI自动化进行输入"""
        try:
            # 使用Windows UI Automation
            import comtypes.client
            
            # 初始化UI自动化
            uia = comtypes.client.CreateObject("UIAutomation.CUIAutomation")
            
            # 从窗口句柄获取元素
            element = uia.ElementFromHandle(hwnd)
            if not element:
                return False
            
            # 获取窗口位置
            rect = win32gui.GetWindowRect(hwnd)
            abs_x = rect[0] + x
            abs_y = rect[1] + y
            
            # 尝试在指定位置找到可点击的元素
            point = comtypes.client.CreateObject("UIAutomation.tagPOINT")
            point.x = abs_x
            point.y = abs_y
            
            target_element = uia.ElementFromPoint(point)
            if target_element:
                # 尝试调用点击模式
                if action == 'click':
                    invoke_pattern = target_element.GetCurrentPattern(10000)  # InvokePattern
                    if invoke_pattern:
                        invoke_pattern.Invoke()
                        print(f"[INPUT] UI自动化点击成功")
                        return True
            
            return False
            
        except Exception as e:
            print(f"[INPUT] UI自动化异常: {e}")
            return False
    
    def _try_post_message_input(self, hwnd: int, x: int, y: int, action: str) -> bool:
        """尝试使用PostMessage进行输入"""
        try:
            # PostMessage 与 SendMessage 的区别：
            # PostMessage 是异步的，消息放入队列后立即返回
            # 某些应用可能对PostMessage的响应更好
            
            lparam = (y << 16) | x
            
            if action == 'click':
                # 发送左键按下和释放
                result1 = win32api.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, 0, lparam)
                time.sleep(0.01)
                result2 = win32api.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lparam)
                
                if result1 and result2:
                    print(f"[INPUT] PostMessage左键点击成功")
                    return True
                    
            elif action == 'right_click':
                # 发送右键按下和释放
                result1 = win32api.PostMessage(hwnd, win32con.WM_RBUTTONDOWN, 0, lparam)
                time.sleep(0.01)
                result2 = win32api.PostMessage(hwnd, win32con.WM_RBUTTONUP, 0, lparam)
                
                if result1 and result2:
                    print(f"[INPUT] PostMessage右键点击成功")
                    return True
            
            return False
            
        except Exception as e:
            print(f"[INPUT] PostMessage异常: {e}")
            return False
    
    def send_input_to_window_direct_mouse(self, hwnd: int, x: int, y: int, action: str = 'click'):
        """直接鼠标控制方案（带全局互斥锁，防止多窗口冲突）"""
        with _global_input_lock:  # 全局输入互斥锁
            try:
                # 获取窗口位置，计算屏幕绝对坐标
                rect = win32gui.GetWindowRect(hwnd)
                abs_x = rect[0] + x
                abs_y = rect[1] + y
                
                print(f"[MOUSE] 互斥鼠标控制: HWND={hwnd}, 窗口坐标=({x},{y}), 屏幕坐标=({abs_x},{abs_y}), 动作={action}")
                
                # 使用pyautogui直接控制鼠标
                import pyautogui
                pyautogui.FAILSAFE = False  # 禁用安全模式
                
                if action == 'click':
                    pyautogui.click(abs_x, abs_y)
                    print(f"[MOUSE] 互斥左键点击完成")
                    return True
                    
                elif action == 'right_click':
                    pyautogui.rightClick(abs_x, abs_y)
                    print(f"[MOUSE] 互斥右键点击完成")
                    return True
                    
                elif action == 'drag_start':
                    pyautogui.moveTo(abs_x, abs_y)
                    pyautogui.mouseDown(button='left')
                    print(f"[MOUSE] 互斥开始拖拽")
                    return True
                    
                elif action == 'drag_end':
                    pyautogui.mouseUp(button='left')
                    print(f"[MOUSE] 互斥结束拖拽")
                    return True
                    
                elif action == 'move':
                    pyautogui.moveTo(abs_x, abs_y)
                    print(f"[MOUSE] 互斥鼠标移动完成")
                    return True
                    
            except Exception as e:
                print(f"[MOUSE] 互斥鼠标控制失败 HWND={hwnd}: {e}")
                return False
    
    def send_input_to_window(self, hwnd: int, x: int, y: int, action: str = 'click'):
        """向窗口发送输入（优先使用驱动级注入）"""
        # 方案1: 驱动级输入注入（最高优先级）
        print(f"[INPUT] 使用驱动级输入注入...")
        try:
            from v2.driver_level_injection import driver_inject_click, driver_inject_right_click, driver_inject_move_and_drag
            
            if action == 'click':
                if driver_inject_click(hwnd, x, y):
                    print(f"[INPUT] 驱动级注入点击成功")
                    return True
            elif action == 'right_click':
                if driver_inject_right_click(hwnd, x, y):
                    print(f"[INPUT] 驱动级注入右键成功")
                    return True
            elif action == 'move_and_drag':
                if driver_inject_move_and_drag(hwnd, x, y):
                    print(f"[INPUT] 驱动级注入拖拽成功")
                    return True
                    
        except Exception as e:
            print(f"[INPUT] 驱动级注入失败: {e}")
        
        # 方案2: 高级非激活输入注入
        print(f"[INPUT] 驱动级失败，尝试高级非激活注入...")
        try:
            from v2.advanced_input_injection import inject_click, inject_right_click, inject_move_and_drag
            
            if action == 'click':
                if inject_click(hwnd, x, y):
                    print(f"[INPUT] 高级注入点击成功")
                    return True
            elif action == 'right_click':
                if inject_right_click(hwnd, x, y):
                    print(f"[INPUT] 高级注入右键成功")
                    return True
            elif action == 'move_and_drag':
                if inject_move_and_drag(hwnd, x, y, 0.5):
                    print(f"[INPUT] 高级注入拖拽成功")
                    return True
                    
        except Exception as e:
            print(f"[INPUT] 高级注入失败: {e}")
        
        # 方案3: 传统非激活方案
        print(f"[INPUT] 高级注入失败，尝试传统非激活方案...")
        if self.send_input_to_window_non_active(hwnd, x, y, action):
            return True
        
        # 方案4: 直接鼠标控制（带互斥锁）
        print(f"[INPUT] 传统方案失败，尝试直接鼠标控制...")
        if self.send_input_to_window_direct_mouse(hwnd, x, y, action):
            return True
        
        # 方案5: 最后回退到激活方案
        print(f"[INPUT] 所有方案失败，回退到激活方案")
        try:
            # 激活目标窗口
            self.activate_window(hwnd)
            time.sleep(0.1)  # 等待激活
            
            # 获取窗口位置
            rect = win32gui.GetWindowRect(hwnd)
            abs_x = rect[0] + x
            abs_y = rect[1] + y
            
            # 使用pyautogui进行输入模拟
            import pyautogui
            pyautogui.FAILSAFE = False  # 禁用安全模式
            
            if action == 'click':
                pyautogui.click(abs_x, abs_y)
            elif action == 'right_click':
                pyautogui.rightClick(abs_x, abs_y)
                    
        except Exception as e:
            print(f"[INPUT] 所有输入方案都失败 HWND={hwnd}: {e}")
    
    def send_key_combination_to_window(self, hwnd: int, keys: list):
        """向窗口发送组合键"""
        try:
            # 激活窗口
            self.activate_window(hwnd)
            time.sleep(0.1)
            
            # 使用pyautogui发送组合键
            import pyautogui
            pyautogui.FAILSAFE = False
            
            if len(keys) == 1:
                pyautogui.press(keys[0])
            else:
                pyautogui.hotkey(*keys)
                
        except Exception as e:
            print(f"[KEY] 按键模拟失败 HWND={hwnd}: {e}")
    
    def click_window_position(self, hwnd: int, x: int, y: int, button: str = 'left', auto_activate: bool = True):
        """在窗口指定位置点击（支持自动激活）"""
        try:
            # 检查窗口是否需要激活
            if auto_activate and (self.is_window_minimized(hwnd) or not self.is_window_visible(hwnd)):
                if not self.activate_window(hwnd):
                    print(f"[CLICK] 窗口激活失败，无法点击: HWND={hwnd}")
                    return False
            
            # 转换为窗口相对坐标
            window_info = self.game_instances[hwnd].window_info
            
            # 计算相对于窗口客户区的坐标
            client_x = x
            client_y = y
            
            # 组合坐标参数
            lparam = win32api.MAKELONG(client_x, client_y)
            
            if button == 'left':
                # 发送鼠标左键按下和释放消息
                self.send_message_to_window(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lparam)
                time.sleep(0.01)  # 短暂延迟
                self.send_message_to_window(hwnd, win32con.WM_LBUTTONUP, 0, lparam)
            elif button == 'right':
                # 发送鼠标右键按下和释放消息
                self.send_message_to_window(hwnd, win32con.WM_RBUTTONDOWN, win32con.MK_RBUTTON, lparam)
                time.sleep(0.01)
                self.send_message_to_window(hwnd, win32con.WM_RBUTTONUP, 0, lparam)
            
            print(f"[CLICK] 窗口点击: HWND={hwnd}, 位置=({x}, {y}), 按键={button}")
            return True
            
        except Exception as e:
            print(f"[CLICK] 窗口点击失败 HWND={hwnd}: {e}")
            return False
    
    def send_key_to_window(self, hwnd: int, key_code: int):
        """向窗口发送按键（非激活状态）"""
        try:
            # 发送按键按下和释放消息
            self.send_message_to_window(hwnd, win32con.WM_KEYDOWN, key_code, 0)
            time.sleep(0.01)
            self.send_message_to_window(hwnd, win32con.WM_KEYUP, key_code, 0)
            
            print(f"[KEY] 窗口按键: HWND={hwnd}, 键码={key_code}")
            
        except Exception as e:
            print(f"[KEY] 窗口按键失败 HWND={hwnd}: {e}")
    
    def activate_window(self, hwnd: int) -> bool:
        """激活窗口（如果是最小化状态）"""
        try:
            # 检查窗口是否最小化
            if win32gui.IsIconic(hwnd):
                print(f"[ACTIVATE] 窗口已最小化，正在恢复: HWND={hwnd}")
                # 恢复窗口
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                time.sleep(0.1)  # 等待窗口恢复
            
            # 检查窗口是否可见
            if not win32gui.IsWindowVisible(hwnd):
                print(f"[ACTIVATE] 窗口不可见，正在显示: HWND={hwnd}")
                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                time.sleep(0.1)
            
            # 方法1: 直接设置前台窗口
            try:
                win32gui.SetForegroundWindow(hwnd)
                print(f"[ACTIVATE] 窗口直接激活成功: HWND={hwnd}")
                return True
            except Exception as e:
                # SetForegroundWindow失败是正常的，继续用其他方法
                pass
            
            # 方法2: 强制显示窗口（不依赖SetForegroundWindow）
            try:
                # 先置顶
                win32gui.BringWindowToTop(hwnd)
                time.sleep(0.05)
                
                # 强制显示和恢复
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                time.sleep(0.1)
                
                # 检查窗口是否成功显示
                if win32gui.IsWindowVisible(hwnd) and not win32gui.IsIconic(hwnd):
                    print(f"[ACTIVATE] 窗口显示成功: HWND={hwnd}")
                    return True
                else:
                    print(f"[ACTIVATE] 窗口显示可能失败，但继续操作: HWND={hwnd}")
                    return True
                
            except Exception as e2:
                print(f"[ACTIVATE] 窗口显示失败，但继续操作: {e2}")
                return True
                    
        except Exception as e:
            print(f"[ACTIVATE] 窗口激活失败 HWND={hwnd}: {e}")
            return False
    
    def is_window_minimized(self, hwnd: int) -> bool:
        """检查窗口是否最小化"""
        try:
            return win32gui.IsIconic(hwnd)
        except Exception:
            return False
    
    def is_window_visible(self, hwnd: int) -> bool:
        """检查窗口是否可见"""
        try:
            return win32gui.IsWindowVisible(hwnd)
        except Exception:
            return False
    
    def _quick_activate_window(self, hwnd: int) -> bool:
        """快速激活窗口（优化版本）"""
        try:
            # 检查窗口是否最小化
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                time.sleep(0.02)
            
            # 检查窗口是否可见
            if not win32gui.IsWindowVisible(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                time.sleep(0.02)
            
            # 尝试多种激活方法
            try:
                # 方法1: 直接设置前台窗口
                win32gui.SetForegroundWindow(hwnd)
                return True
            except:
                try:
                    # 方法2: 先置顶再设置前台
                    win32gui.BringWindowToTop(hwnd)
                    time.sleep(0.01)
                    win32gui.SetForegroundWindow(hwnd)
                    return True
                except:
                    try:
                        # 方法3: 使用ShowWindow激活
                        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                        win32gui.SetForegroundWindow(hwnd)
                        return True
                    except:
                        return False
                        
        except Exception as e:
            print(f"[QUICK_ACTIVATE] 快速激活失败 HWND={hwnd}: {e}")
            return False
    
    def _try_direct_click(self, hwnd: int, x: int, y: int, button: str = 'left') -> bool:
        """尝试直接发送点击消息（不激活窗口）"""
        try:
            # 组合坐标参数
            lparam = win32api.MAKELONG(x, y)
            
            if button == 'left':
                # 尝试多种消息发送方式
                try:
                    # 方法1: SendMessage
                    win32api.SendMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lparam)
                    time.sleep(0.01)
                    win32api.SendMessage(hwnd, win32con.WM_LBUTTONUP, 0, lparam)
                    return True
                except:
                    try:
                        # 方法2: PostMessage
                        win32api.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lparam)
                        time.sleep(0.01)
                        win32api.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lparam)
                        return True
                    except:
                        return False
                        
            elif button == 'right':
                try:
                    # 方法1: SendMessage
                    win32api.SendMessage(hwnd, win32con.WM_RBUTTONDOWN, win32con.MK_RBUTTON, lparam)
                    time.sleep(0.01)
                    win32api.SendMessage(hwnd, win32con.WM_RBUTTONUP, 0, lparam)
                    return True
                except:
                    try:
                        # 方法2: PostMessage
                        win32api.PostMessage(hwnd, win32con.WM_RBUTTONDOWN, win32con.MK_RBUTTON, lparam)
                        time.sleep(0.01)
                        win32api.PostMessage(hwnd, win32con.WM_RBUTTONUP, 0, lparam)
                        return True
                    except:
                        return False
            
            return False
            
        except Exception as e:
            print(f"[DIRECT_CLICK] 直接点击失败 HWND={hwnd}: {e}")
            return False
    
    def _try_direct_key(self, hwnd: int, key_code: int) -> bool:
        """尝试直接发送按键消息（不激活窗口）"""
        try:
            # 尝试多种消息发送方式
            try:
                # 方法1: SendMessage
                win32api.SendMessage(hwnd, win32con.WM_KEYDOWN, key_code, 0)
                time.sleep(0.01)
                win32api.SendMessage(hwnd, win32con.WM_KEYUP, key_code, 0)
                return True
            except:
                try:
                    # 方法2: PostMessage
                    win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, key_code, 0)
                    time.sleep(0.01)
                    win32api.PostMessage(hwnd, win32con.WM_KEYUP, key_code, 0)
                    return True
                except:
                    return False
                    
        except Exception as e:
            print(f"[DIRECT_KEY] 直接按键失败 HWND={hwnd}: {e}")
            return False
    
    def click_all_windows(self, x: int, y: int, button: str = 'left', auto_activate: bool = True) -> Dict[int, bool]:
        """快速循环激活并点击所有窗口"""
        results = {}
        
        print(f"[MULTI_CLICK] 开始多窗口循环点击: 位置=({x}, {y}), 按键={button}")
        
        # 获取所有窗口
        game_instances = self.get_all_game_instances()
        
        if not game_instances:
            print("[MULTI_CLICK] 没有检测到游戏窗口")
            return results
        
        # 记录当前前台窗口，操作完成后恢复
        try:
            current_foreground = win32gui.GetForegroundWindow()
        except:
            current_foreground = None
        
        # 快速循环激活每个窗口并执行操作
        for hwnd in game_instances.keys():
            try:
                window_title = game_instances[hwnd].window_info.title
                print(f"[MULTI_CLICK] 处理窗口: {window_title} (HWND: {hwnd})")
                
                # 方法1: 尝试直接发送消息（对某些窗口有效）
                success_direct = self._try_direct_click(hwnd, x, y, button)
                
                if success_direct:
                    print(f"[MULTI_CLICK] 直接消息成功: {window_title}")
                    results[hwnd] = True
                    continue
                
                # 方法2: 激活窗口后点击（如果直接消息失败）
                if auto_activate:
                    activation_success = self._quick_activate_window(hwnd)
                    if activation_success:
                        time.sleep(0.05)  # 短暂等待激活完成
                        click_success = self._try_direct_click(hwnd, x, y, button)
                        results[hwnd] = click_success
                        print(f"[MULTI_CLICK] 激活后点击: {window_title} - {'成功' if click_success else '失败'}")
                    else:
                        results[hwnd] = False
                        print(f"[MULTI_CLICK] 激活失败: {window_title}")
                else:
                    results[hwnd] = False
                    print(f"[MULTI_CLICK] 跳过激活: {window_title}")
                
                # 短暂延迟，避免操作过快
                time.sleep(0.02)
                
            except Exception as e:
                print(f"[MULTI_CLICK] 窗口 {hwnd} 处理异常: {e}")
                results[hwnd] = False
        
        # 恢复原来的前台窗口
        if current_foreground and win32gui.IsWindow(current_foreground):
            try:
                win32gui.SetForegroundWindow(current_foreground)
            except:
                pass
        
        # 统计结果
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        print(f"[MULTI_CLICK] 多窗口点击完成: 成功 {success_count}/{total_count} 个窗口")
        
        return results
    
    def send_key_to_all_windows(self, key_code: int) -> Dict[int, bool]:
        """快速循环激活并发送按键到所有窗口"""
        results = {}
        
        print(f"[MULTI_KEY] 开始多窗口循环按键: 键码={key_code}")
        
        # 获取所有窗口
        game_instances = self.get_all_game_instances()
        
        if not game_instances:
            print("[MULTI_KEY] 没有检测到游戏窗口")
            return results
        
        # 记录当前前台窗口，操作完成后恢复
        try:
            current_foreground = win32gui.GetForegroundWindow()
        except:
            current_foreground = None
        
        # 快速循环激活每个窗口并执行按键
        for hwnd in game_instances.keys():
            try:
                window_title = game_instances[hwnd].window_info.title
                print(f"[MULTI_KEY] 处理窗口: {window_title} (HWND: {hwnd})")
                
                # 方法1: 尝试直接发送按键消息（对某些窗口有效）
                success_direct = self._try_direct_key(hwnd, key_code)
                
                if success_direct:
                    print(f"[MULTI_KEY] 直接消息成功: {window_title}")
                    results[hwnd] = True
                    continue
                
                # 方法2: 激活窗口后发送按键（如果直接消息失败）
                activation_success = self._quick_activate_window(hwnd)
                if activation_success:
                    time.sleep(0.05)  # 短暂等待激活完成
                    key_success = self._try_direct_key(hwnd, key_code)
                    results[hwnd] = key_success
                    print(f"[MULTI_KEY] 激活后按键: {window_title} - {'成功' if key_success else '失败'}")
                else:
                    results[hwnd] = False
                    print(f"[MULTI_KEY] 激活失败: {window_title}")
                
                # 短暂延迟，避免操作过快
                time.sleep(0.02)
                
            except Exception as e:
                print(f"[MULTI_KEY] 窗口 {hwnd} 处理异常: {e}")
                results[hwnd] = False
        
        # 恢复原来的前台窗口
        if current_foreground and win32gui.IsWindow(current_foreground):
            try:
                win32gui.SetForegroundWindow(current_foreground)
            except:
                pass
        
        # 统计结果
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        print(f"[MULTI_KEY] 多窗口按键完成: 成功 {success_count}/{total_count} 个窗口")
        
        return results
    
    def activate_all_windows(self) -> Dict[int, bool]:
        """激活所有窗口"""
        results = {}
        
        print("[MULTI_ACTIVATE] 开始激活所有窗口")
        
        # 获取所有窗口
        game_instances = self.get_all_game_instances()
        
        if not game_instances:
            print("[MULTI_ACTIVATE] 没有检测到游戏窗口")
            return results
        
        # 逐个激活窗口（避免并发激活导致冲突）
        for hwnd in game_instances.keys():
            try:
                success = self.activate_window(hwnd)
                results[hwnd] = success
                if success:
                    time.sleep(0.2)  # 给每个窗口一些激活时间
            except Exception as e:
                print(f"[MULTI_ACTIVATE] 窗口 {hwnd} 激活异常: {e}")
                results[hwnd] = False
        
        # 统计结果
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        print(f"[MULTI_ACTIVATE] 窗口激活完成: 成功 {success_count}/{total_count} 个窗口")
        
        return results
    
    def get_all_game_instances(self) -> Dict[int, GameInstance]:
        """获取所有游戏实例"""
        with self.management_lock:
            return self.game_instances.copy()
    
    def get_game_instance(self, hwnd: int) -> Optional[GameInstance]:
        """获取指定游戏实例"""
        return self.game_instances.get(hwnd)
    
    def get_window_count(self) -> int:
        """获取窗口数量"""
        return len(self.game_instances)
    
    def scan_game_windows(self) -> List[WindowInfo]:
        """扫描游戏窗口 - 公共接口方法"""
        print("[MANAGER] 开始扫描游戏窗口...")
        
        # 使用内部方法查找游戏窗口
        windows = self._find_game_windows()
        
        if windows:
            print(f"[MANAGER] 找到 {len(windows)} 个游戏窗口:")
            for i, window in enumerate(windows, 1):
                print(f"  {i}. {window.title} - {window.process_name}")
                print(f"     HWND: {window.hwnd}, 尺寸: {window.width}x{window.height}")
        else:
            print("[MANAGER] 未找到符合条件的游戏窗口")
            print(f"[MANAGER] 目标进程: {self.target_process_names}")
            print(f"[MANAGER] 关键词: {self.game_keywords}")
        
        return windows
    
    def print_status(self):
        """打印管理器状态"""
        print(f"\n{'='*60}")
        print(f"多窗口管理器状态")
        print(f"{'='*60}")
        print(f"扫描状态: {'运行中' if self.is_scanning else '已停止'}")
        print(f"管理窗口数: {len(self.game_instances)}")
        
        if self.game_instances:
            print(f"\n窗口列表:")
            for i, (hwnd, instance) in enumerate(self.game_instances.items(), 1):
                window_info = instance.window_info
                status = "运行中" if instance.is_running else "待机"
                minimized_status = " (最小化)" if window_info.is_minimized else ""
                print(f"  {i}. {window_info.title}{minimized_status}")
                print(f"     HWND: {hwnd}")
                print(f"     进程: {window_info.process_name} (PID: {window_info.process_id})")
                print(f"     尺寸: {window_info.width}x{window_info.height}")
                print(f"     状态: {status}")
                print()
        else:
            print("  暂无游戏窗口")
        
        print(f"{'='*60}")
    
    def test_functionality(self):
        """测试多窗口管理器功能"""
        print("\n=== 多窗口管理器功能测试 ===")
        
        # 获取所有游戏实例
        game_instances = self.get_all_game_instances()
        
        if not game_instances:
            print("[警告] 未检测到目标窗口")
            print("请确保目标应用已启动或检查配置文件")
            return False
        
        print(f"[信息] 检测到 {len(game_instances)} 个目标窗口")
        
        # 测试激活功能
        print("\n--- 测试窗口激活功能 ---")
        activation_results = self.activate_all_windows()
        
        success_count = 0
        for hwnd, success in activation_results.items():
            window_title = game_instances[hwnd].window_info.title
            status = "成功" if success else "失败"
            print(f"窗口 '{window_title}' 激活: {status}")
            if success:
                success_count += 1
        
        print(f"激活结果: {success_count}/{len(activation_results)} 个窗口激活成功")
        
        # 测试点击功能
        if success_count > 0:
            print("\n--- 测试多窗口同步点击功能 ---")
            print("在所有窗口中心位置进行测试点击...")
            
            click_results = self.click_all_windows(200, 200, 'left', auto_activate=True)
            
            click_success_count = 0
            for hwnd, success in click_results.items():
                window_title = game_instances[hwnd].window_info.title
                status = "成功" if success else "失败"
                print(f"窗口 '{window_title}' 点击: {status}")
                if success:
                    click_success_count += 1
            
            print(f"点击结果: {click_success_count}/{len(click_results)} 个窗口点击成功")
            
            # 测试按键功能
            print("\n--- 测试多窗口同步按键功能 ---")
            print("向所有窗口发送空格键...")
            
            key_results = self.send_key_to_all_windows(0x20)  # 空格键
            
            key_success_count = 0
            for hwnd, success in key_results.items():
                window_title = game_instances[hwnd].window_info.title
                status = "成功" if success else "失败"
                print(f"窗口 '{window_title}' 按键: {status}")
                if success:
                    key_success_count += 1
            
            print(f"按键结果: {key_success_count}/{len(key_results)} 个窗口按键成功")
        
        # 测试总结
        print(f"\n--- 功能测试总结 ---")
        if success_count == len(game_instances):
            print("[成功] 多窗口管理器功能完全正常")
            return True
        else:
            print("[警告] 部分功能可能存在问题")
            return False

def main():
    """主函数"""
    print("v2多窗口管理器")
    print("=" * 50)
    
    # 启动全局热键监听
    global_stop_manager.start()
    
    manager = MultiWindowManager()
    
    try:
        # 启动窗口扫描
        manager.start_window_scanning()
        
        print("正在扫描目标窗口...")
        time.sleep(3)
        
        # 显示状态
        manager.print_status()
        
        # 询问用户是否进行功能测试
        instances = manager.get_all_game_instances()
        if instances:
            print("\n检测到目标窗口，是否进行功能测试？")
            print("1. 进行完整功能测试（激活、点击、按键）")
            print("2. 仅显示状态，进入监控模式")
            print("3. 退出程序")
            
            choice = input("请选择 (1/2/3): ").strip()
            
            if choice == "1":
                # 进行功能测试
                manager.test_functionality()
                
                # 测试截图功能
                hwnd = list(instances.keys())[0]
                print(f"\n--- 测试窗口截图功能 ---")
                print(f"测试窗口: HWND={hwnd}")
                
                screenshot = manager.get_window_screenshot(hwnd)
                if screenshot is not None:
                    print(f"截图成功: {screenshot.shape}")
                    # 保存测试截图
                    cv2.imwrite(f"test_screenshot_{hwnd}.jpg", screenshot)
                    print(f"截图已保存: test_screenshot_{hwnd}.jpg")
                else:
                    print("截图失败")
                
                print("\n[完成] 功能测试结束")
                
            elif choice == "2":
                # 进入监控模式
                print("\n进入监控模式...")
                print("按 Ctrl+C 停止监控")
                
                while True:
                    time.sleep(10)
                    manager.print_status()
                    
            else:
                print("退出程序")
                
        else:
            print("\n未检测到目标窗口")
            print("请确保目标应用已启动，或检查配置文件中的进程名和关键词设置")
            
    except KeyboardInterrupt:
        print("\n\n程序已停止")
    except Exception as e:
        print(f"\n程序异常: {e}")
        import traceback
        traceback.print_exc()
    finally:
        manager.stop_window_scanning()

if __name__ == "__main__":
    main()
