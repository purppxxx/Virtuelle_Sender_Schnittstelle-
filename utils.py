#!/usr/bin/env python3
from constants import BRIGHTNESS_MAP, FRAME_0107_DATA_LENGTH, FRAME_0AFF_DATA_LENGTH

def get_brightness(brightness_percent):
    #Helligkeits-prozent mithilfe eine Tabelle umwandeln
    brightness = 0x28
    for percent, value in BRIGHTNESS_MAP:
        if brightness_percent >= percent:
            brightness = value
    return brightness

def init_frames(column_count, brightness_percent):
    # Initialization Packet (frameData0107)
    frameData0107 = bytearray(FRAME_0107_DATA_LENGTH)
    frameData0107[21] = brightness_percent
    frameData0107[22] = 5
    frameData0107[24] = brightness_percent
    frameData0107[25] = brightness_percent
    frameData0107[26] = brightness_percent

    # Brightness Packet (frameData0aff)
    brightness = get_brightness(brightness_percent)
    frameData0aff = bytearray(FRAME_0AFF_DATA_LENGTH)
    frameData0aff[0] = 0xFF
    frameData0aff[1] = 0xFF
    frameData0aff[2] = 0xFF

    # Row Data Frame Template (frameData5500)
    frameData5500 = bytearray(7 + column_count * 3)  # 7 bytes header + 3 bytes per column
    frameData5500[3] = column_count >> 8  # High byte of column count
    frameData5500[4] = column_count & 0xFF  # Low byte of column count
    frameData5500[5] = 0x08  # Fixed header
    frameData5500[6] = 0x88  # Fixed header

    return frameData0107, frameData0aff, frameData5500

def update_row_data(frameData5500, row_index, row_data):
    frameData5500[0] = row_index  # Update row index
    frameData5500[7:] = row_data  # Update row data
