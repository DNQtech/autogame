# 🔤 OCR Text Recognition Module

This project includes a high-performance OCR (Optical Character Recognition) module based on PaddleOCR engine, specifically designed for game text recognition and processing.

## ✨ Core Features

- 🚀 **High Performance Recognition** - Advanced deep learning models based on PaddleOCR
- 🎯 **Game Optimized** - Specifically optimized for game interface text recognition
- ⚡ **Fast Response** - Optimized processing pipeline with millisecond-level response
- 🔍 **Precise Positioning** - Accurate text location and bounding box detection
- 🌐 **Multi-language Support** - Supports Chinese, English and other languages
- 🛠️ **Easy Integration** - Simple API interface, easy to integrate into other projects

## 📁 Module Files

### Core Files
- **`ocr_optimized.py`** - Optimized OCR core engine
- **`ocr_server.py`** - OCR HTTP server
- **`ocr_client_real.py`** - OCR client interface
- **`ocr_final.py`** - Basic OCR implementation

### Configuration Files
- **`requirements.txt`** - OCR module dependencies
- **`start_demo.py`** - OCR functionality demo script

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install paddlepaddle paddleocr opencv-python pillow numpy
```

### 2. Basic Usage
```python
from ocr_optimized import OptimizedOCR

# Create OCR instance
ocr = OptimizedOCR()

# Recognize text in image
result = ocr.recognize_text("screenshot.png")

# Find specific text
target_found = ocr.find_target_text("screenshot.png", "target text")
if target_found:
    print(f"Found target text: {target_found['text']}")
    print(f"Position: {target_found['bbox']}")
    print(f"Confidence: {target_found['confidence']}")
```

### 3. Server Mode
```bash
# Start OCR server
python ocr_server.py

# Use client in another terminal
python ocr_client_real.py
```

## 🎮 Game Application Scenarios

### 1. Equipment Attribute Recognition
```python
# Recognize equipment attribute text
equipment_text = ocr.recognize_text("equipment_tooltip.png")
print("Equipment attributes:", equipment_text)
```

### 2. Quest Text Extraction
```python
# Extract quest description
quest_text = ocr.find_target_text("quest_dialog.png", "quest objective")
```

### 3. Game Status Monitoring
```python
# Monitor game status text
status_text = ocr.recognize_text("game_ui.png")
```

## ⚙️ Advanced Configuration

### 1. Recognition Accuracy Adjustment
```python
ocr = OptimizedOCR(
    det_db_thresh=0.3,      # Text detection threshold
    det_db_box_thresh=0.5,  # Text box threshold
    rec_batch_num=6         # Recognition batch size
)
```

### 2. Performance Optimization
```python
# Enable GPU acceleration (if available)
ocr = OptimizedOCR(use_gpu=True)

# Set thread count
ocr = OptimizedOCR(cpu_threads=4)
```

### 3. Language Settings
```python
# Set recognition language
ocr = OptimizedOCR(lang='ch')  # Chinese
ocr = OptimizedOCR(lang='en')  # English
```

## 📊 Performance Metrics

| Metric | Value | Description |
|--------|-------|-------------|
| Recognition Speed | ~50ms | Average processing time per image |
| Accuracy | >95% | Recognition accuracy for clear text |
| Supported Formats | PNG/JPG/BMP | Mainstream image format support |
| Memory Usage | ~500MB | Memory usage after model loading |

## 🔧 API Reference

### OptimizedOCR Class

#### Initialization Parameters
- `use_gpu`: Whether to use GPU acceleration
- `lang`: Recognition language ('ch', 'en')
- `det_db_thresh`: Text detection threshold
- `rec_batch_num`: Recognition batch size

#### Main Methods

**recognize_text(image_path)**
- Recognize all text in image
- Returns: Text list with content, position, confidence

**find_target_text(image_path, target)**
- Find specific text in image
- Returns: Match result or None

**batch_recognize(image_paths)**
- Batch recognize multiple images
- Returns: Batch recognition results

## 🛠️ Troubleshooting

### Common Issues

1. **Low Recognition Accuracy**
   - Ensure sufficient image clarity
   - Adjust detection threshold parameters
   - Check image contrast

2. **Slow Processing Speed**
   - Enable GPU acceleration
   - Adjust batch size
   - Optimize image dimensions

3. **High Memory Usage**
   - Reduce batch size
   - Release unused images promptly
   - Use image compression

## 🔗 Related Links

- [PaddleOCR Official Documentation](https://github.com/PaddlePaddle/PaddleOCR)
- [OpenCV Documentation](https://docs.opencv.org/)
- [Main Project README](./README_EN.md)

## 📄 License

This OCR module follows the main project license.

---

🎯 **OCR Module** - Providing powerful text recognition capabilities for game automation!
