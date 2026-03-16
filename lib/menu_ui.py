# menu_ui.py
import time
import random
from lcd_display import init_display, draw_menu
import displayio
from displayio import OnDiskBitmap, TileGrid, Group
import terminalio
from adafruit_display_text import label
from adafruit_display_shapes.rect import Rect

_idle_state = {
    "caps": False,
    "num": False,
    "connected": False,  # host serial handshake status
}

    # ---------- Idle state management ----------
def set_connection_state(is_connected: bool):
    """Update the connection indicator flag. Callers are responsible for refreshing the display."""
    global _idle_state
    _idle_state["connected"] = is_connected


# ---------- Menu primitives ----------

class MenuItem:
    """
    kind: 'submenu' | 'action' | 'slider' | 'info'
    label: text shown
    submenu: list[MenuItem] for 'submenu' items
    on_select: callable for 'action' (optional)
    slider: dict for 'slider' items: {name, min, max, step, initial}
    """
    def __init__(self, label, kind="action", submenu=None, on_select=None, slider=None):
        self.label = label
        self.kind = kind
        self.submenu = submenu
        self.on_select = on_select
        self.slider = slider or {}

class MenuController:
    def __init__(self, current_monitor=None, led_controller=None):
        self.display = init_display()
        self.current_monitor = current_monitor
        self.leds = led_controller

        # nav state
        self.stack = []                 # list of tuples: (menu_list, selected_index)
        self.current_menu = []          # list[MenuItem]
        self.selected_index = 0

        # slider state
        self.slider_active = False
        self.slider_title = ""
        self.slider_min = 0
        self.slider_max = 100
        self.slider_step = 1
        self.slider_value = 0
        self.slider_return = None       # (menu_list, selected_index_to_focus)

        # info screen state
        self.info_active = False
        self.info_return = None         # (menu_list, selected_index_to_focus)

        # layout
        self.x_center = 120
        self.start_y = 40
        self.line_gap = 35

        # timestamps for debounce and info screen refresh
        self._last_press_time = 0
        self._last_info_update = 0

        # build + open main menu
        self.root_menu = self._build_menu()

    # ---------- Menu definition (YOUR structure) ----------

    def _build_menu(self):
        """
        |Menu        |Sub Menu   | Sub Sub / Action |
        |------------|-----------|------------------|
        |Close       |None       | Back To Idle     |
        |Layers      |Back       | Back To Main     |
        |            |Default    | print + back     |
        |Lights      |Back       | Back To Main     |
        |            |Red        | slider -> print  |
        |            |Green      | slider -> print  |
        |            |Blue       | slider -> print  |
        |Settings    |Back       | Back To Main     |
        |            |Headroom   | slider -> print  |
        |            |Brightness | slider -> print  |
        |System Info |(info)     | info screen      |
        """
        # helpers
        def action_print(msg, then_back=True):
            def _act():
                print(msg)
                if then_back:
                    self.back_to_main()
            return _act

        layers_menu = [
            MenuItem("Back", kind="action", on_select=self.go_back),
            MenuItem("Default", kind="action", on_select=action_print("Layer: Default")),  # TODO: implement actual layer switching
        ]

        lights_menu = [
            MenuItem("Back", kind="action", on_select=self.go_back),
            MenuItem("Red",   kind="slider", slider={"name": "Red",   "min": 0, "max": 100, "step": 2}),
            MenuItem("Green", kind="slider", slider={"name": "Green", "min": 0, "max": 100, "step": 2}),
            MenuItem("Blue",  kind="slider", slider={"name": "Blue",  "min": 0, "max": 100, "step": 2}),
        ]

        settings_menu = [
            MenuItem("Back", kind="action", on_select=self.go_back),
            MenuItem("Brightness", kind="slider", slider={"name": "Brightness", "min": 0, "max": 100, "step": 2}),
        ]

        main_menu = [
            MenuItem("Close", kind="action", on_select=self.return_to_idle),
            MenuItem("Layers", kind="submenu", submenu=layers_menu),
            MenuItem("Lights", kind="submenu", submenu=lights_menu),
            MenuItem("Settings", kind="submenu", submenu=settings_menu),
            MenuItem("System Info", kind="info"),
        ]
        return main_menu

    # ---------- Public API for encoder/key bindings ----------

    def open_menu(self, menu_list):
        self.stack = []
        self.current_menu = menu_list
        self.selected_index = 0
        self.slider_active = False
        self._draw_list()

    def back_to_main(self):
        self.open_menu(self.root_menu)

    def move_selection(self, delta):
        # slider mode hijacks rotation
        if self.slider_active:
            now = time.monotonic()
            diff = now - getattr(self, "_last_move_time", 0)
            self._last_move_time = now

            # adaptive step: faster rotation = bigger jump
            step = self.slider_step
            if diff < 0.1:   # fast spin
                step *= 5
            elif diff < 0.2: # moderate spin
                step *= 2

            self.slider_value = max(self.slider_min, min(self.slider_max, self.slider_value + (delta * step)))
            self._draw_slider()

            # live update LED controller
            if self.leds:
                title = self.slider_title.lower()
                if title == "red":
                    self.leds.set_red(self.slider_value)
                elif title == "green":
                    self.leds.set_green(self.slider_value)
                elif title == "blue":
                    self.leds.set_blue(self.slider_value)
                elif title == "brightness":
                    self.leds.set_brightness(self.slider_value)
            return
        # info screen ignores rotation
        if self.info_active:
            return

        count = len(self.current_menu)
        if count == 0:
            return
        self.selected_index = (self.selected_index + delta) % count
        self._draw_list()

    def press(self):
        if self.slider_active:
            # confirm slider
            print(f"{self.slider_title} set to {self.slider_value}")
            # go back to the menu we came from (Lights/Settings)
            if self.slider_return:
                self.current_menu, self.selected_index = self.slider_return
            self.slider_active = False
            self.slider_return = None
            self._draw_list()
            return

        if self.info_active:
            # leave info, go back to main
            self.info_active = False
            self.info_return = None
            self.back_to_main()
            return

        # normal menu select
        if not self.current_menu:
            return
        item = self.current_menu[self.selected_index]

        if item.kind == "submenu" and item.submenu:
            # push current, dive in
            self.stack.append((self.current_menu, self.selected_index))
            self.current_menu = item.submenu
            self.selected_index = 0
            self._draw_list()
            return

        if item.kind == "action":
            if item.on_select:
                item.on_select()
            else:
                # no-op
                pass
            return

        if item.kind == "slider":
            s = item.slider
            self.slider_active = True
            self.slider_title = s.get("name", item.label)
            self.slider_min = int(s.get("min", 0))
            self.slider_max = int(s.get("max", 100))
            self.slider_step = int(s.get("step", 2))

            # --- pull live LED values if available ---
            if self.leds:
                vals = self.leds.get_values()
                name = self.slider_title.lower()
                self.slider_value = int(vals.get(name, 50))
            else:
                self.slider_value = 50

            # remember where to return (stay at the same index)
            self.slider_return = (self.current_menu, self.selected_index)
            self._draw_slider()
            return

        if item.kind == "info":
            self.info_active = True
            self.info_return = (self.current_menu, self.selected_index)
            self._draw_info()
            return

    def go_back(self):
        # from slider/info, pressing "Back" item should behave like normal back
        if self.slider_active:
            self.slider_active = False
            if self.slider_return:
                self.current_menu, self.selected_index = self.slider_return
                self.slider_return = None
            self._draw_list()
            return
        if self.info_active:
            self.info_active = False
            self.back_to_main()
            return

        if self.stack:
            self.current_menu, self.selected_index = self.stack.pop()
            self._draw_list()
        else:
            # top-level -> idle
            self.return_to_idle()

    # ---------- Renderers ----------

    def _draw_list(self):
        items = []
        y = self.start_y
        for i, m in enumerate(self.current_menu):
            items.append({
                "text": m.label,
                "x": self.x_center,
                "y": y,
                "color": 0x00FF00 if i == self.selected_index else 0xFFFFFF,
                "scale": 2,
                "anchor_point": (0.5, 0.5),
                "highlighted": i == self.selected_index,
            })
            y += self.line_gap
        draw_menu(items, bg_color=0x000000)

    def _draw_slider(self):
        """Draw a fast, clean firmware-style slider bar using block characters."""
        try:
            val = int(self.slider_value)
            vmin = int(self.slider_min)
            vmax = int(self.slider_max)
        except (ValueError, TypeError):
            val, vmin, vmax = 0, 0, 100

        filled_chars = 10  # total bar width in characters
        rng = max(1, vmax - vmin)
        ratio = (val - vmin) / rng
        filled = int(round(ratio * filled_chars))
        filled = max(0, min(filled, filled_chars))

        bar = "[" + "-" * filled + " " * (filled_chars - filled) + "]"

        items = [
            {
                "text": f"{self.slider_title}: {val}",
                "x": self.x_center,
                "y": 70,
                "color": 0xFFFFFF,
                "scale": 2,
                "anchor_point": (0.5, 0.5),
                "highlighted": False,
            },
            {
                "text": bar,
                "x": self.x_center,
                "y": 120,
                "color": 0x00FF00,
                "scale": 2,
                "anchor_point": (0.5, 0.5),
                "highlighted": False,
            },
            {
                "text": "Press to confirm",
                "x": self.x_center,
                "y": 170,
                "color": 0x888888,
                "scale": 1,
                "anchor_point": (0.5, 0.5),
                "highlighted": False,
            },
        ]
        draw_menu(items, bg_color=0x000000)

    def _draw_info(self):
        fw = "0.0.1"
        current_str = "N/A"
        if self.current_monitor and self.current_monitor.ina:
            current_str = f"{self.current_monitor.current:.1f} mA"

        items = [
            {"text": "System Info",           "x": self.x_center, "y": 40,  "color": 0xFFFFFF, "scale": 2, "anchor_point": (0.5, 0.5), "highlighted": False},
            {"text": f"Firmware: {fw}",       "x": self.x_center, "y": 90,  "color": 0x00FF00, "scale": 2, "anchor_point": (0.5, 0.5), "highlighted": False},
            {"text": f"Current: {current_str}", "x": self.x_center, "y": 130, "color": 0x00FF00, "scale": 2, "anchor_point": (0.5, 0.5), "highlighted": False},
            {"text": "Press to return",       "x": self.x_center, "y": 180, "color": 0x888888, "scale": 1, "anchor_point": (0.5, 0.5), "highlighted": False},
        ]
        draw_menu(items, bg_color=0x000000)

    # ---------- Idle (placeholder) ----------

    def return_to_idle(self):
        """Draw the idle display with status indicators in a polished cyberpunk style."""
        # wipe menus
        self.current_menu = []
        self.stack.clear()

        # accent color (Arasaka green)
        accent = 0x00FF66

        # draw the base layout
        items = [
            # Header / title
            {"text": "KMT Systems // ARASAKA Hijack Firmware", 
            "x": 120, "y": 20, "color": accent, "scale": 1, 
            "anchor_point": (0.5, 0), "highlighted": False},

            # Divider line (visual — simulated with underscores)
            {"text": "―" * 20, 
            "x": 120, "y": 40, "color": 0x333333, "scale": 1, 
            "anchor_point": (0.5, 0), "highlighted": False},

            # Device name/version
            {"text": "KMT-KB V0.0.1", 
            "x": 120, "y": 70, "color": 0xFFFFFF, "scale": 2, 
            "anchor_point": (0.5, 0), "highlighted": False},

            # Lock indicators
            {"text": "CAPS:", "x": 40, "y": 110, "color": accent, "scale": 2, "anchor_point": (0, 0)},
            {"text": "ON" if _idle_state["caps"] else "OFF", 
            "x": 160, "y": 110, "color": 0xFFFFFF if _idle_state["caps"] else 0x333333, 
            "scale": 2, "anchor_point": (0, 0)},

            {"text": "NUM:", "x": 40, "y": 150, "color": accent, "scale": 2, "anchor_point": (0, 0)},
            {"text": "ON" if _idle_state["num"] else "OFF", 
            "x": 160, "y": 150, "color": 0xFFFFFF if _idle_state["num"] else 0x333333, 
            "scale": 2, "anchor_point": (0, 0)},
        ]

        # --- Host connection indicator ---
        conn_text = "CONNECTED" if _idle_state.get("connected") else "DISCONNECTED"
        conn_color = 0x00FF00 if _idle_state.get("connected") else 0xFF0000
        items.append({
            "text": f"HOST: {conn_text}",
            "x": 120,
            "y": 195,
            "color": conn_color,
            "scale": 1,
            "anchor_point": (0.5, 0),
            "highlighted": False,
        })

        # Footer / hint text
        items.append({
            "text": ">> PRESS ENCODER TO ACCESS SYSTEM", 
            "x": 120, "y": 215, "color": 0x444444, "scale": 1, 
            "anchor_point": (0.5, 0), "highlighted": False,
        })

        draw_menu(items, bg_color=0x000000)


    def get_ui_state(self):
        if not self.current_menu:
            return "idle"
        if self.slider_active:
            return "slider"
        if self.info_active:
            return "info"
        if not self.stack:
            return "main_menu"

        # try to identify parent
        top_menu = self.stack[-1][0]
        for m in top_menu:
            if m.submenu == self.current_menu:
                return f"{m.label.lower()}_menu"
        return "submenu"
    
    def open_main_menu(self):
        """Open the top-level main menu."""
        self.open_menu(self.root_menu)

    def handle_press(self):
        """Single entry point for encoder press."""
        now = time.monotonic()
        if now - self._last_press_time < 0.2:  # 200ms debounce
            return  # ignore too-fast clicks
        self._last_press_time = now

        # If we're idle, pressing opens the main menu
        if not self.current_menu:
            self.open_main_menu()
            return

        # Otherwise, act like a normal press
        self.press()

    def play_boot_animation(self):
        """ARASAKA → cinematic glitch → boot hack → Wake up, SAMURAI sequence."""
        # 1. Corporate intro — clean and centered
        draw_menu([
            {"text": "ARASAKA", "x": 120, "y": 100,
            "color": 0xFF0000, "scale": 3,
            "anchor_point": (0.5, 0.5), "highlighted": False},
            {"text": "corporation", "x": 120, "y": 140,
            "color": 0xFFFFFF, "scale": 1,
            "anchor_point": (0.5, 0.5), "highlighted": False},
        ], bg_color=0x000000)
        time.sleep(1.3)

        # 2. Controlled chaos: glitch → degrade → vanish
        frames = [
            "ARASAKA",
            "AARSAAK",
            "RAASAK",
            "ARASKA",
            "AARASK",
            "RASAK",
            "ASAKA",
            "ASAA",
            "ASA",
            "AA",
            "A",
        ]

        for txt in frames:
            draw_menu([
                {
                    "text": txt,
                    "x": 120,
                    "y": 100,
                    "color": 0xFF0000,
                    "scale": 3,
                    "anchor_point": (0.5, 0.5),
                    "highlighted": False,
                },
                {
                    "text": "corporation",
                    "x": 120,
                    "y": 140,
                    "color": 0xFFFFFF,
                    "scale": 1,
                    "anchor_point": (0.5, 0.5),
                    "highlighted": False,
                },
            ], bg_color=0x000000)

            time.sleep(random.uniform(0.05, 0.15))

        # 3. Fake firmware boot — accumulative lines
        boot_lines = [
            "[ARASAKA_SYS: CORE_INIT]",
            "[LOAD_KERNEL] v0.9.23... OK",
            "[MOUNT_SECURE_DRIVE] /dev/as-core... OK",
            "[AUTH... BYPASS FAILED]",
            "[PATCHING SIGNATURE]",
            "[INJECTING PAYLOAD]...",
            "[ACCESS GRANTED]",
            "",
            ">>> SYSTEM OVERRIDE DETECTED <<<",
            "",
        ]

        printed = []
        for line in boot_lines:
            printed.append(line)
            items = [{"text": "ARASAKA OS v9.3.2", "x": 0, "y": 10,
                    "color": 0x888888, "scale": 1,
                    "anchor_point": (0, 0), "highlighted": False}]
            # draw all accumulated lines
            for i, l in enumerate(printed[-10:]):  # show last 10 lines max
                items.append({
                    "text": l,
                    "x": 0,
                    "y": 40 + (i * 15),
                    "color": 0x00FF00 if "FAILED" not in l else 0xFF0000,
                    "scale": 1,
                    "anchor_point": (0, 0),
                    "highlighted": False
                })
            draw_menu(items, bg_color=0x000000)
            time.sleep(random.uniform(0.1, 0.26))

        # 4. ACCESS GRANTED — typed out slowly, black background
        msg = "ACCESS GRANTED"
        rendered = ""

        for ch in msg:
            rendered += ch
            draw_menu([
                {
                    "text": rendered,
                    "x": 120,
                    "y": 120,
                    "color": 0x00FF00,
                    "scale": 2,
                    "anchor_point": (0.5, 0.5),
                    "highlighted": False,
                }
            ], bg_color=0x000000)
            time.sleep(random.uniform(0.05, 0.26))

        # brief hold so player can read it
        time.sleep(0.8)

        # 5. “Wake up,”
        draw_menu([
            {"text": "Wake up,", "x": 120, "y": 110,
            "color": 0xFFFFFF, "scale": 2,
            "anchor_point": (0.5, 0.5), "highlighted": False},
        ], bg_color=0x000000)
        time.sleep(1.0)

        # 6. SAMURAI — blood red
        draw_menu([
            {"text": "SAMURAI", "x": 120, "y": 130,
            "color": 0xFF0000, "scale": 3,
            "anchor_point": (0.5, 0.5), "highlighted": False},
        ], bg_color=0x000000)
        time.sleep(1.5)

        # 7. Fade out clean
        for c in [0x880000, 0x440000, 0x000000]:
            draw_menu([
                {"text": "SAMURAI", "x": 120, "y": 130,
                "color": c, "scale": 3,
                "anchor_point": (0.5, 0.5), "highlighted": False}
            ], bg_color=0x000000)
            time.sleep(0.1)

        self.return_to_idle()


    def tick(self):
        """Called from KMK scan loop for background updates."""
        # If we're on the system info screen, redraw it periodically
        if self.info_active and self.current_monitor:
            now = time.monotonic()
            # Only redraw every ~0.25s (match your INA219 poll rate)
            if now - self._last_info_update >= 0.25:
                self._last_info_update = now
                self._draw_info()