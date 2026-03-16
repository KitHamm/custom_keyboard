import sys
import time
import supervisor
from kmk.modules import Module
from kmk.keys import make_key

_HANDSHAKE_INTERVAL = 1.0   # seconds between HANDSHAKE_REQUEST broadcasts
_PING_INTERVAL = 5.0        # seconds between PING keepalives
_PING_TIMEOUT = 15.0        # seconds without PONG before assuming disconnected


def _make_press_handler(get_connected, serial_id):
    def _press(key, keyboard, *args):
        if get_connected():
            print(serial_id)
    return _press


class SerialMacros(Module):
    def __init__(self):
        self.menu = None
        self._buf = ''
        self._connected = False
        self._last_handshake = 0
        self._last_ping_sent = 0
        self._last_pong_received = 0

    def register_macro(self, name, serial_id):
        key = make_key(
            names=(name,),
            on_press=_make_press_handler(lambda: self._connected, serial_id),
        )
        setattr(self, name, key)

    def during_bootup(self, keyboard):
        pass

    def before_matrix_scan(self, keyboard):
        now = time.monotonic()

        # Read incoming serial
        try:
            n = supervisor.runtime.serial_bytes_available
            if n:
                data = sys.stdin.read(n)
                self._buf += data
                while '\n' in self._buf:
                    line, self._buf = self._buf.split('\n', 1)
                    line = line.strip()
                    if line:
                        self._handle_incoming(line, now)
        except Exception:
            pass

        if not self._connected:
            # Broadcast HANDSHAKE_REQUEST until acknowledged
            if now - self._last_handshake >= _HANDSHAKE_INTERVAL:
                self._last_handshake = now
                try:
                    print('HANDSHAKE_REQUEST')
                except Exception:
                    pass
        else:
            # Send PING keepalive
            if now - self._last_ping_sent >= _PING_INTERVAL:
                self._last_ping_sent = now
                try:
                    print('PING')
                except Exception:
                    pass

            # Detect lost connection (no PONG received in time)
            if now - self._last_pong_received >= _PING_TIMEOUT:
                self._set_connected(False)

    def _handle_incoming(self, msg, now):
        if msg == 'HANDSHAKE_ACK':
            self._last_pong_received = now
            self._last_ping_sent = now
            self._set_connected(True)
        elif msg == 'PONG':
            self._last_pong_received = now

    def _set_connected(self, state):
        if self._connected == state:
            return
        self._connected = state
        try:
            from menu_ui import set_connection_state
            set_connection_state(state)
        except Exception:
            pass
        if self.menu and self.menu.get_ui_state() == 'idle':
            try:
                self.menu.return_to_idle()
            except Exception:
                pass

    def after_matrix_scan(self, keyboard):
        pass

    def before_hid_send(self, keyboard):
        pass

    def after_hid_send(self, keyboard):
        pass

    def on_powersave_enable(self, keyboard):
        pass

    def on_powersave_disable(self, keyboard):
        pass
