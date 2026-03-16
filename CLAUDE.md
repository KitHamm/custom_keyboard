# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CircuitPython-based custom keyboard firmware running on an RP2040 microcontroller. Features a 120-key matrix (6×20), 2 rotary encoders, 50 NeoPixel LEDs, a 240×240 ST7789 LCD display, and INA219 power monitoring.

## Deploying

This is CircuitPython firmware — there is no build step. To deploy, copy files to the `CIRCUITPY` USB drive that appears when the keyboard is connected. CircuitPython automatically runs `code.py` on boot.

The keyboard must be connected via USB to appear as `CIRCUITPY`.

## Architecture

### Entry Points
- **`boot.py`** — Runs before `code.py`; enables dual USB CDC (REPL + data serial)
- **`code.py`** — Main firmware: initializes all hardware, registers KMK modules/extensions, defines the keymap, starts `keyboard.go()`

### KMK Module Registration Order (in `code.py`)
```
Extensions: [LCDLockStatus]
Modules:    [Macros, MediaKeys, EncoderHandlerWithFuncs,
             CurrentMonitor, MenuUpdater, SerialMacros, Layers]
```

### Key Subsystems

**Keymap** — Defined inline in `code.py`. Two layers: Layer 0 (QWERTY + macros) and Layer 1 (media keys, accessed via `MO(1)`). `keymaps/default.py` is a placeholder and not used.

**Menu / UI** (`lib/menu_ui.py`) — The primary UI engine. `MenuController` owns the display state machine: idle screen (lock status + connection indicator), hierarchical menus, and slider controls. Driven by `MenuUpdater` module calling `menu.tick()` before each matrix scan. Encoder 1 (menu knob) calls `menu.move_selection()` / `menu.handle_press()` directly.

**LED Control** — Two-phase system:
1. `lib/led_calibration.py` — Boot-time calibration: ramps brightness while monitoring current draw to find a safe maximum, stored as `SAFE_MAX_CURRENT` / `CALIBRATED_BRIGHTNESS` globals.
2. `lib/led_controller.py` — Runtime control: translates user RGB/brightness values to safe NeoPixel output using calibration values.

**Serial Macros** (`lib/modules/serial_macros.py`) — Handshake-based protocol over USB CDC serial. Six macro keys (MACRO_1–MACRO_6) broadcast their IDs to the host when pressed. Includes keepalive ping/pong (5s interval, 15s timeout).

**Encoder** (`encoder_extension.py`) — Subclasses KMK's `EncoderHandler` to support both keycodes and callable lambdas per layer/direction.

**Power Monitoring** (`lib/modules/current_module.py`) — Polls INA219 every 0.25s; value displayed on the info screen.

**Lock Status** (`lib/modules/lcd_lock_status.py`) — Monitors HID LED reports for CAPSLOCK/NUMLOCK changes and updates the idle screen.

### Hardware Pin Summary
| Component | Pins |
|-----------|------|
| Matrix rows | D2–D7 |
| Matrix cols | D8–D11, D13–D15, D18–D25, D28–D32 |
| NeoPixels (50) | D12 |
| Encoder 0 (volume) | CLK=D39, DT=D40, SW=D41 |
| Encoder 1 (menu) | CLK=D36, DT=D37, SW=D38 |
| ST7789 display | SPI D26/D27, CS=D33, DC=D34, RST=D35 |
| INA219 (power) | I2C SCL1/SDA1 |

### Unused / Legacy Files
- `menu_state_machine.py` — Superseded by `menu_ui.py`, not imported
- `serial_lcd.py` — UART interface to an external LCD controller, not active
