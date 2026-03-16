import board, busio, neopixel
from adafruit_ina219 import INA219

# --- KMK Core ---
from kmk.kmk_keyboard import KMKKeyboard
from kmk.scanners import DiodeOrientation
from kmk.modules.macros import Macros
from kmk.modules.layers import Layers
from encoder_extension import EncoderHandlerWithFuncs
from kmk.extensions.media_keys import MediaKeys
from kmk.keys import KC

# --- Custom Modules ---
from lib.modules.current_module import CurrentMonitor
from lib.modules.menu_ticker import MenuUpdater
from lib.modules.lcd_lock_status import LCDLockStatus
from lib.modules.serial_macros import SerialMacros
from lib.keymaps.default import get_keymap
from menu_ui import MenuController

# --- LED + Power ---
from led_calibration import LedCalibration
from led_controller import LedController

# ==========================================================
# HARDWARE INIT
# ==========================================================

# --- LED setup ---
NUM_LEDS = 50
pixels = neopixel.NeoPixel(board.D12, NUM_LEDS, brightness=0, auto_write=True)
pixels.fill((0, 0, 0))
pixels.show()

# --- Power Sensor ---
i2c = busio.I2C(board.SCL1, board.SDA1)
ina = INA219(i2c)

# --- Core Keyboard ---
keyboard = KMKKeyboard()
keyboard.row_pins = (board.D2, board.D3, board.D4, board.D5, board.D6, board.D7)
keyboard.col_pins = (
    board.D8, board.D9, board.D10, board.D14, board.D15,
    board.D18, board.D19, board.D20, board.D21, board.D22,
    board.D23, board.D24, board.D25, board.D13, board.D11,
    board.D28, board.D29, board.D30, board.D31, board.D32
)
keyboard.diode_orientation = DiodeOrientation.ROW2COL

# ==========================================================
# KMK MODULES
# ==========================================================

macros = Macros()
encoder_handler = EncoderHandlerWithFuncs()
media_keys = MediaKeys()
layers = Layers()

# Initialize power monitoring
current_monitor = CurrentMonitor()
current_monitor.ina = ina

# --- Initialize menu (before modules so we can wire everything properly) ---
menu = MenuController(current_monitor=current_monitor)

# --- Menu ticker (drives live updates, e.g. current readout) ---
menu_updater = MenuUpdater(menu)

# --- LED Calibration & Controller ---
cal = LedCalibration(pixels, ina, headroom=0.8)
cal.run()
leds = LedController(pixels, ina)
menu.leds = leds

# --- LCD Lock Extension ---
locks = LCDLockStatus(menu)

serial_macros = SerialMacros()
serial_macros.register_macro("MACRO_1", "MACRO_1")
serial_macros.register_macro("MACRO_2", "MACRO_2")
serial_macros.register_macro("MACRO_3", "MACRO_3")
serial_macros.register_macro("MACRO_4", "MACRO_4")
serial_macros.register_macro("MACRO_5", "MACRO_5")
serial_macros.register_macro("MACRO_6", "MACRO_6")

serial_macros.menu = menu

# ==========================================================
# FINAL MODULE REGISTRATION
# ==========================================================

keyboard.extensions = [locks]
keyboard.modules = [
    macros,
    media_keys,
    encoder_handler,
    current_monitor,
    menu_updater,
    serial_macros,
    layers,
]

# ==========================================================
# ENCODER CONFIG
# ==========================================================

encoder_handler.pins = [
    (board.D39, board.D40, board.D41),  # Encoder 0 - Volume
    (board.D36, board.D37, board.D38),  # Encoder 1 - Menu
]

encoder_handler.map = [
    (
        # Encoder 0 - Volume
        (KC.VOLD, KC.VOLU, KC.MUTE),

        # Encoder 1 - Menu navigation
        (
            lambda: menu.move_selection(-1),  # rotate left
            lambda: menu.move_selection(1),   # rotate right
            lambda: menu.handle_press(),      # press
        ),
    ),
]

MOMENTARY_1 = KC.MO(1)

keyboard.keymap = [
    [   
        serial_macros.MACRO_1, KC.ESC, KC.F1, KC.F2, KC.F3, KC.F4, KC.F5, KC.F6, KC.F7, KC.F8, KC.F9, KC.F10, KC.F11, KC.F12, KC.DEL, KC.HOME, KC.END, KC.PGUP, KC.PGDN, KC.NO,
        serial_macros.MACRO_2, KC.GRAVE, KC.N1, KC.N2, KC.N3, KC.N4, KC.N5, KC.N6, KC.N7, KC.N8, KC.N9, KC.N0, KC.MINS, KC.EQL, KC.NO, KC.BSPC, KC.NLCK, KC.PSLS, KC.PAST, KC.PMNS,
        serial_macros.MACRO_3, KC.TAB, KC.NO, KC.Q, KC.W, KC.E, KC.R, KC.T, KC.Y, KC.U, KC.I, KC.O, KC.P, KC.LBRC, KC.RBRC, KC.NO, KC.P7, KC.P8, KC.P9, KC.NO,
        serial_macros.MACRO_4, KC.CAPSLOCK, KC.NO, KC.A, KC.S, KC.D, KC.F, KC.G, KC.H, KC.J, KC.K, KC.L, KC.SCLN, KC.QUOT, KC.ZKHK, KC.ENT, KC.P4, KC.P5, KC.P6, KC.PPLS,
        serial_macros.MACRO_5, KC.LSFT, KC.BSLASH, KC.Z, KC.X, KC.C, KC.V, KC.B, KC.N, KC.M, KC.COMMA, KC.DOT, KC.SLASH, KC.NO, KC.RSFT, KC.UP, KC.P1, KC.P2, KC.P3, KC.NO,
        serial_macros.MACRO_6, KC.LCTRL, KC.LGUI, KC.NO, KC.LALT, KC.NO, KC.NO, KC.SPACE, KC.NO, KC.NO, KC.NO, KC.RALT, MOMENTARY_1, KC.RCTRL, KC.LEFT, KC.DOWN, KC.RIGHT, KC.P0, KC.KP_DOT, KC.PENT,
    ],
    [   
        KC.TRNS, KC.TRNS, KC.MEDIA_PREV_TRACK, KC.MEDIA_PLAY_PAUSE, KC.MEDIA_NEXT_TRACK, KC.VOLD, KC.VOLU, KC.MUTE, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS,
        KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS,
        KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS,
        KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS,
        KC.TRNS, KC.TRNS, KC.PIPE, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS,
        KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS, KC.TRNS,
    ],
]

# ==========================================================
# RUN KMK
# ==========================================================

if __name__ == "__main__":
    menu.play_boot_animation()
    keyboard.go()