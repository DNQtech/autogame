# 🎮 Game Automation System

An intelligent game automation solution supporting equipment detection, auto-combat, and smart pickup features. Built with multi-threading architecture for high stability and user-friendly operation experience.

## ✨ Core Features

- 🔍 **Smart Equipment Detection** - High-precision equipment recognition based on OpenCV template matching
- ⚔️ **Auto Combat System** - Intelligent random movement + timed attack strategy
- 📦 **Smart Equipment Pickup** - Nearest-priority equipment pickup algorithm
- 🎯 **Real-time Status Monitoring** - Clear system status indicators and operation feedback
- 🔄 **Auto Error Recovery** - Thread auto-restart and exception handling mechanisms
- ⚙️ **Highly Configurable** - Support for movement radius, attack intervals and other parameter adjustments

## 🏗️ System Architecture

```
Game Automation System
┌─────────────────────────────────────────────────────────┐
│                    start_game.py                        │
│                   (Main Controller)                     │
├─────────────────┬─────────────────┬─────────────────────┤
│ Equipment       │    Combat       │   Keyboard          │
│ Monitor Thread  │  Control Thread │ Listener Thread     │
│                 │                 │                     │
│ • Detector      │ • Random        │ • Hotkey            │
│   Startup       │   Movement      │   Monitoring        │
│ • Status        │ • Attack Skill  │ • Program Exit      │
│   Monitoring    │   Release       │   Control           │
│ • Auto Restart  │ • Equipment     │                     │
│                 │   Pickup Pause  │                     │
└─────────────────┴─────────────────┴─────────────────────┘
         │                    │
         ▼                    ▼
┌─────────────────┐   ┌─────────────────┐
│Equipment        │   │Mouse & Keyboard │
│Detector Module  │   │Controller       │
│                 │   │                 │
│• Template       │   │• Mouse          │
│  Matching       │   │  Move/Click     │
│• Screen         │   │• Keyboard       │
│  Capture        │   │  Simulation     │
│• Multi-scale    │   │• Character      │
│  Detection      │   │  Movement       │
│• Result         │   │  Control        │
│  Callback       │   │                 │
└─────────────────┘   └─────────────────┘
```

## 📁 Project Structure

### Core Files
- **`start_game.py`** - Main program entry, game controller core logic
- **`template_equipment_detector.py`** - Equipment detector based on template matching
- **`mouse_keyboard_controller.py`** - Mouse and keyboard controller
- **`requirements.txt`** - Project dependency list

### Configuration Directory
- **`templates/`** - Equipment template image storage directory
  - `image.png` - Equipment template 1 (72x31 pixels)
  - `img.png` - Equipment template 2 (37x54 pixels)

### Documentation
- **`README.md`** - Project documentation (Chinese)
- **`README_EN.md`** - Project documentation (English)
- **`使用指南.md`** - Detailed usage guide (Chinese)
- **`Usage_Guide_EN.md`** - Detailed usage guide (English)
- **`OCR_README.md`** - OCR module introduction (Chinese)
- **`OCR_README_EN.md`** - OCR module introduction (English)

## 🚀 Quick Start

### 1. Environment Requirements
- Python 3.8+
- Windows Operating System
- 1920x1080 resolution display (recommended)

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Prepare Equipment Templates
Save game equipment icon screenshots to `templates/` directory in PNG format.

### 4. Start System
```bash
python start_game.py
```

System will:
- Initialize equipment detector and load templates
- Start multi-threading monitoring system
- Begin automated game process
- Display real-time status information

## 🎯 System Features

### ✅ 1. Smart Equipment Detection
- **High Precision Recognition**: Based on OpenCV template matching with multi-scale detection support
- **Real-time Monitoring**: 20FPS high-frequency scanning for timely equipment drop detection
- **Auto Restart**: Automatic recovery when detector encounters exceptions, ensuring continuous operation

### ✅ 2. Robust Combat System
- **Smart Movement**: Random movement strategy based on screen coordinates
- **Configurable Parameters**: Adjustable movement radius, attack intervals, movement count, etc.
- **Combat Pause**: Automatically pause combat when equipment is found, prioritize pickup

### ✅ 3. Smart Pickup Algorithm
- **Nearest Priority**: Automatically select equipment closest to character
- **Path Optimization**: Intelligently determine if movement to equipment position is needed
- **Safe Pickup**: Ensure pickup process is not interrupted by other operations

## 📊 System Status Indicators

During operation, you will see clear status information:

| Status Type | Display Example | Description |
|-------------|-----------------|-------------|
| System Normal | ✅ [System Status] Equipment Detection Normal \| Auto Combat Normal \| Auto Pickup Ready | All functions operating normally |
| Equipment Detection | 🔍 [Equipment Detection] Continuously monitoring equipment drops... | Detector working normally |
| Equipment Found | 🎯 [Equipment Found] Found 1 equipment! | Equipment drop detected |
| Equipment Pickup | 📦 [Equipment Pickup] Pickup completed! | Equipment pickup successful |
| Combat System | ▶️ [Combat System] Resume auto combat | Combat status change |

## 🌟 System Advantages

1. **High Stability** - Multi-threading architecture with automatic exception recovery
2. **User Friendly** - Clear status indicators and operation feedback
3. **Highly Configurable** - Support for multiple parameter customizations
4. **High Intelligence** - Automatic optimal operation strategy judgment
5. **Low Resource Usage** - Optimized algorithms and memory management

## ⚙️ Configuration Parameters

System supports the following parameter configurations (adjustable in code):

```python
# Movement system configuration
game_controller.set_movement_radius(150)        # Movement radius (pixels)
game_controller.set_max_random_moves(30)        # Maximum random movement count

# Combat system configuration
game_controller.set_fight_intervals(2.0, 1.5)   # Movement interval, attack interval (seconds)

# Pickup system configuration
pickup_safe_distance = 50                       # Safe pickup distance (pixels)
```

## 🎮 Operation Instructions

### Starting System
1. Ensure game window is visible and in foreground
2. Run `python start_game.py`
3. Observe console status information
4. System will automatically begin working

### Stopping System
- Press `Ctrl+C` or `Ctrl+Q` to safely stop
- System will automatically clean up resources and exit

### Adding Equipment Templates
1. Capture equipment icons in game
2. Save as PNG format to `templates/` directory
3. Restart system to load new templates

## 🛠️ Technology Stack

- **Image Processing**: OpenCV, NumPy
- **Screen Capture**: MSS (Multi-Screen Shot)
- **Input Control**: PyAutoGUI
- **Multi-threading**: Python Threading
- **Keyboard Monitoring**: Keyboard
- **Language**: Python 3.8+

## 🔧 Troubleshooting

### Common Issues

1. **Equipment Detection Not Working**
   - Check if `templates/` directory has equipment templates
   - Confirm template images match game equipment icons
   - Adjust detection threshold or add more templates

2. **Movement or Attack Not Responding**
   - Ensure game window is in foreground
   - Check if screen resolution is 1920x1080
   - Adjust movement and attack coordinate parameters

3. **System Frequent Restarts**
   - Check for interference from other programs
   - Confirm sufficient system resources
   - Review console error messages

## 📞 Technical Support

If you encounter issues, please:
1. Review detailed error information in console output
2. Check system environment and dependency package versions
3. Refer to troubleshooting section solutions

---

🎉 **Game Automation System** - Intelligent, stable, and efficient game assistance solution!
