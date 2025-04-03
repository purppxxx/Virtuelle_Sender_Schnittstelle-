#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog, colorchooser

class MainView:
    def __init__(self, root):
        # Initialisierung des Hauptfensters
        self.root = root
        self.root.title("Colorlight Image Player (MVC)")
        self.root.geometry("1000x750")
        
        # Variablen für MAC-Adressen und Helligkeit
        self.src_mac_var = tk.StringVar(value="22:22:33:44:55:66")
        self.dst_mac_var = tk.StringVar(value="11:22:33:44:55:66")
        self.brightness_var = tk.IntVar(value=50)
        
        # Aufbau der Benutzeroberfläche
        self.create_widgets()

    def create_widgets(self):
        """Erstellt und ordnet alle GUI-Elemente an."""
        # Oberer Bereich: Netzwerkschnittstelle und MAC-Adressen
        self.interface_frame = ttk.Frame(self.root)
        self.interface_frame.pack(pady=10, fill=tk.X)
        # Beschriftung für die Netzwerkschnittstelle
        ttk.Label(self.interface_frame, text="Select Network Interface:").pack(side=tk.LEFT, padx=10)
        # Dropdown-Menü zur Auswahl der Netzwerkschnittstelle
        self.interface_combo = ttk.Combobox(self.interface_frame, state="readonly")
        self.interface_combo.pack(side=tk.LEFT, padx=5, expand=True)
        # Button zum Aktualisieren der Schnittstellen
        self.refresh_button = ttk.Button(self.interface_frame, text="Refresh")
        self.refresh_button.pack(side=tk.LEFT, padx=10)

        # Bereich für MAC-Adressen
        mac_frame = ttk.LabelFrame(self.root, text="MAC Addresses")
        mac_frame.pack(pady=10, fill=tk.X)
        # Beschriftung und Eingabefeld für Quell-MAC-Adresse
        ttk.Label(mac_frame, text="Source MAC:").grid(row=0, column=0, padx=10, pady=5, sticky=tk.E)
        self.src_mac_entry = ttk.Entry(mac_frame, textvariable=self.src_mac_var)
        self.src_mac_entry.grid(row=0, column=1, padx=10, pady=5)
        # Beschriftung und Eingabefeld für Ziel-MAC-Adresse
        ttk.Label(mac_frame, text="Destination MAC:").grid(row=1, column=0, padx=10, pady=5, sticky=tk.E)
        self.dst_mac_entry = ttk.Entry(mac_frame, textvariable=self.dst_mac_var)
        self.dst_mac_entry.grid(row=1, column=1, padx=10, pady=5)

        # Bereich zur Bildauswahl
        image_frame = ttk.Frame(self.root)
        image_frame.pack(pady=10, fill=tk.X)
        # Beschriftung für Bildauswahl
        ttk.Label(image_frame, text="Select Images:").pack(side=tk.LEFT, padx=10)
        # Button zum Durchsuchen der Bilder
        self.browse_button = ttk.Button(image_frame, text="Browse Images")
        self.browse_button.pack(side=tk.LEFT, padx=10)

        # Bereich für den Helligkeitsregler
        brightness_frame = ttk.Frame(self.root)
        brightness_frame.pack(pady=10, fill=tk.X)
        # Beschriftung für Helligkeit
        ttk.Label(brightness_frame, text="Brightness (%):").pack(side=tk.LEFT, padx=10)
        # Regler zur Einstellung der Helligkeit
        self.brightness_slider = ttk.Scale(brightness_frame, from_=0, to=100, orient=tk.HORIZONTAL, variable=self.brightness_var)
        self.brightness_slider.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        # Navigationsbereich für Bildsteuerung und weitere Funktionen
        navigation_frame = ttk.Frame(self.root)
        navigation_frame.pack(pady=10, fill=tk.X)
        # Button zum Senden des aktuellen Bildes
        self.send_button = ttk.Button(navigation_frame, text="Send Image")
        self.send_button.pack(side=tk.LEFT, padx=10)
        # Button zum Wechseln zum vorherigen Bild
        self.prev_button = ttk.Button(navigation_frame, text="Previous")
        self.prev_button.pack(side=tk.LEFT, padx=10)
        # Button zum Wechseln zum nächsten Bild
        self.next_button = ttk.Button(navigation_frame, text="Next")
        self.next_button.pack(side=tk.LEFT, padx=10)
        # Button zum Erkennen der Karte (Card Detection)
        self.detect_button = ttk.Button(navigation_frame, text="Detect Card")
        self.detect_button.pack(side=tk.LEFT, padx=10)
        # Button zum Starten des Auto-Play-Modus
        self.auto_play_button = ttk.Button(navigation_frame, text="Start Auto Play")
        self.auto_play_button.pack(side=tk.LEFT, padx=10)
        # Button zum Stoppen des Auto-Play-Modus
        self.stop_auto_button = ttk.Button(navigation_frame, text="Stop")
        self.stop_auto_button.pack(side=tk.LEFT, padx=10)

        # Bereich zur Anzeige der Leistungsdaten
        perf_frame = ttk.Frame(self.root)
        perf_frame.pack(pady=5, fill=tk.X)
        # Label zur Anzeige der Performance-Daten (FPS, Bytes/s etc.)
        self.performance_label = ttk.Label(perf_frame, text="Performance: N/A", relief=tk.SUNKEN, anchor=tk.W)
        self.performance_label.pack(fill=tk.X, padx=10)

        # Bereich für Marquee-spezifische Funktionen
        marquee_frame = ttk.Frame(self.root)
        marquee_frame.pack(pady=10, fill=tk.X)
        # Button zum Konfigurieren der Laufschrift
        self.show_marquee_dialog_button = ttk.Button(marquee_frame, text="Configure Marquee")
        self.show_marquee_dialog_button.pack(side=tk.LEFT, padx=10)
        # Button zum Starten der Laufschrift
        self.start_marquee_button = ttk.Button(marquee_frame, text="Start Marquee")
        self.start_marquee_button.pack(side=tk.LEFT, padx=10)

        # Bereich für den Quit-Button
        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=10, fill=tk.X)
        # Button zum Beenden der Anwendung
        self.quit_button = ttk.Button(button_frame, text="Quit")
        self.quit_button.pack(side=tk.RIGHT, padx=10)

        # Statuszeile am unteren Rand des Fensters
        self.status_label = ttk.Label(self.root, text="Status: Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

    def update_performance(self, text):
        
        self.performance_label.config(text=text)

    def show_status(self, text):
      
        self.status_label.config(text=text)

    def show_error(self, title, msg):
        
        messagebox.showerror(title, msg)

    def show_warning(self, msg):
        
        messagebox.showwarning("Warning", msg)

    def show_info(self, title, msg):
       
        messagebox.showinfo(title, msg)

    def prompt_file_paths(self):
       
        return filedialog.askopenfilenames(filetypes=[("All Files", "*.*")])

    def prompt_marquee_config(self):
       
        config = {}
        # Abfrage des Textes für die Laufschrift
        config["text"] = simpledialog.askstring("Marquee", "Bitte Text für die Laufschrift eingeben:")
        if not config["text"]:
            return None
        # Abfrage der Schriftgröße
        font_size_str = simpledialog.askstring("Schriftgröße", "Bitte Schriftgröße eingeben (z.B. 24):")
        try:
            config["font_size"] = int(font_size_str)
        except:
            config["font_size"] = 24
        # Abfrage der Laufschriftsrichtung
        config["direction"] = simpledialog.askstring("Richtung", "Bitte Richtung eingeben (left/right/up/down):")
        if config["direction"] not in ("left", "right", "up", "down"):
            config["direction"] = "left"
        # Auswahl der Textfarbe
        text_color_result = colorchooser.askcolor(color="#FFFFFF", title="Textfarbe auswählen")
        config["text_color"] = (255, 255, 255) if text_color_result[0] is None else tuple(map(int, text_color_result[0]))
        # Auswahl der Hintergrundfarbe
        bg_color_result = colorchooser.askcolor(color="#000000", title="Hintergrundfarbe auswählen")
        config["bg_color"] = (0, 0, 0) if bg_color_result[0] is None else tuple(map(int, bg_color_result[0]))
        # Abfrage des horizontalen Versatzes
        margin_x_str = simpledialog.askstring("Position X", "Start-Versatz X (z.B. 0):")
        try:
            config["margin_x"] = int(margin_x_str)
        except:
            config["margin_x"] = 0
        # Abfrage des vertikalen Versatzes
        margin_y_str = simpledialog.askstring("Position Y", "Start-Versatz Y (z.B. 0):")
        try:
            config["margin_y"] = int(margin_y_str)
        except:
            config["margin_y"] = 0
        # Abfrage der Geschwindigkeit (Pixel pro Frame)
        speed_str = simpledialog.askstring("Geschwindigkeit (px pro Frame)", "Bitte Speed eingeben (z.B. 2):")
        try:
            config["speed"] = int(speed_str)
        except:
            config["speed"] = 1
        return config
