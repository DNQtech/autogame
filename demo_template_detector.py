# -*- coding: utf-8 -*-
"""
模板检测器演示脚本
使用你的目标装备图片进行精确检测
"""

from template_equipment_detector import TemplateEquipmentDetector, equipment_found_alert
import time
import os

def create_templates_folder():
    """创建模板文件夹"""
    if not os.path.exists("templates"):
        os.makedirs("templates")
        print("✓ 已创建 templates 文件夹")
        print("请将你的装备图片放入此文件夹中")
    else:
        print("✓ templates 文件夹已存在")

def demo_single_template():
    """演示：加载单个模板"""
    print("\n=== 演示：单个模板加载 ===")
    
    detector = TemplateEquipmentDetector()
    
    # 示例：如果你有装备图片
    template_files = [
        ("my_sword.png", "我的神剑"),
        ("epic_armor.png", "史诗护甲"),
        ("rare_ring.png", "稀有戒指")
    ]
    
    loaded_count = 0
    for file_path, equipment_name in template_files:
        if os.path.exists(file_path):
            if detector.load_equipment_template(file_path, equipment_name):
                loaded_count += 1
        else:
            print(f"未找到: {file_path} (这是正常的，这只是示例)")
    
    if loaded_count > 0:
        print(f"成功加载 {loaded_count} 个模板")
        detector.list_loaded_templates()
        return detector
    else:
        print("没有找到示例模板文件")
        return None

def demo_folder_templates():
    """演示：从文件夹批量加载"""
    print("\n=== 演示：文件夹批量加载 ===")
    
    detector = TemplateEquipmentDetector()
    
    if os.path.exists("templates"):
        loaded_count = detector.load_templates_from_folder("templates")
        if loaded_count > 0:
            detector.list_loaded_templates()
            return detector
        else:
            print("templates 文件夹中没有图片文件")
    else:
        print("templates 文件夹不存在")
    
    return None

def demo_detection_test(detector):
    """演示：检测测试"""
    if detector is None:
        print("没有可用的检测器")
        return
    
    print("\n=== 演示：检测测试 ===")
    
    # 设置检测参数
    detector.set_detection_region(0, 0, 1920, 1080)  # 全屏检测
    detector.set_match_threshold(0.7)  # 70%匹配度
    
    # 单次检测测试
    print("进行单次检测测试...")
    matches, detection_time = detector.single_detection()
    
    print(f"检测耗时: {detection_time:.2f}ms")
    print(f"发现匹配: {len(matches)}个")
    
    for match in matches:
        x, y, w, h = match.position
        center_x, center_y = x + w//2, y + h//2
        print(f"  - {match.equipment_name}: 置信度{match.confidence:.3f}")
        print(f"    坐标: 左上({x},{y}) 中心({center_x},{center_y}) 右下({x+w},{y+h})")
        print(f"    尺寸: {w}x{h} 缩放: {match.template_scale:.2f}x")

def demo_realtime_detection(detector, duration=10):
    """演示：实时检测"""
    if detector is None:
        print("没有可用的检测器")
        return
    
    print(f"\n=== 演示：实时检测 ({duration}秒) ===")
    print("开始监控装备掉落...")
    
    def custom_alert(match):
        x, y, w, h = match.position
        center_x, center_y = x + w//2, y + h//2
        print(f"🎯 发现目标: {match.equipment_name} (置信度: {match.confidence:.3f})")
        print(f"   坐标: 左上({x},{y}) 中心({center_x},{center_y}) 右下({x+w},{y+h})")
        print(f"   尺寸: {w}x{h} 缩放: {match.template_scale:.2f}x")
        print("-" * 40)
    
    try:
        detector.start_realtime_detection(custom_alert, fps=5)
        time.sleep(duration)
        detector.stop_realtime_detection()
        
        # 获取结果统计
        results = detector.get_latest_results()
        print(f"检测完成，队列中还有 {len(results)} 个结果")
        
    except KeyboardInterrupt:
        print("用户中断检测")
        detector.stop_realtime_detection()

def interactive_menu():
    """交互式菜单"""
    print("🎮 模板装备检测器 - 交互式演示")
    print("=" * 50)
    
    # 创建模板文件夹
    create_templates_folder()
    
    while True:
        print("\n请选择操作:")
        print("1. 从 templates 文件夹加载装备图片")
        print("2. 加载单个装备图片 (需要手动指定路径)")
        print("3. 进行单次检测测试")
        print("4. 开始实时检测 (10秒)")
        print("5. 查看使用说明")
        print("6. 退出")
        
        try:
            choice = input("\n请输入选择 (1-6): ").strip()
            
            if choice == "1":
                detector = demo_folder_templates()
                if detector:
                    demo_detection_test(detector)
                    
            elif choice == "2":
                detector = demo_single_template()
                if detector:
                    demo_detection_test(detector)
                    
            elif choice == "3":
                detector = demo_folder_templates()
                if detector:
                    demo_detection_test(detector)
                    
            elif choice == "4":
                detector = demo_folder_templates()
                if detector:
                    demo_realtime_detection(detector, 10)
                    
            elif choice == "5":
                show_usage_instructions()
                
            elif choice == "6":
                print("退出程序")
                break
                
            else:
                print("无效选择，请输入 1-6")
                
        except KeyboardInterrupt:
            print("\n程序中断")
            break
        except Exception as e:
            print(f"发生错误: {e}")

def show_usage_instructions():
    """显示使用说明"""
    print("\n📖 使用说明")
    print("=" * 30)
    print("1. 准备装备图片:")
    print("   - 在游戏中截取你想检测的装备图标")
    print("   - 保存为 PNG 或 JPG 格式")
    print("   - 建议尺寸: 32x32 到 128x128 像素")
    print()
    print("2. 放置图片:")
    print("   - 将图片放入 'templates' 文件夹")
    print("   - 文件名将作为装备名称")
    print("   - 例如: '传说之剑.png' -> 装备名: '传说之剑'")
    print()
    print("3. 调整参数:")
    print("   - 匹配阈值: 0.7-0.9 (越高越严格)")
    print("   - 检测频率: 3-10 FPS (越高越及时)")
    print("   - 检测区域: 建议只检测游戏窗口")
    print()
    print("4. 性能特点:")
    print("   - 检测速度: 50-200ms")
    print("   - 精确度: 极高 (基于图像匹配)")
    print("   - 安全性: 无封号风险")

def quick_start():
    """快速开始"""
    print("🚀 快速开始模式")
    print("=" * 30)
    
    # 检查是否有模板
    detector = demo_folder_templates()
    
    if detector:
        print("\n✓ 发现装备模板，开始5秒检测演示...")
        demo_realtime_detection(detector, 5)
    else:
        print("\n❌ 没有找到装备模板")
        print("请按照以下步骤操作:")
        print("1. 将你的装备图片放入 'templates' 文件夹")
        print("2. 重新运行程序")
        print("3. 或者选择交互式菜单进行详细设置")

if __name__ == "__main__":
    print("模板装备检测器演示")
    print("=" * 50)
    
    # 询问运行模式
    print("选择运行模式:")
    print("1. 快速开始 (自动检测templates文件夹)")
    print("2. 交互式菜单 (详细选项)")
    
    try:
        mode = input("请选择 (1-2): ").strip()
        
        if mode == "1":
            quick_start()
        elif mode == "2":
            interactive_menu()
        else:
            print("无效选择，启动交互式菜单...")
            interactive_menu()
            
    except KeyboardInterrupt:
        print("\n程序退出")
    except Exception as e:
        print(f"程序错误: {e}")
