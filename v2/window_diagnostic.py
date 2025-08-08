# -*- coding: utf-8 -*-
"""
窗口诊断工具
帮助诊断为什么v2系统扫描不到目标窗口
"""

import win32gui
import win32process
import psutil
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from v2.config import TARGET_PROCESSES, GAME_WINDOW_KEYWORDS, WINDOW_SCAN_CONFIG

class WindowDiagnostic:
    """窗口诊断器"""
    
    def __init__(self):
        self.all_windows = []
        self.target_processes = TARGET_PROCESSES
        self.game_keywords = GAME_WINDOW_KEYWORDS
        self.min_width = WINDOW_SCAN_CONFIG['min_window_width']
        self.min_height = WINDOW_SCAN_CONFIG['min_window_height']
    
    def scan_all_windows(self):
        """扫描所有窗口"""
        print("正在扫描所有可见窗口...")
        
        def enum_callback(hwnd, windows_list):
            if win32gui.IsWindow(hwnd) and win32gui.IsWindowVisible(hwnd):
                try:
                    title = win32gui.GetWindowText(hwnd)
                    if not title:
                        return True
                    
                    # 获取进程信息
                    _, process_id = win32process.GetWindowThreadProcessId(hwnd)
                    try:
                        process = psutil.Process(process_id)
                        process_name = process.name()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        process_name = "Unknown"
                    
                    # 获取窗口尺寸
                    rect = win32gui.GetWindowRect(hwnd)
                    width = rect[2] - rect[0]
                    height = rect[3] - rect[1]
                    
                    is_minimized = win32gui.IsIconic(hwnd)
                    
                    window_info = {
                        'hwnd': hwnd,
                        'title': title,
                        'process_name': process_name,
                        'process_id': process_id,
                        'width': width,
                        'height': height,
                        'is_minimized': is_minimized,
                        'rect': rect
                    }
                    
                    windows_list.append(window_info)
                    
                except Exception as e:
                    pass
            
            return True
        
        win32gui.EnumWindows(enum_callback, self.all_windows)
        print(f"扫描完成，找到 {len(self.all_windows)} 个可见窗口")
    
    def analyze_windows(self):
        """分析窗口匹配情况"""
        print(f"\n{'='*80}")
        print(f"窗口匹配分析")
        print(f"{'='*80}")
        
        print(f"配置的目标进程: {self.target_processes}")
        print(f"配置的关键词: {self.game_keywords}")
        print(f"最小窗口尺寸: {self.min_width}x{self.min_height}")
        
        # 查找匹配的窗口
        matching_windows = []
        potential_windows = []
        
        for window in self.all_windows:
            match_reasons = []
            
            # 检查进程名匹配
            process_match = False
            for target_process in self.target_processes:
                if target_process.lower() in window['process_name'].lower():
                    process_match = True
                    match_reasons.append(f"进程名匹配: {target_process}")
                    break
            
            # 检查窗口标题匹配
            title_match = False
            for keyword in self.game_keywords:
                if keyword.lower() in window['title'].lower():
                    title_match = True
                    match_reasons.append(f"标题匹配: {keyword}")
                    break
            
            # 检查窗口尺寸
            size_ok = window['width'] >= self.min_width and window['height'] >= self.min_height
            if not size_ok:
                match_reasons.append(f"尺寸不符: {window['width']}x{window['height']} < {self.min_width}x{self.min_height}")
            
            # 检查是否最小化
            if window['is_minimized']:
                match_reasons.append("窗口已最小化")
            
            # 判断匹配情况
            if (process_match or title_match) and size_ok and not window['is_minimized']:
                window['match_reasons'] = match_reasons
                matching_windows.append(window)
            elif process_match or title_match:
                window['match_reasons'] = match_reasons
                potential_windows.append(window)
        
        # 显示结果
        print(f"\n完全匹配的窗口: {len(matching_windows)} 个")
        for i, window in enumerate(matching_windows, 1):
            print(f"  {i}. {window['title']}")
            print(f"     进程: {window['process_name']} (PID: {window['process_id']})")
            print(f"     尺寸: {window['width']}x{window['height']}")
            print(f"     匹配原因: {', '.join(window['match_reasons'])}")
            print()
        
        print(f"潜在匹配的窗口: {len(potential_windows)} 个")
        for i, window in enumerate(potential_windows, 1):
            print(f"  {i}. {window['title']}")
            print(f"     进程: {window['process_name']} (PID: {window['process_id']})")
            print(f"     尺寸: {window['width']}x{window['height']}")
            print(f"     问题: {', '.join(window['match_reasons'])}")
            print()
        
        return matching_windows, potential_windows
    
    def show_all_windows(self):
        """显示所有窗口（用于调试）"""
        print(f"\n所有可见窗口列表:")
        print(f"{'序号':<4} {'窗口标题':<40} {'进程名':<20} {'尺寸':<12} {'状态'}")
        print(f"{'-'*4} {'-'*40} {'-'*20} {'-'*12} {'-'*10}")
        
        for i, window in enumerate(self.all_windows, 1):
            title = window['title'][:38] + '..' if len(window['title']) > 40 else window['title']
            process = window['process_name'][:18] + '..' if len(window['process_name']) > 20 else window['process_name']
            size = f"{window['width']}x{window['height']}"
            status = "最小化" if window['is_minimized'] else "正常"
            
            print(f"{i:<4} {title:<40} {process:<20} {size:<12} {status}")
    
    def find_target_processes(self):
        """查找目标进程"""
        print(f"\n查找目标进程:")
        
        found_processes = set()
        for window in self.all_windows:
            found_processes.add(window['process_name'])
        
        print(f"当前运行的所有进程:")
        sorted_processes = sorted(found_processes)
        for i, process in enumerate(sorted_processes, 1):
            is_target = any(target.lower() in process.lower() for target in self.target_processes)
            marker = "[目标]" if is_target else "      "
            print(f"{marker} {i:<3} {process}")
        
        # 检查是否有微信相关进程
        weixin_processes = [p for p in sorted_processes if 'weixin' in p.lower() or 'wechat' in p.lower()]
        if weixin_processes:
            print(f"\n发现微信相关进程:")
            for process in weixin_processes:
                print(f"  - {process}")
        
        # 检查是否有钉钉相关进程
        dingtalk_processes = [p for p in sorted_processes if 'dingtalk' in p.lower() or '钉钉' in p.lower()]
        if dingtalk_processes:
            print(f"\n发现钉钉相关进程:")
            for process in dingtalk_processes:
                print(f"  - {process}")
    
    def suggest_fixes(self, matching_windows, potential_windows):
        """建议修复方案"""
        print(f"\n诊断建议:")
        
        if matching_windows:
            print(f"找到 {len(matching_windows)} 个匹配窗口，系统应该能正常工作")
        elif potential_windows:
            print(f"找到 {len(potential_windows)} 个潜在匹配窗口，但有问题需要解决:")
            
            for window in potential_windows:
                print(f"\n窗口: {window['title']}")
                for reason in window['match_reasons']:
                    if "尺寸不符" in reason:
                        print(f"  建议: 调整最小窗口尺寸配置")
                        print(f"     当前配置: {self.min_width}x{self.min_height}")
                        print(f"     窗口尺寸: {window['width']}x{window['height']}")
                        print(f"     修改 config.py 中的 min_window_width 和 min_window_height")
                    
                    if "窗口已最小化" in reason:
                        print(f"  建议: 请将窗口恢复到正常状态（不要最小化）")
        else:
            print(f"未找到任何匹配窗口，可能的原因:")
            print(f"  1. 目标程序未运行")
            print(f"  2. 进程名配置不正确")
            print(f"  3. 窗口标题关键词配置不正确")
            
            # 提供具体建议
            print(f"\n建议的修复方案:")
            print(f"  1. 确保微信已经启动")
            print(f"  2. 检查微信的实际进程名（可能不是 Weixin.exe）")
            print(f"  3. 检查微信窗口的实际标题")
            
            # 查找可能的微信进程
            possible_weixin = []
            for window in self.all_windows:
                if any(keyword in window['title'].lower() for keyword in ['微信', 'wechat', 'weixin']):
                    possible_weixin.append(window)
                elif any(keyword in window['process_name'].lower() for keyword in ['weixin', 'wechat']):
                    possible_weixin.append(window)
            
            if possible_weixin:
                print(f"\n发现可能的微信窗口:")
                for window in possible_weixin:
                    print(f"  - 标题: {window['title']}")
                    print(f"    进程: {window['process_name']}")
                    print(f"    尺寸: {window['width']}x{window['height']}")
                    print(f"    建议添加到配置:")
                    print(f"      TARGET_PROCESSES: '{window['process_name']}'")
                    print(f"      GAME_WINDOW_KEYWORDS: '微信' 或窗口标题中的关键词")
                    print()

def main():
    """主函数"""
    print("v2系统窗口诊断工具")
    print("帮助诊断为什么扫描不到目标窗口")
    print("="*60)
    
    diagnostic = WindowDiagnostic()
    
    # 扫描所有窗口
    diagnostic.scan_all_windows()
    
    # 查找目标进程
    diagnostic.find_target_processes()
    
    # 分析匹配情况
    matching, potential = diagnostic.analyze_windows()
    
    # 显示所有窗口（调试用）
    show_all = input("\n是否显示所有窗口列表？(y/N): ").strip().lower()
    if show_all == 'y':
        diagnostic.show_all_windows()
    
    # 提供修复建议
    diagnostic.suggest_fixes(matching, potential)
    
    print("\n" + "="*60)
    print("诊断完成！请根据上述建议调整配置。")

if __name__ == "__main__":
    main()
