"""
简洁的多窗口同时控制测试
"""

import win32con
import win32gui
import threading
import time

class WindowController:
    """窗口控制器 - 向指定窗口发送输入消息"""
    def __init__(self, hwnd):
        self.hwnd = hwnd
        self.window_title = win32gui.GetWindowText(hwnd) if win32gui.IsWindow(hwnd) else "Unknown"
        
    def click_at(self, x, y):
        """向窗口发送左键点击消息（相对坐标）"""
        lParam = (y << 16) | x
        win32gui.PostMessage(self.hwnd, win32con.WM_LBUTTONDOWN, 0, lParam)
        win32gui.PostMessage(self.hwnd, win32con.WM_LBUTTONUP, 0, lParam)
        print(f"[{self.window_title[:20]}] 左键点击: ({x}, {y})")
        
    def right_click_at(self, x, y):
        """向窗口发送右键点击消息（相对坐标）"""
        lParam = (y << 16) | x
        win32gui.PostMessage(self.hwnd, win32con.WM_RBUTTONDOWN, 0, lParam)
        win32gui.PostMessage(self.hwnd, win32con.WM_RBUTTONUP, 0, lParam)
        print(f"[{self.window_title[:20]}] 右键点击: ({x}, {y})")
        
    def move_character(self, x, y):
        """移动角色（右键点击）"""
        self.right_click_at(x, y)

def find_windows():
    """查找可用窗口"""
    windows = []
    def enum_callback(hwnd, windows):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title and len(title) > 0:
                rect = win32gui.GetWindowRect(hwnd)
                width = rect[2] - rect[0]
                height = rect[3] - rect[1]
                if width > 200 and height > 200:
                    windows.append({
                        'handle': hwnd,
                        'title': title,
                        'size': (width, height)
                    })
    win32gui.EnumWindows(enum_callback, windows)
    return windows

def control_window(controller, x, y):
    """控制单个窗口"""
    controller.move_character(x, y)

def test_multi_window_control():
    """测试多窗口同时控制"""
    print("=== 多窗口同时控制测试 ===")
    
    # 查找窗口
    windows = find_windows()
    
    if len(windows) < 3:
        print(f"只找到 {len(windows)} 个窗口，需要至少3个窗口")
        print("可用窗口:")
        for i, window in enumerate(windows):
            print(f"  {i+1}. {window['title']} - {window['size']}")
        return
    
    # 选择前3个窗口
    target_windows = windows[:3]
    print("选择的窗口:")
    for i, window in enumerate(target_windows):
        print(f"  {i+1}. {window['title']} - {window['size']}")
    
    # 创建控制器
    controllers = [WindowController(window['handle']) for window in target_windows]
    
    # 定义不同的点击位置
    positions = [(100, 100), (200, 200), (300, 300)]
    
    print("\n准备同时向3个窗口发送右键点击...")
    print("位置:", positions)
    
    # 创建线程同时执行
    threads = []
    for i, (controller, pos) in enumerate(zip(controllers, positions)):
        thread = threading.Thread(
            target=control_window, 
            args=(controller, pos[0], pos[1]),
            name=f"Window-{i+1}"
        )
        threads.append(thread)
    
    # 倒计时
    for i in range(3, 0, -1):
        print(f"倒计时: {i}")
        time.sleep(1)
    
    print("开始同时控制!")
    
    # 同时启动所有线程
    start_time = time.time()
    for thread in threads:
        thread.start()
    
    # 等待所有操作完成
    for thread in threads:
        thread.join()
    
    end_time = time.time()
    print(f"多窗口控制完成，耗时: {end_time - start_time:.3f}秒")

if __name__ == "__main__":
    test_multi_window_control()
