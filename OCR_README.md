[![Language](https://img.shields.io/badge/Language-中文-blue?style=for-the-badge)](./README.md)
[![English](https://img.shields.io/badge/English-README-green?style=for-the-badge)](./README_EN.md)
[![使用指南](https://img.shields.io/badge/使用指南-中文-orange?style=for-the-badge)](./使用指南.md)
[![Usage Guide](https://img.shields.io/badge/Usage_Guide-English-orange?style=for-the-badge)](./Usage_Guide_EN.md)
[![OCR文档](https://img.shields.io/badge/OCR文档-中文-purple?style=for-the-badge)](./OCR_README.md)
[![OCR Docs](https://img.shields.io/badge/OCR_Docs-English-purple?style=for-the-badge)](./OCR_README_EN.md)

# 🔤 OCR文字识别模块

本项目包含一个高性能的OCR（光学字符识别）模块，基于PaddleOCR引擎，专门用于游戏文字识别和处理。

## ✨ 核心特性

- 🚀 **高性能识别** - 基于PaddleOCR的先进深度学习模型
- 🎯 **游戏优化** - 专门针对游戏界面文字识别优化
- ⚡ **快速响应** - 优化的处理流程，毫秒级响应
- 🔍 **精确定位** - 准确识别文字位置和边界框
- 🌐 **多语言支持** - 支持中文、英文等多种语言
- 🛠️ **易于集成** - 简单的API接口，易于集成到其他项目

## 📁 模块文件

### 核心文件
- **`ocr_optimized.py`** - 优化版OCR核心引擎
- **`ocr_server.py`** - OCR HTTP服务端
- **`ocr_client_real.py`** - OCR客户端调用接口
- **`ocr_final.py`** - 基础OCR实现

### 配置文件
- **`requirements.txt`** - OCR模块依赖包
- **`start_demo.py`** - OCR功能演示脚本

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install paddlepaddle paddleocr opencv-python pillow numpy
```

### 2. 基础使用
```python
from ocr_optimized import OptimizedOCR

# 创建OCR实例
ocr = OptimizedOCR()

# 识别图片中的文字
result = ocr.recognize_text("screenshot.png")

# 查找特定文字
target_found = ocr.find_target_text("screenshot.png", "目标文字")
if target_found:
    print(f"找到目标文字: {target_found['text']}")
    print(f"位置: {target_found['bbox']}")
    print(f"置信度: {target_found['confidence']}")
```

### 3. 服务端模式
```bash
# 启动OCR服务端
python ocr_server.py

# 在另一个终端使用客户端
python ocr_client_real.py
```

## 🎮 游戏应用场景

### 1. 装备属性识别
```python
# 识别装备属性文字
equipment_text = ocr.recognize_text("equipment_tooltip.png")
print("装备属性:", equipment_text)
```

### 2. 任务文字提取
```python
# 提取任务描述
quest_text = ocr.find_target_text("quest_dialog.png", "任务目标")
```

### 3. 游戏状态监控
```python
# 监控游戏状态文字
status_text = ocr.recognize_text("game_ui.png")
```

## ⚙️ 高级配置

### 1. 识别精度调整
```python
ocr = OptimizedOCR(
    det_db_thresh=0.3,      # 文字检测阈值
    det_db_box_thresh=0.5,  # 文字框阈值
    rec_batch_num=6         # 识别批次大小
)
```

### 2. 性能优化
```python
# 启用GPU加速（如果可用）
ocr = OptimizedOCR(use_gpu=True)

# 设置线程数
ocr = OptimizedOCR(cpu_threads=4)
```

### 3. 语言设置
```python
# 设置识别语言
ocr = OptimizedOCR(lang='ch')  # 中文
ocr = OptimizedOCR(lang='en')  # 英文
```

## 📊 性能指标

| 指标 | 数值 | 说明 |
|------|------|------|
| 识别速度 | ~50ms | 单张图片平均处理时间 |
| 准确率 | >95% | 清晰文字识别准确率 |
| 支持格式 | PNG/JPG/BMP | 主流图片格式支持 |
| 内存占用 | ~500MB | 模型加载后内存占用 |

## 🔧 API参考

### OptimizedOCR类

#### 初始化参数
- `use_gpu`: 是否使用GPU加速
- `lang`: 识别语言 ('ch', 'en')
- `det_db_thresh`: 文字检测阈值
- `rec_batch_num`: 识别批次大小

#### 主要方法

**recognize_text(image_path)**
- 识别图片中的所有文字
- 返回: 文字列表，包含文本、位置、置信度

**find_target_text(image_path, target)**
- 查找图片中的特定文字
- 返回: 匹配结果或None

**batch_recognize(image_paths)**
- 批量识别多张图片
- 返回: 批量识别结果

## 🛠️ 故障排除

### 常见问题

1. **识别准确率低**
   - 确保图片清晰度足够
   - 调整检测阈值参数
   - 检查图片对比度

2. **处理速度慢**
   - 启用GPU加速
   - 调整批次大小
   - 优化图片尺寸

3. **内存占用高**
   - 减少批次大小
   - 及时释放不用的图片
   - 使用图片压缩

## 🔗 相关链接

- [PaddleOCR官方文档](https://github.com/PaddlePaddle/PaddleOCR)
- [OpenCV文档](https://docs.opencv.org/)
- [项目主README](./README.md)

## 📄 许可证

本OCR模块遵循项目主许可证。

---

🎯 **OCR模块** - 为游戏自动化提供强大的文字识别能力！
