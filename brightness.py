import cv2
import numpy as np
import wmi
import time

def set_brightness(level):
    level = max(0, min(100, level))
    c = wmi.WMI(namespace='wmi')
    methods = c.WmiMonitorBrightnessMethods()[0]
    methods.WmiSetBrightness(level, 0)

def get_camera_brightness(camera_index=0):
    cap = cv2.VideoCapture(camera_index)  # For IR camera, try index=1
    ret, frame = cap.read()
    if not ret:
        return None
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    brightness = np.mean(gray)  # 0-255 scale
    cap.release()
    return brightness

def auto_adjust_brightness():
    # Use IR camera (if available) by setting camera_index=1
    brightness = get_camera_brightness(camera_index=0)
    if brightness is None:
        print("Camera error")
        return
    
    # Map camera brightness (0-255) to screen brightness (0-100)
    # Adjust these thresholds based on testing
    min_cam, max_cam = 20, 200  # Tune for your environment
    screen_brightness = np.interp(brightness, [min_cam, max_cam], [20, 80])
    set_brightness(int(screen_brightness)+30)
    print(f"Camera Brightness: {brightness}, Screen Brightness Set to: {int(screen_brightness)+50}")

# Run continuously
while True:
    auto_adjust_brightness()
    time_long = 10*60  # Adjust every 10 minutes
    time.sleep(time_long)  # Adjust every 10 seconds
