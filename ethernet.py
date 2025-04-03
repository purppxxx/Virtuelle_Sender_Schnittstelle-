#!/usr/bin/env python3

import socket
import struct
import fcntl
import time
from constants import ETH_P_ALL, ETH_FRAME_LEN, IF_NAMESIZE

class L2Ethernet:                                       #ethernet layer 2 klasse
    
    def __init__(self, interface_name):                 #Initialisierung
        self.interface_name = interface_name            
        self.socket = None
        self.ifindex = None
        self.src_mac = None
        self.stop_sending_flag = False                  # Control flag for sending loop

    def open(self):
        """Open a raw Ethernet socket and initialize interface details."""
        try:
            self.socket = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(ETH_P_ALL))  #Sockets öffnen durch AF_PACKET (root Berechtigungen sind erforderlich)
            self.socket.bind((self.interface_name, 0))
            self.ifindex = self._get_interface_index(self.interface_name)
            print(f"Interface {self.interface_name} initialized. ")                                     #log
        except PermissionError:
            print("Permission denied. Please run with root privileges.")               
            self.close()
        except Exception as e:
            print(f"Error opening socket: {e}")
            self.close()

    def close(self):                                    
        if self.socket:
            self.socket.close()
            self.socket = None
            print("Socket closed.")

    def send(self, dest_mac, src_mac, ether_type, payload):
        if not self.socket:
            print("Socket is not open. Call open() first.")
            return 0
        eth_header = struct.pack("!6s6sH", dest_mac, src_mac, ether_type)
        #!struct nutzen um in Binär form umzuwandeln
        #!: Netzwerk-Byte-Reihenfolge (Big-Endian)
        #6s: Ein 6-Byte-String (für die Ziel-MAC-Adresse)
        #6s: Ein weiterer 6-Byte-String (für die Quell-MAC-Adresse)
        #H: Ein unsigned short (2 Byte) für den Ether-Type
        frame = eth_header + payload
        start = time.monotonic()
        bytes_sent = self.socket.send(frame)
        elapsed = time.monotonic() - start
        print(f"Sent {bytes_sent} bytes in {elapsed:.6f} seconds.")
        return bytes_sent

    def recv(self):
        return self.socket.recv(ETH_FRAME_LEN)

    def _get_interface_index(self, interface_name):
        SIOCGIFINDEX = 0x8933
        ifreq = struct.pack(f"{IF_NAMESIZE}sH", interface_name.encode("utf-8"))
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            res = fcntl.ioctl(s.fileno(), SIOCGIFINDEX, ifreq) 
            _, ifindex = struct.unpack(f"{IF_NAMESIZE}sH", res)
            return ifindex

    def stop_sending(self):
        self.stop_sending_flag = True
