from lcd_display import draw_menu
import time
import random

# --- menu states ---
STATE_BOOT = "boot"
STATE_WAKE = "wake"
STATE_IDLE = "idle"
STATE_MAIN_MENU = "main_menu"
STATE_SETTINGS = "settings"

current_state = STATE_BOOT
menu_state = {"caps": False, "num": False}

def play_boot_sequence():
    """Animated boot splash with ARASAKA -> Wake up, SAMURAI"""
    # Step 1: show ARASAKA
    draw_menu([
        {"text": "ARASAKA", "x": 120, "y": 100, "color": 0xFF0000, "scale": 3, "anchor_point": (0.5, 0.5)},
        {"text": "corporation", "x": 120, "y": 140, "color": 0xFFFFFF, "scale": 1, "anchor_point": (0.5, 0.5)},
    ], bg_color=0x000000)
    time.sleep(1.5)

    # Step 2: glitch effect
    for _ in range(6):
        offset_x = random.randint(-10, 10)
        offset_y = random.randint(-5, 5)
        color = random.choice([0xFF0000, 0x880000, 0xFFFFFF, 0x0000FF])
        draw_menu([
            {"text": "ARASAKA", "x": 120 + offset_x, "y": 120 + offset_y, "color": color, "scale": 3, "anchor_point": (0.5, 0.5)},
        ], bg_color=random.choice([0x000000, 0x101010, 0x111111]))
        time.sleep(0.01)

    # Step 3: flicker to black
    draw_menu([], bg_color=0x000000)
    time.sleep(0.2)

    # Step 4: show “Wake up, SAMURAI”
    draw_menu([
        {"text": "Wake up,", "x": 120, "y": 80, "color": 0x00FF00, "scale": 2, "anchor_point": (0.5, 0.5)},
        {"text": "SAMURAI", "x": 120, "y": 130, "color": 0xFFFFFF, "scale": 3, "anchor_point": (0.5, 0.5)},
    ], bg_color=0x000000)

    time.sleep(3)  # hold before switching to idle

# --- boot screen ---
def get_boot_screen():
    return [
        {"text": "ARASAKA", "x": 125, "y": 125, "color": 0xFF0000, "scale": 3, "anchor_point": (0.5, 0.5)},
    ]

def get_wake_screen():
        return [
        {"text": "Wake up,", "x": 120, "y": 80, "color": 0x00FF00, "scale": 2, "anchor_point": (0.5, 0.5)},
        {"text": "SAMURAI", "x": 120, "y": 130, "color": 0xFFFFFF, "scale": 3, "anchor_point": (0.5, 0.5)},
    ]


# --- idle screen ---
def get_idle_screen():
    return [
        {"text": "KMT KB V0.1", "x": 120, "y": 30, "color": 0x00FF00, "scale": 2, "anchor_point": (0.5, 0)},
        {"text": "Caps Lock:", "x": 20, "y": 100, "color": 0x00FF00, "scale": 2},
        {"text": "ON" if menu_state["caps"] else "OFF", "x": 150, "y": 100, "color": 0x00FF00, "scale": 2},
        {"text": "Num Lock:", "x": 20, "y": 140, "color": 0x00FF00, "scale": 2},
        {"text": "ON" if menu_state["num"] else "OFF", "x": 150, "y": 140, "color": 0x00FF00, "scale": 2},
    ]

# --- main menu ---
def get_main_menu(selected=0):
    items = [
        {"text": "Close", "x": 120, "y": 40, "color": 0xFFFFFF, "scale": 2, "anchor_point": (0.5, 0.5)},
        {"text": "Settings", "x": 120, "y": 90, "color": 0xFFFFFF, "scale": 2, "anchor_point": (0.5, 0.5)},
        {"text": "About", "x": 120, "y": 140, "color": 0xFFFFFF, "scale": 2, "anchor_point": (0.5, 0.5)},
    ]

    # highlight current selection
    for i, item in enumerate(items):
        item["highlighted"] = (i == selected)
    return items


def draw_current_screen(selected_index=0):
    """Draw screen based on current_state"""
    if current_state == STATE_BOOT:
        draw_menu(get_boot_screen(), bg_color=0x000000)
    elif current_state == STATE_WAKE:
        draw_menu(get_wake_screen(), bg_color=0x000000)
    elif current_state == STATE_IDLE:
        draw_menu(get_idle_screen(), bg_color=0x000000)
    elif current_state == STATE_MAIN_MENU:
        draw_menu(get_main_menu(selected_index), bg_color=0x000010)
    elif current_state == STATE_SETTINGS:
        draw_menu([
            {"text": "Back", "x": 120, "y": 40, "color": 0xFFFFFF, "scale": 2, "anchor_point": (0.5, 0.5)},
            {"text": "Brightness", "x": 120, "y": 100, "color": 0xFFFFFF, "scale": 2, "anchor_point": (0.5, 0.5)},
        ], bg_color=0x101000)

def set_state(new_state):
    global current_state
    current_state = new_state
    draw_current_screen()

def get_current_state():
    return current_state