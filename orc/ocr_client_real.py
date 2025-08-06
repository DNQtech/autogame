#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简洁的OCR客户端 - 通过HTTP调用服务端识别文字
"""
import requests
import time
from typing import Dict, List

class OCRClient:
    """简洁的OCR客户端"""
    
    def __init__(self, server_url='http://127.0.0.1:5000'):
        """
        初始化客户端
        
        Args:
            server_url: OCR服务端地址
        """
        self.server_url = server_url.rstrip('/')
        self.session = requests.Session()
    
    def is_server_ready(self) -> bool:
        """检查服务端是否就绪"""
        try:
            response = self.session.get(f"{self.server_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def find_text(self, image_path: str, target_text: str) -> Dict:
        """
        查找文字
        
        Args:
            image_path: 图像路径
            target_text: 目标文字
            
        Returns:
            识别结果: {
                'success': bool,
                'found': bool,
                'targets': [{'text': str, 'confidence': float, 'position': tuple}],
                'error': str  # 仅在失败时存在
            }
        """
        try:
            request_data = {
                'image_path': image_path,
                'target_text': target_text,
                'early_exit': True
            }
            
            response = self.session.post(
                f"{self.server_url}/find_text",
                json=request_data,
                timeout=60
            )
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    
                    # 简化返回结果
                    if result['success']:
                        return {
                            'success': True,
                            'found': result['target_found'],
                            'targets': result.get('targets', [])
                        }
                    else:
                        return {'success': False, 'error': result.get('error', '服务端处理失败')}
                except Exception as json_error:
                    return {'success': False, 'error': f'响应解析失败: {type(json_error).__name__}'}
            else:
                return {'success': False, 'error': f"服务端错误: HTTP {response.status_code}"}
                
        except requests.exceptions.ConnectionError:
            return {'success': False, 'error': '无法连接到服务端，请检查服务端是否启动'}
        except requests.exceptions.Timeout:
            return {'success': False, 'error': '请求超时，服务端响应过慢'}
        except requests.exceptions.RequestException as req_error:
            return {'success': False, 'error': f'网络请求错误: {type(req_error).__name__}'}
        except Exception as e:
            return {'success': False, 'error': f'未知错误: {type(e).__name__}'}
    
    def find_game_item(self, screenshot_path: str, item_name: str) -> Dict:
        """查找游戏物品"""
        return self.find_text(screenshot_path, item_name)
    
    def batch_find(self, image_path: str, target_texts: List[str]) -> Dict:
        """
        批量查找文字
        
        Args:
            image_path: 图像路径
            target_texts: 目标文字列表
            
        Returns:
            批量查找结果
        """
        try:
            request_data = {
                'image_path': image_path,
                'target_texts': target_texts,
                'early_exit': True
            }
            
            response = self.session.post(
                f"{self.server_url}/batch_find",
                json=request_data,
                timeout=120
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {'success': False, 'error': f"批量请求失败: {response.status_code}"}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

# 简单使用示例
def main():
    """简单使用示例"""
    # 创建客户端
    t1 = time.time()
    client = OCRClient()
    
    # 检查服务端状态
    if not client.is_server_ready():
        print("错误: 服务端未就绪，请先启动: python ocr_server.py")
        return
    
    # 查找游戏物品
    result = client.find_game_item(
        screenshot_path=r"/orc/game_screenshot.png",
        item_name="普通明月宝石"
    )
    
    # 处理结果
    if result['success']:
        if result['found']:
            target = result['targets'][0]
            print(f"找到物品: {target['text']}")
            print(f"置信度: {target['confidence']:.1%}")
            if target.get('position'):
                pos = target['position']
                print(f"位置: ({pos[0]}, {pos[1]}) - ({pos[2]}, {pos[3]})")
        else:
            print("未找到目标物品")
    else:
        print(f"识别失败: {result['error']}")
    print(f"耗时：{time.time()-t1}秒")

if __name__ == "__main__":
    main()
