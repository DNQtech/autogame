# 📖 Game Automation System - Usage Guide

<div align="center">

[![Usage Guide](https://img.shields.io/badge/Usage_Guide-English-blue?style=for-the-badge)](./Usage_Guide_EN.md)
[![使用指南](https://img.shields.io/badge/使用指南-中文-green?style=for-the-badge)](./使用指南.md)
[![Project Home](https://img.shields.io/badge/Project_Home-English-purple?style=for-the-badge)](./README_EN.md)
[![项目主页](https://img.shields.io/badge/项目主页-中文-purple?style=for-the-badge)](./README.md)

---

</div>

This guide provides detailed instructions for setting up, configuring, and using the Game Automation System.

## 🛠️ Environment Setup

### System Requirements
- **Operating System**: Windows 10/11
- **Python Version**: 3.8 or higher
- **Screen Resolution**: 1920x1080 (recommended)
- **Memory**: At least 2GB available RAM
- **Game Requirements**: Game window must be visible and accessible

### Python Environment Setup
1. **Install Python**
   ```bash
   # Download from https://python.org
   # Ensure Python is added to PATH during installation
   ```

2. **Create Virtual Environment (Recommended)**
   ```bash
   python -m venv game_automation_env
   game_automation_env\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Dependency Package Details
```
opencv-python==4.8.1.78    # Image processing and template matching
mss==9.0.1                 # High-performance screen capture
pyautogui==0.9.54          # Mouse and keyboard automation
keyboard==0.13.5           # Global hotkey monitoring
numpy==1.24.3              # Numerical computation support
pillow==10.0.1             # Image format processing
```

## 🎯 Equipment Template Preparation

### Template Creation Process

1. **Capture Equipment Icons**
   - Use game's built-in screenshot function or Windows Snipping Tool
   - Capture clear, unobstructed equipment icons
   - Ensure icons are complete without cropping

2. **Image Processing**
   - Save as PNG format (recommended)
   - Maintain original size and proportions
   - Avoid compression that reduces image quality

3. **Template Storage**
   ```
   templates/
   ├── sword_icon.png      # Weapon template
   ├── armor_icon.png      # Armor template
   ├── accessory_icon.png  # Accessory template
   └── ...                 # More equipment templates
   ```

### Template Quality Requirements
- **Clarity**: Icons should be sharp and clear
- **Completeness**: Include complete equipment icon
- **Uniqueness**: Each template should represent a distinct equipment type
- **Size**: Recommended 20x20 to 100x100 pixels

## 🚀 System Startup

### Basic Startup
```bash
# Navigate to project directory
cd d:\ggc\projects\only

# Start the automation system
python start_game.py
```

### Startup Process
1. **Initialization Phase**
   ```
   🔧 [System] Initializing Game Automation System...
   📁 [Template] Loading equipment templates from templates/
   ✅ [Template] Loaded 3 equipment templates
   ```

2. **Thread Startup**
   ```
   🚀 [Equipment Monitor] Starting equipment detection thread...
   ⚔️ [Combat System] Auto combat system ready
   ⌨️ [Keyboard] Hotkey listener activated
   ```

3. **System Ready**
   ```
   ✅ [System Status] Equipment Detection Normal | Auto Combat Normal | Auto Pickup Ready
   🎮 System is now running! Press Ctrl+C or Ctrl+Q to exit
   ```

## ⚙️ Configuration Parameters

### Movement System Configuration
```python
# In start_game.py, modify these parameters:

# Movement radius (pixels from screen center)
game_controller.set_movement_radius(150)  # Default: 150

# Maximum random moves before returning
game_controller.set_max_random_moves(30)  # Default: 30
```

### Combat System Configuration
```python
# Combat timing intervals
game_controller.set_fight_intervals(
    move_interval=2.0,    # Seconds between movements
    attack_interval=1.5   # Seconds between attacks
)

# Pickup system
pickup_safe_distance = 50  # Pixels - minimum distance for direct pickup
```

### Detection System Configuration
```python
# In template_equipment_detector.py:

# Detection frequency
fps = 20  # Detections per second

# Template matching threshold
threshold = 0.8  # Similarity threshold (0.0-1.0)
```

## 🎮 Practical Usage Examples

### Example 1: Basic Auto-Combat
```
Scenario: Character needs to farm monsters in a specific area

1. Position character in desired farming location
2. Start system: python start_game.py
3. System will:
   - Move randomly within configured radius
   - Attack at regular intervals
   - Monitor for equipment drops
   - Automatically pickup any detected equipment

Status Output:
🔍 [Equipment Detection] Continuously monitoring equipment drops... (1247 detections)
⚔️ [Combat] Random movement to (960, 540) - Move #15
🎯 [Combat] Executing attack skill at (1200, 650)
```

### Example 2: Equipment Drop Response
```
Scenario: Equipment drops during combat

1. System detects equipment drop:
   🎯 [Equipment Found] Found 1 equipment at position (1150, 680)!

2. Combat system pauses:
   ⏸️ [Combat System] Pausing auto combat for equipment pickup

3. Pickup process:
   📦 [Equipment Pickup] Distance to equipment: 89 pixels
   📦 [Equipment Pickup] Moving to equipment position...
   📦 [Equipment Pickup] Pickup completed!

4. Combat resumes:
   ▶️ [Combat System] Resume auto combat
```

### Example 3: System Recovery
```
Scenario: Detection thread encounters an error

1. Error occurs:
   ❌ [DETECTOR] Detection loop error: Screen capture failed

2. Auto recovery:
   🔄 [Equipment Monitor] Detector stopped, restarting...
   🚀 [Equipment Monitor] Equipment detector restarted successfully

3. Normal operation resumes:
   ✅ [Equipment Detection] Normal operation... 1 detection completed
```

## 🔧 Advanced Configuration

### Custom Movement Patterns
```python
# Modify movement behavior in start_game.py

def custom_movement_pattern(self):
    """Custom movement strategy"""
    # Example: Square pattern movement
    positions = [
        (960 + 100, 540),      # Right
        (960 + 100, 540 + 100), # Down-Right
        (960, 540 + 100),       # Down
        (960 - 100, 540 + 100), # Down-Left
        (960 - 100, 540),       # Left
        (960 - 100, 540 - 100), # Up-Left
        (960, 540 - 100),       # Up
        (960 + 100, 540 - 100)  # Up-Right
    ]
    
    for pos in positions:
        get_controller().move_character(pos[0], pos[1])
        time.sleep(2)
```

### Multi-Template Detection
```python
# Add multiple templates for the same equipment type
templates/
├── sword_1.png
├── sword_2.png
├── sword_3.png
└── armor_rare.png
```

### Performance Optimization
```python
# Adjust detection frequency based on system performance
if system_performance == "high":
    fps = 30  # Higher detection rate
elif system_performance == "medium":
    fps = 20  # Balanced performance
else:
    fps = 10  # Lower CPU usage
```

## 🛠️ Troubleshooting

### Common Issues and Solutions

#### 1. Equipment Not Detected
**Problem**: System doesn't detect equipment drops
**Solutions**:
- Verify template images are in `templates/` directory
- Check template image quality and clarity
- Ensure templates match actual in-game equipment icons
- Lower detection threshold if needed

#### 2. Movement Not Working
**Problem**: Character doesn't move as expected
**Solutions**:
- Ensure game window is active and in foreground
- Check screen resolution matches system expectations (1920x1080)
- Verify PyAutoGUI is not blocked by game's anti-cheat
- Adjust movement coordinates in code

#### 3. High CPU Usage
**Problem**: System uses too much CPU
**Solutions**:
- Reduce detection FPS: `fps = 10`
- Increase sleep intervals in combat loop
- Close unnecessary background applications
- Use lower resolution templates

#### 4. Frequent Thread Restarts
**Problem**: Detection thread restarts frequently
**Solutions**:
- Check for memory leaks in detection loop
- Ensure stable screen capture
- Review error logs for specific issues
- Update graphics drivers

### Debug Mode
Enable detailed logging for troubleshooting:
```python
# In start_game.py, add:
import logging
logging.basicConfig(level=logging.DEBUG)

# This will show detailed operation logs
```

### Performance Monitoring
```python
# Monitor system performance
def monitor_performance():
    import psutil
    cpu_usage = psutil.cpu_percent()
    memory_usage = psutil.virtual_memory().percent
    print(f"CPU: {cpu_usage}% | Memory: {memory_usage}%")
```

## 📊 System Monitoring

### Status Indicators
| Indicator | Meaning | Action Required |
|-----------|---------|-----------------|
| ✅ Normal | System operating correctly | None |
| 🔍 Monitoring | Actively scanning for equipment | None |
| 🎯 Found | Equipment detected | System handles automatically |
| 📦 Pickup | Pickup in progress | Wait for completion |
| ⚔️ Combat | Combat operations active | None |
| ❌ Error | System error occurred | Check logs, may auto-recover |
| 🔄 Restart | Component restarting | Wait for completion |

### Log Analysis
Monitor console output for:
- Detection frequency and success rate
- Movement and attack timing
- Error patterns and recovery
- Performance metrics

## 🔒 Safety Considerations

### Game Compatibility
- Ensure automation complies with game's terms of service
- Some games may have anti-automation measures
- Use responsibly and ethically

### System Safety
- Monitor system resource usage
- Don't leave system running unattended for extended periods
- Regular breaks to prevent hardware stress

### Data Safety
- Keep backup copies of template images
- Document custom configuration changes
- Regular system maintenance and updates

## 📈 Performance Optimization Tips

1. **Template Optimization**
   - Use high-quality, distinctive templates
   - Remove similar or duplicate templates
   - Optimize template file sizes

2. **System Optimization**
   - Close unnecessary applications
   - Use SSD for faster file access
   - Ensure adequate RAM availability

3. **Detection Optimization**
   - Adjust FPS based on system capability
   - Use appropriate detection thresholds
   - Monitor CPU and memory usage

## 🎯 Best Practices

1. **Template Management**
   - Organize templates by equipment type
   - Use descriptive filenames
   - Regular template quality review

2. **System Operation**
   - Start with conservative settings
   - Gradually optimize based on performance
   - Regular monitoring and adjustment

3. **Maintenance**
   - Regular system updates
   - Template library updates
   - Performance monitoring and optimization

---

🎮 **Happy Gaming!** This automation system is designed to enhance your gaming experience while maintaining system stability and performance.
