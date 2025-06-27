import cv2
import numpy as np
import wmi
import time
import threading
import pystray
from PIL import Image, ImageDraw
import tkinter as tk
from tkinter import messagebox

class BrightnessController:
    def __init__(self):
        self.running = True
        self.adjustment_thread = None
        self.min_cam = 20
        self.max_cam = 200
        self.adjustment_interval = 10 * 60  # 10 minutes
        
    def set_brightness(self, level):
        level = max(0, min(100, level))
        try:
            c = wmi.WMI(namespace='wmi')
            methods = c.WmiMonitorBrightnessMethods()[0]
            methods.WmiSetBrightness(level, 0)
        except Exception as e:
            print(f"Error setting brightness: {e}")

    def get_camera_brightness(self, camera_index=0):
        try:
            cap = cv2.VideoCapture(camera_index)  # For IR camera, try index=1
            ret, frame = cap.read()
            if not ret:
                return None
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            brightness = np.mean(gray)  # 0-255 scale
            cap.release()
            return brightness
        except Exception as e:
            print(f"Camera error: {e}")
            return None

    def auto_adjust_brightness(self):
        # Use IR camera (if available) by setting camera_index=1
        brightness = self.get_camera_brightness(camera_index=0)
        if brightness is None:
            print("Camera error")
            return
        
        # Map camera brightness (0-255) to screen brightness (0-100)
        # Adjust these thresholds based on testing
        screen_brightness = np.interp(brightness, [self.min_cam, self.max_cam], [20, 80])
        self.set_brightness(int(screen_brightness) + 30)
        print(f"Camera Brightness: {brightness:.1f}, Screen Brightness Set to: {int(screen_brightness) + 30}")
    
    def brightness_adjustment_loop(self):
        while self.running:
            self.auto_adjust_brightness()
            time.sleep(self.adjustment_interval)
    
    def start_adjustment(self):
        if self.adjustment_thread is None or not self.adjustment_thread.is_alive():
            self.adjustment_thread = threading.Thread(target=self.brightness_adjustment_loop, daemon=True)
            self.adjustment_thread.start()
    
    def stop_adjustment(self):
        self.running = False
        if self.adjustment_thread:
            self.adjustment_thread.join(timeout=1)

class SystemTrayApp:
    def __init__(self):
        self.brightness_controller = BrightnessController()
        
    def show_status(self):
        """Zeigt den aktuellen Status in einem Popup-Fenster"""
        try:
            brightness = self.brightness_controller.get_camera_brightness()
            if brightness is not None:
                messagebox.showinfo("Brightness Controller Status", 
                                  f"Kamera-Helligkeit: {brightness:.1f}\n"
                                  f"Status: {'Aktiv' if self.brightness_controller.running else 'Inaktiv'}")
            else:
                messagebox.showerror("Fehler", "Kamera nicht verfügbar")
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Abrufen des Status: {e}")
    
    def toggle_adjustment(self):
        """Schaltet die automatische Helligkeitsanpassung ein/aus"""
        if self.brightness_controller.running:
            self.brightness_controller.stop_adjustment()
            messagebox.showinfo("Brightness Controller", "Automatische Anpassung gestoppt")
        else:
            self.brightness_controller.running = True
            self.brightness_controller.start_adjustment()
            messagebox.showinfo("Brightness Controller", "Automatische Anpassung gestartet")
    
    def quit_app(self):
        """Beendet die Anwendung"""
        self.brightness_controller.stop_adjustment()
        if hasattr(self, 'icon'):
            self.icon.stop()
    
    def create_icon(self):
        """Erstellt ein Icon für das Systemtray"""
        # Erstelle ein einfaches Icon
        image = Image.new('RGB', (64, 64), color='black')
        draw = ImageDraw.Draw(image)
        draw.ellipse([16, 16, 48, 48], fill='yellow', outline='orange')
        
        return image
    
    def run(self):
        """Startet die Systemtray-Anwendung"""
        # Starte die Helligkeitsanpassung
        self.brightness_controller.start_adjustment()
        
        # Erstelle das Menü für das Systemtray
        menu = pystray.Menu(
            pystray.MenuItem("Status anzeigen", self.show_status),
            pystray.MenuItem("Ein/Aus", self.toggle_adjustment),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Beenden", self.quit_app)
        )
        
        # Erstelle das Icon
        icon_image = self.create_icon()
        self.icon = pystray.Icon("BrightnessController", icon_image, menu=menu)
        self.icon.title = "Brightness Controller"
        
        # Starte das Icon im Systemtray
        self.icon.run()

if __name__ == "__main__":
    app = SystemTrayApp()
    app.run()
