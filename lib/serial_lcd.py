# lib/modules/serial_lcd.py
import board
import busio

uart = busio.UART(board.D1, None, baudrate=115200)

def send(msg: str):
    """Send a text line to the Pro Micro LCD controller."""
    if not msg.endswith("\n"):
        msg += "\n"
    uart.write(msg.encode("utf-8"))
    print(f"Sent to LCD: {msg.strip()}")
