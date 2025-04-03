#!/usr/bin/env python3

from PIL import Image
import numpy as np

def pil_to_bgr_bytes(pil_image, width, height):
# Für die benutzte LED-Modulen ist eine RGB zu BGR Konvertierung erforderlich
 
        if pil_image.size != (width, height):
            pil_image = pil_image.resize((width, height), Image.LANCZOS)
        arr = np.array(pil_image)
        if arr.ndim == 2:                     # wenn das Bild ist eine "Grayscale image"[2D]
            arr = np.stack((arr,)*3, axis=-1) # 3 mal den selben Kanal Duplizieren
        elif arr.shape[2] == 4:               # wenn Das Bild ist RGBA
            arr = arr[:, :, :3]               # Nur die 3 RGB Kanäle nehmen
            # R- und B-Kanäle vertauschen
        bgr_arr = arr[:, :, ::-1]
        return bgr_arr.tobytes()

def process_image(image_path, width, height):

    with Image.open(image_path) as img:
        img = img.convert("RGB")
        return pil_to_bgr_bytes(img, width, height)
