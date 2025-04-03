#!/usr/bin/env python3
# Ethernet constants
ETH_P_ALL = 0x0003  # Receive all packets
ETH_FRAME_LEN = 1518  # Maximum Ethernet frame size
IF_NAMESIZE = 16  # Fixed memory allocation for interface names.

# Brightness mapping
BRIGHTNESS_MAP = [
    (0, 0x28),
    (10, 0x29),
    (20, 0x2A),
    (30, 0x2B),
    (40, 0x2C),
    (50, 0x2D),
    (60, 0x2E),
    (70, 0x2F),
    (80, 0x30),
    (90, 0x31),
    (100, 0x32),
]

# Frame data lengths
FRAME_0107_DATA_LENGTH = 98  # Length of initialization frame
FRAME_0AFF_DATA_LENGTH = 63   # Length of brightness frame
