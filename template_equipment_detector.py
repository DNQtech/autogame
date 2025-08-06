# -*- coding: utf-8 -*-
import cv2
import numpy as np
import time
import mss
import os
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
import threading
import queue

@dataclass
class EquipmentMatch:
    """装备匹配结果"""
    equipment_name: str
    confidence: float
    position: Tuple[int, int, int, int]  # x, y, width, height
    template_scale: float
    timestamp: float

class TemplateEquipmentDetector:
    """基于模板匹配的装备检测器 - 使用你的目标装备图片"""
    
    def __init__(self):
        self.templates = {}  # 存储装备模板
        self.detection_region = None
        self.is_running = False
        self.detection_thread = None
        self.result_queue = queue.Queue()
        self.match_threshold = 0.7  # 匹配阈值
        
    def load_equipment_template(self, image_path: str, equipment_name: str) -> bool:
        """加载装备模板图片
        
        Args:
            image_path: 装备图片路径
            equipment_name: 装备名称
            
        Returns:
            bool: 是否加载成功
        """
        if not os.path.exists(image_path):
            print(f"错误: 找不到图片文件 {image_path}")
            return False
            
        try:
            # 加载图片
            template = cv2.imread(image_path, cv2.IMREAD_COLOR)
            if template is None:
                print(f"错误: 无法读取图片 {image_path}")
                return False
            
            # 存储模板的多个版本（不同尺寸）
            self.templates[equipment_name] = {
                'original': template,
                'gray': cv2.cvtColor(template, cv2.COLOR_BGR2GRAY),
                'size': template.shape[:2]  # (height, width)
            }
            
            print(f"✓ 成功加载装备模板: {equipment_name}")
            print(f"  图片尺寸: {template.shape[1]}x{template.shape[0]}")
            return True
            
        except Exception as e:
            print(f"错误: 加载模板时出错 {e}")
            return False
    
    def load_templates_from_folder(self, folder_path: str) -> int:
        """从文件夹批量加载模板
        
        Args:
            folder_path: 包含装备图片的文件夹路径
            
        Returns:
            int: 成功加载的模板数量
        """
        if not os.path.exists(folder_path):
            print(f"错误: 文件夹不存在 {folder_path}")
            return 0
        
        loaded_count = 0
        supported_formats = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff')
        
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(supported_formats):
                image_path = os.path.join(folder_path, filename)
                equipment_name = os.path.splitext(filename)[0]  # 使用文件名作为装备名
                
                if self.load_equipment_template(image_path, equipment_name):
                    loaded_count += 1
        
        print(f"从文件夹 {folder_path} 加载了 {loaded_count} 个模板")
        return loaded_count
    
    def set_detection_region(self, x: int, y: int, width: int, height: int):
        """设置检测区域"""
        self.detection_region = {"top": y, "left": x, "width": width, "height": height}
        print(f"设置检测区域: ({x}, {y}, {width}, {height})")
    
    def set_match_threshold(self, threshold: float):
        """设置匹配阈值 (0.0-1.0)"""
        self.match_threshold = max(0.0, min(1.0, threshold))
        print(f"设置匹配阈值: {self.match_threshold}")
    
    def capture_screen_safe(self) -> Optional[np.ndarray]:
        """线程安全的截屏"""
        try:
            with mss.mss() as sct:
                if self.detection_region:
                    screenshot = sct.grab(self.detection_region)
                else:
                    screenshot = sct.grab(sct.monitors[1])
                
                img = np.array(screenshot)[:, :, :3]
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                return img
        except Exception as e:
            print(f"截屏错误: {e}")
            return None
    
    def match_template_multiscale(self, image: np.ndarray, template_name: str, 
                                 template_data: Dict) -> List[EquipmentMatch]:
        """多尺度模板匹配"""
        results = []
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        template_gray = template_data['gray']
        
        # 多个缩放比例
        scales = [0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3]
        
        for scale in scales:
            # 缩放模板
            scaled_template = cv2.resize(template_gray, None, fx=scale, fy=scale)
            
            # 检查模板是否超出图像大小
            if (scaled_template.shape[0] > gray_image.shape[0] or 
                scaled_template.shape[1] > gray_image.shape[1]):
                continue
            
            # 模板匹配
            result = cv2.matchTemplate(gray_image, scaled_template, cv2.TM_CCOEFF_NORMED)
            
            # 查找匹配位置
            locations = np.where(result >= self.match_threshold)
            
            for pt in zip(*locations[::-1]):  # (x, y)
                confidence = result[pt[1], pt[0]]
                h, w = scaled_template.shape
                
                match = EquipmentMatch(
                    equipment_name=template_name,
                    confidence=confidence,
                    position=(pt[0], pt[1], w, h),
                    template_scale=scale,
                    timestamp=time.time()
                )
                results.append(match)
        
        return results
    
    def detect_equipment_templates(self, image: np.ndarray) -> Tuple[List[EquipmentMatch], float]:
        """检测所有模板装备"""
        start_time = time.time()
        all_matches = []
        
        try:
            for template_name, template_data in self.templates.items():
                matches = self.match_template_multiscale(image, template_name, template_data)
                all_matches.extend(matches)
            
            # 去除重叠的匹配结果
            filtered_matches = self._remove_overlapping_matches(all_matches)
            
        except Exception as e:
            print(f"模板检测错误: {e}")
            filtered_matches = []
        
        detection_time = (time.time() - start_time) * 1000
        return filtered_matches, detection_time
    
    def _remove_overlapping_matches(self, matches: List[EquipmentMatch], 
                                   overlap_threshold: float = 0.5) -> List[EquipmentMatch]:
        """去除重叠的匹配结果"""
        if not matches:
            return matches
        
        # 按置信度排序
        matches.sort(key=lambda x: x.confidence, reverse=True)
        
        filtered = []
        for match in matches:
            is_overlapping = False
            
            for existing in filtered:
                if self._calculate_overlap(match.position, existing.position) > overlap_threshold:
                    is_overlapping = True
                    break
            
            if not is_overlapping:
                filtered.append(match)
        
        return filtered
    
    def _calculate_overlap(self, box1: Tuple[int, int, int, int], 
                          box2: Tuple[int, int, int, int]) -> float:
        """计算两个框的重叠比例"""
        x1, y1, w1, h1 = box1
        x2, y2, w2, h2 = box2
        
        # 计算交集
        x_overlap = max(0, min(x1 + w1, x2 + w2) - max(x1, x2))
        y_overlap = max(0, min(y1 + h1, y2 + h2) - max(y1, y2))
        intersection = x_overlap * y_overlap
        
        # 计算并集
        area1 = w1 * h1
        area2 = w2 * h2
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0
    
    def single_detection(self) -> Tuple[List[EquipmentMatch], float]:
        """单次检测"""
        image = self.capture_screen_safe()
        if image is None:
            return [], 0.0
        
        return self.detect_equipment_templates(image)
    
    def start_realtime_detection(self, callback=None, fps: int = 10):
        """启动实时检测"""
        if not self.templates:
            print("错误: 没有加载任何模板，请先加载装备图片")
            return
        
        if self.is_running:
            print("检测已在运行中")
            return
        
        self.is_running = True
        self.detection_thread = threading.Thread(
            target=self._detection_loop,
            args=(callback, fps),
            daemon=True
        )
        self.detection_thread.start()
        print(f"实时模板检测已启动 (FPS: {fps})")
        print(f"正在监控 {len(self.templates)} 种装备")
    
    def stop_realtime_detection(self):
        """停止实时检测"""
        self.is_running = False
        if self.detection_thread and self.detection_thread.is_alive():
            self.detection_thread.join(timeout=2.0)
        print("实时检测已停止")
    
    def _detection_loop(self, callback, fps):
        """检测循环"""
        frame_time = 1.0 / fps
        detection_count = 0
        loop_count = 0
        
        print(f"[DETECTOR] 检测循环开始，初始状态: is_running={self.is_running}")
        
        while self.is_running:
            try:
                # 检查状态一致性
                if not self.is_running:
                    print(f"[DETECTOR] 检测到 is_running=False，退出循环")
                    break
                    
                loop_start = time.time()
                loop_count += 1
                
                # 每50次检测输出一次状态
                if loop_count % 50 == 0:
                    print(f"[DETECTOR] 第{loop_count}次检测，状态: is_running={self.is_running}")
                
                matches, detection_time = self.single_detection()
                
                # 输出每次检测的耗时
                if matches:
                    detection_count += len(matches)
                    print(f"\n🔍 第{loop_count}次检测耗时: {detection_time:.2f}ms - 发现{len(matches)}个装备!")
                    print(f"[DETECTOR] 回调前状态: is_running={self.is_running}")
                    
                    for match in matches:
                        self.result_queue.put(match)
                        if callback:
                            try:
                                callback(match)
                                print(f"[DETECTOR] 回调后状态: is_running={self.is_running}")
                            except Exception as e:
                                print(f"回调函数错误: {e}")
                                import traceback
                                traceback.print_exc()
                                print(f"[DETECTOR] 回调异常后状态: is_running={self.is_running}")
                                # 回调异常不应该影响检测循环，继续运行
                                
                    # 检查回调后状态
                    if not self.is_running:
                        print(f"[DETECTOR] 警告: 回调后 is_running 被设置为 False，强制恢复为 True")
                        self.is_running = True
                        
                else:
                    print(f"第{loop_count}次检测耗时: {detection_time:.2f}ms - 未发现装备", end="\r")  # \r 覆盖显示
                
                # 控制帧率
                elapsed = time.time() - loop_start
                sleep_time = max(0, frame_time - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
            except Exception as e:
                print(f"检测循环错误: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(0.1)
        
        print(f"[DETECTOR] 检测线程结束，最终状态: is_running={self.is_running}")
        print(f"检测线程结束，总共进行了{loop_count}次检测，发现 {detection_count} 个目标装备")
    
    def get_latest_results(self) -> List[EquipmentMatch]:
        """获取最新检测结果"""
        results = []
        while not self.result_queue.empty():
            try:
                results.append(self.result_queue.get_nowait())
            except queue.Empty:
                break
        return results
    
    def list_loaded_templates(self):
        """列出已加载的模板"""
        if not self.templates:
            print("没有加载任何模板")
            return
        
        print("已加载的装备模板:")
        for i, (name, data) in enumerate(self.templates.items(), 1):
            h, w = data['size']
            print(f"  {i}. {name} ({w}x{h})")

def equipment_found_alert(match: EquipmentMatch):
    """装备发现警报"""
    x, y, w, h = match.position
    center_x, center_y = x + w//2, y + h//2
    
    print(f"🎯 发现目标装备: {match.equipment_name}")
    print(f"   置信度: {match.confidence:.3f}")
    print(f"   左上角坐标: ({x}, {y})")
    print(f"   中心坐标: ({center_x}, {center_y})")
    print(f"   装备尺寸: {w}x{h}")
    print(f"   右下角坐标: ({x+w}, {y+h})")
    print(f"   模板缩放: {match.template_scale:.2f}x")
    print(f"   发现时间: {time.strftime('%H:%M:%S', time.localtime(match.timestamp))}")
    print("=" * 60)

def main():
    print("基于模板匹配的装备检测器")
    print("=" * 50)
    
    detector = TemplateEquipmentDetector()
    
    # 使用示例
    print("\n使用方法:")
    print("1. 将你的目标装备图片放在 'templates' 文件夹中")
    print("2. 或者使用 load_equipment_template() 加载单个图片")
    print("3. 调用 start_realtime_detection() 开始监控")
    
    # 示例代码（注释掉，用户需要根据实际情况修改）
    """
    # 方法1: 加载单个模板
    detector.load_equipment_template("my_sword.png", "传说之剑")
    detector.load_equipment_template("epic_armor.png", "史诗护甲")
    
    # 方法2: 批量加载文件夹中的所有图片
    detector.load_templates_from_folder("templates")
    
    # 设置检测区域（可选，默认全屏）
    detector.set_detection_region(0, 0, 1920, 1080)
    
    # 设置匹配阈值（可选，默认0.7）
    detector.set_match_threshold(0.8)
    
    # 开始实时检测
    detector.start_realtime_detection(equipment_found_alert, fps=5)
    
    # 运行一段时间
    time.sleep(30)
    
    # 停止检测
    detector.stop_realtime_detection()
    """

if __name__ == "__main__":
    main()
