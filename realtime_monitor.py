# -*- coding: utf-8 -*-
"""
实时装备监测器 - 专用版本
检测到装备后暂停并等待用户输入
"""

from template_equipment_detector import TemplateEquipmentDetector, EquipmentMatch
from mouse_keyboard_controller import get_controller
import time
import os
import threading

class RealtimeMonitor:
    """实时装备监测器"""
    
    def __init__(self):
        self.detector = TemplateEquipmentDetector()
        self.is_paused = False
        self.pause_lock = threading.Lock()
        self.detection_count = 0
        
    def setup_detector(self):
        """设置检测器"""
        print("🔧 设置装备检测器...")
        
        # 设置检测区域（全屏）
        self.detector.set_detection_region(0, 0, 1920, 1080)
        
        # 设置匹配阈值
        self.detector.set_match_threshold(0.7)
        
        # 加载模板
        loaded_count = 0
        
        # 尝试从templates文件夹加载
        if os.path.exists("templates"):
            loaded_count = self.detector.load_templates_from_folder("templates")
            
        if loaded_count == 0:
            print("❌ 没有找到装备模板！")
            print("请将你的装备图片放入 'templates' 文件夹中")
            return False
        
        print(f"✅ 成功加载 {loaded_count} 个装备模板")
        self.detector.list_loaded_templates()
        return True
    
    def equipment_detected_callback(self, match: EquipmentMatch):
        """装备检测回调函数"""
        with self.pause_lock:
            if self.is_paused:
                return  # 如果已经暂停，忽略新检测
            
            self.is_paused = True  # 暂停检测
        
        self.detection_count += 1
        x, y, w, h = match.position
        center_x, center_y = x + w//2, y + h//2
        
        # 注意：这里显示的是从检测开始到发现装备的时间间隔
        # 实际的单次检测耗时已经在检测器中输出了
        time_since_detection = (time.time() - match.timestamp) * 1000  # 转换为毫秒
        
        # 记录最终识别开始时间
        final_recognition_start = time.time()

        print("\n" + "="*60)
        print(f"🎯 第{self.detection_count}次检测 - 发现目标装备!")
        print("="*60)
        print(f"装备名称: {match.equipment_name}")
        print(f"置信度: {match.confidence:.3f} ({match.confidence*100:.1f}%)")
        # 检测耗时已经在检测器中实时输出，这里不再重复显示
        print(f"左上角坐标: ({x}, {y})")
        print(f"中心坐标: ({center_x}, {center_y})  ← 点击坐标")
        print(f"右下角坐标: ({x+w}, {y+h})")
        print(f"装备尺寸: {w}x{h} 像素")
        print(f"模板缩放: {match.template_scale:.2f}x")
        print(f"发现时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(match.timestamp))}")
        print("="*60)
        
        # 自动捡装备（移动+持续左键点击）
        controller = get_controller()
        print(f"🎁 正在自动捡装备: ({center_x}, {center_y})")
        print(f"🏃 第一步: 移动到装备位置...")
        print(f"💆 第二步: 持续2秒左键点击拾取...")
        
        pickup_result = controller.pickup_equipment(center_x, center_y, pickup_duration=2.0)
        
        if pickup_result.success:
            print(f"✅ 自动捡装备成功! 总耗时: {pickup_result.click_time:.2f}ms")
        else:
            print(f"❌ 自动捡装备失败: {pickup_result.error_message}")
            print(f"   拾取耗时: {pickup_result.click_time:.2f}ms")
        
        # 等待用户输入
        try:
            user_input = input("按 Enter 继续监测，输入 'q' 退出，输入 's' 查看统计: ")
            
            # 记录最终识别结束时间
            final_recognition_end = time.time()
            final_recognition_cost = (final_recognition_end - final_recognition_start) * 1000  # ms
            print(f"最终识别装备耗时: {final_recognition_cost:.2f}ms")

            if user_input.lower() == 'q':
                print("正在退出监测...")
                self.detector.stop_realtime_detection()
                return
            elif user_input.lower() == 's':
                self.show_statistics()
            else:
                print("继续监测中...")
                
        except KeyboardInterrupt:
            print("\n用户中断，退出监测...")
            self.detector.stop_realtime_detection()
            return
        
        # 恢复检测
        with self.pause_lock:
            self.is_paused = False
        
        print("🔍 监测已恢复...")
    
    def show_statistics(self):
        """显示统计信息"""
        print(f"\n📊 监测统计:")
        print(f"   检测次数: {self.detection_count}")
        print(f"   运行时间: {time.strftime('%H:%M:%S', time.gmtime(time.time() - self.start_time))}")
        print(f"   平均检测间隔: {(time.time() - self.start_time) / max(1, self.detection_count):.1f}秒")
    
    def start_monitoring(self, fps=10):
        """开始实时监测"""
        if not self.setup_detector():
            return
        
        self.start_time = time.time()
        
        print("\n🚀 开始实时装备监测...")
        print(f"监测频率: {fps} FPS")
        print("检测到装备时会自动暂停等待你的操作")
        print("按 Ctrl+C 可以随时退出")
        print("-" * 60)
        
        try:
            # 启动实时检测
            self.detector.start_realtime_detection(
                self.equipment_detected_callback, 
                fps=fps
            )
            
            # 主循环 - 保持程序运行
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n\n⏹️  用户手动停止监测")
        except Exception as e:
            print(f"\n❌ 监测过程中出错: {e}")
        finally:
            self.detector.stop_realtime_detection()
            self.show_statistics()
            print("监测已结束")

def main():
    print("🎮 实时装备监测器")
    print("=" * 50)
    print("功能特点:")
    print("✅ 无限时间监测")
    print("✅ 检测到装备自动暂停")
    print("✅ 显示完整坐标信息")
    print("✅ 支持继续/退出操作")
    print("=" * 50)
    
    # 检查templates文件夹
    if not os.path.exists("templates"):
        print("\n⚠️  警告: 没有找到 'templates' 文件夹")
        create_folder = input("是否创建 templates 文件夹? (y/n): ")
        if create_folder.lower() == 'y':
            os.makedirs("templates")
            print("✅ 已创建 templates 文件夹")
            print("请将你的装备图片放入此文件夹，然后重新运行程序")
            return
        else:
            print("❌ 无法继续，需要装备模板图片")
            return
    
    # 检查是否有图片文件
    template_files = []
    for file in os.listdir("templates"):
        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
            template_files.append(file)
    
    if not template_files:
        print("\n❌ templates 文件夹中没有图片文件")
        print("请添加你的装备图片后重新运行")
        return
    
    print(f"\n✅ 找到 {len(template_files)} 个装备模板:")
    for i, file in enumerate(template_files, 1):
        print(f"   {i}. {file}")
    
    # 直接使用20 FPS获得最佳响应速度
    fps = 20
    print(f"\n⚙️  监测参数: {fps} FPS (最大检测频率)")
    
    # 开始监测
    monitor = RealtimeMonitor()
    monitor.start_monitoring(fps)

if __name__ == "__main__":
    main()
