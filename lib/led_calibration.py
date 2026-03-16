import time

SAFE_MAX_CURRENT = None
CALIBRATED_BRIGHTNESS = None

class LedCalibration:
    """Boot-time LED calibration. Run once, store globals for later."""
    def __init__(self, pixels, ina, headroom=0.9, step=0.05, delay=0.05,
                 window_size=5, plateau_steps=3, threshold=2.0):
        self.pixels = pixels
        self.ina = ina
        self.headroom = headroom
        self.step = step
        self.delay = delay
        self.window_size = window_size
        self.plateau_steps = plateau_steps
        self.threshold = threshold
        self.max_current = 0.0

    def run(self):
        global SAFE_MAX_CURRENT, CALIBRATED_BRIGHTNESS

        print("[LED CALIBRATION] Starting...")
        self.pixels.fill((0, 0, 0))
        self.pixels.show()
        time.sleep(0.1)

        readings = []
        consecutive_plateau = 0
        brightness = 0.0

        while True:
            self.pixels.brightness = brightness
            self.pixels.fill((0, 255, 0))
            self.pixels.show()
            time.sleep(self.delay)

            current = self.ina.current
            self.max_current = max(self.max_current, current)

            readings.append(current)
            if len(readings) > self.window_size:
                readings.pop(0)

            avg_current = sum(readings) / len(readings)
            if len(readings) == self.window_size:
                prev_avg = sum(readings[:-1]) / (self.window_size - 1)
                delta = avg_current - prev_avg
                if delta < self.threshold:
                    consecutive_plateau += 1
                else:
                    consecutive_plateau = 0

                if consecutive_plateau >= self.plateau_steps:
                    print(f"Plateau at brightness {brightness:.2f}")
                    break

            brightness += self.step
            if brightness >= 1.0:
                print("Reached max brightness.")
                break

        SAFE_MAX_CURRENT = self.max_current * self.headroom
        CALIBRATED_BRIGHTNESS = brightness

        print(f"[LED CAL DONE] Max {self.max_current:.2f} mA | Safe {SAFE_MAX_CURRENT:.2f} mA | Bright {CALIBRATED_BRIGHTNESS:.2f}")

        # Leave LEDs lit green at calibrated brightness
        # self.pixels.brightness = CALIBRATED_BRIGHTNESS
        # self.pixels.fill((0, 255, 0))
        # self.pixels.show()
