"""
人物检测器 - 用于检测屏幕上的人物位置
"""

import cv2
import numpy as np
import mss
import time
from typing import Optional, Tuple
from dataclasses import dataclass

@dataclass
class HeroPosition:
    """人物位置信息"""
    x: int
    y: int
    confidence: float
    timestamp: float

class HeroDetector:
    """人物检测器"""
    
    def __init__(self, hero_template_path: str = "D:/ggc/projects/only/hero/image.png"):
        """
        初始化人物检测器
        
        Args:
            hero_template_path: 人物模板图片路径
        """
        self.hero_template_path = hero_template_path
        self.hero_template = None
        # 不在初始化时创建 mss 实例，避免线程安全问题
        self.load_hero_template()
        
    def load_hero_template(self):
        """加载人物模板图片"""
        try:
            self.hero_template = cv2.imread(self.hero_template_path, cv2.IMREAD_COLOR)
            if self.hero_template is None:
                raise ValueError(f"无法加载人物模板图片: {self.hero_template_path}")
            print(f"[OK] 人物模板加载成功: {self.hero_template.shape}")
        except Exception as e:
            print(f"[ERROR] 人物模板加载失败: {e}")
            raise
    
    def capture_screen(self, monitor_id: int = 1) -> np.ndarray:
        """截取屏幕"""
        try:
            # 每次截屏时创建新的 mss 实例，避免线程安全问题
            with mss.mss() as sct:
                monitor = sct.monitors[monitor_id]
                screenshot = sct.grab(monitor)
                img = np.array(screenshot)
                # 转换颜色格式 BGRA -> BGR
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                return img
        except Exception as e:
            print(f"[ERROR] 屏幕截取失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def detect_hero(self, threshold: float = 0.8) -> Optional[HeroPosition]:
        """
        检测人物位置
        
        Args:
            threshold: 匹配阈值
            
        Returns:
            HeroPosition: 人物位置信息，如果未检测到则返回None
        """
        if self.hero_template is None:
            print("[ERROR] 人物模板未加载")
            return None
            
        # 截取屏幕
        screen = self.capture_screen()
        if screen is None:
            return None
            
        try:
            # 模板匹配
            result = cv2.matchTemplate(screen, self.hero_template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= threshold:
                # 计算人物中心位置
                h, w = self.hero_template.shape[:2]
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                
                return HeroPosition(
                    x=center_x,
                    y=center_y,
                    confidence=max_val,
                    timestamp=time.time()
                )
            else:
                print(f"[INFO] 人物检测置信度不足: {max_val:.3f} < {threshold}")
                return None
                
        except Exception as e:
            print(f"[ERROR] 人物检测失败: {e}")
            return None
    
    def calculate_distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> float:
        """计算两点之间的距离"""
        return np.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
    
    def get_move_position_near_equipment(self, hero_pos: Tuple[int, int], 
                                       equipment_pos: Tuple[int, int], 
                                       distance: int = 500) -> Tuple[int, int]:
        """
        计算人物移动到装备附近的位置
        
        Args:
            hero_pos: 人物当前位置 (x, y)
            equipment_pos: 装备位置 (x, y)
            distance: 目标距离（像素）
            
        Returns:
            目标移动位置 (x, y)
        """
        hx, hy = hero_pos
        ex, ey = equipment_pos
        
        # 计算方向向量
        dx = ex - hx
        dy = ey - hy
        current_distance = np.sqrt(dx*dx + dy*dy)
        
        if current_distance <= distance:
            # 已经在范围内，不需要移动
            return hero_pos
        
        # 计算单位向量
        unit_x = dx / current_distance
        unit_y = dy / current_distance
        
        # 计算目标位置（装备位置向人物方向偏移distance距离）
        target_x = int(ex - unit_x * distance)
        target_y = int(ey - unit_y * distance)
        
        return (target_x, target_y)
    
    def is_hero_near_equipment(self, hero_pos: Tuple[int, int], 
                             equipment_pos: Tuple[int, int], 
                             threshold: int = 20) -> bool:
        """
        检查人物是否在装备附近
        
        Args:
            hero_pos: 人物位置
            equipment_pos: 装备位置
            threshold: 距离阈值
            
        Returns:
            bool: 是否在范围内
        """
        distance = self.calculate_distance(hero_pos, equipment_pos)
        return distance <= threshold

def main():
    """测试函数"""
    print("[HERO] 人物检测器测试")
    print("=" * 50)
    
    detector = HeroDetector()
    
    # 测试人物检测
    print("正在检测人物位置...")
    hero_pos = detector.detect_hero()
    
    if hero_pos:
        print(f"[OK] 检测到人物:")
        print(f"   位置: ({hero_pos.x}, {hero_pos.y})")
        print(f"   置信度: {hero_pos.confidence:.3f}")
        print(f"   时间戳: {hero_pos.timestamp}")
        
        # 测试移动位置计算
        equipment_pos = (41, 962)  # 假设装备位置
        target_pos = detector.get_move_position_near_equipment(
            (hero_pos.x, hero_pos.y), equipment_pos, 25
        )
        print(f"[INFO] 装备位置: {equipment_pos}")
        print(f"[INFO] 目标移动位置: {target_pos}")
        
        # 测试距离检查
        is_near = detector.is_hero_near_equipment(
            (hero_pos.x, hero_pos.y), equipment_pos, 25
        )
        print(f"[INFO] 是否在装备附近: {is_near}")
        
    else:
        print("[ERROR] 未检测到人物")

if __name__ == "__main__":
    main()
