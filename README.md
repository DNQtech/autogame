# OCR服务端-客户端架构

高性能的OCR文字识别服务，采用服务端-客户端架构，支持提前退出优化和模型预加载。

## 🏗️ 项目架构

```
服务端 (独立进程)          客户端 (纯HTTP调用)
┌─────────────────┐       ┌─────────────────┐
│  ocr_server.py  │◄─────►│ocr_client_real.py│
│                 │ HTTP  │                 │
│ • 预加载OCR模型  │       │ • 零模型加载     │
│ • Flask API     │       │ • 启动即用       │
│ • 提前退出优化   │       │ • 网络调用       │
└─────────────────┘       └─────────────────┘
         │
         ▼
┌─────────────────┐
│ ocr_optimized.py│
│                 │
│ • PaddleOCR核心 │
│ • 单例模式      │
│ • 性能优化      │
└─────────────────┘
```

## 📁 文件说明

### 核心文件
- **`ocr_server.py`** - HTTP服务端，预加载模型，提供API接口
- **`ocr_client_real.py`** - 真正的客户端，纯HTTP调用，无模型加载
- **`ocr_optimized.py`** - 优化版OCR核心，支持提前退出
- **`ocr_final.py`** - 基础版OCR脚本（参考用）

### 配置文件
- **`requirements.txt`** - 项目依赖包
- **`start_demo.py`** - 演示启动脚本
- **`game_screenshot.png`** - 测试用游戏截图

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 启动服务端
```bash
python ocr_server.py
```
服务端将：
- 预加载OCR模型（约7-8秒）
- 启动HTTP服务器在 `http://127.0.0.1:5000`
- 等待客户端请求

### 3. 运行客户端
```bash
python ocr_client_real.py
```
客户端将：
- 瞬间启动（无模型加载）
- 连接服务端进行OCR识别
- 演示各种功能

### 4. 使用演示脚本
```bash
python start_demo.py
```

## 🎯 核心优化

### ✅ 1. 耗时统计精确化
- **分离统计**：服务端OCR时间 vs 客户端网络时间
- **透明化**：客户端可查看服务端详细耗时
- **网络开销**：通常仅0.004秒

### ✅ 2. 真正的模型预加载
- **服务端**：模型只加载一次，多客户端复用
- **客户端**：完全无模型依赖，启动即用
- **架构分离**：不同进程，真正解耦

### ✅ 3. 提前退出优化
- **智能终止**：找到目标文字后立即返回
- **效率提升**：节省70.6%的处理时间
- **处理优化**：只处理必要的文字区域

## 📊 性能表现

| 指标 | 数值 | 说明 |
|------|------|------|
| 模型加载 | 7.56秒 | 仅服务端启动时一次 |
| OCR识别 | ~21秒 | 服务端处理时间 |
| 网络开销 | 0.004秒 | 客户端HTTP调用 |
| 提前退出 | 70.6%节省 | 10/34文字处理 |
| 目标识别 | 100%置信度 | "普通明月宝石" |

## 🌟 架构优势

1. **零启动成本** - 客户端无模型加载，启动即用
2. **高效复用** - 服务端模型一次加载，多客户端共享
3. **分布式支持** - 服务端可部署到任意机器
4. **并发处理** - 支持多客户端同时请求
5. **提前优化** - 智能终止，大幅提升效率

## 🔧 API接口

### 健康检查
```http
GET /health
```

### 文字查找
```http
POST /find_text
Content-Type: application/json

{
    "image_path": "path/to/image.png",
    "target_text": "目标文字",
    "early_exit": true
}
```

### 批量查找
```http
POST /batch_find
Content-Type: application/json

{
    "image_path": "path/to/image.png",
    "target_texts": ["文字1", "文字2", "文字3"],
    "early_exit": true
}
```

## 📝 使用示例

### 简单客户端调用

```python
from orc.ocr_client_real import RealOCRClient

# 创建客户端（无模型加载）
client = RealOCRClient()

# 查找游戏物品
result = client.find_game_item("screenshot.png", "普通明月宝石")

if result['success'] and result['target_found']:
    print(f"找到物品: {result['targets'][0]['text']}")
    print(f"置信度: {result['targets'][0]['confidence']:.1%}")
```

## 🛠️ 技术栈

- **OCR引擎**: PaddleOCR
- **Web框架**: Flask
- **HTTP客户端**: Requests
- **图像处理**: OpenCV, NumPy
- **语言**: Python 3.7+

---

🎉 **项目完成** - 高性能OCR服务端-客户端架构，满足所有优化需求！
