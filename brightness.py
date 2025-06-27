import cv2
import numpy as np
import wmi
import time
import threading
import pystray
from PIL import Image, ImageDraw
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import json
import os

class BrightnessController:
    def __init__(self):
        self.running = True
        self.adjustment_thread = None
        self.min_cam = 20
        self.max_cam = 200
        self.adjustment_interval = 10 * 60  # 10 minutes
        self.sensitivity = 1.0  # Sensitivity multiplier (0.1 - 2.0)
        self.config_file = "brightness_config.json"
        self.load_config()
        
    def load_config(self):
        """Lädt die Konfiguration aus einer JSON-Datei"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.sensitivity = config.get('sensitivity', 1.0)
                    self.min_cam = config.get('min_cam', 20)
                    self.max_cam = config.get('max_cam', 200)
                    self.adjustment_interval = config.get('interval', 10 * 60)
        except Exception as e:
            print(f"Error loading config: {e}")
    
    def save_config(self):
        """Speichert die Konfiguration in eine JSON-Datei"""
        try:
            config = {
                'sensitivity': self.sensitivity,
                'min_cam': self.min_cam,
                'max_cam': self.max_cam,
                'interval': self.adjustment_interval
            }
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
        
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
        # Apply sensitivity multiplier to make adjustments more or less aggressive
        base_screen_brightness = np.interp(brightness, [self.min_cam, self.max_cam], [20, 80])
        
        # Apply sensitivity: higher sensitivity = more aggressive adjustments
        adjusted_brightness = base_screen_brightness * self.sensitivity
        final_brightness = max(10, min(100, int(adjusted_brightness) + 30))
        
        self.set_brightness(final_brightness)
        print(f"Camera Brightness: {brightness:.1f}, Sensitivity: {self.sensitivity:.1f}, Screen Brightness Set to: {final_brightness}")
    
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
                                  f"Empfindlichkeit: {self.brightness_controller.sensitivity:.1f}\n"
                                  f"Status: {'Aktiv' if self.brightness_controller.running else 'Inaktiv'}")
            else:
                messagebox.showerror("Fehler", "Kamera nicht verfügbar")
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Abrufen des Status: {e}")
    
    def show_settings(self):
        """Zeigt die Einstellungs-GUI"""
        self.create_settings_window()
    
    def create_settings_window(self):
        """Erstellt ein Einstellungsfenster"""
        settings_window = tk.Toplevel()
        settings_window.title("Brightness Controller - Einstellungen")
        settings_window.geometry("400x300")
        settings_window.resizable(False, False)
        
        # Empfindlichkeit
        tk.Label(settings_window, text="Empfindlichkeit (0.1 - 2.0):", font=("Arial", 10)).pack(pady=5)
        
        sensitivity_frame = tk.Frame(settings_window)
        sensitivity_frame.pack(pady=5)
        
        self.sensitivity_var = tk.DoubleVar(value=self.brightness_controller.sensitivity)
        sensitivity_scale = tk.Scale(sensitivity_frame, from_=0.1, to=2.0, resolution=0.1, 
                                   orient=tk.HORIZONTAL, variable=self.sensitivity_var, length=300)
        sensitivity_scale.pack()
        
        tk.Label(settings_window, text="Niedrig = weniger aggressive Anpassung\nHoch = aggressivere Anpassung", 
                font=("Arial", 8), fg="gray").pack(pady=5)
        
        # Kamera-Grenzwerte
        tk.Label(settings_window, text="Kamera Helligkeit - Minimum:", font=("Arial", 10)).pack(pady=(10,5))
        self.min_cam_var = tk.IntVar(value=self.brightness_controller.min_cam)
        min_cam_scale = tk.Scale(settings_window, from_=10, to=100, orient=tk.HORIZONTAL, 
                               variable=self.min_cam_var, length=300)
        min_cam_scale.pack()
        
        tk.Label(settings_window, text="Kamera Helligkeit - Maximum:", font=("Arial", 10)).pack(pady=(10,5))
        self.max_cam_var = tk.IntVar(value=self.brightness_controller.max_cam)
        max_cam_scale = tk.Scale(settings_window, from_=150, to=255, orient=tk.HORIZONTAL, 
                               variable=self.max_cam_var, length=300)
        max_cam_scale.pack()
        
        # Anpassungsintervall
        tk.Label(settings_window, text="Anpassungsintervall (Minuten):", font=("Arial", 10)).pack(pady=(10,5))
        self.interval_var = tk.IntVar(value=self.brightness_controller.adjustment_interval // 60)
        interval_scale = tk.Scale(settings_window, from_=1, to=60, orient=tk.HORIZONTAL, 
                                variable=self.interval_var, length=300)
        interval_scale.pack()
        
        # Buttons
        button_frame = tk.Frame(settings_window)
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="Speichern", command=lambda: self.save_settings(settings_window), 
                 bg="green", fg="white", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Abbrechen", command=settings_window.destroy, 
                 bg="red", fg="white", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        
        # Fenster zentrieren
        settings_window.transient()
        settings_window.grab_set()
        settings_window.focus_set()
    
    def save_settings(self, window):
        """Speichert die Einstellungen"""
        try:
            # Einstellungen übernehmen
            self.brightness_controller.sensitivity = self.sensitivity_var.get()
            self.brightness_controller.min_cam = self.min_cam_var.get()
            self.brightness_controller.max_cam = self.max_cam_var.get()
            self.brightness_controller.adjustment_interval = self.interval_var.get() * 60
            
            # Konfiguration speichern
            self.brightness_controller.save_config()
            
            # Fenster schließen
            window.destroy()
            
            messagebox.showinfo("Erfolg", "Einstellungen wurden gespeichert!")
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Speichern: {e}")
    
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
            pystray.MenuItem("Einstellungen", self.show_settings),
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
