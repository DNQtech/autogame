#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全局热键管理器
支持Ctrl+Q等热键组合来控制脚本运行
"""

import sys
import time
import threading
import signal
from typing import Callable, Dict, Any
import win32api
import win32con
import win32gui

class HotkeyManager:
    """全局热键管理器"""
    
    def __init__(self):
        self.is_running = False
        self.hotkey_thread = None
        self.callbacks: Dict[str, Callable] = {}
        self.stop_event = threading.Event()
        
        # 热键状态跟踪
        self.key_states = {}
        
        print("[HOTKEY] 热键管理器初始化完成")
    
    def register_hotkey(self, key_combination: str, callback: Callable):
        """注册热键回调"""
        self.callbacks[key_combination] = callback
        print(f"[HOTKEY] 注册热键: {key_combination}")
    
    def start_monitoring(self):
        """开始监听热键"""
        if self.is_running:
            print("[HOTKEY] 热键监听已在运行")
            return
        
        self.is_running = True
        self.stop_event.clear()
        self.hotkey_thread = threading.Thread(
            target=self._hotkey_loop,
            daemon=True,
            name="HotkeyMonitor"
        )
        self.hotkey_thread.start()
        print("[HOTKEY] 热键监听已启动")
    
    def stop_monitoring(self):
        """停止监听热键"""
        if not self.is_running:
            return
        
        self.is_running = False
        self.stop_event.set()
        
        if self.hotkey_thread and self.hotkey_thread.is_alive():
            self.hotkey_thread.join(timeout=2.0)
        
        print("[HOTKEY] 热键监听已停止")
    
    def _hotkey_loop(self):
        """热键监听循环"""
        print("[HOTKEY] 开始监听热键...")
        
        while self.is_running and not self.stop_event.is_set():
            try:
                # 检查Ctrl+Q组合键
                if self._is_key_pressed(win32con.VK_CONTROL) and self._is_key_pressed(ord('Q')):
                    if 'ctrl+q' in self.callbacks:
                        print("[HOTKEY] 检测到 Ctrl+Q 组合键")
                        self.callbacks['ctrl+q']()
                        # 等待按键释放，避免重复触发
                        self._wait_key_release([win32con.VK_CONTROL, ord('Q')])
                
                # 检查其他热键组合
                if self._is_key_pressed(win32con.VK_CONTROL) and self._is_key_pressed(ord('S')):
                    if 'ctrl+s' in self.callbacks:
                        print("[HOTKEY] 检测到 Ctrl+S 组合键")
                        self.callbacks['ctrl+s']()
                        self._wait_key_release([win32con.VK_CONTROL, ord('S')])
                
                time.sleep(0.1)  # 减少CPU占用
                
            except Exception as e:
                print(f"[HOTKEY] 热键监听异常: {e}")
                time.sleep(1)
        
        print("[HOTKEY] 热键监听循环结束")
    
    def _is_key_pressed(self, key_code: int) -> bool:
        """检查按键是否被按下"""
        try:
            state = win32api.GetAsyncKeyState(key_code)
            return (state & 0x8000) != 0
        except:
            return False
    
    def _wait_key_release(self, key_codes: list, timeout: float = 2.0):
        """等待按键释放"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            all_released = True
            for key_code in key_codes:
                if self._is_key_pressed(key_code):
                    all_released = False
                    break
            
            if all_released:
                break
            
            time.sleep(0.05)

class GlobalStopManager:
    """全局停止管理器"""
    
    def __init__(self):
        self.stop_requested = False
        self.stop_callbacks = []
        self.hotkey_manager = HotkeyManager()
        
        # 注册Ctrl+Q热键
        self.hotkey_manager.register_hotkey('ctrl+q', self._handle_stop_request)
        
        # 注册信号处理器作为备用停止机制
        try:
            signal.signal(signal.SIGINT, self._signal_handler)  # Ctrl+C
            signal.signal(signal.SIGTERM, self._signal_handler)  # 终止信号
        except Exception as e:
            print(f"[STOP_MANAGER] 信号处理器注册失败: {e}")
        
        print("[STOP_MANAGER] 全局停止管理器初始化完成")
        print("[STOP_MANAGER] 使用 Ctrl+Q 或 Ctrl+C 可随时停止所有脚本")
    
    def start(self):
        """启动全局停止监听"""
        self.hotkey_manager.start_monitoring()
    
    def stop(self):
        """停止全局停止监听"""
        self.hotkey_manager.stop_monitoring()
    
    def register_stop_callback(self, callback: Callable):
        """注册停止回调函数"""
        self.stop_callbacks.append(callback)
        print(f"[STOP_MANAGER] 注册停止回调: {callback.__name__}")
    
    def _handle_stop_request(self):
        """处理停止请求"""
        if self.stop_requested:
            return  # 避免重复处理
        
        self.stop_requested = True
        print("\n" + "="*50)
        print("检测到 Ctrl+Q 停止信号")
        print("正在安全停止所有脚本...")
        print("="*50)
        
        # 调用所有注册的停止回调
        for callback in self.stop_callbacks:
            try:
                callback()
            except Exception as e:
                print(f"[STOP_MANAGER] 停止回调异常: {e}")
        
        print("所有脚本已安全停止")
        print("程序将在2秒后退出...")
        
        # 立即强制退出，确保程序能够停止
        def delayed_exit():
            time.sleep(2)
            print("强制退出程序...")
            import os
            try:
                # 尝试正常退出
                sys.exit(0)
            except:
                # 强制退出
                os._exit(0)
        
        exit_thread = threading.Thread(target=delayed_exit, daemon=True)
        exit_thread.start()
    
    def is_stop_requested(self) -> bool:
        """检查是否请求停止"""
        return self.stop_requested
    
    def should_stop(self) -> bool:
        """检查是否应该停止（别名方法）"""
        return self.stop_requested
    
    def _signal_handler(self, signum, frame):
        """信号处理器（处理 Ctrl+C 等信号）"""
        print(f"\n[STOP_MANAGER] 接收到信号 {signum}")
        if signum == signal.SIGINT:
            print("[STOP_MANAGER] 检测到 Ctrl+C 信号")
        elif signum == signal.SIGTERM:
            print("[STOP_MANAGER] 检测到终止信号")
        
        # 调用停止处理
        self._handle_stop_request()

# 全局实例
global_stop_manager = GlobalStopManager()

def main():
    """测试主函数"""
    print("全局热键管理器测试")
    print("按 Ctrl+Q 测试停止功能")
    
    def test_callback():
        print("测试回调被触发！")
    
    global_stop_manager.register_stop_callback(test_callback)
    global_stop_manager.start()
    
    try:
        while not global_stop_manager.is_stop_requested():
            time.sleep(1)
            print("脚本运行中... (按 Ctrl+Q 停止)")
    except KeyboardInterrupt:
        print("用户中断")
    finally:
        global_stop_manager.stop()

if __name__ == "__main__":
    main()
