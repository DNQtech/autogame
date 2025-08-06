#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
速度优化OCR服务端 - 独立进程，预加载模型，提供HTTP API
性能提升: 1.6倍加速，36%时间节省
"""

import os
import sys
import time
import json
import base64
import subprocess
import platform
from flask import Flask, request, jsonify
from ocr_speed_optimized import get_speed_optimized_ocr
import threading

app = Flask(__name__)

# 全局OCR实例
ocr_service = None
server_start_time = None

def init_ocr_service():
    """初始化OCR服务（服务端启动时调用）"""
    global ocr_service, server_start_time
    
    print("=" * 50)
    print("速度优化OCR服务端启动中...")
    print("=" * 50)
    
    server_start_time = time.time()
    
    print("预加载OCR模型...")
    model_start = time.time()
    
    # 预加载速度优化模型
    ocr_service = get_speed_optimized_ocr()
    
    model_time = time.time() - model_start
    total_time = time.time() - server_start_time
    
    print(f"[OK] OCR模型加载完成，耗时: {model_time:.2f}秒")
    print(f"[OK] 服务端启动完成，总耗时: {total_time:.2f}秒")
    print("服务端已就绪，等待客户端请求...")
    print("=" * 50)

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    uptime = time.time() - server_start_time if server_start_time else 0
    return jsonify({
        'status': 'healthy',
        'uptime': f"{uptime:.1f}秒",
        'model_loaded': ocr_service is not None
    })

@app.route('/find_text', methods=['POST'])
def find_text_api():
    """文字查找API"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': '请求数据为空'}), 400
        
        # 获取参数
        image_path = data.get('image_path')
        target_text = data.get('target_text', '')
        early_exit = data.get('early_exit', True)
        
        if not image_path:
            return jsonify({'error': '缺少image_path参数'}), 400
        
        if not os.path.exists(image_path):
            return jsonify({'error': f'图像文件不存在: {image_path}'}), 400
        
        # 记录请求开始时间
        request_start = time.time()
        
        print(f"[请求] 查找'{target_text}' in {os.path.basename(image_path)}")
        
        # 调用速度优化OCR服务
        result = ocr_service.find_text_speed_optimized(image_path, target_text, early_exit)
        
        request_time = time.time() - request_start
        
        # 添加服务端信息
        if result['success']:
            result['server_info'] = {
                'request_time': request_time,
                'server_uptime': time.time() - server_start_time,
                'model_preloaded': True
            }
            
            status = "找到" if result['target_found'] else "未找到"
            early_info = "提前退出" if result.get('early_exit') else "完整处理"
            processed = result.get('processed_texts', 0)
            total = result['total_texts']
            
            print(f"[OK] 请求完成: {status} | {request_time:.3f}s | {early_info} | {processed}/{total}")
        else:
            print(f"[ERROR] 请求失败: {result['error']}")
        
        return jsonify(result)
        
    except Exception as e:
        print(f"[ERROR] 服务端错误: {str(e)}")
        return jsonify({'error': f'服务端错误: {str(e)}'}), 500

@app.route('/batch_find', methods=['POST'])
def batch_find_api():
    """批量查找API"""
    try:
        data = request.get_json()
        
        image_path = data.get('image_path')
        target_texts = data.get('target_texts', [])
        early_exit = data.get('early_exit', True)
        
        if not image_path or not target_texts:
            return jsonify({'error': '缺少必要参数'}), 400
        
        print(f"[批量] 收到批量请求: {len(target_texts)}个目标文字")
        
        request_start = time.time()
        results = {}
        
        for target_text in target_texts:
            result = ocr_service.find_text_speed_optimized(image_path, target_text, early_exit)
            results[target_text] = result
        
        request_time = time.time() - request_start
        
        print(f"[OK] 批量请求完成: {request_time:.3f}s")
        
        return jsonify({
            'success': True,
            'results': results,
            'batch_info': {
                'total_requests': len(target_texts),
                'batch_time': request_time
            }
        })
        
    except Exception as e:
        print(f"[ERROR] 批量请求错误: {str(e)}")
        return jsonify({'error': f'批量请求错误: {str(e)}'}), 500

def cleanup_existing_servers(port=5000):
    """
    清理已存在的OCR服务进程
    
    Args:
        port: 要清理的端口号
    """
    try:
        print(f"正在检查端口 {port} 是否被占用...")
        
        if platform.system().lower() == 'windows':
            # Windows系统
            result = subprocess.run(
                ['netstat', '-ano'], 
                capture_output=True, 
                text=True, 
                encoding='gbk'  # Windows中文系统编码
            )
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                pids_to_kill = set()
                
                for line in lines:
                    if f':{port}' in line and 'LISTENING' in line:
                        parts = line.split()
                        if len(parts) >= 5:
                            pid = parts[-1]
                            if pid.isdigit() and pid != '0':
                                pids_to_kill.add(pid)
                
                if pids_to_kill:
                    print(f"发现 {len(pids_to_kill)} 个进程占用端口 {port}: {', '.join(pids_to_kill)}")
                    
                    for pid in pids_to_kill:
                        try:
                            subprocess.run(
                                ['taskkill', '/F', '/PID', pid], 
                                capture_output=True, 
                                check=True
                            )
                            print(f"已终止进程 PID: {pid}")
                        except subprocess.CalledProcessError:
                            print(f"警告: 无法终止进程 PID: {pid}")
                    
                    # 等待进程完全终止
                    time.sleep(2)
                    print(f"端口 {port} 清理完成")
                else:
                    print(f"端口 {port} 未被占用")
            else:
                print("警告: 无法检查端口占用情况")
        
        else:
            # Linux/Mac系统
            result = subprocess.run(
                ['lsof', '-ti', f':{port}'], 
                capture_output=True, 
                text=True
            )
            
            if result.returncode == 0 and result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                print(f"发现 {len(pids)} 个进程占用端口 {port}: {', '.join(pids)}")
                
                for pid in pids:
                    if pid.strip():
                        try:
                            subprocess.run(['kill', '-9', pid.strip()], check=True)
                            print(f"已终止进程 PID: {pid.strip()}")
                        except subprocess.CalledProcessError:
                            print(f"警告: 无法终止进程 PID: {pid.strip()}")
                
                time.sleep(1)
                print(f"端口 {port} 清理完成")
            else:
                print(f"端口 {port} 未被占用")
                
    except Exception as e:
        print(f"警告: 端口清理过程中出现错误: {str(e)}")
        print("继续启动服务...")

def run_server(host='127.0.0.1', port=5000, debug=False, use_waitress=True):
    """启动OCR服务端"""
    print("正在启动OCR服务端...")
    
    # 自动清理已存在的服务进程
    cleanup_existing_servers(port)
    
    print(f"服务地址: http://{host}:{port}")
    print("可用接口:")
    print(f"   GET  /health     - 健康检查")
    print(f"   POST /find_text  - 文字查找")
    print(f"   POST /batch_find - 批量查找")
    print()
    
    if use_waitress:
        try:
            from waitress import serve
            print("使用Waitress生产级WSGI服务器...")
            print("服务端运行中，按 Ctrl+C 停止...")
            serve(app, host=host, port=port, threads=6)
        except ImportError:
            print("警告: Waitress未安装，回退到Flask开发服务器")
            print("建议安装: pip install waitress")
            use_waitress = False
    
    if not use_waitress:
        print("使用Flask开发服务器（仅用于开发）...")
        print("服务端运行中，按 Ctrl+C 停止...")
        try:
            app.run(host=host, port=port, debug=debug, threaded=True)
        except KeyboardInterrupt:
            print("\n服务端已停止")

if __name__ == "__main__":
    init_ocr_service()
    run_server()
