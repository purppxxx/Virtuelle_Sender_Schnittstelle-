#!/usr/bin/env python3
"""
Virtuelle Sending-Schnittstelle - Praxisphase
Author: Jihed Maddouri, Electrical Engineering '24
Frankfurt University Of Applied Sciences.

Main Modul for virtual Sending card using raw Ethernet Sockets.
Handles image processing and marquee text effects.
"""
import tkinter as tk
from view import MainView
from controller import LEDController

def main():
    fenster = tk.Tk()
    ansicht = MainView(fenster)
    steuerung = LEDController(ansicht)
    fenster.mainloop()

if __name__ == "__main__":
    main()
