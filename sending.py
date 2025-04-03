#!/usr/bin/env python3

import struct
from enum import Enum, auto
from utils import init_frames, update_row_data, get_brightness

class SenderState(Enum):
    INIT = auto()
    BRIGHTNESS = auto()
    SEND_ROWS = auto()
    FINISHED = auto()
    ERROR = auto()

class FrameSenderFSM:
    def __init__(self, l2, src_mac, dest_mac, brightness_percent, frame_data, column_count, row_count):
        self.l2 = l2
        self.src_mac = src_mac
        self.dest_mac = dest_mac
        self.brightness_percent = brightness_percent
        self.frame_data = frame_data
        self.column_count = column_count
        self.row_count = row_count
        self.state = SenderState.INIT
        self.total_bytes_sent = 0
        self.current_row = 0
        self.frameData0107, self.frameData0aff, self.frameData5500 = init_frames(column_count, brightness_percent)

    def send_frame_zero_copy(self, ether_type, payload):
        if self.l2 is None or not hasattr(self.l2, 'socket') or self.l2.socket is None:
            raise Exception("L2Ethernet instance is not properly initialized (socket is None).")
        
        eth_header = struct.pack("!6s6sH", self.dest_mac, self.src_mac, ether_type)    #wurde in ethernet.py erklärt

        # sendmsg nimmt eine Liste von Byteobjekten (partielle Zero-Copy-technik per Scatter/Gather)
        bytes_sent = self.l2.socket.sendmsg([eth_header, payload])
        return bytes_sent


    def run(self):
        try:
            while self.state != SenderState.FINISHED:
                if self.state == SenderState.INIT:
                    self.handle_init()
                elif self.state == SenderState.BRIGHTNESS:
                    self.handle_brightness()
                elif self.state == SenderState.SEND_ROWS:
                    self.handle_send_rows()
                elif self.state == SenderState.ERROR:
                    raise Exception("Error encountered in FSM.")
            return self.total_bytes_sent
        except Exception as e:
            print(f"FSM error: {e}")
            self.state = SenderState.ERROR
            return self.total_bytes_sent

    def handle_init(self):
        bytes_sent = self.send_frame_zero_copy(0x0107, self.frameData0107)
        self.total_bytes_sent += bytes_sent
        self.state = SenderState.BRIGHTNESS

    def handle_brightness(self):
        brightness = get_brightness(self.brightness_percent)
        ether_type = 0x0AFF
        bytes_sent = self.send_frame_zero_copy(ether_type, self.frameData0aff)
        self.total_bytes_sent += bytes_sent
        self.state = SenderState.SEND_ROWS

    def handle_send_rows(self):
        bytes_per_row = self.column_count * 3
        if self.current_row < self.row_count:
            row_data = self.frame_data[self.current_row * bytes_per_row : (self.current_row + 1) * bytes_per_row]
            if len(row_data) == bytes_per_row:
                update_row_data(self.frameData5500, self.current_row, row_data)
                bytes_sent = self.send_frame_zero_copy(0x5500, self.frameData5500)
                self.total_bytes_sent += bytes_sent
            else:
                print(f"Skipping invalid row {self.current_row}")
            self.current_row += 1
        else:
            self.state = SenderState.FINISHED

def send_single_frame_sync(l2, src_mac, dest_mac, brightness_percent, frame_data, column_count, row_count): #nutzt die Zustandmaschine um einen kompletten Frame zu senden.
    fsm = FrameSenderFSM(l2, src_mac, dest_mac, brightness_percent, frame_data, column_count, row_count)
    return fsm.run()
