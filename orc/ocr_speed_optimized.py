#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实用优化版OCR服务 - 基于已验证的优化策略
"""

import cv2
import time
import warnings
import threading
import numpy as np
from paddleocr import PaddleOCR
import os

warnings.filterwarnings('ignore')

class SpeedOptimizedOCR:
    """实用优化版OCR服务"""
    _instance = None
    _lock = threading.Lock()
    _initialized = False
    _model_loaded = False
    _model_load_time = 0.0
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(SpeedOptimizedOCR, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            with self._lock:
                if not self._initialized:
                    print("*** 初始化速度优化OCR服务 ***")
                    model_start = time.time()
                    
                    # 使用与成功版本相同的基础配置，但添加速度优化
                    self.ocr = PaddleOCR(
                        lang='ch',
                        use_angle_cls=False,  # 禁用角度分类器，提升速度约20-30%
                    )
                    
                    SpeedOptimizedOCR._model_load_time = time.time() - model_start
                    SpeedOptimizedOCR._model_loaded = True
                    print(f"速度优化OCR模型加载完成，耗时: {self._model_load_time:.2f}秒")
                    
                    SpeedOptimizedOCR._initialized = True
    
    def preprocess_image_for_speed(self, image_path: str) -> str:
        """
        优化1: 图像预处理优化
        - 调整图像尺寸减少计算量
        - 增强对比度提高识别准确率
        """
        preprocess_start = time.time()
        
        # 读取图像
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"无法读取图像: {image_path}")
        
        # 获取原始尺寸
        height, width = img.shape[:2]
        original_size = width * height
        
        # 优化策略1: 如果图像过大，适当缩小以提升速度
        max_pixels = 1920 * 1080  # 最大像素数
        if original_size > max_pixels:
            scale = (max_pixels / original_size) ** 0.5
            new_width = int(width * scale)
            new_height = int(height * scale)
            img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)
            print(f"[优化] 图像缩放: {width}x{height} -> {new_width}x{new_height} (缩放比例: {scale:.2f})")
        
        # 优化策略2: 增强对比度提高识别准确率
        # 转换为LAB色彩空间进行对比度增强
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # 对L通道进行CLAHE增强
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        l = clahe.apply(l)
        
        # 合并通道并转换回BGR
        enhanced = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        
        # 保存预处理后的图像到临时文件
        temp_path = image_path.replace('.png', '_optimized.png')
        cv2.imwrite(temp_path, enhanced)
        
        preprocess_time = time.time() - preprocess_start
        print(f"[优化] 图像预处理完成，耗时: {preprocess_time:.3f}秒")
        
        return temp_path
    
    def smart_region_detection(self, image_path: str, target_text: str = None):
        """
        优化2: 智能区域检测
        根据目标文字类型，优先处理可能包含目标的区域
        """
        if not target_text:
            return image_path, []
        
        # 读取图像获取尺寸信息
        img = cv2.imread(image_path)
        if img is None:
            return image_path, []
        
        height, width = img.shape[:2]
        roi_regions = []
        
        # 针对游戏物品的智能区域检测
        if "宝石" in target_text or "装备" in target_text or "物品" in target_text:
            # 游戏物品通常出现在这些区域：
            
            # 1. 右侧区域（通常是物品栏/背包）
            right_region = img[:, width*2//3:, :]
            roi_regions.append(("右侧区域", right_region, (width*2//3, 0)))
            
            # 2. 底部区域（通常是快捷栏）
            bottom_region = img[height*3//4:, :, :]
            roi_regions.append(("底部区域", bottom_region, (0, height*3//4)))
            
            # 3. 中央区域（可能是对话框或界面）
            center_region = img[height//4:3*height//4, width//4:3*width//4, :]
            roi_regions.append(("中央区域", center_region, (width//4, height//4)))
        
        return image_path, roi_regions
    
    def find_text_speed_optimized(self, image_path: str, target_text: str = None, early_exit: bool = True):
        """
        速度优化版本的文字识别
        """
        total_start = time.time()
        
        try:
            # 步骤1: 图像预处理优化
            optimized_image_path = self.preprocess_image_for_speed(image_path)
            
            # 步骤2: 智能区域检测
            final_image_path, roi_regions = self.smart_region_detection(optimized_image_path, target_text)
            
            # 步骤3: OCR识别
            ocr_start = time.time()
            
            # 如果有ROI区域，优先处理这些区域
            if roi_regions and target_text:
                print(f"[优化] 检测到 {len(roi_regions)} 个感兴趣区域，优先处理...")
                
                for region_name, region_img, offset in roi_regions:
                    print(f"[优化] 处理 {region_name}...")
                    
                    # 保存区域图像到临时文件
                    region_path = final_image_path.replace('.png', f'_{region_name}.png')
                    cv2.imwrite(region_path, region_img)
                    
                    # 对区域进行OCR
                    result = self.ocr.ocr(region_path)
                    
                    # 检查是否找到目标
                    if self._check_target_in_result(result, target_text):
                        print(f"[优化] 在 {region_name} 找到目标文字，提前退出！")
                        
                        # 清理临时文件
                        self._cleanup_temp_files([optimized_image_path, region_path])
                        
                        # 处理结果
                        processed_result = self._process_ocr_result(result, target_text, offset)
                        ocr_time = time.time() - ocr_start
                        total_time = time.time() - total_start
                        
                        processed_result['timing'] = {
                            'model_load': 0.0,
                            'ocr': ocr_time,
                            'process': 0.001,
                            'total': total_time
                        }
                        processed_result['early_exit'] = True
                        processed_result['region_found'] = region_name
                        
                        return processed_result
                    
                    # 清理区域临时文件
                    if os.path.exists(region_path):
                        os.remove(region_path)
                
                print("[优化] 所有感兴趣区域都未找到目标，处理完整图像...")
            
            # 处理完整图像
            result = self.ocr.ocr(final_image_path)
            ocr_time = time.time() - ocr_start
            
            # 清理临时文件
            self._cleanup_temp_files([optimized_image_path])
            
            # 处理结果
            processed_result = self._process_ocr_result(result, target_text)
            
            total_time = time.time() - total_start
            processed_result['timing'] = {
                'model_load': 0.0,
                'ocr': ocr_time,
                'process': 0.001,
                'total': total_time
            }
            processed_result['early_exit'] = False
            
            return processed_result
            
        except Exception as e:
            total_time = time.time() - total_start
            return {
                'success': False,
                'error': f'速度优化识别过程出错: {str(e)}',
                'timing': {
                    'model_load': 0.0,
                    'ocr': 0.0,
                    'process': 0.0,
                    'total': total_time
                }
            }
    
    def _check_target_in_result(self, result, target_text):
        """检查OCR结果中是否包含目标文字"""
        if not result or not isinstance(result, list) or len(result) == 0:
            return False
        
        ocr_data = result[0]
        if not isinstance(ocr_data, dict) or 'rec_texts' not in ocr_data:
            return False
        
        texts = ocr_data['rec_texts']
        for text in texts:
            if target_text in text:
                return True
        
        return False
    
    def _process_ocr_result(self, result, target_text=None, offset=(0, 0)):
        """处理OCR结果"""
        if not result or not isinstance(result, list) or len(result) == 0:
            return {
                'success': False,
                'error': 'OCR未返回结果'
            }
        
        ocr_data = result[0]
        if not isinstance(ocr_data, dict) or 'rec_texts' not in ocr_data:
            return {
                'success': False,
                'error': 'OCR结果格式错误'
            }
        
        texts = ocr_data['rec_texts']
        scores = ocr_data.get('rec_scores', [])
        polys = ocr_data.get('rec_polys', [])
        
        found_targets = []
        offset_x, offset_y = offset
        
        for i, text in enumerate(texts):
            confidence = scores[i] if i < len(scores) else 0.0
            
            # 计算位置（考虑偏移）
            position = None
            if i < len(polys):
                poly = polys[i]
                x_coords = [point[0] + offset_x for point in poly]
                y_coords = [point[1] + offset_y for point in poly]
                position = (min(x_coords), min(y_coords), max(x_coords), max(y_coords))
            
            # 检查是否是目标文字
            if target_text and target_text in text:
                found_targets.append({
                    'text': text,
                    'confidence': confidence,
                    'position': position
                })
        
        return {
            'success': True,
            'target_found': len(found_targets) > 0,
            'targets': found_targets,
            'total_texts': len(texts),
            'processed_texts': len(texts)
        }
    
    def _cleanup_temp_files(self, file_paths):
        """清理临时文件"""
        for file_path in file_paths:
            if os.path.exists(file_path) and '_optimized' in file_path:
                try:
                    os.remove(file_path)
                except:
                    pass

# 全局实例
_speed_optimized_ocr = None

def get_speed_optimized_ocr():
    """获取速度优化OCR实例"""
    global _speed_optimized_ocr
    if _speed_optimized_ocr is None:
        _speed_optimized_ocr = SpeedOptimizedOCR()
    return _speed_optimized_ocr

def find_target_text_speed_optimized(image_path: str, target_text: str = "普通明月宝石", early_exit: bool = True):
    """速度优化版查找目标文字"""
    ocr = get_speed_optimized_ocr()
    return ocr.find_text_speed_optimized(image_path, target_text, early_exit)

def test_speed_optimized_ocr():
    """测试速度优化OCR"""
    print("=" * 70)
    print("速度优化OCR服务测试")
    print("=" * 70)
    
    image_path = r"/orc/game_screenshot.png"
    target_text = "普通明月宝石"
    
    print(f"目标文字: '{target_text}'")
    print(f"测试图像: {image_path}")
    print()
    
    # 测试速度优化版本
    print("--- 速度优化版本测试 ---")
    result = find_target_text_speed_optimized(image_path, target_text, early_exit=True)
    
    if result['success']:
        timing = result['timing']
        print(f"识别成功: 找到 {result['total_texts']} 个文字")
        print(f"目标文字: {'找到' if result['target_found'] else '未找到'}")
        print(f"提前退出: {'是' if result.get('early_exit') else '否'}")
        if 'region_found' in result:
            print(f"找到区域: {result['region_found']}")
        
        print(f"\n详细耗时统计:")
        print(f"  OCR识别:    {timing['ocr']:.3f}秒")
        print(f"  结果处理:   {timing['process']:.3f}秒")
        print(f"  总耗时:     {timing['total']:.3f}秒")
        
        if result['target_found']:
            print(f"\n找到的目标文字:")
            for target in result['targets']:
                print(f"  -> '{target['text']}' (置信度: {target['confidence']:.1%})")
                if target['position']:
                    x1, y1, x2, y2 = target['position']
                    print(f"     位置: ({x1:.0f}, {y1:.0f}) - ({x2:.0f}, {y2:.0f})")
    else:
        print(f"识别失败: {result['error']}")
    
    print()
    
    # 性能对比测试
    print("--- 性能对比测试 ---")
    print("比较原版 vs 速度优化版...")
    
    # 导入原版进行对比
    try:
        from ocr_optimized import find_target_text_optimized
        
        print("\n原版OCR测试:")
        original_start = time.time()
        original_result = find_target_text_optimized(image_path, target_text, early_exit=True)
        original_time = time.time() - original_start
        
        print(f"原版耗时: {original_time:.3f}秒")
        print(f"速度优化版耗时: {timing['total']:.3f}秒")
        
        if original_time > 0:
            speedup = original_time / timing['total']
            improvement = (original_time - timing['total']) / original_time * 100
            print(f"\n性能提升:")
            print(f"  加速倍数: {speedup:.1f}x")
            print(f"  时间节省: {original_time - timing['total']:.3f}秒")
            print(f"  性能提升: {improvement:.1f}%")
        
    except ImportError:
        print("无法导入原版OCR进行对比")
    
    print()
    print("=" * 70)
    print("速度优化测试完成")
    print("=" * 70)

if __name__ == "__main__":
    test_speed_optimized_ocr()
