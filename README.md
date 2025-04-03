#Virtuelle Sender-Schnittstelle-
# Colorlight-5a75B/E Image Player 

A Python desktop application for sending images and scrolling text to an LED display using raw Layer 2 Ethernet sockets. Built with a user-friendly GUI, the tool is ideal for testing or simulating LED sending cards such as Colorlight devices.

---

## 🔧 Features

- Load and send static images over Ethernet
- Auto-play image sequences at up to 60 FPS (adjustable)
- Display custom scrolling marquee text (left, right, up, down)
- Adjustable brightness control
- Real-time performance stats: FPS, bandwidth, bitrate
- Caching for fast image switching
- Clean GUI built with Tkinter

---

## 🚀 Performance Notes

- 🥧 **Raspberry Pi 4**: Default playback is optimized for **60 FPS**
- 💻 **Commercial PC**: You can modify the app to reach **120 FPS** or more depending on hardware performance

The frame rate is defined in the source (e.g. `target_interval = 1 / 60`) and can be adjusted.

---

## 📦 Dependencies

Make sure Python 3.7+ is installed.

Install external packages using pip:

```bash
pip install pillow netifaces numpy
