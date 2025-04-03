#!/usr/bin/env python3

import sys
import os
import time
import threading
import logging
import netifaces
from view import MainView
from ethernet import L2Ethernet
from processing import process_image
from sending import send_single_frame_sync
from utils import init_frames
from marquee_manager import MarqueeEngine
from lru_cache import LRUCache
from thread_manager import ThreadManager

# Konfiguration des Loggings:
# - level: DEBUG (alle Debug-, Info-, Warnungs- und Fehlermeldungen werden protokolliert)
# - format: Enthält Datum, Uhrzeit, Log-Level und Nachricht
# - handlers: Loggt in die Datei  und in die Standardausgabe 
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("debug_log.txt", mode='a'),
        logging.StreamHandler(sys.stdout)
    ]
)

class LEDController:
    def __init__(self, view: MainView):
        self.view = view                        # Aggregation: Externe GUI (View)
        self.l2 = None                          # Wird später als Layer2 Ethernet-Objekt initialisiert
        self.columns = 128                      # Standard-Auflösung
        self.rows = 128                         # Standard-Auflösung
        
        self.thread_mgr = ThreadManager()       # Manager für allgemeine Threads
        self.send_mgr = ThreadManager()         # Manager für Sende-Threads
        self.marquee = None                     # Aggregation: Externe MarqueeEngine wird später gesetzt
        
        # Leistungsüberwachung
        self.bandwidth = 0
        self.frame_count = 0
        self.total_frame_time = 0.0
        self._perf_lock = threading.Lock()    # Lock für atomare Operationen auf den Performance-Daten
        self._perf_stop_event = threading.Event()
        self._perf_monitor = None

        # Komposition: Interner Cache und Bildpfad-Liste, die nur von LEDController verwaltet werden
        self.image_cache = LRUCache()
        self.image_paths = []
        self.current_image = 0

        self._setup_ui_callbacks()              
        self._refresh_interfaces()              # Netzwerkschnittstellen aktualisieren

    def _setup_ui_callbacks(self):              # GUI-Callbacks mit Funktionen verbinden
        self.view.refresh_button.config(command=self._refresh_interfaces)
        self.view.browse_button.config(command=self.browse_images)
        self.view.send_button.config(command=lambda: self.send_current_image(auto_play=False))
        self.view.prev_button.config(command=self.show_previous_image)
        self.view.next_button.config(command=self.show_next_image)
        self.view.detect_button.config(command=lambda: self.thread_mgr.start_thread(self._detect_card))
        self.view.auto_play_button.config(command=self.start_auto_play)
        self.view.stop_auto_button.config(command=self.stop_sending)
        self.view.show_marquee_dialog_button.config(command=self.show_marquee_dialog)
        self.view.start_marquee_button.config(command=self.start_marquee)
        self.view.quit_button.config(command=self.quit_app)
        
    def _refresh_interfaces(self):
        interfaces = netifaces.interfaces()
        self.view.interface_combo['values'] = interfaces
   
    def _detect_card(self, stop_event):
        interface = self.view.interface_combo.get()
        if not interface:
            self.view.show_warning("Please select a network interface.")
            return
        try:
            self.l2 = L2Ethernet(interface)    # Erzeugt ein Layer2 Ethernet-Objekt
            self.l2.open()                      # Öffnet den Socket
            if self.l2.socket is None:
                raise Exception("Failed to initialize network socket for L2Ethernet.")
            src_mac = bytes.fromhex(self.view.src_mac_var.get().replace(":", ""))
            dst_mac = bytes.fromhex(self.view.dst_mac_var.get().replace(":", ""))
            detection_packet = b'\x00' * 270
            self.l2.send(dst_mac, src_mac, 0x0700, detection_packet)
            data = self.l2.recv()
            if len(data) > 38 and data[12] == 8 and data[13] == 5:
                self.columns = data[34] * 256 + data[35]
                self.rows = data[36] * 256 + data[37]
                self.view.show_status("Card Detected!")
            init_frames(self.columns, self.view.brightness_var.get())
        except Exception as e:
            self.view.show_error("Error", str(e))
            logging.error(f"Error in card detection: {e}")

    def _get_frame_data(self, path):  
        # Lädt und verarbeitet Bilddaten; nutzt den Cache, falls vorhanden
        frame_data = self.image_cache.get(path)
        if frame_data is None:
            frame_data = process_image(path, self.columns, self.rows)
            self.image_cache.put(path, frame_data)
            if frame_data is None:
                raise ValueError(f"Frame data for {path} is None after processing.")
        return frame_data
    
    def browse_images(self):
        # Bilder aussuchen und vorbereiten für verarbeitung => Komposition da interne Verwaltung der Bildpfade)
        file_paths = self.view.prompt_file_paths()
        if file_paths:
            self.image_paths = list(file_paths)
            self.current_image = 0
            self.view.show_info("Images Loaded", f"{len(self.image_paths)} images selected.")
            for path in self.image_paths:
                self._get_frame_data(path)

    def show_previous_image(self):
        if not self.image_paths:
            self.view.show_warning("No images loaded.")
            return
        self.thread_mgr.stop_all()  # Stoppt laufende Threads  => erfordelich um ein anders inhalt zu senden
        self.current_image = (self.current_image - 1) % len(self.image_paths)  #index - 1
        self.send_current_image(auto_play=False)

    def show_next_image(self):
        if not self.image_paths:
            self.view.show_warning("No images loaded.")
            return
        self.thread_mgr.stop_all()  # Stoppt laufende Threads => erfordelich um ein anders inhalt zu senden
        self.current_image = (self.current_image + 1) % len(self.image_paths) #index + 1
        self.send_current_image(auto_play=False)

    def send_current_image(self, auto_play=False):
        if not self.l2 or not hasattr(self.l2, 'socket') or self.l2.socket is None:
            self.view.show_warning("Please detect the card first.")
            return
        if not (0 <= self.current_image < len(self.image_paths)):
            return
        file_path = self.image_paths[self.current_image]
        self.view.show_status(f"Sending: {os.path.basename(file_path)}") #zeigen welches bild ist gesendet
        frame_data = self._get_frame_data(file_path)
        self.send_mgr.stop_all()
        self.send_mgr.start_thread(self._send_image, frame_data, auto_play)

    def _send_image(self, stop_event, frame_data, auto_play=False):  
        try:
            self.start_perf_monitor()     #thread starten beim senden
            target_interval = 1 / 60      # Gewünschte Framerate
            brightness = self.view.brightness_var.get()
            src_mac = bytes.fromhex(self.view.src_mac_var.get().replace(":", ""))
            dst_mac = bytes.fromhex(self.view.dst_mac_var.get().replace(":", ""))
            compensation = 0.0            # Initiale Kompensation

            while not stop_event.is_set():
                frame_start = time.monotonic()
                sent = send_single_frame_sync(
                    self.l2, src_mac, dst_mac,
                    brightness, frame_data,
                    self.columns, self.rows
                )
                self._update_stats(sent, time.monotonic() - frame_start)
                elapsed = time.monotonic() - frame_start    
                wait_time = max(0, target_interval - elapsed - compensation) # tatsächliche Wartezeit
                sleep_start_time = time.monotonic()
                if stop_event.wait(wait_time):
                    break
                sleep_end_time = time.monotonic()
                actual_sleep_duration = sleep_end_time - sleep_start_time
                compensation = actual_sleep_duration - wait_time
        except Exception as e:
            logging.error(f"Transmission error: {e}")
            self.view.show_error("Send Failed", str(e))
        finally:
            self.stop_perf_monitor()

    def start_auto_play(self):
        if not self.image_paths:
            self.view.show_warning("No images loaded.")
            return
        self.auto_play_active = True
        self.thread_mgr.start_thread(self._auto_play_thread)

    def _auto_play_thread(self, stop_event):
        while self.auto_play_active and not stop_event.is_set():
            self.send_mgr.stop_all()
            self.current_image = (self.current_image + 1) % len(self.image_paths)
            self.send_current_image(auto_play=True)
            if stop_event.wait(0.08):       # autoplay abstand
                break

    def stop_auto_play(self):
        self.auto_play_active = False
        self.thread_mgr.stop_all()

    def show_marquee_dialog(self):
                                            # Aggregation: Erhält Konfigurationsparameter aus der externen GUI
        config = self.view.prompt_marquee_config()
        if not config:
            return
                                            # Aggregation: Erstellt ein MarqueeEngine-Objekt, das externe Abhängigkeiten nutzt
        self.marquee = MarqueeEngine(
            self,
            config["text"],
            config["font_size"],
            config["text_color"],
            config["bg_color"],
            config["direction"],
            config["margin_x"],
            config["margin_y"],
            config["speed"]
        )
        self.view.show_status("Marquee configured.")

    def start_marquee(self):
        if not self.marquee:
            self.view.show_warning("Please configure marquee first.")
            return
        self.thread_mgr.stop_all()
        self.marquee.start()
        self.view.show_status("Marquee started.")

    def stop_sending(self):                         
        self.thread_mgr.stop_all()
        self.send_mgr.stop_all()
        self.stop_perf_monitor()
        self.view.show_status("Stopped.")

    def quit_app(self):
                                                     # Sorgt dafür, dass alle Threads und Verbindungen sauber beendet werden (sicheres Stoppen)
        self.stop_auto_play()
        self.stop_sending()
        self.thread_mgr.stop_all()
        if self.l2:
            try:
                self.l2.close()
            except Exception as e:
                logging.error(f"Error closing L2Ethernet socket: {e}")
        self.view.root.quit()
        self.view.root.destroy()

    def _update_stats(self, bytes_sent, frame_time):
                                                     # Atomare Aktualisierung der Performance-Statistiken
        with self._perf_lock:                        # Sperrt den Zugriff auf die Performance-Daten um eine atomare operation
            self.bandwidth += bytes_sent             # daten schreiben
            self.frame_count += 1
            self.total_frame_time += frame_time

    def _monitor_performance(self, stop_event):
        while not self._perf_stop_event.wait(1):
            with self._perf_lock:                   # Sperrt den Zugriff auf die Performance-Daten
                bytes_this_sec = self.bandwidth     # daten lesen
                frames_this_sec = self.frame_count
                self.bandwidth = 0                  # reset zähler 
                self.frame_count = 0
                self.total_frame_time = 0.0
            bits_per_sec = bytes_this_sec * 8
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            log_line = (f"[Performance] {timestamp}: {bytes_this_sec} bytes/s, "
                        f"{bits_per_sec} bps, {frames_this_sec} fps")
            logging.debug(log_line)
            self.view.update_performance(
                f"FPS: {frames_this_sec} | Bytes/s: {bytes_this_sec} | BPS: {bits_per_sec}"
            )
            with open("performance_log.txt", "a") as f:
                f.write(log_line + "\n")
        self.view.update_performance("")
        logging.debug("Performance monitoring stopped.")

    def start_perf_monitor(self):                 #thread_starten
        if self._perf_monitor and self._perf_monitor.is_alive():
            return
        self._perf_stop_event.clear()
        self._perf_monitor = self.thread_mgr.start_thread(self._monitor_performance)

    def stop_perf_monitor(self):
        self._perf_stop_event.set()
        if self._perf_monitor:
            self._perf_monitor.join(timeout=1)
            self._perf_monitor = None
