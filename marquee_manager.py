import time
import logging
import os
from PIL import Image, ImageFont, ImageDraw
from processing import pil_to_bgr_bytes
from sending import send_single_frame_sync

class MarqueeEngine:
    FONT_PATH = "/usr/share/fonts/truetype/ubuntu/UbuntuMono-RI.ttf"
    FALLBACK_FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    
    def __init__(self, ctrl, text, font_size=24, text_color=(255, 255, 255), 
                 bg_color=(0, 0, 0), direction='left', margin_x=2, margin_y=2, speed=1):
        self.ctrl = ctrl
        self.view = ctrl.view  # View through controller
        self.l2 = ctrl.l2

        # Hardware parameters
        self.width = ctrl.columns
        self.height = ctrl.rows
        self.brightness = self.view.brightness_var.get()  # Helligkeitsparameter aufrufen.

        # MAC-addressen
        self.src_mac = bytes.fromhex(self.view.src_mac_var.get().replace(':', ''))
        self.dst_mac = bytes.fromhex(self.view.dst_mac_var.get().replace(':', ''))

        # Animationsbilder
        self.frames = []
        self.current_frame = 0
        self._generate_frames(text, font_size, text_color, bg_color, 
                              direction, speed, margin_x, margin_y)

    def _load_font(self, font_path, font_size):
        try:
            if os.path.exists(font_path):
                return ImageFont.truetype(font_path, font_size)
            else:
                logging.warning(f"Font not found: {font_path}")
        except IOError as e:
            logging.warning(f"Failed to load font: {font_path}, Error: {e}")
        try:
            logging.warning("Using fallback font!")
            return ImageFont.truetype(self.FALLBACK_FONT_PATH, font_size)
        except IOError as e:
            logging.error(f"Failed to load fallback font as well. Error: {e}")
            return ImageFont.load_default()

    def _generate_frames(self, text, font_size, color, bg, direction, speed, mx, my):
        start_time = time.time()
        # Load the main font for the marquee text
        font = self._load_font(self.FONT_PATH, font_size)

        bbox = font.getbbox(text)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        #wörterbuch benutzen
        params = {
            'left': {'axis': 'x', 'start': self.width, 'end': -text_w, 'step': -speed},
            'right': {'axis': 'x', 'start': -text_w, 'end': self.width, 'step': speed},
            'up': {'axis': 'y', 'start': self.height, 'end': -text_h, 'step': -speed},
            'down': {'axis': 'y', 'start': -text_h, 'end': self.height, 'step': speed}
        }[direction]

        pos = params['start']
        frame_index = 0

        # Create output directory for debugging frames
        #output_dir = "marquee_frames"
        #os.makedirs(output_dir, exist_ok=True)

        while (pos > params['end'] if params['step'] < 0 else pos < params['end']):
            frame = Image.new('RGB', (self.width, self.height), bg)
            draw = ImageDraw.Draw(frame)

            # Draw marquee text
            if params['axis'] == 'x':
                draw.text((pos, my), text, font=font, fill=color)
            else:
                draw.text((mx, pos), text, font=font, fill=color)

            #Funktionen für emperisches testen.
            # Draw frame number in the top-left corner in white
            # The frame number font is set to a fixed size of 30
            #number_font = self._load_font(self.FONT_PATH, 30)
            #number_text = str(frame_index + 1)  # Starting at 1
            #draw.text((2, 2), number_text, font=number_font, fill=(255, 255, 255))
            # Optionally, save frame as image for debugging
            # frame_path = os.path.join(output_dir, f"frame_{frame_index:03d}.png")
            # frame.save(frame_path)

            # Convert to bytes for LED matrix
            self.frames.append(pil_to_bgr_bytes(frame, self.ctrl.columns, self.ctrl.rows))

            frame_index += 1
            pos += params['step']

        elapsed = time.time() - start_time
        logging.debug(f"Marquee creation completed in {elapsed:.3f} sec, generated {len(self.frames)} frames.")
        # logging.debug(f"Frames saved to {output_dir}")

    def start(self):
        self.ctrl.start_perf_monitor()
        self.ctrl.thread_mgr.start_thread(self._send_loop)

    def _send_loop(self, stop_event):
        try:
            target_interval = 1 / 60  #Änddern wenn mehr FPS möchten oder weniger
            total_frames = len(self.frames)
            compensation = 0.0  #Kompensation

            while not stop_event.is_set():       #wenn false weiter senden
                frame_start = time.monotonic()
                current_brightness = self.view.brightness_var.get()
                bytes_sent = send_single_frame_sync(
                    self.l2, self.src_mac, self.dst_mac,
                    self.brightness, self.frames[self.current_frame],
                    self.width, self.height
                )
                self.ctrl._update_stats(bytes_sent, time.monotonic() - frame_start)
                self.current_frame = (self.current_frame + 1) % total_frames

                elapsed = time.monotonic() - frame_start
                #Kompensation subtrahieren
                wait_time = max(0, target_interval - elapsed - compensation)
                
                sleep_start_time = time.monotonic()
                if stop_event.wait(wait_time):
                    break
                sleep_end_time = time.monotonic()

                # Dynamisches Kompensation
                actual_sleep_duration = sleep_end_time - sleep_start_time
                compensation = actual_sleep_duration - wait_time
        except Exception as e:
            logging.error(f"Marquee error: {str(e)}")
            self.view.show_error("Marquee Failure", str(e))
        finally:
            self.ctrl.stop_perf_monitor()
