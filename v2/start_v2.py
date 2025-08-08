# -*- coding: utf-8 -*-
"""
v2多开智能游戏系统启动脚本
简化的启动入口，自动检查环境和依赖
"""

import sys
import os
import time
from pathlib import Path

def check_dependencies():
    """检查依赖库"""
    required_packages = [
        'cv2', 'numpy', 'PIL', 'mss', 'psutil', 'win32gui', 'win32api', 'win32con'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'cv2':
                import cv2
            elif package == 'PIL':
                from PIL import Image
            elif package == 'win32gui':
                import win32gui
            elif package == 'win32api':
                import win32api
            elif package == 'win32con':
                import win32con
            else:
                __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    return missing_packages

def check_templates():
    """检查装备模板"""
    template_dir = Path(__file__).parent.parent / "templates"
    
    if not template_dir.exists():
        return False, f"模板目录不存在: {template_dir}"
    
    template_files = list(template_dir.glob("*.jpg")) + list(template_dir.glob("*.png")) + list(template_dir.glob("*.bmp"))
    
    if not template_files:
        return False, f"模板目录为空: {template_dir}"
    
    return True, f"找到 {len(template_files)} 个装备模板"

def print_banner():
    """打印启动横幅"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                🚀 v2多开智能游戏自动化系统                    ║
    ║                                                              ║
    ║  ✅ 多窗口同时控制     ✅ 非激活窗口操作                      ║
    ║  ✅ 自适应分辨率       ✅ 智能装备检测                        ║
    ║  ✅ 独立窗口管理       ✅ 线程安全设计                        ║
    ║                                                              ║
    ║  版本: v2.0.0         作者: DnqTech Team            ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def main():
    """主启动函数"""
    print_banner()
    
    print("正在进行系统检查...")
    
    # 检查Python版本
    if sys.version_info < (3, 7):
        print("Python版本过低，需要Python 3.7+")
        print(f"   当前版本: {sys.version}")
        return False
    else:
        print(f"Python版本检查通过: {sys.version_info.major}.{sys.version_info.minor}")
    
    # 检查操作系统
    if os.name != 'nt':
        print("系统仅支持Windows操作系统")
        return False
    else:
        print("操作系统检查通过: Windows")
    
    # 检查依赖库
    missing_deps = check_dependencies()
    if missing_deps:
        print("缺少必要的依赖库:")
        for dep in missing_deps:
            print(f"   - {dep}")
        print("\n请安装缺少的依赖:")
        print("   pip install opencv-python numpy pillow mss psutil pywin32")
        return False
    else:
        print("依赖库检查通过")
    
    # 检查装备模板
    template_ok, template_msg = check_templates()
    if template_ok:
        print(f"装备模板检查通过: {template_msg}")
    else:
        print(f"装备模板警告: {template_msg}")
        print("   系统仍可运行，但装备检测功能将受限")
    
    print("\n系统检查完成，准备启动...")
    time.sleep(2)
    
    # 导入并启动主系统
    try:
        # 添加项目根目录到路径
        project_root = Path(__file__).parent.parent
        sys.path.append(str(project_root))
        
        from multi_window_manager import MultiWindowManager
        from v2.intelligent_game_controller import IntelligentGameController
        from v2.hotkey_manager import global_stop_manager
        
        # 启动全局停止管理器（包含热键和信号处理）
        print("正在启动全局停止管理器...")
        global_stop_manager.start()
        
        # 创建窗口管理器
        print("正在初始化多窗口管理器...")
        window_manager = MultiWindowManager()
        
        # 启动窗口扫描
        print("正在扫描游戏窗口...")
        window_manager.start_window_scanning()
        time.sleep(3)
        
        # 显示发现的窗口
        game_instances = window_manager.get_all_game_instances()
        if not game_instances:
            print("❌ 未发现游戏窗口，请确保游戏已启动")
            return False
        
        print(f"✅ 发现 {len(game_instances)} 个游戏窗口:")
        for i, (hwnd, instance) in enumerate(game_instances.items(), 1):
            print(f"   {i}. {instance.window_info.title} (HWND: {hwnd})")
        
        # 创建智能控制器
        controllers = []
        for hwnd, instance in game_instances.items():
            controller = IntelligentGameController(hwnd, window_manager)
            controllers.append(controller)
        
        # 启动所有控制器
        print(f"\n正在启动 {len(controllers)} 个智能控制器...")
        for i, controller in enumerate(controllers, 1):
            hwnd = controller.hwnd
            window_title = game_instances[hwnd].window_info.title
            print(f"   启动控制器 {i}: HWND={hwnd}, 窗口='{window_title}'")
            controller.start()
            
            # 检查控制器状态
            time.sleep(0.5)  # 等待启动
            status = controller.get_status()
            print(f"   控制器 {i} 状态: 运行={status['is_running']}, 战斗={status['is_fighting']}")
        
        print("\n🚀 v2智能游戏自动化系统已启动!")
        print("   - 按 Ctrl+Q 或 Ctrl+C 可随时退出")
        print("   - 系统将自动进行移动、攻击、拾取装备")
        
        # 注册控制器停止回调
        def stop_all_controllers():
            print("正在停止所有控制器...")
            for controller in controllers:
                try:
                    controller.stop()
                except Exception as e:
                    print(f"停止控制器异常: {e}")
        
        global_stop_manager.register_stop_callback(stop_all_controllers)
        
        # 保持运行直到用户停止
        try:
            while not global_stop_manager.should_stop():
                time.sleep(0.5)  # 更频繁检查停止状态
                
                # 检查控制器状态
                active_controllers = sum(1 for c in controllers if c.is_running)
                if active_controllers == 0:
                    print("所有控制器已停止运行")
                    break
                    
        except KeyboardInterrupt:
            print("\n检测到 Ctrl+C，正在停止...")
            global_stop_manager._handle_stop_request()
        
        # 停止所有控制器
        print("\n正在停止所有控制器...")
        for controller in controllers:
            controller.stop()
        
        print("✅ 系统已安全退出")
        return True
        
    except ImportError as e:
        print(f"导入模块失败: {e}")
        print("   请确保所有文件都在正确位置")
        return False
    except Exception as e:
        print(f"系统启动失败: {e}")
        return False

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            print("\n系统启动失败，请检查上述错误信息")
            input("按回车键退出...")
    except KeyboardInterrupt:
        print("\n用户取消启动")
    except Exception as e:
        print(f"\n启动脚本异常: {e}")
        input("按回车键退出...")
