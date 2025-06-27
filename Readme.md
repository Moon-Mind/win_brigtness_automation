# Brightness Controller

Automatic screen brightness adjustment based on camera input.

## Installation

### Requirements
- Windows 10/11
- Python 3.8+
- Webcam

### Install Steps
1. **Install Python dependencies:**
   ```bash
   pip install opencv-python numpy wmi pystray pillow
   ```

2. **Run the application:**
   ```bash
   python brightness.py
   ```

3. **Look for yellow icon in system tray**

## Usage
- **Right-click tray icon** for menu
- **Settings** - Configure sensitivity (0.1-2.0) and intervals
- **Status** - View current brightness levels
- **Toggle** - Enable/disable auto-adjustment

## Troubleshooting
- **Camera error**: Check webcam connection
- **Brightness error**: Run as Administrator
- **Dependencies**: Reinstall with `pip install -r requirements.txt`
