import time
import board
import busio
import displayio
import terminalio
from adafruit_display_text import label
from adafruit_st7789 import ST7789

try:
    from fourwire import FourWire
except ImportError:
    from displayio import FourWire

# --- Singletons ---
_SPI = None
_DISPLAY = None
_ROOT = None
_BG_TILE = None
_LABELS = []
_LAST_ITEM_COUNT = 0


def _get_spi():
    global _SPI
    if _SPI is None:
        _SPI = busio.SPI(clock=board.D27, MOSI=board.D26)
        while not _SPI.try_lock():
            pass
        _SPI.configure(baudrate=48_000_000, phase=0, polarity=0)
        _SPI.unlock()
    return _SPI


def init_display(cs=board.D33, dc=board.D34, rst=board.D35, rotation=180):
    """Initialize ST7789 once, safely."""
    global _DISPLAY, _ROOT, _BG_TILE
    if _DISPLAY is not None:
        return _DISPLAY

    displayio.release_displays()
    time.sleep(0.05)

    spi = _get_spi()
    bus = FourWire(spi, command=dc, chip_select=cs, reset=rst)

    display = ST7789(
        bus,
        width=240,
        height=240,
        rotation=rotation,
        rowstart=80,
        colstart=0,
    )
    display.auto_refresh = False  # We'll push manually
    _DISPLAY = display

    # Create the persistent root group and background
    _ROOT = displayio.Group()

    bg_bitmap = displayio.Bitmap(240, 240, 1)
    bg_palette = displayio.Palette(1)
    bg_palette[0] = 0x000000
    _BG_TILE = displayio.TileGrid(bg_bitmap, pixel_shader=bg_palette)
    _ROOT.append(_BG_TILE)

    # Attach the root group
    display.root_group = _ROOT
    return display


def draw_menu(items, bg_color=0x000000, highlight_bg=0x005500):
    """Fast menu renderer using cached objects."""
    global _DISPLAY, _ROOT, _BG_TILE, _LABELS, _LAST_ITEM_COUNT

    display = init_display()
    display.auto_refresh = False

    # update background color
    _BG_TILE.pixel_shader[0] = bg_color

    count = len(items)

    # rebuild labels if count changed
    if count != _LAST_ITEM_COUNT:
        # remove old labels from root
        for lbl in _LABELS:
            _ROOT.remove(lbl)
        _LABELS = []
        for _ in range(count):
            lbl = label.Label(terminalio.FONT, text="", color=0xFFFFFF, scale=1)
            _ROOT.append(lbl)
            _LABELS.append(lbl)
        _LAST_ITEM_COUNT = count

    # update label data in place
    for i, item in enumerate(items):
        lbl = _LABELS[i]
        text = str(item.get("text", ""))
        lbl.text = text
        lbl.color = item.get("color", 0xFFFFFF)
        lbl.scale = item.get("scale", 1)
        lbl.anchor_point = item.get("anchor_point", (0, 0))
        lbl.anchored_position = (item.get("x", 0), item.get("y", 0))

        # crude highlight handling — tint highlighted items
        if item.get("highlighted", False):
            lbl.color = highlight_bg

    # ensure our group is the active one (fixes stuck Arasaka logo)
    if _DISPLAY.root_group is not _ROOT:
        _DISPLAY.root_group = _ROOT

    # manual push
    _DISPLAY.refresh()
