from led_calibration import SAFE_MAX_CURRENT, CALIBRATED_BRIGHTNESS

class LedController:
    """Controls NeoPixels safely using calibration globals."""
    def __init__(self, pixels, ina):
        self.pixels = pixels
        self.ina = ina

        # color and brightness state
        self.red = 0
        self.green = 255
        self.blue = 0
        self.user_brightness = 100

        # calibration + safety limits
        self.safe_max_current = SAFE_MAX_CURRENT or 500  # mA
        self.calibrated_brightness = CALIBRATED_BRIGHTNESS or 0.5
        self.max_led_current_mA = 60
        self.num_leds = len(pixels)

        # initialize
        self._apply_brightness()

    # --- internal helpers ---

    def _estimate_current(self, r, g, b, brightness):
        ratio = (r + g + b) / (255 * 3)
        return ratio * self.max_led_current_mA * brightness * self.num_leds

    def _calculate_safe_brightness(self):
        color_ratio = (self.red + self.green + self.blue) / (255.0 * 3.0)
        est_per_unit = color_ratio * self.max_led_current_mA * self.num_leds

        if est_per_unit > 0:
            safe_brightness = min(
                self.safe_max_current / est_per_unit,
                self.calibrated_brightness
            )
        else:
            safe_brightness = self.calibrated_brightness

        user_scale = self.user_brightness / 100.0
        return safe_brightness * user_scale

    def _apply_brightness(self):
        self.actual_brightness = self._calculate_safe_brightness()
        self.pixels.brightness = self.actual_brightness
        self.pixels.fill((self.red, self.green, self.blue))
        self.pixels.show()

    # --- public controls ---

    def set_red(self, v):
        self.red = int((v / 100) * 255)
        self._apply_brightness()

    def set_green(self, v):
        self.green = int((v / 100) * 255)
        self._apply_brightness()

    def set_blue(self, v):
        self.blue = int((v / 100) * 255)
        self._apply_brightness()

    def set_brightness(self, value):
        self.user_brightness = max(0, min(100, value))
        self._apply_brightness()

    # expose current state to UI
    def get_values(self):
        return {
            "red": int((self.red / 255) * 100),
            "green": int((self.green / 255) * 100),
            "blue": int((self.blue / 255) * 100),
            "brightness": self.user_brightness,
        }
