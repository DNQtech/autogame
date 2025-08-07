"""
非侵入式窗口截图 - 不激活窗口的截图方法
"""

import win32gui
import win32ui
import win32con
import win32api
from ctypes import windll, c_int, c_uint, c_void_p, c_long, byref, Structure, POINTER
from ctypes.wintypes import HWND, HDC, RECT, BOOL
import numpy as np
from PIL import Image
import cv2
import time

# Windows API 常量
SRCCOPY = 0x00CC0020
DIB_RGB_COLORS = 0

# 定义Windows结构体
class BITMAPINFOHEADER(Structure):
    _fields_ = [
        ("biSize", c_uint),
        ("biWidth", c_long),
        ("biHeight", c_long),
        ("biPlanes", c_uint),
        ("biBitCount", c_uint),
        ("biCompression", c_uint),
        ("biSizeImage", c_uint),
        ("biXPelsPerMeter", c_long),
        ("biYPelsPerMeter", c_long),
        ("biClrUsed", c_uint),
        ("biClrImportant", c_uint)
    ]

class BITMAPINFO(Structure):
    _fields_ = [
        ("bmiHeader", BITMAPINFOHEADER),
        ("bmiColors", c_uint * 3)
    ]

def capture_window_non_intrusive(hwnd):
    """
    非侵入式窗口截图 - 不激活窗口
    """
    print(f"[非侵入截图] 开始截图窗口 {hwnd}")
    
    if not win32gui.IsWindow(hwnd):
        print("[错误] 窗口句柄无效")
        return None
    
    # 获取窗口信息
    rect = win32gui.GetWindowRect(hwnd)
    width = rect[2] - rect[0]
    height = rect[3] - rect[1]
    
    print(f"[信息] 窗口尺寸: {width}x{height}")
    
    # 方法1: 使用GetWindowDC + PrintWindow (推荐)
    image = try_getwindowdc_printwindow(hwnd, width, height)
    if image is not None and not is_blank_image(image):
        print("[成功] GetWindowDC + PrintWindow 方法成功")
        return image
    
    # 方法2: 使用UpdateLayeredWindow技术
    image = try_layered_window_technique(hwnd, width, height)
    if image is not None and not is_blank_image(image):
        print("[成功] LayeredWindow 技术成功")
        return image
    
    # 方法3: 使用DwmGetWindowAttribute
    image = try_dwm_thumbnail(hwnd, width, height)
    if image is not None and not is_blank_image(image):
        print("[成功] DWM缩略图方法成功")
        return image
    
    # 方法4: 使用WM_PRINT消息
    image = try_wm_print_message(hwnd, width, height)
    if image is not None and not is_blank_image(image):
        print("[成功] WM_PRINT消息方法成功")
        return image
    
    print("[失败] 所有非侵入方法都失败了")
    return None

def try_getwindowdc_printwindow(hwnd, width, height):
    """使用GetWindowDC + PrintWindow的改进方法"""
    try:
        print("[方法1] 尝试GetWindowDC + PrintWindow...")
        
        # 获取窗口DC
        hwndDC = win32gui.GetWindowDC(hwnd)
        if not hwndDC:
            print("  获取窗口DC失败")
            return None
        
        try:
            # 创建内存DC
            memDC = win32gui.CreateCompatibleDC(hwndDC)
            if not memDC:
                print("  创建内存DC失败")
                return None
            
            try:
                # 创建位图
                hBitmap = win32gui.CreateCompatibleBitmap(hwndDC, width, height)
                if not hBitmap:
                    print("  创建位图失败")
                    return None
                
                try:
                    # 选择位图到内存DC
                    win32gui.SelectObject(memDC, hBitmap)
                    
                    # 尝试不同的PrintWindow参数
                    success = False
                    for flag in [0x2, 0x0, 0x1, 0x3]:  # 不同的打印标志
                        result = windll.user32.PrintWindow(hwnd, memDC, flag)
                        if result:
                            print(f"  PrintWindow成功，标志: 0x{flag:x}")
                            success = True
                            break
                    
                    if not success:
                        print("  PrintWindow失败，尝试BitBlt...")
                        # 如果PrintWindow失败，尝试BitBlt
                        result = windll.gdi32.BitBlt(memDC, 0, 0, width, height, hwndDC, 0, 0, SRCCOPY)
                        if result:
                            print("  BitBlt成功")
                            success = True
                    
                    if success:
                        # 获取位图数据
                        return get_bitmap_data(hBitmap, width, height)
                    
                finally:
                    win32gui.DeleteObject(hBitmap)
            finally:
                win32gui.DeleteDC(memDC)
        finally:
            win32gui.ReleaseDC(hwnd, hwndDC)
            
    except Exception as e:
        print(f"  GetWindowDC方法失败: {e}")
        return None

def try_wm_print_message(hwnd, width, height):
    """使用WM_PRINT消息方法"""
    try:
        print("[方法4] 尝试WM_PRINT消息...")
        
        # 获取窗口DC
        hwndDC = win32gui.GetWindowDC(hwnd)
        if not hwndDC:
            return None
        
        try:
            # 创建内存DC和位图
            memDC = win32gui.CreateCompatibleDC(hwndDC)
            hBitmap = win32gui.CreateCompatibleBitmap(hwndDC, width, height)
            win32gui.SelectObject(memDC, hBitmap)
            
            # 发送WM_PRINT消息
            # PRF_CHECKVISIBLE | PRF_CHILDREN | PRF_CLIENT | PRF_ERASEBKGND | PRF_NONCLIENT | PRF_OWNED
            flags = 0x01 | 0x10 | 0x04 | 0x08 | 0x02 | 0x20
            
            result = win32gui.SendMessage(hwnd, win32con.WM_PRINT, memDC, flags)
            print(f"  WM_PRINT结果: {result}")
            
            # 获取位图数据
            image = get_bitmap_data(hBitmap, width, height)
            
            win32gui.DeleteObject(hBitmap)
            win32gui.DeleteDC(memDC)
            
            return image
            
        finally:
            win32gui.ReleaseDC(hwnd, hwndDC)
            
    except Exception as e:
        print(f"  WM_PRINT方法失败: {e}")
        return None

def try_layered_window_technique(hwnd, width, height):
    """分层窗口技术"""
    try:
        print("[方法2] 尝试分层窗口技术...")
        
        # 检查窗口扩展样式
        ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        
        # 临时设置为分层窗口
        if not (ex_style & win32con.WS_EX_LAYERED):
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style | win32con.WS_EX_LAYERED)
            print("  设置为分层窗口")
        
        # 获取屏幕DC
        screenDC = win32gui.GetDC(0)
        
        try:
            # 创建内存DC
            memDC = win32gui.CreateCompatibleDC(screenDC)
            hBitmap = win32gui.CreateCompatibleBitmap(screenDC, width, height)
            win32gui.SelectObject(memDC, hBitmap)
            
            # 获取窗口位置
            rect = win32gui.GetWindowRect(hwnd)
            
            # 从屏幕复制窗口区域
            result = windll.gdi32.BitBlt(memDC, 0, 0, width, height, screenDC, rect[0], rect[1], SRCCOPY)
            
            if result:
                image = get_bitmap_data(hBitmap, width, height)
            else:
                image = None
            
            win32gui.DeleteObject(hBitmap)
            win32gui.DeleteDC(memDC)
            
            # 恢复原始样式
            if not (ex_style & win32con.WS_EX_LAYERED):
                win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)
            
            return image
            
        finally:
            win32gui.ReleaseDC(0, screenDC)
            
    except Exception as e:
        print(f"  分层窗口技术失败: {e}")
        return None

def try_dwm_thumbnail(hwnd, width, height):
    """DWM缩略图方法"""
    try:
        print("[方法3] 尝试DWM缩略图...")
        
        # 这个方法需要更复杂的DWM API调用
        # 暂时返回None，可以后续实现
        print("  DWM缩略图方法暂未实现")
        return None
        
    except Exception as e:
        print(f"  DWM缩略图失败: {e}")
        return None

def get_bitmap_data(hBitmap, width, height):
    """从位图句柄获取图像数据 - 使用win32ui方法"""
    try:
        # 使用win32ui的更简单方法
        bmp = win32ui.CreateBitmapFromHandle(hBitmap)
        bmp_info = bmp.GetInfo()
        bmp_str = bmp.GetBitmapBits(True)
        
        print(f"  位图信息: {bmp_info}")
        
        # 根据位深度处理
        if bmp_info['bmBitsPixel'] == 32:
            # 32位BGRA格式
            img_array = np.frombuffer(bmp_str, dtype=np.uint8)
            img_array = img_array.reshape((bmp_info['bmHeight'], bmp_info['bmWidth'], 4))
            img_bgr = img_array[:, :, :3]  # 去掉Alpha通道
            # 不需要翻转，直接返回
            return img_bgr
            
        elif bmp_info['bmBitsPixel'] == 24:
            # 24位BGR格式
            img_array = np.frombuffer(bmp_str, dtype=np.uint8)
            img_array = img_array.reshape((bmp_info['bmHeight'], bmp_info['bmWidth'], 3))
            # 不需要翻转，直接返回
            return img_array
            
        else:
            print(f"  不支持的位深度: {bmp_info['bmBitsPixel']}")
            return None
            
    except Exception as e:
        print(f"  获取位图数据失败: {e}")
        # 尝试备用方法
        return get_bitmap_data_fallback(hBitmap, width, height)

def get_bitmap_data_fallback(hBitmap, width, height):
    """备用的位图数据获取方法"""
    try:
        print("  尝试备用方法获取位图数据...")
        
        # 创建设备上下文
        screenDC = win32gui.GetDC(0)
        memDC = win32gui.CreateCompatibleDC(screenDC)
        
        try:
            # 选择位图
            win32gui.SelectObject(memDC, hBitmap)
            
            # 创建新的兼容位图用于数据提取
            newBitmap = win32gui.CreateCompatibleBitmap(screenDC, width, height)
            newMemDC = win32gui.CreateCompatibleDC(screenDC)
            win32gui.SelectObject(newMemDC, newBitmap)
            
            # 复制位图数据
            windll.gdi32.BitBlt(newMemDC, 0, 0, width, height, memDC, 0, 0, SRCCOPY)
            
            # 使用win32ui获取数据
            bmp = win32ui.CreateBitmapFromHandle(newBitmap)
            bmp_info = bmp.GetInfo()
            bmp_str = bmp.GetBitmapBits(True)
            
            if bmp_info['bmBitsPixel'] == 32:
                img_array = np.frombuffer(bmp_str, dtype=np.uint8)
                img_array = img_array.reshape((height, width, 4))
                img_bgr = img_array[:, :, :3]
                # 不需要翻转，直接返回
                return img_bgr
            elif bmp_info['bmBitsPixel'] == 24:
                img_array = np.frombuffer(bmp_str, dtype=np.uint8)
                img_array = img_array.reshape((height, width, 3))
                # 不需要翻转，直接返回
                return img_array
            
            win32gui.DeleteObject(newBitmap)
            win32gui.DeleteDC(newMemDC)
            
        finally:
            win32gui.DeleteDC(memDC)
            win32gui.ReleaseDC(0, screenDC)
            
    except Exception as e:
        print(f"  备用方法也失败: {e}")
        return None

def is_blank_image(image, threshold=10):
    """检查图像是否为空白"""
    if image is None:
        return True
    
    std_dev = np.std(image)
    if std_dev < threshold:
        print(f"  图像可能为空白 (标准差: {std_dev:.2f})")
        return True
    
    return False

def test_non_intrusive_capture():
    """测试非侵入式截图"""
    print("=== 非侵入式窗口截图测试 ===")
    
    # 查找窗口
    def find_windows():
        windows = []
        def enum_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title and len(title) > 0:
                    rect = win32gui.GetWindowRect(hwnd)
                    width = rect[2] - rect[0]
                    height = rect[3] - rect[1]
                    if width > 200 and height > 200:
                        windows.append({
                            'handle': hwnd,
                            'title': title,
                            'size': (width, height)
                        })
        win32gui.EnumWindows(enum_callback, windows)
        return windows
    
    windows = find_windows()

    # 查找微信窗口
    wechat_window = None
    for window in windows:
        print(window)
        if "钉钉" in window['title'] or "WeChat" in window['title'].lower():
            wechat_window = window
            break
    
    if wechat_window:
        print(f"找到微信窗口: {wechat_window['title']}")
        target_window = wechat_window
    else:
        print("未找到微信窗口，显示所有窗口:")
        for i, window in enumerate(windows[:10]):
            print(f"{i+1}. {window['title'][:50]} - {window['size']}")
        
        try:
            choice = int(input("\n请选择窗口编号: ")) - 1
            if 0 <= choice < len(windows):
                target_window = windows[choice]
            else:
                print("无效选择")
                return
        except:
            print("无效输入")
            return
    
    hwnd = target_window['handle']
    print(f"\n目标窗口: {target_window['title']}")
    print(f"窗口句柄: {hwnd}")
    
    # 执行非侵入式截图
    image = capture_window_non_intrusive(hwnd)
    
    if image is not None:
        filename = f"non_intrusive_capture_{hwnd}.png"
        cv2.imwrite(filename, image)
        print(f"\n[成功] 非侵入式截图保存为: {filename}")
        print(f"[信息] 图像尺寸: {image.shape}")
        print(f"[信息] 图像统计: min={image.min()}, max={image.max()}, mean={image.mean():.1f}, std={np.std(image):.1f}")
    else:
        print("\n[失败] 非侵入式截图失败")

if __name__ == "__main__":
    test_non_intrusive_capture()
